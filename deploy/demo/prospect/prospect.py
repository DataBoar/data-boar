#!/usr/bin/env python3
"""prospect-up/down: ephemeral per-prospect Data Boar pod in the dashboard slot (#2280).

Design: ``docs/desenho/2280.1.md``. Host-only Linux script, standard library only
(Python 3.11+), installed by the ``demo_prospect`` role under ``~/demo/prospect/bin``.
Subcommands: ``up``, ``down``, ``list``, ``reap``, ``restore-slot``, ``teardown``.

Operator messages are pt-BR (the operator's language); one line each on stderr, never
with a secret. Every side effect goes through the seams of section 15 (``Context``).
"""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import http.client
import json
import os
import re
import secrets
import shutil
import socket
import ssl
import subprocess
import sys
import time
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, TextIO

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_LEFTOVERS = 3
EXIT_BUSY = 4
EXIT_PREREQ = 5
EXIT_PROXY = 6
EXIT_UNHEALTHY = 7
EXIT_SLOT = 8

TEMPLATES = Path(__file__).resolve().parent
LABEL = "databoar.prospect"
UNIT_PREFIX = "demo-prospect@"
POD_PREFIX = "prospect-"
USER = "prospect"
MIN_OPERATOR_PASSWORD_CHARS = 20
MAX_OPERATOR_PASSWORD_UTF8_BYTES = 72
POD_MEMORY_MIB = 700
SLOT_HEALTH_S = 180
POD_HEALTH_S = 120
MEM_WAIT_S = 15
REAP_GRACE_S = 60
POLL_S = 3.0
ROUTE_WAIT_S = 15
ALERT_TAG = "databoar-prospect"

_SLUG = re.compile(r"^[a-z][a-z0-9-]{1,18}[a-z0-9]$")
_RESERVED = frozenset(
    {"dashboard", "apresentacao", "www", "api", "admin", "status", "mail", "demo"}
    | {"prospect"}
)
_TTL = re.compile(r"^([1-9][0-9]{0,2})([mh])$")
_DOMAIN = re.compile(
    r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+$"
)
_PATH = re.compile(r"^/[^\n:,]+$")
_PROXY_DIR = re.compile(r"^/[A-Za-z0-9._/-]+$")
_BCRYPT = re.compile(r"^\$2[aby]\$\d{2}\$[./A-Za-z0-9]{53}$")
_API_KEY = re.compile(r"^[0-9a-f]{64}$")
_ENV_KEY = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_PLACEHOLDER = re.compile(r"\$\{([a-z_]+)\}")
_SEED_KEY = "DATA_BOAR_MACHINE_SEED"
_ALLOWED_LICENSE = {"enforced": ("VALID", "GRACE"), "open": ("OPEN",)}


class CliError(Exception):
    """A one-line error for stderr with its exit code."""

    def __init__(self, code: int, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _read_operator_password(ctx: Context) -> str:
    stream = ctx.in_
    if stream is None:
        raise CliError(
            EXIT_USAGE,
            "stdin indisponível: envie a senha pelo stdin com --password-stdin",
        )
    try:
        raw = stream.readline()
    except UnicodeDecodeError:
        raise CliError(
            EXIT_USAGE, "senha ilegível: envie texto UTF-8 pelo stdin"
        ) from None
    except ValueError:
        raise CliError(
            EXIT_USAGE,
            "stdin indisponível: envie a senha pelo stdin com --password-stdin",
        ) from None
    except OSError:
        raise CliError(
            EXIT_USAGE,
            "stdin indisponível: envie a senha pelo stdin com --password-stdin",
        ) from None
    if raw == "":
        raise CliError(EXIT_USAGE, "senha vazia: envie pelo stdin com --password-stdin")
    if any(0xD800 <= ord(ch) <= 0xDFFF for ch in raw):
        raise CliError(EXIT_USAGE, "senha ilegível: envie texto UTF-8 pelo stdin")
    try:
        raw.encode("utf-8")
    except UnicodeEncodeError:
        raise CliError(
            EXIT_USAGE, "senha ilegível: envie texto UTF-8 pelo stdin"
        ) from None
    password = raw.rstrip("\r\n")
    if len(password) < MIN_OPERATOR_PASSWORD_CHARS:
        raise CliError(
            EXIT_USAGE,
            f"senha precisa de pelo menos {MIN_OPERATOR_PASSWORD_CHARS} caracteres",
        )
    if len(password.encode("utf-8")) > MAX_OPERATOR_PASSWORD_UTF8_BYTES:
        raise CliError(EXIT_USAGE, "senha precisa ter no máximo 72 bytes em UTF-8")
    return password


class Occupied:
    """Third outcome of ``restore_slot`` (design revision 2, DEC-20): a prospect pod is
    alive, so the slot was left as it was. It is neither 0 (restored) nor 8 (did not
    come back); the caller prints the line and exits 0 (or 3 with leftovers)."""

    def __init__(self, occupants: list[str]) -> None:
        self.occupants = occupants

    @property
    def line(self) -> str:
        return "dashboard não religada: slot ocupado por " + ", ".join(self.occupants)


_OCCUPYING_UNIT = ("active", "activating", "reloading")


def _stamp(dt: datetime) -> str:
    """UTC, no fraction, ``Z`` suffix (never ``isoformat()``, which gives ``+00:00``)."""
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_stamp(text: str) -> datetime:
    return datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)


# --------------------------------------------------------------------------- slug, TTL
def validate_slug(slug: str, reserved: Iterable[str] = ()) -> str:
    """Section 2. Syntax first; reserved names (built-in plus inventory) after."""
    if not isinstance(slug, str) or not _SLUG.fullmatch(slug) or "--" in slug:
        raise CliError(
            EXIT_USAGE, "slug inválido: use de 3 a 20 caracteres [a-z0-9-], sem ponto"
        )
    if slug in _RESERVED or slug in set(reserved):
        raise CliError(EXIT_USAGE, f"slug reservado: {slug}")
    return slug


def parse_ttl(text: str) -> int:
    """``--ttl`` with an ``m`` or ``h`` suffix, from 5m to 90m (P-2)."""
    m = _TTL.fullmatch(text or "")
    if not m:
        raise CliError(EXIT_USAGE, "ttl inválido: use <n>m ou <n>h, de 5m a 90m")
    seconds = int(m.group(1)) * (60 if m.group(2) == "m" else 3600)
    if not 300 <= seconds <= 5400:
        raise CliError(EXIT_USAGE, "ttl inválido: use <n>m ou <n>h, de 5m a 90m")
    return seconds


# --------------------------------------------------------------------------- inventory
_INV_SCHEMA: dict[str, tuple[str, bool, Any]] = {
    # key: (type, required, default)
    "prospect_domain": ("domain", True, None),
    "prospect_port": ("int", False, 18100),
    "prospect_proxy_port": ("int", False, 443),
    "prospect_proxy_container": ("name", True, None),
    "prospect_tls_line": ("tls", True, None),
    "prospect_caddy_dir": ("path", True, None),
    "prospect_caddy_dir_in_proxy": ("proxydir", False, "/etc/caddy/prospects"),
    "prospect_caddy_admin_socket": ("path", True, None),
    "prospect_caddyfile": ("path", True, None),
    "prospect_corpus_dir": ("dir", True, None),
    "prospect_extras_dir": ("dir", False, None),
    "prospect_profile_file": ("file", True, None),
    "prospect_recommendations_file": ("file", True, None),
    "prospect_license_mode": ("license_mode", False, "enforced"),
    "prospect_license_file": ("file", False, None),
    "prospect_base_env": ("file", True, None),
    "prospect_reserve": ("int", False, 128),
    "prospect_slot_container": ("name", False, "dashboard"),
    "prospect_slot_mode": ("slot_mode", False, "podman"),
    "prospect_slot_health_url": ("health_url", False, "https://127.0.0.1:8088/status"),
    "prospect_protected_containers": ("names", False, ["apresentacao"]),
    "prospect_alert_cmd": ("exe", False, None),
    "prospect_alert_path": ("path", False, None),
    "prospect_reserved_slugs": ("names", False, []),
    "prospect_image": ("str", False, None),
    "prospect_license_hostname": ("str", False, None),
}
_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")


def _bad(key: str, why: str) -> CliError:
    return CliError(EXIT_PREREQ, f"inventário: {key}: {why}")


def _check_value(key: str, kind: str, value: Any) -> Any:  # noqa: C901
    if kind == "int":
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise _bad(key, "precisa ser um inteiro positivo")
        return value
    if kind == "names":
        if not isinstance(value, list) or not all(
            isinstance(v, str) and _NAME.fullmatch(v) for v in value
        ):
            raise _bad(key, "precisa ser uma lista de nomes")
        return list(value)
    if not isinstance(value, str):
        raise _bad(key, "precisa ser um texto")
    if kind == "str":
        if "\n" in value:
            raise _bad(key, "não pode ter quebra de linha")
        return value
    if kind == "name":
        if not _NAME.fullmatch(value):
            raise _bad(key, "nome inválido")
        return value
    if kind == "domain":
        if not _DOMAIN.fullmatch(value):
            raise _bad(key, "domínio inválido")
        return value
    if kind == "tls":
        try:
            _check_tls_line(value, key)
        except ValueError:
            raise _bad(
                key, "precisa ser uma linha 'tls ...' sem {, }, # nem quebra"
            ) from None
        return value
    if kind == "proxydir":
        if not _PROXY_DIR.fullmatch(value):
            raise _bad(key, "caminho absoluto inválido")
        return value
    if kind == "license_mode":
        if value not in _ALLOWED_LICENSE:
            raise _bad(key, "use enforced ou open")
        return value
    if kind == "slot_mode":
        if value not in ("podman", "systemd"):
            raise _bad(key, "use podman ou systemd")
        return value
    if kind == "health_url":
        if not re.fullmatch(r"https://127\.0\.0\.1:\d{1,5}/[A-Za-z0-9/_-]*", value):
            raise _bad(key, "precisa ser https://127.0.0.1:<porta>/...")
        return value
    # path kinds
    if not _PATH.fullmatch(value):
        raise _bad(
            key, "precisa ser um caminho absoluto sem ':', ',' nem quebra de linha"
        )
    p = Path(value)
    if kind == "dir" and not p.is_dir():
        raise _bad(key, "diretório não existe")
    if kind == "file" and not p.is_file():
        raise _bad(key, "arquivo não existe")
    if kind == "exe" and not (p.is_file() and os.access(p, os.X_OK)):
        raise _bad(key, "executável não existe")
    return value


def load_inventory(path: Path) -> dict[str, Any]:
    """Section 16: one closed-schema JSON object, mode 0600 or 0400."""
    try:
        st = path.stat()
    except OSError:
        raise CliError(EXIT_PREREQ, "inventário ausente") from None
    if st.st_mode & 0o777 not in (0o600, 0o400):
        raise CliError(EXIT_PREREQ, "inventário legível por grupo ou outros (use 0600)")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError):
        raise CliError(EXIT_PREREQ, "inventário não é JSON válido") from None
    if not isinstance(data, dict):
        raise CliError(EXIT_PREREQ, "inventário precisa ser um objeto JSON")
    for key in sorted(data):
        if key not in _INV_SCHEMA:
            raise _bad(str(key)[:64], "chave desconhecida")
    inv: dict[str, Any] = {}
    for key, (kind, required, default) in _INV_SCHEMA.items():
        if key not in data or data[key] is None:
            if required:
                raise _bad(key, "chave obrigatória ausente")
            inv[key] = default
            continue
        inv[key] = _check_value(key, kind, data[key])
    if inv["prospect_slot_container"] in inv["prospect_protected_containers"]:
        raise _bad("prospect_slot_container", "não pode ser um contêiner protegido")
    if inv["prospect_license_mode"] == "enforced" and not inv["prospect_license_file"]:
        raise _bad(
            "prospect_license_file", "obrigatória com prospect_license_mode enforced"
        )
    return inv


# --------------------------------------------------------------------------- rendering
def render_ttl_dropin(ttl_s: int) -> str:
    return f"[Service]\nRuntimeMaxSec={int(ttl_s)}\n"


def _read_base_env(path: str) -> dict[str, str]:
    """Section 7: the prospect base env may hold only DATA_BOAR_MACHINE_SEED."""
    if Path(path).parts[-2:] == ("demo", "env"):  # the public demo env file
        raise _bad("prospect_base_env", "o env da demo pública nunca é usado")
    out: dict[str, str] = {}
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        key, sep, value = line.partition("=")
        key = key.strip()
        if not sep or not _ENV_KEY.fullmatch(key):
            raise _bad("prospect_base_env", "linha fora do formato CHAVE=valor")
        if key != _SEED_KEY:
            raise _bad("prospect_base_env", f"chave fora da allowlist: {key}")
        out[key] = value
    return out


def render_pod_env(api_key: str, inventory: dict[str, Any]) -> str:
    if not _API_KEY.fullmatch(api_key):
        raise ValueError("api key")
    base = _read_base_env(inventory["prospect_base_env"])
    mode = inventory["prospect_license_mode"]
    lines = [
        "CONFIG_PATH=/cfg/config.yaml",
        f"PROSPECT_API_KEY={api_key}",
        f"DATA_BOAR_LICENSE_MODE={mode}",
    ]
    if mode == "enforced":
        lines.append(
            f"DATA_BOAR_LICENSE_PATH=/lic/{Path(inventory['prospect_license_file']).name}"
        )
    lines.append("DATA_BOAR_CREDENTIAL_STRICT=1")
    if _SEED_KEY in base:
        lines.append(f"{_SEED_KEY}={base[_SEED_KEY]}")
    return "\n".join(lines) + "\n"


def render_state_env(port: int, corpus_dir: str, extras_dir: str) -> str:
    for value in (corpus_dir, extras_dir):
        if not _PATH.fullmatch(value) or not Path(value).is_dir():
            raise CliError(EXIT_PREREQ, "caminho de pasta compartilhada inválido")
    return (
        f"PROSPECT_PORT={int(port)}\n"
        f"PROSPECT_CORPUS_DIR={corpus_dir}\n"
        f"PROSPECT_EXTRAS_DIR={extras_dir}\n"
    )


def _fill(template: str, fields: dict[str, str]) -> str:
    def sub(m: re.Match[str]) -> str:
        if m.group(1) not in fields:
            raise ValueError(f"campo sem valor: {m.group(1)}")
        return fields[m.group(1)]

    text = _PLACEHOLDER.sub(sub, template)
    if "${" in text:
        raise ValueError("sobrou ${ no template")
    return text


def render_config(slug: str, inventory: dict[str, Any]) -> str:
    validate_slug(slug)
    domain = inventory["prospect_domain"]
    if not _DOMAIN.fullmatch(domain):
        raise ValueError("domain")
    template = (TEMPLATES / "config.prospect.yaml").read_text(encoding="utf-8")
    return _fill(template, {"trusted_host": f"{slug}.{domain}"})


def _check_tls_line(value: str, key: str = "tls_line") -> None:
    if (
        not isinstance(value, str)
        or not value.startswith("tls ")
        or any(ch in value for ch in "{}#\n\r")
    ):
        raise ValueError(f"{key} fora do formato")


def render_site(
    *,
    slug: str,
    domain: str,
    proxy_port: int,
    pod_port: int,
    tls_line: str,
    bcrypt_hash: str,
    api_key: str,
    caddy_dir_in_proxy: str,
) -> str:
    """Section 10: fixed template, every field validated; ValueError otherwise."""
    if not isinstance(slug, str) or not _SLUG.fullmatch(slug) or "--" in slug:
        raise ValueError("slug")
    if not isinstance(domain, str) or not _DOMAIN.fullmatch(domain):
        raise ValueError("domain")
    for port in (proxy_port, pod_port):
        if isinstance(port, bool) or not isinstance(port, int) or not 0 < port < 65536:
            raise ValueError("port")
    _check_tls_line(tls_line)
    if not isinstance(bcrypt_hash, str) or not _BCRYPT.fullmatch(bcrypt_hash):
        raise ValueError("hash")
    if not isinstance(api_key, str) or not _API_KEY.fullmatch(api_key):
        raise ValueError("api key")
    if not isinstance(caddy_dir_in_proxy, str) or not _PROXY_DIR.fullmatch(
        caddy_dir_in_proxy
    ):
        raise ValueError("caddy_dir_in_proxy")
    template = (TEMPLATES / "site.caddy.tmpl").read_text(encoding="utf-8")
    return _fill(
        template,
        {
            "host": f"{slug}.{domain}",
            "proxy_port": str(proxy_port),
            "tls_line": tls_line,
            "bcrypt_hash": bcrypt_hash,
            "pod_port": str(pod_port),
            "api_key": api_key,
            "caddy_dir_in_proxy": caddy_dir_in_proxy.rstrip("/"),
            "slug": slug,
        },
    )


def openssl_argv(slug: str, directory: Path) -> list[str]:
    """Section 9: self-signed EC P-256, CN and SAN prospect-<slug>, 2 days."""
    validate_slug(slug)
    name = f"{POD_PREFIX}{slug}"
    return [
        "openssl", "req", "-x509", "-newkey", "ec",
        "-pkeyopt", "ec_paramgen_curve:prime256v1", "-nodes",
        "-keyout", str(directory / "tls.key"), "-out", str(directory / "tls.crt"),
        "-days", "2", "-subj", f"/CN={name}", "-addext", f"subjectAltName=DNS:{name}",
    ]  # fmt: skip


# --------------------------------------------------------------------------- real seams
class Runner:
    """Runs a command without a shell: ``run(argv, input=None) -> (rc, stdout, stderr)``."""

    def __init__(self, timeout: float = 300.0) -> None:
        self.timeout = timeout

    def run(self, argv: list[str], input: str | None = None) -> tuple[int, str, str]:
        try:
            proc = subprocess.run(  # noqa: S603 - argv list, no shell
                argv,
                input=input,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="strict",
                timeout=self.timeout,
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            return 127, "", type(exc).__name__
        return proc.returncode, proc.stdout, proc.stderr


class _UnixHTTPConnection(http.client.HTTPConnection):
    def __init__(self, path: str, timeout: float = 30.0) -> None:
        super().__init__("localhost", timeout=timeout)
        self._path = path

    def connect(self) -> None:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        try:
            sock.connect(self._path)
        except OSError:
            sock.close()
            raise
        self.sock = sock


class AdminClient:
    """``POST /load`` of a Caddyfile on the proxy admin unix socket; 0 = no connection."""

    def __init__(self, socket_path: str) -> None:
        self.socket_path = socket_path

    def load(self, text: str) -> int:
        conn = _UnixHTTPConnection(self.socket_path)
        try:
            conn.request(
                "POST",
                "/load",
                body=text.encode("utf-8"),
                headers={"Content-Type": "text/caddyfile"},
            )
            resp = conn.getresponse()
            resp.read()
            return resp.status
        except (OSError, http.client.HTTPException):
            return 0
        finally:
            conn.close()


class _SNIHTTPSConnection(http.client.HTTPSConnection):
    """HTTPS to 127.0.0.1 with a chosen SNI and Host (route check through the proxy)."""

    def __init__(self, sni: str, port: int, context: ssl.SSLContext) -> None:
        super().__init__(sni, port, timeout=10, context=context)
        self._sni = sni
        self._ctx = context

    def connect(self) -> None:
        raw = socket.create_connection(("127.0.0.1", self.port), self.timeout)
        try:
            self.sock = self._ctx.wrap_socket(raw, server_hostname=self._sni)
        except OSError:
            raw.close()
            raise


class HealthProbe:
    """Loopback HTTPS probes: ``/status`` of the pod or the slot, and the route check."""

    @staticmethod
    def _loopback_only(url: str) -> tuple[int, str]:
        m = re.fullmatch(r"https://127\.0\.0\.1:(\d{1,5})(/[A-Za-z0-9/_-]*)", url)
        if not m:
            raise ValueError("só https no loopback")
        return int(m.group(1)), m.group(2)

    def status(
        self, url: str, key: str | None = None, cafile: str | None = None
    ) -> dict | None:
        port, path = self._loopback_only(url)
        ctx = (
            ssl.create_default_context(cafile=cafile)
            if cafile
            else ssl.create_default_context()
        )
        # Pinned self-signed pod certificate (cafile): chain verified, the name is
        # prospect-<slug>, not 127.0.0.1. Slot probe: loopback only, no verification.
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        ctx.check_hostname = False
        if not cafile:
            ctx.verify_mode = ssl.CERT_NONE
        conn = http.client.HTTPSConnection("127.0.0.1", port, timeout=10, context=ctx)
        try:
            conn.request("GET", path, headers={"X-API-Key": key} if key else {})
            resp = conn.getresponse()
            body = resp.read()
            if resp.status != 200:
                return None
            data = json.loads(body.decode("utf-8"))
            return data if isinstance(data, dict) else None
        except (OSError, ValueError, http.client.HTTPException):
            return None
        finally:
            conn.close()

    def route_status(self, host: str, port: int) -> int:
        ctx = ssl.create_default_context()
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        # Route check through the local proxy (loopback only): any certificate.
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        conn = _SNIHTTPSConnection(host, port, ctx)
        try:
            conn.request("GET", "/", headers={"Host": host})
            resp = conn.getresponse()
            resp.read()
            return resp.status
        except (OSError, http.client.HTTPException):
            return 0
        finally:
            conn.close()


class Alerter:
    """journal ``err`` line plus the operator's optional notifier."""

    def __init__(self, runner: Runner, alert_cmd: str | None = None) -> None:
        self.runner = runner
        self.alert_cmd = alert_cmd

    def emit(self, msg: str) -> None:
        self.runner.run(["systemd-cat", "-t", ALERT_TAG, "-p", "err"], input=msg + "\n")
        if self.alert_cmd:
            self.runner.run([self.alert_cmd, msg])

    def info(self, msg: str) -> None:
        self.runner.run(
            ["systemd-cat", "-t", ALERT_TAG, "-p", "info"], input=msg + "\n"
        )


def _meminfo_mib() -> int:
    with open("/proc/meminfo", encoding="ascii") as fh:
        for line in fh:
            if line.startswith("MemAvailable:"):
                return int(line.split()[1]) // 1024
    return 0


def _port_busy(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", port))
        except OSError:
            return True
    return False


@dataclass
class Context:
    """Every side effect of the CLI goes through these seams (design, section 15)."""

    runner: Any
    admin: Any
    probe: Any
    alerter: Any
    clock: Callable[[], datetime]
    sleep: Callable[[float], None]
    meminfo: Callable[[], int]
    port_busy: Callable[[int], bool]
    which: Callable[[str], str | None]
    runtime_dir: Path
    systemd_runtime_dir: Path
    quadlet_dir: Path
    home: Path
    inventory_path: Path | None = None
    lock_timeout_up: float = 30.0
    lock_timeout_reap: float = 60.0
    out: TextIO = field(default_factory=lambda: sys.stdout)
    err: TextIO = field(default_factory=lambda: sys.stderr)
    in_: TextIO = field(default_factory=lambda: sys.stdin)

    @classmethod
    def from_env(cls) -> Context:
        home = Path.home()
        runtime = Path(os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}")
        config_home = Path(os.environ.get("XDG_CONFIG_HOME") or home / ".config")
        runner = Runner()
        return cls(
            runner=runner,
            admin=None,
            probe=HealthProbe(),
            alerter=None,
            clock=lambda: datetime.now(UTC),
            sleep=time.sleep,
            meminfo=_meminfo_mib,
            port_busy=_port_busy,
            which=shutil.which,
            runtime_dir=runtime,
            systemd_runtime_dir=runtime / "systemd" / "user",
            quadlet_dir=config_home / "containers" / "systemd",
            home=home,
        )


# --------------------------------------------------------------------------- the CLI
class Cli:
    def __init__(self, ctx: Context, inv: dict[str, Any]) -> None:
        self.ctx = ctx
        self.inv = inv
        self.base = ctx.runtime_dir / "demo-prospect"
        self.caddy_dir = Path(inv["prospect_caddy_dir"])
        alert = inv["prospect_alert_path"] or str(
            ctx.home / "demo" / "prospect" / "ALERT"
        )
        self.alert_path = Path(alert)
        if ctx.admin is None:
            ctx.admin = AdminClient(inv["prospect_caddy_admin_socket"])
        if ctx.alerter is None:
            ctx.alerter = Alerter(ctx.runner, inv["prospect_alert_cmd"])
        self.dash = inv["prospect_slot_container"]
        self.protected = set(inv["prospect_protected_containers"])

    # -- output
    def say(self, text: str) -> None:
        print(text, file=self.ctx.out)

    def run(self, argv: list[str], input: str | None = None) -> tuple[int, str, str]:
        # D-39: nothing but `podman ps`/`podman inspect` ever names a protected container.
        if self.protected & set(argv) and argv[:2] not in (
            ["podman", "ps"],
            ["podman", "inspect"],
        ):
            raise CliError(EXIT_PREREQ, "recusado: comando contra contêiner protegido")
        return self.ctx.runner.run(argv, input)

    # -- files
    def _mkdir(self, path: Path, mode: int = 0o700) -> None:
        path.mkdir(parents=True, exist_ok=True)
        path.chmod(mode)

    def write(self, path: Path, text: str | bytes, mode: int) -> None:
        """Atomic write with the final mode set before the rename."""
        tmp = path.with_name(f".{path.name}.tmp")
        data = text.encode("utf-8") if isinstance(text, str) else text
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode)
        try:
            with os.fdopen(fd, "wb") as fh:
                fh.write(data)
            os.chmod(tmp, mode)
            os.replace(tmp, path)
        except BaseException:
            tmp.unlink(missing_ok=True)
            raise

    def slug_dir(self, slug: str) -> Path:
        return self.base / slug

    def ttl_dropin(self, slug: str) -> Path:
        return (
            self.ctx.systemd_runtime_dir
            / f"{UNIT_PREFIX}{slug}.service.d"
            / "10-ttl.conf"
        )

    @staticmethod
    def unit(slug: str) -> str:
        return f"{UNIT_PREFIX}{slug}.service"

    def read_json(self, path: Path) -> dict[str, Any] | None:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        return data if isinstance(data, dict) else None

    def state(self, slug: str) -> dict[str, Any] | None:
        return self.read_json(self.slug_dir(slug) / "state.json")

    def slot(self) -> dict[str, Any] | None:
        return self.read_json(self.base / "slot.json")

    def write_slot(self, record: dict[str, Any]) -> None:
        self._mkdir(self.base)
        self.write(
            self.base / "slot.json", json.dumps(record, sort_keys=True) + "\n", 0o600
        )

    def now(self) -> datetime:
        return self.ctx.clock()

    # -- lock (DEC-17): blocking with a deadline for up/down/reap, non-blocking --from-unit
    @contextlib.contextmanager
    def lock(self, timeout: float | None) -> Iterator[bool]:
        self._mkdir(self.base)
        path = self.base / ".lock"
        fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
        acquired = False
        try:
            deadline = time.monotonic() + (timeout or 0)
            while True:
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    acquired = True
                    break
                except BlockingIOError:
                    if timeout is None or time.monotonic() >= deadline:
                        break
                    time.sleep(0.1)
            yield acquired
        finally:
            if acquired:
                fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)

    # -- host queries (reads)
    def containers(self, label: str | None = None) -> list[dict[str, Any]]:
        argv = ["podman", "ps", "-a", "--format", "json"]
        if label is not None:
            argv += ["--filter", f"label={label}"]
        rc, out, _ = self.run(argv)
        if rc != 0:
            raise CliError(EXIT_PREREQ, "podman ps falhou")
        try:
            data = json.loads(out or "[]")
        except ValueError:
            raise CliError(EXIT_PREREQ, "podman ps devolveu JSON inválido") from None
        return data if isinstance(data, list) else []

    @staticmethod
    def _name(c: dict[str, Any]) -> str:
        names = c.get("Names") or []
        return str(names[0] if isinstance(names, list) and names else names)

    def container_state(self, name: str) -> str | None:
        for c in self.containers():
            if self._name(c) == name:
                return str(c.get("State", "")).lower()
        return None

    def running_instances(self) -> list[str]:
        image = self.inv["prospect_image"]
        out = []
        for c in self.containers():
            if str(c.get("State", "")).lower() != "running":
                continue
            img = str(c.get("Image", ""))
            if "data_boar" in img or (image and img == image):
                out.append(self._name(c))
        return out

    def unit_state(self, slug: str) -> str:
        _, out, _ = self.run(["systemctl", "--user", "is-active", self.unit(slug)])
        return out.strip() or "unknown"

    def timer_active(self) -> bool:
        rc, out, _ = self.run(["systemctl", "--user", "is-active", "demo-reset.timer"])
        return rc == 0 and out.strip() == "active"

    def network_exists(self, slug: str) -> bool:
        rc, _, _ = self.run(["podman", "network", "exists", f"{POD_PREFIX}{slug}"])
        return rc == 0

    def labelled_networks(self) -> list[tuple[str, str]]:
        rc, out, _ = self.run(
            [
                "podman",
                "network",
                "ls",
                "--format",
                "json",
                "--filter",
                f"label={LABEL}",
            ]
        )
        result = []
        if rc == 0:
            try:
                for n in json.loads(out or "[]"):
                    name = str(n.get("name") or n.get("Name") or "")
                    labels = n.get("labels") or n.get("Labels") or {}
                    result.append((name, str(labels.get(LABEL, ""))))
            except (ValueError, AttributeError):
                pass
        return result

    def labelled_volumes(self, slug: str) -> list[str]:
        rc, out, _ = self.run(
            [
                "podman",
                "volume",
                "ls",
                "--format",
                "json",
                "--filter",
                f"label={LABEL}={slug}",
            ]
        )
        if rc != 0:
            return []
        try:
            return [
                str(v.get("Name") or v.get("name")) for v in json.loads(out or "[]")
            ]
        except (ValueError, AttributeError):
            return []

    def active(self, slug: str) -> bool:
        st = self.state(slug)
        if not st or "expires_at" not in st:
            return False
        try:
            expired = self.now() >= _parse_stamp(str(st["expires_at"]))
        except ValueError:
            return False
        return not expired and self.unit_state(slug) == "active"

    def known_slugs(self) -> list[str]:
        if not self.base.is_dir():
            return []
        return sorted(
            p.name
            for p in self.base.iterdir()
            if p.is_dir() and _SLUG.fullmatch(p.name)
        )

    # -- prerequisites (exit 5)
    def prerequisites(self) -> None:
        missing = None
        dropin = self.ctx.quadlet_dir / "demo-prospect@.container.d" / "10-host.conf"
        if sys.version_info < (3, 11):
            missing = "python3 3.11 ou mais"
        elif not dropin.is_file():
            missing = "drop-in de imagem e hostname (10-host.conf)"
        elif not Path(self.inv["prospect_caddy_admin_socket"]).exists():
            missing = "socket do proxy (prospect_caddy_admin_socket)"
        elif not Path(self.inv["prospect_caddyfile"]).is_file():
            missing = "Caddyfile do proxy (prospect_caddyfile)"
        elif not Path(self.inv["prospect_caddy_dir"]).is_dir():
            missing = "diretório de fragmentos (prospect_caddy_dir)"
        else:
            for tool in ("systemd-run", "openssl", "podman"):
                if not self.ctx.which(tool):
                    missing = tool
                    break
        if missing is None:
            rc, out, _ = self.run(
                ["podman", "version", "--format", "{{.Client.Version}}"]
            )
            m = re.match(r"(\d+)\.", out.strip())
            if rc != 0 or not m or int(m.group(1)) < 5:
                missing = "Podman 5.0 ou mais"
        if missing is not None:
            raise CliError(EXIT_PREREQ, f"pré-requisito ausente: {missing}")
        _read_base_env(self.inv["prospect_base_env"])

    # -- slot (section 3)
    def stop_slot(self) -> int:
        if self.inv["prospect_slot_mode"] == "systemd":
            argv = ["systemctl", "--user", "stop", f"{self.dash}.service"]
        else:
            argv = ["podman", "stop", "-t", "20", self.dash]
        return self.run(argv)[0]

    def slot_occupants(self) -> list[str]:
        """Section 3, step 0: slugs with a running labelled container, or whose unit is
        active/activating/reloading, read from the host (not from the caller's intent)."""
        slugs = set(self.known_slugs())
        running: set[str] = set()
        for c in self.containers(LABEL):
            value = str((c.get("Labels") or {}).get(LABEL, ""))
            if not _SLUG.fullmatch(value):
                continue
            slugs.add(value)
            if str(c.get("State", "")).lower() == "running":
                running.add(value)
        out = []
        for slug in sorted(slugs):
            if slug in running or self.unit_state(slug) in _OCCUPYING_UNIT:
                exp = (self.state(slug) or {}).get("expires_at")
                out.append(f"{slug} até {exp}" if exp else slug)
        return out

    def restore_slot(self, slug_hint: str | None = None) -> int | Occupied:
        occupants = self.slot_occupants()
        if occupants:  # no write at all: slot.json and ALERT stay byte for byte
            return Occupied(occupants)
        slot = self.slot()
        slug = slug_hint or (slot or {}).get("taken_by") or "desconhecida"
        if self.inv["prospect_slot_mode"] == "systemd":
            argv = ["systemctl", "--user", "start", f"{self.dash}.service"]
        else:
            epoch = int(self.now().timestamp())
            argv = [
                "systemd-run", "--user", "--scope", "--collect",
                f"--unit=databoar-slot-{epoch}", "podman", "start", self.dash,
            ]  # fmt: skip
        rc, _, _ = self.run(argv)
        if rc != 0:
            return self._slot_failed(slot, str(slug), f"start falhou (rc={rc})")
        if slot and slot.get("reset_timer_was_active"):
            self.run(["systemctl", "--user", "start", "demo-reset.timer"])
        if self._wait_slot_health():
            (self.base / "slot.json").unlink(missing_ok=True)
            if self.alert_path.exists():
                self.alert_path.unlink(missing_ok=True)
                self.ctx.alerter.info(
                    f"dashboard recuperada após a sessão de prospecto {slug}"
                )
            return EXIT_OK
        return self._slot_failed(slot, str(slug), "saúde não confirmada em 180 s")

    def _wait_slot_health(self) -> bool:
        url = self.inv["prospect_slot_health_url"]
        deadline = self.now() + timedelta(seconds=SLOT_HEALTH_S)
        while True:
            st = self.ctx.probe.status(url)
            integrity = (st or {}).get("integrity")
            if (
                st
                and st.get("trust_state") == "trusted"
                and isinstance(integrity, dict)
                and integrity.get("integrity_state") == "validated"
            ):
                return True
            if self.now() >= deadline:
                return False
            self.ctx.sleep(POLL_S)

    def _slot_failed(self, slot: dict[str, Any] | None, slug: str, reason: str) -> int:
        now = _stamp(self.now())
        record = dict(slot or {"slot": self.dash, "taken_by": slug, "taken_at": now})
        record.setdefault("mode", self.inv["prospect_slot_mode"])
        record["restore_failed_at"] = now
        self.write_slot(record)
        if not self.alert_path.exists():  # one alert per incident (DEC-18)
            self._mkdir(self.alert_path.parent)
            self.write(self.alert_path, f"ALERT {now} sessão {slug}: {reason}\n", 0o600)
            self.ctx.alerter.emit(
                f"dashboard não voltou após a sessão de prospecto {slug}: {reason}"
            )
        print(f"dashboard FORA DO AR: {reason}", file=self.ctx.err)
        return EXIT_SLOT

    # -- teardown (section 11)
    def leftovers(self, slug: str) -> bool:
        return bool(
            self.slug_dir(slug).exists()
            or list(self.caddy_dir.glob(f"{slug}.caddy"))
            or list(self.caddy_dir.glob(f"{slug}.crt"))
            or self.ttl_dropin(slug).exists()
            or self.containers(f"{LABEL}={slug}")
            or self.network_exists(slug)
            or self.unit_state(slug)
            in ("active", "failed", "activating", "deactivating")
        )

    def teardown(self, slug: str, *, from_unit: bool = False) -> list[str]:
        """Idempotent; returns the leftovers (empty = clean)."""
        rest: list[str] = []
        removed_fragment = False
        for suffix in (".caddy", ".crt"):
            p = self.caddy_dir / f"{slug}{suffix}"
            if p.exists():
                p.unlink()
                removed_fragment = True
        if removed_fragment and self.reload_proxy() != 200:
            rest.append("rota pode persistir até o próximo recarregamento")
        dropin = self.ttl_dropin(slug)
        dropin.unlink(missing_ok=True)
        with contextlib.suppress(OSError):
            dropin.parent.rmdir()
        rc, _, _ = self.run(
            ["podman", "rm", "-f", "-i", "--filter", f"label={LABEL}={slug}"]
        )
        if rc != 0:
            rest.append(f"contêiner {POD_PREFIX}{slug}")
        if self.network_exists(slug):
            rc, _, _ = self.run(
                ["podman", "network", "rm", "-f", f"{POD_PREFIX}{slug}"]
            )
            if rc != 0:
                rest.append(f"rede {POD_PREFIX}{slug}")
        for vol in self.labelled_volumes(slug):
            rc, _, _ = self.run(["podman", "volume", "rm", "-f", vol])
            if rc != 0:
                rest.append(f"volume {vol}")
        shutil.rmtree(self.slug_dir(slug), ignore_errors=True)
        if self.slug_dir(slug).exists():
            rest.append(f"estado {slug}")
        if not from_unit and self.unit_state(slug) in ("failed",):
            self.run(["systemctl", "--user", "reset-failed", self.unit(slug)])
        return rest

    def reload_proxy(self) -> int:
        try:
            text = Path(self.inv["prospect_caddyfile"]).read_text(encoding="utf-8")
        except OSError:
            return 0
        return int(self.ctx.admin.load(text))

    def stop_and_teardown(self, slug: str) -> list[str]:
        if self.unit_state(slug) in ("active", "activating", "reloading"):
            self.run(["systemctl", "--user", "stop", self.unit(slug)])
        return self.teardown(slug)

    # -- up (section 10)
    def up(
        self,
        slug: str,
        ttl_s: int,
        stop_dashboard: bool,
        rotate: bool,
        password_stdin: bool,
    ) -> int:
        if rotate and not password_stdin:
            raise CliError(
                EXIT_USAGE,
                "use --password-stdin para enviar a nova senha pelo stdin",
            )
        operator_password: str | None = None
        if password_stdin:
            operator_password = _read_operator_password(self.ctx)

        with self.lock(self.ctx.lock_timeout_up) as got:
            if not got:
                raise CliError(EXIT_BUSY, "outra operação de prospecto em andamento")
            self.prerequisites()
            for other in self.known_slugs():
                if other != slug and self.active(other):
                    exp = (self.state(other) or {}).get("expires_at", "?")
                    raise CliError(
                        EXIT_BUSY,
                        f"já há um prospecto ativo: {other} até {exp}; "
                        f"rode prospect-down {other} antes",
                    )
            if self.active(slug):
                return self._existing(
                    slug, rotate, operator_password if rotate else None
                )
            dash_running = self.container_state(self.dash) == "running"
            if dash_running and not stop_dashboard:
                raise CliError(
                    EXIT_USAGE,
                    "a dashboard pública vai ficar fora do ar durante a sessão; "
                    "para confirmar, repita com --stop-dashboard",
                )
            if not password_stdin:
                raise CliError(
                    EXIT_USAGE,
                    "use --password-stdin e envie a senha pelo stdin "
                    f"(mínimo {MIN_OPERATOR_PASSWORD_CHARS} caracteres)",
                )
            # Leftovers of the same slug (failed unit or past the deadline) go first:
            # the old pod still counts as an instance and holds the port.
            if self.leftovers(slug):
                rest = self.stop_and_teardown(slug)
                if rest:
                    raise CliError(
                        EXIT_LEFTOVERS, "restos de " + slug + ": " + "; ".join(rest)
                    )
            instances = self.running_instances()
            others = [n for n in instances if n != self.dash]
            if dash_running and len(instances) > 2:
                raise CliError(
                    EXIT_BUSY,
                    f"contagem de instâncias fora do modelo: {len(instances)}",
                )
            if not dash_running and len(others) > 1:
                raise CliError(
                    EXIT_BUSY,
                    f"contagem de instâncias fora do modelo: {len(instances)}",
                )
            port = self.inv["prospect_port"]
            if self.ctx.port_busy(port):
                raise CliError(EXIT_BUSY, f"porta {port} ocupada")
            assert operator_password is not None
            self.take_slot(slug, dash_running)
            try:
                return self._create(slug, ttl_s, operator_password)
            except CliError as exc:
                if self._rollback(slug) == EXIT_SLOT:
                    raise CliError(
                        EXIT_SLOT, exc.message + "; dashboard não voltou"
                    ) from None
                raise
            except BaseException as exc:  # Ctrl-C too: never leave the slot down
                if self._rollback(slug) == EXIT_SLOT and isinstance(exc, Exception):
                    raise CliError(
                        EXIT_SLOT, "falha inesperada; dashboard não voltou"
                    ) from None
                raise

    def _rollback(self, slug: str) -> int | Occupied:
        """Teardown of a failed up, then restore_slot even if the teardown raised (the
        leftovers are reported and the reaper finishes them). An Occupied outcome only
        means the pod of ``slug`` survived; the exit code of the up does not change."""
        try:
            self.stop_and_teardown(slug)
        except Exception as exc:
            print(
                f"restos de {slug}: teardown falhou ({type(exc).__name__})",
                file=self.ctx.err,
            )
        finally:  # Ctrl-C in the teardown too
            rc = self.restore_slot(slug)
        return rc

    def take_slot(self, slug: str, dash_running: bool) -> None:
        previous = self.slot() or {}
        timer = self.timer_active()
        record = {
            "slot": self.dash,
            "taken_by": slug,
            "taken_at": previous.get("taken_at") or _stamp(self.now()),
            "mode": self.inv["prospect_slot_mode"],
            "reset_timer_was_active": bool(
                previous.get("reset_timer_was_active") or timer
            ),
            "dashboard_was_running": bool(
                previous.get("dashboard_was_running", False) or dash_running
            ),
        }
        self.write_slot(
            record
        )  # before stopping: a crash leaves a trail for the reaper
        if timer:
            self.run(["systemctl", "--user", "stop", "demo-reset.timer"])
        if dash_running:
            stop_rc = self.stop_slot()
            if stop_rc != 0:  # the dashboard may still be up: never start a third one
                msg = f"parada da dashboard falhou (rc={stop_rc})"
                if self.restore_slot(slug) == EXIT_SLOT:
                    raise CliError(EXIT_SLOT, msg + "; dashboard não voltou")
                raise CliError(EXIT_BUSY, msg)
        need = POD_MEMORY_MIB + self.inv["prospect_reserve"]
        deadline = self.now() + timedelta(seconds=MEM_WAIT_S)
        while self.ctx.meminfo() < need:
            if self.now() >= deadline:
                msg = f"memória insuficiente: MemAvailable < {need} MiB"
                if self.restore_slot(slug) == EXIT_SLOT:
                    raise CliError(EXIT_SLOT, msg + "; dashboard não voltou")
                raise CliError(EXIT_BUSY, msg)
            self.ctx.sleep(1.0)

    def _create(self, slug: str, ttl_s: int, operator_password: str) -> int:
        inv = self.inv
        created = self.now()
        expires = created + timedelta(seconds=ttl_s)
        port = inv["prospect_port"]
        d = self.slug_dir(slug)
        self._mkdir(d)
        api_key = secrets.token_hex(32)
        extras = inv["prospect_extras_dir"]
        if not extras:
            self._mkdir(d / "extras", 0o755)
            extras = str(d / "extras")
        state = {
            "slug": slug,
            "port": port,
            "created_at": _stamp(created),
            "expires_at": _stamp(expires),
            "ttl_s": ttl_s,
            "phase": "A",
        }
        self.write(d / "state.json", json.dumps(state, sort_keys=True) + "\n", 0o600)
        self.write(
            d / "state.env",
            render_state_env(port, inv["prospect_corpus_dir"], extras),
            0o600,
        )
        self.write(d / "pod.env", render_pod_env(api_key, inv), 0o600)
        self.write(d / "config.yaml", render_config(slug, inv), 0o644)
        for src_key, name in (
            ("prospect_profile_file", "profile.yaml"),
            ("prospect_recommendations_file", "recommendations.yaml"),
        ):
            self.write(d / name, Path(inv[src_key]).read_bytes(), 0o644)
        self._mkdir(d / "lic", 0o700)
        if inv["prospect_license_mode"] == "enforced":
            lic = Path(inv["prospect_license_file"])
            self.write(d / "lic" / lic.name, lic.read_bytes(), 0o644)
        rc, _, _ = self.run(openssl_argv(slug, d))
        if rc != 0 or not (d / "tls.crt").is_file():
            raise CliError(EXIT_UNHEALTHY, "openssl não gerou o certificado do pod")
        for name in ("tls.crt", "tls.key"):
            (d / name).chmod(0o644)
        dropin = self.ttl_dropin(slug)
        self._mkdir(dropin.parent, 0o755)
        self.write(dropin, render_ttl_dropin(ttl_s), 0o644)
        self.run(["systemctl", "--user", "daemon-reload"])
        rc, _, _ = self.run(["systemctl", "--user", "start", self.unit(slug)])
        if rc != 0:
            raise CliError(EXIT_UNHEALTHY, f"a unidade {self.unit(slug)} não subiu")
        self._wait_pod_health(port, api_key, str(d / "tls.crt"))
        self._publish_route(slug, operator_password, api_key)
        self.print_session(slug, state, session_kind="new")
        return EXIT_OK

    def _wait_pod_health(self, port: int, key: str, cafile: str) -> None:
        allowed = _ALLOWED_LICENSE[self.inv["prospect_license_mode"]]
        url = f"https://127.0.0.1:{port}/status"
        deadline = self.now() + timedelta(seconds=POD_HEALTH_S)
        last = "sem resposta"
        while True:
            st = self.ctx.probe.status(url, key, cafile)
            if st:
                lic = (
                    (st.get("license") or {})
                    if isinstance(st.get("license"), dict)
                    else {}
                )
                state = lic.get("license_state")
                if st.get("trust_state") == "trusted" and state in allowed:
                    return
                last = f"trust_state={st.get('trust_state')} license_state={state}"
            if self.now() >= deadline:
                raise CliError(EXIT_UNHEALTHY, f"instância não ficou saudável: {last}")
            self.ctx.sleep(POLL_S)

    def _hash(self, password: str) -> str:
        rc, out, _ = self.run(
            [
                "podman",
                "exec",
                "-i",
                self.inv["prospect_proxy_container"],
                "caddy",
                "hash-password",
            ],
            input=password + "\n",
        )
        digest = out.strip()
        if rc != 0 or not _BCRYPT.fullmatch(digest):
            raise CliError(EXIT_PROXY, "o proxy não gerou o hash da senha")
        return digest

    def _render_route(self, slug: str, digest: str, api_key: str) -> str:
        inv = self.inv
        try:
            return render_site(
                slug=slug,
                domain=inv["prospect_domain"],
                proxy_port=inv["prospect_proxy_port"],
                pod_port=inv["prospect_port"],
                tls_line=inv["prospect_tls_line"],
                bcrypt_hash=digest,
                api_key=api_key,
                caddy_dir_in_proxy=inv["prospect_caddy_dir_in_proxy"],
            )
        except ValueError:
            raise CliError(
                EXIT_PROXY, "fragmento de rota recusado na validação"
            ) from None

    def _publish_route(self, slug: str, password: str, api_key: str) -> None:
        site = self._render_route(slug, self._hash(password), api_key)
        crt = self.caddy_dir / f"{slug}.crt"
        frag = self.caddy_dir / f"{slug}.caddy"
        self.write(crt, (self.slug_dir(slug) / "tls.crt").read_bytes(), 0o644)
        self.write(frag, site, 0o600)
        code = self.reload_proxy()
        if code != 200:
            frag.unlink(missing_ok=True)
            crt.unlink(missing_ok=True)
            self.reload_proxy()
            raise CliError(EXIT_PROXY, f"o proxy recusou a config (/load {code})")
        host = f"{slug}.{self.inv['prospect_domain']}"
        deadline = self.now() + timedelta(seconds=ROUTE_WAIT_S)
        while True:
            got = self.ctx.probe.route_status(host, self.inv["prospect_proxy_port"])
            if got != 0 or self.now() >= deadline:  # 0 = no answer yet (TLS warming up)
                break
            self.ctx.sleep(1.0)
        if got != 401:
            raise CliError(EXIT_PROXY, f"a rota não respondeu 401 (recebeu {got})")

    def _existing(self, slug: str, rotate: bool, operator_password: str | None) -> int:
        state = self.state(slug) or {}
        if not rotate:
            self.print_session(slug, state, session_kind="existing")
            return EXIT_OK
        assert operator_password is not None
        frag = self.caddy_dir / f"{slug}.caddy"
        try:
            old = frag.read_text(encoding="utf-8")
        except OSError:
            raise CliError(EXIT_PROXY, "fragmento da sessão ausente") from None
        m = re.search(r'header_up X-API-Key "([0-9a-f]{64})"', old)
        if not m:
            raise CliError(EXIT_PROXY, "fragmento da sessão fora do formato")
        self.write(
            frag,
            self._render_route(slug, self._hash(operator_password), m.group(1)),
            0o600,
        )
        code = self.reload_proxy()
        if code != 200:
            self.write(frag, old, 0o600)
            self.reload_proxy()
            raise CliError(EXIT_PROXY, f"o proxy recusou a config (/load {code})")
        self.print_session(slug, state, session_kind="rotated")
        return EXIT_OK

    def print_session(
        self, slug: str, state: dict[str, Any], *, session_kind: str
    ) -> None:
        exp = state.get("expires_at", "?")
        self.say(f"url: https://{slug}.{self.inv['prospect_domain']}/")
        self.say(f"usuário: {USER}")
        if session_kind == "existing":
            self.say(
                "senha já emitida; use --rotate-password com --password-stdin para trocar"
            )
        self.say(f"expires_at: {exp}")
        self.say(
            f"ATENÇÃO: a dashboard pública está FORA DO AR até prospect-down {slug} ou {exp}"
        )

    # -- down (section 11)
    def down(self, slug: str) -> int:
        with self.lock(self.ctx.lock_timeout_up) as got:
            if not got:
                raise CliError(EXIT_BUSY, "outra operação de prospecto em andamento")
            had = self.leftovers(slug)
            rest = self.stop_and_teardown(slug) if had else []
            outcome: int | Occupied = EXIT_OK
            if self.slot() is not None or self.container_state(self.dash) != "running":
                outcome = self.restore_slot(slug)
            if not had:
                self.say(f"nada a remover: {slug}")
                if isinstance(outcome, Occupied):
                    self.say(outcome.line)
            elif isinstance(outcome, Occupied):
                self.say(f"removido: {slug}; {outcome.line}")
            elif outcome == EXIT_OK:
                self.say(f"removido: {slug}; dashboard no ar")
            else:
                self.say(f"removido: {slug}; dashboard FORA DO AR")
            rc = EXIT_OK if isinstance(outcome, Occupied) else outcome
            if rest:
                print(f"restos de {slug}: " + "; ".join(rest), file=self.ctx.err)
                self.say("restos: " + "; ".join(rest))
                if rc == EXIT_OK:
                    rc = EXIT_LEFTOVERS
            return rc

    def teardown_from_unit(self, slug: str) -> int:
        with self.lock(None) as got:
            if not got:
                return EXIT_OK  # the lock holder (down, reap, up rollback) finishes the job
            rest = self.teardown(slug, from_unit=True)
        self.run(
            ["systemctl", "--user", "start", "--no-block", "demo-slot-restore.service"]
        )
        return EXIT_LEFTOVERS if rest else EXIT_OK

    # -- list
    def listing(self) -> dict[str, Any]:
        now = self.now()
        prospects = []
        for slug in self.known_slugs():
            st = self.state(slug) or {}
            try:
                exp = _parse_stamp(str(st.get("expires_at")))
            except ValueError:
                exp = now
            unit = self.unit_state(slug)
            if unit != "active":
                status = "órfão"
            elif now >= exp:
                status = "vencido"
            else:
                status = "ativo"
            left = max(0, int((exp - now).total_seconds() // 60))
            prospects.append(
                {
                    "slug": slug,
                    "status": status,
                    "created_at": st.get("created_at"),
                    "expires_at": st.get("expires_at"),
                    "minutes_left": left,
                }
            )
        slot = self.slot()
        if slot is None:
            info = {
                "state": "no_ar",
                "taken_by": None,
                "since": None,
                "failed_at": None,
            }
        else:
            info = {
                "state": "fora_do_ar" if slot.get("restore_failed_at") else "parada",
                "taken_by": slot.get("taken_by"),
                "since": slot.get("taken_at"),
                "failed_at": slot.get("restore_failed_at"),
            }
        return {"prospects": prospects, "slot": info}

    def list(self, as_json: bool) -> int:
        data = self.listing()
        if as_json:
            self.say(json.dumps(data, ensure_ascii=False, sort_keys=True))
            return EXIT_OK
        for p in data["prospects"]:
            self.say(
                f"{p['slug']} {p['status']} {p['created_at']} {p['expires_at']} "
                f"{p['minutes_left']} min"
            )
        s = data["slot"]
        if s["state"] == "no_ar":
            self.say("dashboard: no ar")
        elif s["state"] == "parada":
            self.say(
                f"dashboard: parada pela sessão {s['taken_by']} desde {s['since']}"
            )
        else:
            self.say(f"dashboard: FORA DO AR, restauração falhou às {s['failed_at']}")
        return EXIT_OK

    # -- reap (section 12)
    def reap(self) -> int:
        with self.lock(self.ctx.lock_timeout_reap) as got:
            if not got:
                raise CliError(EXIT_BUSY, "outra operação de prospecto em andamento")
            rc = EXIT_OK
            now = self.now()
            live: set[str] = set()
            for slug in self.known_slugs():
                st = self.state(slug)
                unit = self.unit_state(slug)
                try:
                    exp = _parse_stamp(str((st or {}).get("expires_at")))
                except ValueError:
                    exp = now
                if (
                    st
                    and unit == "active"
                    and now < exp + timedelta(seconds=REAP_GRACE_S)
                ):
                    live.add(slug)
                    continue
                rest = self.stop_and_teardown(slug)
                self.say(
                    f"reap: {slug} removido"
                    + (f" com restos: {'; '.join(rest)}" if rest else "")
                )
                if rest:
                    rc = EXIT_LEFTOVERS
            for slug in sorted(self.orphans() - live):
                rest = self.stop_and_teardown(slug)
                self.say(
                    f"reap: órfão {slug} removido"
                    + (f" com restos: {'; '.join(rest)}" if rest else "")
                )
                if rest:
                    rc = EXIT_LEFTOVERS
            if not live and (
                self.slot() is not None or self.container_state(self.dash) != "running"
            ):
                slot_rc = self.restore_slot()
                if isinstance(slot_rc, Occupied):  # retried on the next cycle
                    self.say(f"reap: {slot_rc.line}")
                elif slot_rc == EXIT_OK:
                    self.say("reap: dashboard no ar")
                else:
                    self.say("reap: dashboard FORA DO AR")
                    rc = slot_rc
            return rc

    def orphans(self) -> set[str]:
        found: set[str] = set()
        for c in self.containers(LABEL):
            value = str((c.get("Labels") or {}).get(LABEL, ""))
            found.add(value)
        for _name, value in self.labelled_networks():
            found.add(value)
        if self.caddy_dir.is_dir():
            for p in self.caddy_dir.iterdir():
                if p.suffix in (".caddy", ".crt"):
                    found.add(p.stem)
        root = self.ctx.systemd_runtime_dir
        if root.is_dir():
            for p in root.glob(f"{UNIT_PREFIX}*.service.d"):
                found.add(p.name[len(UNIT_PREFIX) : -len(".service.d")])
        found |= self.failed_units()
        return {s for s in found if _SLUG.fullmatch(s) and "--" not in s}

    def failed_units(self) -> set[str]:
        """Instances left `failed` by the TTL or a dead pod: the ExecStopPost teardown
        never resets its own unit, so the reaper does (section 12, step 1)."""
        rc, out, _ = self.run(
            [
                "systemctl",
                "--user",
                "show",
                f"{UNIT_PREFIX}*",
                "-p",
                "Id",
                "-p",
                "ActiveState",
            ]
        )
        found: set[str] = set()
        if rc != 0:
            return found
        for block in out.split("\n\n"):
            fields = dict(
                line.split("=", 1) for line in block.splitlines() if "=" in line
            )
            unit = fields.get("Id", "")
            if (
                fields.get("ActiveState") == "failed"
                and unit.startswith(UNIT_PREFIX)
                and unit.endswith(".service")
            ):
                found.add(unit[len(UNIT_PREFIX) : -len(".service")])
        return found


# --------------------------------------------------------------------------- argv
class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> Any:  # one line, exit 2
        raise CliError(EXIT_USAGE, "uso inválido: " + message.replace("\n", " "))


def _parser() -> argparse.ArgumentParser:
    p = _Parser(prog="prospect.py", add_help=False)
    sub = p.add_subparsers(dest="cmd", required=True, parser_class=_Parser)
    up = sub.add_parser("up", add_help=False)
    up.add_argument("slug")
    up.add_argument("--stop-dashboard", action="store_true")
    up.add_argument("--ttl", default="30m")
    up.add_argument("--rotate-password", action="store_true")
    up.add_argument(
        "--password-stdin",
        action="store_true",
        help="lê a senha do operador do stdin (mínimo 20 caracteres)",
    )
    up.add_argument("--upload", action="store_true")
    down = sub.add_parser("down", add_help=False)
    down.add_argument("slug")
    lst = sub.add_parser("list", add_help=False)
    lst.add_argument("--json", action="store_true")
    sub.add_parser("reap", add_help=False)
    sub.add_parser("restore-slot", add_help=False)
    td = sub.add_parser("teardown", add_help=False)
    td.add_argument("slug")
    td.add_argument("--from-unit", action="store_true", required=True)
    return p


def _inventory_path(ctx: Context) -> Path:
    if ctx.inventory_path is not None:
        return ctx.inventory_path
    env = os.environ.get("PROSPECT_INVENTORY")
    if env:
        return Path(env)
    return ctx.home / "demo" / "prospect" / "inventory.json"


def _dispatch(args: argparse.Namespace, ctx: Context) -> int:
    ttl_s = 0
    if args.cmd == "up":
        if args.upload:
            raise CliError(EXIT_USAGE, "upload: fase B não habilitada")
        validate_slug(args.slug)
        ttl_s = parse_ttl(args.ttl)
    elif args.cmd in ("down", "teardown"):
        validate_slug(args.slug)
    inv = load_inventory(_inventory_path(ctx))
    if args.cmd in ("up", "down", "teardown"):
        validate_slug(args.slug, inv["prospect_reserved_slugs"])
    cli = Cli(ctx, inv)
    if args.cmd == "up":
        return cli.up(
            args.slug,
            ttl_s,
            args.stop_dashboard,
            args.rotate_password,
            args.password_stdin,
        )
    if args.cmd == "down":
        return cli.down(args.slug)
    if args.cmd == "list":
        return cli.list(args.json)
    if args.cmd == "reap":
        return cli.reap()
    if args.cmd == "restore-slot":
        with cli.lock(ctx.lock_timeout_reap) as got:
            if not got:
                raise CliError(EXIT_BUSY, "outra operação de prospecto em andamento")
            outcome = cli.restore_slot()
        if isinstance(outcome, Occupied):
            cli.say(outcome.line)
            return EXIT_OK
        if outcome == EXIT_OK:
            cli.say("dashboard no ar")
        return outcome
    return cli.teardown_from_unit(args.slug)


def main(argv: list[str] | None = None, ctx: Context | None = None) -> int:
    ctx = ctx or Context.from_env()
    try:
        args = _parser().parse_args(sys.argv[1:] if argv is None else argv)
        return _dispatch(args, ctx)
    except CliError as exc:
        print(exc.message.replace("\n", " "), file=ctx.err)
        return exc.code


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        with contextlib.suppress(AttributeError, ValueError):
            stream.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    sys.exit(main())
