"""TDD spec of ``deploy/demo/prospect/prospect.py`` (task 2280.2, epic #2280, issue #2283).

Source of truth: ``docs/desenho/2280.1.md``, "Especificação para o TDD do dev"
(D2280.1-1 to D2280.1-30 and D2280.1-38 to D2280.1-44; the contract items D-31 to D-35
live in ``tests/test_deploy_demo_prospect_contract.py``).

Everything goes through the seams of section 15: a fake host (``Runner``) that simulates
``podman``/``systemctl``/``systemd-run``/``openssl``, a fake proxy admin, fake probes, a
fake alerter and a fixed clock at 2026-11-18T12:00:00Z. No network, no real systemctl.
The lock is real (``fcntl.flock`` in ``tmp_path``).

The CLI is a host-only Linux script (``fcntl``, unix modes), so this module is skipped
as a whole on Windows; the skip-ceiling job (#2233) runs on Linux. Slugs are the
placeholders ``acme`` and ``bravo``.
"""

from __future__ import annotations

import codecs
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import threading
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

if os.name == "nt":
    pytest.skip("prospect.py is a Linux host script (fcntl)", allow_module_level=True)

REPO = Path(__file__).resolve().parents[1]
CLI = REPO / "deploy" / "demo" / "prospect" / "prospect.py"
DOMAIN = "prospect.test"
T0 = datetime(2026, 11, 18, 12, 0, 0, tzinfo=UTC)
IMAGE = "docker.io/fabioleitao/data_boar:1.8.0"
TEST_OPERATOR_PASSWORD = "operador-senha-teste-20"
TEST_OPERATOR_PASSWORD_B = "outra-senha-operador-21"


def _load_module():
    """Import the CLI without writing ``__pycache__`` into ``deploy/demo`` (the demo
    contract test reads every file there as UTF-8)."""
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec = importlib.util.spec_from_file_location("prospect_cli", CLI)
        assert spec and spec.loader
        mod = importlib.util.module_from_spec(spec)
        sys.modules["prospect_cli"] = mod
        spec.loader.exec_module(mod)
        return mod
    finally:
        sys.dont_write_bytecode = previous


P = _load_module()


def _fake_hash() -> str:
    # Built at runtime: the demo contract forbids a bcrypt literal under deploy/demo,
    # and keeping it out of tests too avoids teaching scanners a false positive.
    return "$" + "2a" + "$" + "14" + "$" + "N" * 53


def _z(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


READ_PREFIXES = (
    ("podman", "ps"),
    ("podman", "inspect"),
    ("podman", "version"),
    ("podman", "network", "exists"),
    ("podman", "network", "ls"),
    ("podman", "volume", "ls"),
    ("systemctl", "--user", "is-active"),
    ("systemctl", "--user", "show"),
)


def is_read(argv: list[str]) -> bool:
    return any(tuple(argv[: len(p)]) == p for p in READ_PREFIXES)


# --------------------------------------------------------------------------- fakes
class FakeClock:
    def __init__(self) -> None:
        self.t = T0
        self._lock = threading.Lock()

    def now(self) -> datetime:
        with self._lock:
            return self.t

    def sleep(self, seconds: float) -> None:
        with self._lock:
            self.t += timedelta(seconds=seconds)

    def advance(self, seconds: float) -> None:
        self.sleep(seconds)


class FakeHost:
    """Scripted host: podman containers/networks/volumes, user units and the timer."""

    def __init__(self, runtime: Path, caddy_dir: Path) -> None:
        self.runtime = runtime
        self.caddy_dir = caddy_dir
        self.lock = threading.RLock()
        self.calls: list[list[str]] = []
        self.inputs: list[str | None] = []
        self.snaps: list[set[str]] = []
        self.containers: dict[str, dict[str, Any]] = {}
        self.networks: dict[str, dict[str, str]] = {}
        self.volumes: dict[str, dict[str, str]] = {}
        self.units: dict[str, str] = {}
        self.timer_active = False
        self.podman_version = "5.4.2"
        self.fail: dict[str, tuple[int, str, str]] = {}
        self.dash_start_rc = 0
        self.hash_output: str | None = None
        self.on_stop_unit: Any = None
        self.on_start_unit: Any = None
        self.add_container("dashboard", IMAGE, "running")
        self.add_container("apresentacao", IMAGE, "running")

    # -- state helpers
    def add_container(
        self,
        name: str,
        image: str,
        state: str,
        labels: dict[str, str] | None = None,
    ) -> None:
        self.containers[name] = {
            "Id": f"id-{name}",
            "Names": [name],
            "Image": image,
            "State": state,
            "Labels": labels or {},
        }

    def state(self, name: str) -> str | None:
        c = self.containers.get(name)
        return c["State"] if c else None

    def _snapshot(self) -> set[str]:
        found: set[str] = set()
        for root in (self.runtime / "demo-prospect", self.caddy_dir):
            if root.exists():
                for p in root.rglob("*"):
                    found.add(str(p.relative_to(root.parent)))
        return found

    def writes(self) -> list[list[str]]:
        return [c for c in self.calls if not is_read(c)]

    def index(self, pred) -> int:
        for i, c in enumerate(self.calls):
            if pred(c):
                return i
        return -1

    # -- Runner seam
    def run(self, argv: list[str], input: str | None = None) -> tuple[int, str, str]:
        with self.lock:
            self.calls.append(list(argv))
            self.inputs.append(input)
            self.snaps.append(self._snapshot())
            joined = " ".join(argv)
            for key, resp in self.fail.items():
                if key in joined:
                    return resp
            return self._dispatch(list(argv), input)

    def _labelled(self, filt: str | None) -> list[dict[str, Any]]:
        out = []
        for c in self.containers.values():
            if filt is None:
                out.append(c)
                continue
            key, _, value = filt.partition("=")
            if key in c["Labels"] and (not value or c["Labels"][key] == value):
                out.append(c)
        return out

    @staticmethod
    def _filter_arg(argv: list[str]) -> str | None:
        if "--filter" in argv:
            raw = argv[argv.index("--filter") + 1]
            assert raw.startswith("label=")
            return raw[len("label=") :]
        return None

    def _dispatch(self, argv: list[str], input: str | None) -> tuple[int, str, str]:
        if argv[:2] == ["podman", "version"]:
            return 0, self.podman_version + "\n", ""
        if argv[:2] == ["podman", "ps"]:
            return 0, json.dumps(self._labelled(self._filter_arg(argv))), ""
        if argv[:2] == ["podman", "stop"]:
            name = argv[-1]
            if name in self.containers:
                self.containers[name]["State"] = "exited"
            return 0, "", ""
        if argv[:2] == ["podman", "rm"]:
            filt = self._filter_arg(argv)
            for c in self._labelled(filt):
                del self.containers[c["Names"][0]]
            return 0, "", ""
        if argv[:3] == ["podman", "network", "exists"]:
            return (0 if argv[3] in self.networks else 1), "", ""
        if argv[:3] == ["podman", "network", "ls"]:
            filt = self._filter_arg(argv)
            nets = [
                {"name": n, "labels": lab}
                for n, lab in self.networks.items()
                if filt is None or filt.partition("=")[0] in lab
            ]
            return 0, json.dumps(nets), ""
        if argv[:3] == ["podman", "network", "rm"]:
            self.networks.pop(argv[-1], None)
            return 0, "", ""
        if argv[:3] == ["podman", "volume", "ls"]:
            filt = self._filter_arg(argv)
            vols = [
                {"Name": n, "Labels": lab}
                for n, lab in self.volumes.items()
                if filt is None or filt.partition("=")[0] in lab
            ]
            return 0, json.dumps(vols), ""
        if argv[:3] == ["podman", "volume", "rm"]:
            self.volumes.pop(argv[-1], None)
            return 0, "", ""
        if argv[:2] == ["podman", "exec"] and argv[-2:] == ["caddy", "hash-password"]:
            assert input, "the password goes through stdin"
            return 0, (self.hash_output or _fake_hash()) + "\n", ""
        if argv[0] == "systemd-run":
            assert argv[:4] == ["systemd-run", "--user", "--scope", "--collect"]
            assert argv[4].startswith("--unit=databoar-slot-")
            assert argv[5:7] == ["podman", "start"]
            if self.dash_start_rc:
                return self.dash_start_rc, "", "Error: start failed"
            self.containers[argv[7]]["State"] = "running"
            return 0, "", ""
        if argv[:2] == ["systemctl", "--user"]:
            return self._systemctl(argv[2:])
        if argv[0] == "openssl":
            key = Path(argv[argv.index("-keyout") + 1])
            crt = Path(argv[argv.index("-out") + 1])
            key.write_text("fake key material\n", encoding="utf-8")
            crt.write_text("fake certificate\n", encoding="utf-8")
            return 0, "", ""
        return 0, "", ""

    def _systemctl(self, rest: list[str]) -> tuple[int, str, str]:
        verb = rest[0]
        unit = rest[-1] if len(rest) > 1 else ""
        if verb == "is-active":
            if unit == "demo-reset.timer":
                st = "active" if self.timer_active else "inactive"
            else:
                st = self.units.get(unit, "inactive")
            return (0 if st == "active" else 3), st + "\n", ""
        if verb == "daemon-reload":
            return 0, "", ""
        if verb == "stop":
            if unit == "demo-reset.timer":
                self.timer_active = False
            elif unit == "dashboard.service":
                self.containers["dashboard"]["State"] = "exited"
            elif unit.startswith("demo-prospect@"):
                if self.on_stop_unit:
                    self.on_stop_unit(unit)
                slug = unit[len("demo-prospect@") : -len(".service")]
                self.containers.pop(f"prospect-{slug}", None)
                if unit in self.units:
                    self.units[unit] = "failed"
            return 0, "", ""
        if verb == "start":
            if unit == "demo-reset.timer":
                self.timer_active = True
            elif unit == "dashboard.service":
                if self.dash_start_rc:
                    return self.dash_start_rc, "", "failed"
                self.containers["dashboard"]["State"] = "running"
            elif unit.startswith("demo-prospect@"):
                if self.on_start_unit:
                    self.on_start_unit(unit)
                slug = unit[len("demo-prospect@") : -len(".service")]
                lab = {"databoar.prospect": slug}
                self.networks[f"prospect-{slug}"] = dict(lab)
                self.add_container(f"prospect-{slug}", IMAGE, "running", lab)
                self.units[unit] = "active"
            return 0, "", ""
        if verb == "reset-failed":
            self.units.pop(unit, None)
            return 0, "", ""
        if verb == "show" and rest[1] == "demo-prospect@*":
            blocks = [
                f"Id={u}\nActiveState={st}"
                for u, st in sorted(self.units.items())
                if u.startswith("demo-prospect@")
            ]
            return 0, "\n\n".join(blocks) + ("\n" if blocks else ""), ""
        return 0, "", ""


class FakeAdmin:
    def __init__(self) -> None:
        self.loads: list[str] = []
        self.codes: list[int] = []
        self.default = 200

    def load(self, text: str) -> int:
        self.loads.append(text)
        return self.codes.pop(0) if self.codes else self.default


class FakeProbe:
    def __init__(self, host: FakeHost) -> None:
        self.host = host
        self.pod: dict | None = {
            "trust_state": "trusted",
            "license": {"license_state": "OPEN"},
        }
        self.slot: dict | None = {
            "trust_state": "trusted",
            "integrity": {"integrity_state": "validated"},
        }
        self.calls: list[tuple[str, str | None, str | None]] = []
        self.route_calls: list[tuple[str, int]] = []
        self.route_code = 401
        self.route_codes: list[int] = []

    def status(self, url: str, key: str | None = None, cafile: str | None = None):
        self.calls.append((url, key, cafile))
        with self.host.lock:
            self.host.calls.append(["#probe", url])
            self.host.inputs.append(None)
            self.host.snaps.append(set())
        if ":18100/" in url:
            return self.pod
        if self.host.state("dashboard") != "running":
            return None
        return self.slot

    def route_status(self, host: str, port: int) -> int:
        self.route_calls.append((host, port))
        return self.route_codes.pop(0) if self.route_codes else self.route_code


class FakeAlerter:
    def __init__(self) -> None:
        self.emitted: list[str] = []
        self.infos: list[str] = []

    def emit(self, msg: str) -> None:
        self.emitted.append(msg)

    def info(self, msg: str) -> None:
        self.infos.append(msg)


class TrackingStdin(io.StringIO):
    """Records when ``readline()`` runs relative to executor calls and the lock (D-54)."""

    def __init__(self, data: str = "", *, env: Env | None = None) -> None:
        super().__init__(data)
        self.readline_calls = 0
        self.executor_calls_at_read = -1
        self.lock_existed_at_read: bool | None = None
        self._env = env

    def readline(self, *args: Any, **kwargs: Any) -> str:
        self.readline_calls += 1
        if self._env is not None:
            self.executor_calls_at_read = len(self._env.host.calls)
            self.lock_existed_at_read = self._env.lock_path().exists()
        return super().readline(*args, **kwargs)


class _BrokenStdin:
    def readline(self) -> str:
        raise OSError("stdin indisponível no teste")


class _ClosedStringIO(io.StringIO):
    def readline(self, *args: Any, **kwargs: Any) -> str:
        raise ValueError("I/O operation on closed file")


def _assert_p0_dec22(
    env: Env,
    rc: int,
    err: str,
    needle: str,
    *,
    fp_before: dict[str, bytes],
    writes_before: int,
    loads_before: int,
    tracked: TrackingStdin | None = None,
    readline_expect: int = 0,
    expect_no_slot: bool = True,
    dash_state: str = "running",
) -> None:
    assert rc == 2, (rc, err)
    assert needle in err
    assert "Traceback" not in err
    assert env.tree_fingerprint() == fp_before
    assert len(env.host.writes()) == writes_before
    assert len(env.admin.loads) == loads_before
    if expect_no_slot:
        assert not env.slot_json().exists()
    assert env.host.state("dashboard") == dash_state
    if tracked is not None:
        assert tracked.readline_calls == readline_expect


def _assert_p0_plus_dec22(
    env: Env,
    rc: int,
    err: str,
    needle: str,
    *,
    fp_before: dict[str, bytes],
    writes_before: int,
    loads_before: int,
    calls_before: int,
    lock_existed_before: bool,
    tracked: TrackingStdin | None = None,
    readline_expect: int | None = None,
    expect_no_slot: bool = True,
    dash_state: str = "running",
) -> None:
    _assert_p0_dec22(
        env,
        rc,
        err,
        needle,
        fp_before=fp_before,
        writes_before=writes_before,
        loads_before=loads_before,
        tracked=tracked,
        readline_expect=readline_expect if readline_expect is not None else 0,
        expect_no_slot=expect_no_slot,
        dash_state=dash_state,
    )
    assert len(env.host.calls) == calls_before
    if (
        tracked is not None
        and tracked.lock_existed_at_read is not None
        and not lock_existed_before
    ):
        assert tracked.lock_existed_at_read is False


class Env:
    """One test world: inventory, fakes and a factory of CLI contexts."""

    def __init__(self, tmp: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        self.tmp = tmp
        self.home = tmp / "home"
        self.runtime = tmp / "run"
        self.caddy_dir = tmp / "srv" / "caddy" / "prospects"
        self.quadlet_dir = tmp / "cfg" / "containers" / "systemd"
        for d in (self.home, self.runtime, self.caddy_dir, self.quadlet_dir):
            d.mkdir(parents=True)
        dropin = self.quadlet_dir / "demo-prospect@.container.d"
        dropin.mkdir()
        (dropin / "10-host.conf").write_text(
            "[Container]\nImage=x\nHostName=y\n", encoding="utf-8"
        )
        srv = tmp / "srv"
        (srv / "corpus").mkdir()
        (srv / "corpus" / "a.txt").write_text("x\n", encoding="utf-8")
        (srv / "profile.yaml").write_text("{}\n", encoding="utf-8")
        (srv / "recommendations.yaml").write_text("{}\n", encoding="utf-8")
        (srv / "Caddyfile").write_text("# main caddyfile\n", encoding="utf-8")
        (srv / "admin.sock").write_text("", encoding="utf-8")
        (srv / "demo.lic").write_text("license\n", encoding="utf-8")
        self.base_env = srv / "base.env"
        self.base_env.write_text("", encoding="utf-8")
        self.base_env.chmod(0o600)
        self.alert_path = self.home / "demo" / "prospect" / "ALERT"
        self.inventory_path = tmp / "inventory.json"
        self.inv: dict[str, Any] = {
            "prospect_domain": DOMAIN,
            "prospect_port": 18100,
            "prospect_proxy_port": 8443,
            "prospect_proxy_container": "caddy-demo",
            "prospect_tls_line": "tls internal",
            "prospect_caddy_dir": str(self.caddy_dir),
            "prospect_caddy_dir_in_proxy": "/etc/caddy/prospects",
            "prospect_caddy_admin_socket": str(srv / "admin.sock"),
            "prospect_caddyfile": str(srv / "Caddyfile"),
            "prospect_corpus_dir": str(srv / "corpus"),
            "prospect_profile_file": str(srv / "profile.yaml"),
            "prospect_recommendations_file": str(srv / "recommendations.yaml"),
            "prospect_license_mode": "open",
            "prospect_base_env": str(self.base_env),
            "prospect_alert_path": str(self.alert_path),
            "prospect_protected_containers": ["apresentacao"],
            "prospect_reserved_slugs": [],
        }
        self.write_inventory()
        monkeypatch.setenv("PROSPECT_INVENTORY", str(self.inventory_path))
        self.clock = FakeClock()
        self.host = FakeHost(self.runtime, self.caddy_dir)
        self.admin = FakeAdmin()
        self.probe = FakeProbe(self.host)
        self.alerter = FakeAlerter()
        self.mem_mib = 4096
        self.busy_ports: set[int] = set()
        self.which_missing: set[str] = set()

    def write_inventory(self, mode: int = 0o600) -> None:
        self.inventory_path.write_text(json.dumps(self.inv), encoding="utf-8")
        self.inventory_path.chmod(mode)

    def ctx(self) -> Any:
        return P.Context(
            runner=self.host,
            admin=self.admin,
            probe=self.probe,
            alerter=self.alerter,
            clock=self.clock.now,
            sleep=self.clock.sleep,
            meminfo=lambda: self.mem_mib,
            port_busy=lambda port: port in self.busy_ports,
            which=lambda name: (
                None if name in self.which_missing else f"/usr/bin/{name}"
            ),
            runtime_dir=self.runtime,
            systemd_runtime_dir=self.runtime / "systemd" / "user",
            quadlet_dir=self.quadlet_dir,
            home=self.home,
            lock_timeout_up=5.0,
            lock_timeout_reap=5.0,
            out=io.StringIO(),
            err=io.StringIO(),
        )

    def cli(
        self,
        *args: str,
        stdin: str | io.IOBase | None = None,
    ) -> tuple[int, str, str]:
        c = self.ctx()
        if stdin is not None:
            c.in_ = io.StringIO(stdin) if isinstance(stdin, str) else stdin
        rc = P.main(list(args), c)
        return rc, c.out.getvalue(), c.err.getvalue()

    def tree_fingerprint(self) -> dict[str, bytes]:
        lock = self.lock_path()
        found: dict[str, bytes] = {}
        for path in self.tmp.rglob("*"):
            if not path.is_file() or path == lock:
                continue
            found[str(path.relative_to(self.tmp))] = path.read_bytes()
        return found

    def up(
        self, slug: str = "acme", *extra: str, stdin: str | None = None
    ) -> tuple[int, str, str]:
        args = list(extra)
        if "--password-stdin" not in args:
            args = ["--password-stdin", *args]
        payload = stdin if stdin is not None else f"{TEST_OPERATOR_PASSWORD}\n"
        return self.cli("up", slug, "--stop-dashboard", *args, stdin=payload)

    # -- paths
    def slug_dir(self, slug: str) -> Path:
        return self.runtime / "demo-prospect" / slug

    def slot_json(self) -> Path:
        return self.runtime / "demo-prospect" / "slot.json"

    def ttl_dropin(self, slug: str) -> Path:
        return (
            self.runtime
            / "systemd"
            / "user"
            / f"demo-prospect@{slug}.service.d"
            / "10-ttl.conf"
        )

    def lock_path(self) -> Path:
        return self.runtime / "demo-prospect" / ".lock"

    def state(self, slug: str) -> dict[str, Any]:
        return json.loads((self.slug_dir(slug) / "state.json").read_text("utf-8"))

    def assert_clean(self, slug: str) -> None:
        """Postconditions of section 11, step 5."""
        h = self.host
        assert not [
            c
            for c in h.containers.values()
            if c["Labels"].get("databoar.prospect") == slug
        ]
        assert f"prospect-{slug}" not in h.networks
        assert not [v for v in h.volumes.values() if v.get("databoar.prospect") == slug]
        assert not list(self.caddy_dir.glob(f"{slug}.*"))
        assert not self.slug_dir(slug).exists()
        assert not self.ttl_dropin(slug).exists()
        assert h.units.get(f"demo-prospect@{slug}.service") not in ("active", "failed")
        assert h.state("dashboard") == "running"


@pytest.fixture
def env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    e = Env(tmp_path, monkeypatch)
    yield e
    # D2280.1-20 and D2280.1-39 hold in every test of this file.
    for argv in e.host.calls:
        if argv[:1] == ["#probe"]:
            continue
        if argv[:1] == ["podman"] and "dashboard" in argv:
            assert argv[1] not in ("run", "restart", "rm", "start"), argv
            assert argv[1:3] != ["container", "clone"], argv
        if "start" in argv and "podman" in argv:
            assert argv[0] == "systemd-run" and argv[1:3] == ["--user", "--scope"], argv
        if not is_read(argv):
            for protected in e.inv["prospect_protected_containers"]:
                assert protected not in " ".join(argv), argv


def _pod_gone(env: Env, slug: str, unit_state: str = "failed") -> None:
    """The pod of ``slug`` is gone as after the TTL's ExecStopPost: no labelled container
    and the unit out of active/activating/reloading (design revision 2, DEC-20)."""
    for name in [
        n
        for n, c in env.host.containers.items()
        if c["Labels"].get("databoar.prospect") == slug
    ]:
        del env.host.containers[name]
    env.host.units[f"demo-prospect@{slug}.service"] = unit_state


def _session_lines(out: str) -> list[str]:
    return [line for line in out.splitlines() if line.strip()]


def _password_sent_to_hash(env: Env, occurrence: int = -1) -> str:
    """Password the CLI passed to caddy hash-password (design D, no stdout echo)."""
    hits = [
        i
        for i, c in enumerate(env.host.calls)
        if c[-1:] == ["hash-password"] and env.host.inputs[i]
    ]
    assert hits, "nenhuma chamada hash-password com stdin"
    idx = hits[occurrence]
    return (env.host.inputs[idx] or "").rstrip("\n")


# --------------------------------------------------------------------------- slug, TTL
@pytest.mark.parametrize("slug", ["acme", "a1-b2", "a" + "b" * 18 + "c"])
def test_D2280_1_1_slug_valido_aceito(slug: str) -> None:
    """D2280.1-1: valid slugs (incl. 20 chars) are accepted."""
    assert len(slug) <= 20
    assert P.validate_slug(slug) == slug


BAD_SLUGS = [
    "Acme",
    "acme.com",
    "ac_me",
    "ac me",
    "1acme",
    "-acme",
    "acme-",
    "ac--me",
    "xn--acme",
    "ab",
    "a" * 21,
    "",
    "açme",
    "../x",
    "acme\n",
]


@pytest.mark.parametrize("slug", BAD_SLUGS)
def test_D2280_1_2_slug_invalido_sai_2_sem_efeito(env: Env, slug: str) -> None:
    """D2280.1-2: invalid slug -> exit 2, no executor call, no file created."""
    rc, _out, err = env.up(slug)
    assert rc == 2
    assert env.host.calls == []
    assert not (env.runtime / "demo-prospect").exists()
    assert not list(env.caddy_dir.iterdir())
    assert len(err.strip().splitlines()) == 1


@pytest.mark.parametrize(
    "slug",
    ["dashboard", "apresentacao", "www", "api", "admin", "status", "mail", "demo"]
    + ["prospect", "bravo"],
)
def test_D2280_1_3_slug_reservado(env: Env, slug: str) -> None:
    """D2280.1-3: built-in and inventory reserved slugs -> exit 2 'slug reservado'."""
    env.inv["prospect_reserved_slugs"] = ["bravo"]
    env.write_inventory()
    rc, _out, err = env.up(slug)
    assert rc == 2
    assert "slug reservado" in err
    assert env.host.writes() == []


@pytest.mark.parametrize(
    ("text", "seconds"), [("5m", 300), ("30m", 1800), ("1h", 3600), ("90m", 5400)]
)
def test_D2280_1_4_ttl_aceito(text: str, seconds: int) -> None:
    """D2280.1-4: accepted TTLs."""
    assert P.parse_ttl(text) == seconds


@pytest.mark.parametrize("text", ["4m", "91m", "0", "-5m", "30", "abc"])
def test_D2280_1_4_ttl_recusado(env: Env, text: str) -> None:
    """D2280.1-4: rejected TTLs exit 2; the default TTL is 1800 s."""
    with pytest.raises(P.CliError) as exc:
        P.parse_ttl(text)
    assert exc.value.code == 2
    rc, _, _ = env.up("acme", "--ttl", text)
    assert rc == 2
    assert env.host.writes() == []


def test_D2280_1_4_ttl_padrao_1800(env: Env) -> None:
    """D2280.1-4: without --ttl the state has ttl_s 1800."""
    rc, _, err = env.up()
    assert rc == 0, err
    assert env.state("acme")["ttl_s"] == 1800


# --------------------------------------------------------------------------- rendering
def test_D2280_1_5_dropin_de_ttl(env: Env) -> None:
    """D2280.1-5: the TTL drop-in is exactly [Service] and RuntimeMaxSec=1800."""
    assert P.render_ttl_dropin(1800) == "[Service]\nRuntimeMaxSec=1800\n"
    rc, _, err = env.up()
    assert rc == 0, err
    assert (
        env.ttl_dropin("acme").read_text("utf-8") == "[Service]\nRuntimeMaxSec=1800\n"
    )


def _pod_env(env: Env) -> dict[str, str]:
    text = (env.slug_dir("acme") / "pod.env").read_text("utf-8")
    return dict(line.split("=", 1) for line in text.splitlines() if line)


def test_D2280_1_6_pod_env_allowlist_com_seed(env: Env) -> None:
    """D2280.1-6: with the seed, pod.env has only allowlisted keys."""
    env.base_env.write_text("DATA_BOAR_MACHINE_SEED=seed-de-teste\n", encoding="utf-8")
    rc, _, err = env.up()
    assert rc == 0, err
    kv = _pod_env(env)
    allow = {
        "CONFIG_PATH",
        "PROSPECT_API_KEY",
        "DATA_BOAR_LICENSE_MODE",
        "DATA_BOAR_LICENSE_PATH",
        "DATA_BOAR_CREDENTIAL_STRICT",
        "DATA_BOAR_MACHINE_SEED",
    }
    assert set(kv) <= allow
    assert re.fullmatch(r"[0-9a-f]{64}", kv["PROSPECT_API_KEY"])
    assert kv["DATA_BOAR_CREDENTIAL_STRICT"] == "1"
    assert kv["CONFIG_PATH"] == "/cfg/config.yaml"
    assert kv["DATA_BOAR_MACHINE_SEED"] == "seed-de-teste"
    assert kv["DATA_BOAR_LICENSE_MODE"] == "open"
    assert "DATA_BOAR_LICENSE_PATH" not in kv
    assert not [k for k in kv if k.endswith("_ALLOWED_HOSTS") or k == "API_HOST"]
    assert (env.slug_dir("acme") / "pod.env").stat().st_mode & 0o777 == 0o600


def test_D2280_1_6_pod_env_sem_seed(env: Env) -> None:
    """D2280.1-6: without the seed, DATA_BOAR_MACHINE_SEED does not appear."""
    rc, _, err = env.up()
    assert rc == 0, err
    assert "DATA_BOAR_MACHINE_SEED" not in _pod_env(env)


def test_D2280_1_6_pod_env_enforced_aponta_licenca(env: Env) -> None:
    """D2280.1-6 / section 7: enforced mode points the license path at /lic/<name>."""
    env.inv["prospect_license_mode"] = "enforced"
    env.inv["prospect_license_file"] = str(env.tmp / "srv" / "demo.lic")
    env.write_inventory()
    env.probe.pod = {"trust_state": "trusted", "license": {"license_state": "VALID"}}
    rc, _, err = env.up()
    assert rc == 0, err
    kv = _pod_env(env)
    assert kv["DATA_BOAR_LICENSE_MODE"] == "enforced"
    assert kv["DATA_BOAR_LICENSE_PATH"] == "/lic/demo.lic"
    assert (env.slug_dir("acme") / "lic" / "demo.lic").read_text("utf-8") == "license\n"


def test_D2280_1_6_chave_extra_no_env_base_sai_5(env: Env) -> None:
    """D2280.1-6: an extra key in the base env -> exit 5 naming the key, never the value."""
    env.base_env.write_text(
        "DATA_BOAR_MACHINE_SEED=s\nAPI_HOST=valor-que-nao-pode-sair\n", encoding="utf-8"
    )
    rc, out, err = env.up()
    assert rc == 5
    assert "API_HOST" in err
    assert "valor-que-nao-pode-sair" not in out + err
    assert not [c for c in env.host.writes() if c[:2] == ["podman", "stop"]]


def test_D2280_1_6_nunca_abre_o_env_da_demo_publica(
    env: Env, monkeypatch: pytest.MonkeyPatch
) -> None:
    """D2280.1-6: a path ending in /demo/env is never opened."""
    public = env.tmp / "pub" / "demo" / "env"
    public.parent.mkdir(parents=True)
    public.write_text("DATA_BOAR_MACHINE_SEED=s\n", encoding="utf-8")
    public.chmod(0o600)
    env.inv["prospect_base_env"] = str(public)
    env.write_inventory()
    opened: list[str] = []
    real_open = Path.open

    def spy(self: Path, *a: Any, **k: Any):
        opened.append(str(self))
        return real_open(self, *a, **k)

    monkeypatch.setattr(Path, "open", spy)
    rc, _, _ = env.up()
    assert rc == 5
    assert not [p for p in opened if p.endswith("/demo/env")]


def _render_config(env: Env, slug: str = "acme") -> str:
    inv = P.load_inventory(env.inventory_path)
    return P.render_config(slug, inv)


def test_D2280_1_7_config_do_prospecto(
    env: Env, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """D2280.1-7: config.yaml loads with load_config and has the section 8 contract."""
    from config.loader import load_config

    text = _render_config(env)
    assert "${" not in text
    path = tmp_path / "config.yaml"
    path.write_text(text, encoding="utf-8")
    monkeypatch.setenv("PROSPECT_API_KEY", "a" * 64)
    cfg = load_config(path)
    targets = cfg["targets"]
    assert [t["path"] for t in targets] == ["/corpus"]
    assert all(t["type"] == "filesystem" for t in targets)
    api = cfg["api"]
    assert api["port"] == 8088
    assert api["require_api_key"] is True
    assert api["api_key_from_env"] == "PROSPECT_API_KEY"
    assert api["trusted_hosts"] == [f"acme.{DOMAIN}"]
    assert str(api["host"]) == "0.0.0" + ".0"
    assert not (cfg.get("learned_patterns") or {}).get("enabled")
    assert cfg["sqlite_path"].startswith("/data/")
    assert cfg["report"]["output_dir"] == "/data"
    fs = cfg["file_scan"]
    assert fs["scan_compressed"] is True
    assert fs["max_inner_size"] == 8388608
    assert fs["max_members"] == 200
    assert fs["max_total_uncompressed"] == 67108864
    assert fs["max_expansion_ratio"] == 50
    assert fs["scan_image_ocr"] is False
    assert cfg["rate_limit"]["max_concurrent_scans"] == 1
    assert cfg["report"]["jurisdiction_hints"]["enabled"] is True


def test_D2280_1_8_segredos_so_onde_devem(env: Env) -> None:
    """D2280.1-8: after a full up, the password is in no file; the key only in pod.env and
    <slug>.caddy; config.yaml has no key, password or hash."""
    rc, out, err = env.up()
    assert rc == 0, err
    senha = _password_sent_to_hash(env)
    assert not re.search(r"^senha: ", out, re.M)
    key = _pod_env(env)["PROSPECT_API_KEY"]
    with_key = []
    for p in env.tmp.rglob("*"):
        if not p.is_file() or p.is_socket():
            continue
        data = p.read_bytes()
        assert senha.encode() not in data, p
        if key.encode() in data:
            with_key.append(p.name)
    assert sorted(with_key) == ["acme.caddy", "pod.env"]
    cfg = (env.slug_dir("acme") / "config.yaml").read_text("utf-8")
    assert key not in cfg and _fake_hash() not in cfg


def _site_kwargs(**over: Any) -> dict[str, Any]:
    kw: dict[str, Any] = {
        "slug": "acme",
        "domain": DOMAIN,
        "proxy_port": 443,
        "pod_port": 18100,
        "tls_line": "tls internal",
        "bcrypt_hash": _fake_hash(),
        "api_key": "b" * 64,
        "caddy_dir_in_proxy": "/etc/caddy/prospects",
    }
    kw.update(over)
    return kw


def test_D2280_1_9_rota_bate_com_snapshot() -> None:
    """D2280.1-9: the rendered route matches the snapshot and has no `log`."""
    expected = (
        f"acme.{DOMAIN}:443 {{\n"
        "\ttls internal\n"
        "\tbasic_auth {\n"
        f"\t\tprospect {_fake_hash()}\n"
        "\t}\n"
        "\treverse_proxy https://127.0.0.1:18100 {\n"
        f'\t\theader_up X-API-Key "{"b" * 64}"\n'
        "\t\theader_up -Authorization\n"
        "\t\ttransport http {\n"
        "\t\t\ttls_trust_pool file /etc/caddy/prospects/acme.crt\n"
        "\t\t\ttls_server_name prospect-acme\n"
        "\t\t}\n"
        "\t}\n"
        "}\n"
    )
    text = P.render_site(**_site_kwargs())
    assert text == expected
    assert not re.search(r"^\s*log\b", text, re.M)


@pytest.mark.parametrize(
    "over",
    [
        {"bcrypt_hash": "nao-e-hash"},
        {"bcrypt_hash": _fake_hash() + "\n}"},
        {"proxy_port": "443"},
        {"pod_port": "18100 {"},
        {"api_key": "B" * 64},
        {"api_key": "b" * 63},
        {"slug": "Acme"},
        {"slug": "acme.evil"},
        {"domain": "prospect.test }"},
        {"tls_line": "tls internal {"},
        {"tls_line": "tls a\ntls b"},
        {"tls_line": "respond 200"},
        {"tls_line": "tls internal # x"},
        {"caddy_dir_in_proxy": "relativo/dir"},
        {"caddy_dir_in_proxy": "/etc/caddy dir"},
    ],
)
def test_D2280_1_9_campo_fora_do_formato_levanta(over: dict[str, Any]) -> None:
    """D2280.1-9: any field out of format raises ValueError."""
    with pytest.raises(ValueError):
        P.render_site(**_site_kwargs(**over))


def test_D2280_1_9_hash_invalido_nada_gravado(env: Env) -> None:
    """D2280.1-9: an invalid hash from the proxy writes no fragment (rollback, exit 6)."""
    env.host.hash_output = "isso-nao-e-bcrypt"
    rc, _, _ = env.up()
    assert rc == 6
    assert not list(env.caddy_dir.iterdir())
    env.assert_clean("acme")


def test_D2280_1_10_certificado_do_pod(env: Env) -> None:
    """D2280.1-10: openssl argv makes EC P-256, SAN prospect-acme, 2 days; tls.crt copied to
    <caddy_dir>/acme.crt."""
    rc, _, err = env.up()
    assert rc == 0, err
    ossl = [c for c in env.host.calls if c[:1] == ["openssl"]]
    assert len(ossl) == 1
    argv = ossl[0]
    joined = " ".join(argv)
    assert "-x509" in argv and "-nodes" in argv
    assert "ec_paramgen_curve:prime256v1" in joined
    assert "subjectAltName=DNS:prospect-acme" in joined
    assert argv[argv.index("-days") + 1] == "2"
    assert argv == P.openssl_argv("acme", env.slug_dir("acme"))
    crt = env.slug_dir("acme") / "tls.crt"
    assert (env.caddy_dir / "acme.crt").read_bytes() == crt.read_bytes()


# --------------------------------------------------------------------------- port, session
def test_D2280_1_11_porta_ocupada_sai_4(env: Env) -> None:
    """D2280.1-11: prospect_port busy -> exit 4 and nothing changes, not even the dashboard."""
    env.busy_ports.add(18100)
    rc, _, err = env.up()
    assert rc == 4
    assert "18100" in err
    assert env.host.writes() == []
    assert env.host.state("dashboard") == "running"
    assert not env.slot_json().exists()


def test_D2280_1_12_dois_up_concorrentes(env: Env) -> None:
    """D2280.1-12: two concurrent ups of different slugs with the real lock (two flows in
    threads, each with its own descriptor): one creates, the other exits 4, and the
    dashboard is stopped once."""
    entered = threading.Event()
    release = threading.Event()

    def hold(unit: str) -> None:
        entered.set()
        assert release.wait(10)

    env.host.on_start_unit = hold
    results: dict[str, Any] = {}

    def worker(slug: str) -> None:
        try:
            results[slug] = env.up(slug)
        except BaseException as exc:  # surfaced below, not as a thread warning
            results[slug] = exc
            entered.set()

    t1 = threading.Thread(target=worker, args=("acme",))
    t1.start()
    assert entered.wait(10)
    if isinstance(results.get("acme"), BaseException):
        raise results["acme"]
    env.host.on_start_unit = None
    t2 = threading.Thread(target=worker, args=("bravo",))
    t2.start()
    time.sleep(0.3)
    assert "bravo" not in results  # still waiting for the lock
    release.set()
    t1.join(15)
    t2.join(15)
    assert results["acme"][0] == 0, results["acme"]
    assert results["bravo"][0] == 4, results["bravo"]
    stops = [c for c in env.host.calls if c[:2] == ["podman", "stop"]]
    assert len(stops) == 1


def test_D2280_1_13_outro_prospecto_ativo_sai_4(env: Env) -> None:
    """D2280.1-13: with acme active, up bravo -> exit 4 naming acme, no write call."""
    rc, _, err = env.up("acme")
    assert rc == 0, err
    expires = env.state("acme")["expires_at"]
    before = len(env.host.calls)
    rc, out, err = env.up("bravo")
    assert rc == 4
    assert f"já há um prospecto ativo: acme até {expires}" in out + err
    assert [c for c in env.host.calls[before:] if not is_read(c)] == []
    assert not env.slug_dir("bravo").exists()


def test_D2280_1_13_memoria_insuficiente_sai_4(env: Env) -> None:
    """D2280.1-13: MemAvailable below 828 MiB 15 s after the stop -> exit 4, restore_slot
    called and nothing of the pod created."""
    env.mem_mib = 827
    rc, _, err = env.up()
    assert rc == 4
    assert "mem" in err.lower()
    assert [c for c in env.host.calls if c[:1] == ["systemd-run"]]
    assert not [c for c in env.host.calls if c[-1:] == ["demo-prospect@acme.service"]
                and "start" in c]  # fmt: skip
    assert not env.slug_dir("acme").exists()
    assert env.host.state("dashboard") == "running"
    assert env.clock.now() - T0 >= timedelta(seconds=15)


@pytest.mark.parametrize(
    ("mode", "stop"),
    [
        ("podman", "podman stop -t 20 dashboard"),
        ("systemd", "systemctl --user stop dashboard.service"),
    ],
)
def test_parada_da_dashboard_falha_sai_4(env: Env, mode: str, stop: str) -> None:
    """S3 of the PR #2292 review: a failed stop of the dashboard (exit code != 0) restores
    the slot and exits 4, like the memory path of D2280.1-13; no pod is created."""
    env.inv["prospect_slot_mode"] = mode
    env.write_inventory()
    env.host.timer_active = True
    env.host.fail[stop] = (125, "", "Error: stop failed")
    rc, _, err = env.up()
    assert rc == 4, err
    assert "parada da dashboard falhou (rc=125)" in err
    assert not [c for c in env.host.calls if c[-1:] == ["demo-prospect@acme.service"]
                and "start" in c]  # fmt: skip
    assert not env.slug_dir("acme").exists()
    assert not env.slot_json().exists()
    assert env.host.timer_active is True
    assert env.host.state("dashboard") == "running"


def test_rollback_do_up_religa_mesmo_com_teardown_quebrado(
    env: Env, monkeypatch: pytest.MonkeyPatch
) -> None:
    """S4 of the PR #2292 review: if the teardown of the up rollback raises (an OSError
    removing a fragment), restore_slot still runs and the exit code of the up stays."""
    env.probe.pod = None  # no pod health -> 7 (D2280.1-17a)

    def broken(self: Any, slug: str, *, from_unit: bool = False) -> list[str]:
        raise OSError("fragmento preso")

    monkeypatch.setattr(P.Cli, "teardown", broken)
    rc, _, err = env.up()
    assert rc == 7, err
    assert [c for c in env.host.calls if c[:1] == ["systemd-run"]]
    assert env.host.state("dashboard") == "running"
    assert not env.slot_json().exists()


# --------------------------------------------------------------------------- up
def test_D2280_1_13b_up_exige_password_stdin(env: Env) -> None:
    """D-48: sem --password-stdin no cenário limpo → P0, stderr da seção 1, sem readline."""
    fp_before = env.tree_fingerprint()
    writes_before = len(env.host.writes())
    loads_before = len(env.admin.loads)
    tracked = TrackingStdin("", env=env)
    rc, _out, err = env.cli("up", "acme", "--stop-dashboard", stdin=tracked)
    _assert_p0_dec22(
        env,
        rc,
        err,
        "use --password-stdin e envie a senha pelo stdin (mínimo 20 caracteres)",
        fp_before=fp_before,
        writes_before=writes_before,
        loads_before=loads_before,
        tracked=tracked,
        readline_expect=0,
    )


def test_D2280_DEC22_D49_senha_curta_ou_vazia_linha(env: Env) -> None:
    """D-49: 19 caracteres ou só newline → P0+, senha precisa de pelo menos 20."""
    fp_before = env.tree_fingerprint()
    writes_before = len(env.host.writes())
    loads_before = len(env.admin.loads)
    calls_before = len(env.host.calls)
    for senha, expect_read in (("a" * 19 + "\n", 1), ("\n", 1)):
        tracked = TrackingStdin(senha, env=env)
        rc, _out, err = env.cli(
            "up",
            "acme",
            "--stop-dashboard",
            "--password-stdin",
            stdin=tracked,
        )
        _assert_p0_plus_dec22(
            env,
            rc,
            err,
            "senha precisa de pelo menos 20 caracteres",
            fp_before=fp_before,
            writes_before=writes_before,
            loads_before=loads_before,
            calls_before=calls_before,
            lock_existed_before=False,
            tracked=tracked,
            readline_expect=expect_read,
        )


def test_D2280_DEC22_D50_stdin_vazio_eof(env: Env) -> None:
    """D-50: EOF imediato → P0+ com senha vazia."""
    tracked = TrackingStdin("", env=env)
    fp_before = env.tree_fingerprint()
    rc, _out, err = env.cli(
        "up",
        "acme",
        "--stop-dashboard",
        "--password-stdin",
        stdin=tracked,
    )
    _assert_p0_plus_dec22(
        env,
        rc,
        err,
        "senha vazia: envie pelo stdin com --password-stdin",
        fp_before=fp_before,
        writes_before=len(env.host.writes()),
        loads_before=len(env.admin.loads),
        calls_before=len(env.host.calls),
        lock_existed_before=False,
        tracked=tracked,
        readline_expect=1,
    )


def test_D2280_DEC22_D51_stdin_indisponivel(env: Env) -> None:
    """D-51: None, fluxo fechado (ValueError) ou OSError → P0+."""
    needle = "stdin indisponível: envie a senha pelo stdin com --password-stdin"
    fp_before = env.tree_fingerprint()
    writes_before = len(env.host.writes())
    loads_before = len(env.admin.loads)
    calls_before = len(env.host.calls)

    c = env.ctx()
    c.in_ = None
    rc = P.main(["up", "acme", "--stop-dashboard", "--password-stdin"], c)
    _assert_p0_plus_dec22(
        env,
        rc,
        c.err.getvalue(),
        needle,
        fp_before=fp_before,
        writes_before=writes_before,
        loads_before=loads_before,
        calls_before=calls_before,
        lock_existed_before=False,
    )

    closed = _ClosedStringIO()
    closed.close()
    c = env.ctx()
    c.in_ = closed
    rc = P.main(["up", "acme", "--stop-dashboard", "--password-stdin"], c)
    _assert_p0_plus_dec22(
        env,
        rc,
        c.err.getvalue(),
        needle,
        fp_before=fp_before,
        writes_before=writes_before,
        loads_before=loads_before,
        calls_before=calls_before,
        lock_existed_before=False,
    )

    c = env.ctx()
    c.in_ = _BrokenStdin()
    rc = P.main(["up", "acme", "--stop-dashboard", "--password-stdin"], c)
    _assert_p0_plus_dec22(
        env,
        rc,
        c.err.getvalue(),
        needle,
        fp_before=fp_before,
        writes_before=writes_before,
        loads_before=loads_before,
        calls_before=calls_before,
        lock_existed_before=False,
    )


def test_D2280_DEC22_D52_stdin_ilegivel_utf8(env: Env) -> None:
    """D-52: bytes inválidos ou substituto solto → P0+ senha ilegível."""
    needle = "senha ilegível: envie texto UTF-8 pelo stdin"
    fp_before = env.tree_fingerprint()
    writes_before = len(env.host.writes())
    loads_before = len(env.admin.loads)
    calls_before = len(env.host.calls)

    strict = io.TextIOWrapper(
        io.BytesIO(b"\xff\n"),
        encoding="utf-8",
        errors="strict",
    )
    c = env.ctx()
    c.in_ = strict
    rc = P.main(["up", "acme", "--stop-dashboard", "--password-stdin"], c)
    _assert_p0_plus_dec22(
        env,
        rc,
        c.err.getvalue(),
        needle,
        fp_before=fp_before,
        writes_before=writes_before,
        loads_before=loads_before,
        calls_before=calls_before,
        lock_existed_before=False,
    )

    surrogate_line = (
        codecs.decode(b"a" * 20 + b"\xed\xa0\x80", "utf-8", "surrogateescape") + "\n"
    )
    tracked = TrackingStdin(surrogate_line, env=env)
    c = env.ctx()
    c.in_ = tracked
    rc = P.main(["up", "acme", "--stop-dashboard", "--password-stdin"], c)
    _assert_p0_plus_dec22(
        env,
        rc,
        c.err.getvalue(),
        needle,
        fp_before=fp_before,
        writes_before=writes_before,
        loads_before=loads_before,
        calls_before=calls_before,
        lock_existed_before=False,
        tracked=tracked,
        readline_expect=1,
    )


def _restos_acme_falhou(env: Env) -> None:
    """Restos como no D-16, com a dashboard de teste ainda ``running``."""
    env.host.units["demo-prospect@acme.service"] = "failed"
    env.slug_dir("acme").mkdir(parents=True, exist_ok=True)
    (env.slug_dir("acme") / "state.json").write_text(
        json.dumps(
            {
                "slug": "acme",
                "expires_at": _z(T0 + timedelta(minutes=30)),
                "port": env.inv["prospect_port"],
            }
        ),
        encoding="utf-8",
    )
    env.host.add_container(
        "prospect-acme",
        IMAGE,
        "exited",
        labels={"databoar.prospect": "acme"},
    )


def test_D2280_DEC22_D53_restos_sem_entrada_valida_sem_teardown(env: Env) -> None:
    """D-53: restos de acme e recusa por senha → P0, sem teardown de restos."""
    _restos_acme_falhou(env)
    assert env.slug_dir("acme").exists()
    assert env.host.state("dashboard") == "running"
    fp_before = env.tree_fingerprint()
    writes_before = len(env.host.writes())
    loads_before = len(env.admin.loads)
    tracked = TrackingStdin("", env=env)
    rc, _out, err = env.cli("up", "acme", "--stop-dashboard", stdin=tracked)
    _assert_p0_dec22(
        env,
        rc,
        err,
        "use --password-stdin e envie a senha pelo stdin (mínimo 20 caracteres)",
        fp_before=fp_before,
        writes_before=writes_before,
        loads_before=loads_before,
        tracked=tracked,
        readline_expect=0,
        expect_no_slot=True,
        dash_state="running",
    )
    assert env.slug_dir("acme").exists()
    assert not any(c[:2] == ["podman", "rm"] for c in env.host.calls[writes_before:])

    _restos_acme_falhou(env)
    fp_before = env.tree_fingerprint()
    writes_before = len(env.host.writes())
    tracked = TrackingStdin(f"{TEST_OPERATOR_PASSWORD}\n", env=env)
    rc, _out, err = env.cli(
        "up",
        "acme",
        "--password-stdin",
        stdin=tracked,
    )
    _assert_p0_dec22(
        env,
        rc,
        err,
        "repita com --stop-dashboard",
        fp_before=fp_before,
        writes_before=writes_before,
        loads_before=loads_before,
        tracked=tracked,
        readline_expect=1,
        expect_no_slot=True,
        dash_state="running",
    )
    assert env.slug_dir("acme").exists()


@pytest.mark.parametrize(
    "payload",
    [
        "z" * 20,
        "z" * 20 + "\r\n",
        f"{TEST_OPERATOR_PASSWORD}\nsegunda-linha-ignorada\n",
    ],
    ids=["sem-newline", "crlf", "primeira-linha-so"],
)
def test_D2280_DEC22_D54_leitura_antes_do_lock_criacao(env: Env, payload: str) -> None:
    """D-54 (criação): readline uma vez antes do lock; hash-password recebe senha + \\n."""
    tracked = TrackingStdin(payload, env=env)
    c = env.ctx()
    c.in_ = tracked
    rc = P.main(["up", "acme", "--stop-dashboard", "--password-stdin"], c)
    assert rc == 0, c.err.getvalue()
    assert tracked.readline_calls == 1
    assert tracked.lock_existed_at_read is False
    assert tracked.executor_calls_at_read == 0
    esperada = payload.splitlines()[0].rstrip("\r")
    assert _password_sent_to_hash(env).rstrip("\n") == esperada


def test_D2280_DEC22_D54_idempotente_com_senha_valida_ou_curta(env: Env) -> None:
    """D-54: slug ativo — senha válida idempotente; 19 caracteres → P0+ no passo 1b."""
    rc, _out1, _ = env.up()
    assert rc == 0
    fp = {p: p.read_bytes() for p in env.tmp.rglob("*") if p.is_file()}
    loads = len(env.admin.loads)
    before_calls = len(env.host.calls)
    rc, out2, err = env.cli(
        "up",
        "acme",
        "--password-stdin",
        stdin=f"{TEST_OPERATOR_PASSWORD}\n",
    )
    assert rc == 0, err
    assert [c for c in env.host.calls[before_calls:] if not is_read(c)] == []
    assert len(env.admin.loads) == loads
    assert {p: p.read_bytes() for p in env.tmp.rglob("*") if p.is_file()} == fp
    assert "senha já emitida" in out2

    calls_before_short = len(env.host.calls)
    lock_before_short = env.lock_path().exists()
    tracked = TrackingStdin("x" * 19 + "\n", env=env)
    fp_before = env.tree_fingerprint()
    rc, _out, err = env.cli(
        "up",
        "acme",
        "--password-stdin",
        stdin=tracked,
    )
    _assert_p0_plus_dec22(
        env,
        rc,
        err,
        "senha precisa de pelo menos 20 caracteres",
        fp_before=fp_before,
        writes_before=len(env.host.writes()),
        loads_before=len(env.admin.loads),
        calls_before=calls_before_short,
        lock_existed_before=lock_before_short,
        tracked=tracked,
        readline_expect=1,
        expect_no_slot=False,
        dash_state="exited",
    )


def test_D2280_DEC22_D55_rotate_password_sem_stdin(env: Env) -> None:
    """D-55: --rotate-password sem stdin ou com senha curta → P0+."""
    rc, _out, _ = env.up()
    assert rc == 0
    fp_before = env.tree_fingerprint()
    frag = (env.caddy_dir / "acme.caddy").read_bytes()
    loads_before = len(env.admin.loads)
    calls_before = len(env.host.calls)
    lock_before = env.lock_path().exists()
    rc, _out, err = env.cli("up", "acme", "--rotate-password")
    _assert_p0_plus_dec22(
        env,
        rc,
        err,
        "use --password-stdin para enviar a nova senha pelo stdin",
        fp_before=fp_before,
        writes_before=len(env.host.writes()),
        loads_before=loads_before,
        calls_before=calls_before,
        lock_existed_before=lock_before,
        expect_no_slot=False,
        dash_state="exited",
    )
    assert (env.caddy_dir / "acme.caddy").read_bytes() == frag

    tracked = TrackingStdin("y" * 19 + "\n", env=env)
    fp_before = env.tree_fingerprint()
    loads_before = len(env.admin.loads)
    calls_before = len(env.host.calls)
    lock_before = env.lock_path().exists()
    rc, _out, err = env.cli(
        "up",
        "acme",
        "--rotate-password",
        "--password-stdin",
        stdin=tracked,
    )
    _assert_p0_plus_dec22(
        env,
        rc,
        err,
        "senha precisa de pelo menos 20 caracteres",
        fp_before=fp_before,
        writes_before=len(env.host.writes()),
        loads_before=loads_before,
        calls_before=calls_before,
        lock_existed_before=lock_before,
        tracked=tracked,
        readline_expect=1,
        expect_no_slot=False,
        dash_state="exited",
    )
    assert (env.caddy_dir / "acme.caddy").read_bytes() == frag
    assert not any(c[-1:] == ["hash-password"] for c in env.host.calls[calls_before:])


def test_D2280_1_14_caminho_feliz_ordem_e_saida(env: Env) -> None:
    """D2280.1-14: call order of sections 3 and 10 and the exact five stdout lines."""
    rc, out, err = env.up("acme", "--ttl", "30m")
    assert rc == 0, err
    h = env.host
    i_stop = h.index(lambda c: c[:4] == ["podman", "stop", "-t", "20"])
    assert h.calls[i_stop][-1] == "dashboard"
    assert "demo-prospect/slot.json" in h.snaps[i_stop]
    i_reload = h.index(lambda c: c[2:3] == ["daemon-reload"])
    for rel in ("state.json", "state.env", "pod.env", "config.yaml", "profile.yaml"):
        assert f"demo-prospect/acme/{rel}" in h.snaps[i_reload], rel
    i_start = h.index(lambda c: c[2:] == ["start", "demo-prospect@acme.service"])
    i_probe = h.index(lambda c: c[0] == "#probe" and ":18100/" in c[1])
    i_hash = h.index(lambda c: c[-1:] == ["hash-password"])
    assert i_stop < i_reload < i_start < i_probe < i_hash
    assert h.inputs[i_hash] and h.inputs[i_hash].strip()
    assert len(env.admin.loads) == 1
    assert env.probe.route_calls == [(f"acme.{DOMAIN}", 8443)]
    lines = _session_lines(out)
    exp = env.state("acme")["expires_at"]
    assert exp == _z(T0 + timedelta(minutes=30)) or exp.endswith("Z")
    assert len(lines) == 4
    assert lines[0] == f"url: https://acme.{DOMAIN}/"
    assert lines[1] == "usuário: prospect"
    assert lines[2] == f"expires_at: {exp}"
    assert lines[3] == (
        f"ATENÇÃO: a dashboard pública está FORA DO AR até prospect-down acme ou {exp}"
    )
    assert _password_sent_to_hash(env) == TEST_OPERATOR_PASSWORD
    assert not re.search(r"^senha: ", out, re.M)
    first_stamp = re.search(r"\d{4}-\d\d-\d\dT[\d:.]+Z", out)
    assert first_stamp and first_stamp.group(0) == exp
    assert "+00:00" not in out
    assert env.state("acme")["port"] == 18100
    assert env.state("acme")["phase"] == "A"


def test_D2280_1_15_up_repetido_idempotente(env: Env) -> None:
    """D2280.1-15: a second up of the active slug (no flag) exits 0 with the same URL and
    deadline and 'senha já emitida', with no start/stop/load and no file changed."""
    rc, out1, err = env.up()
    assert rc == 0, err
    files = {p: p.read_bytes() for p in env.tmp.rglob("*") if p.is_file()}
    before = len(env.host.calls)
    loads = len(env.admin.loads)
    rc, out2, err = env.cli("up", "acme")
    assert rc == 0, err
    assert [c for c in env.host.calls[before:] if not is_read(c)] == []
    assert len(env.admin.loads) == loads
    assert {p: p.read_bytes() for p in env.tmp.rglob("*") if p.is_file()} == files
    lines = _session_lines(out2)
    assert lines[0] == _session_lines(out1)[0]
    assert (
        "senha já emitida; use --rotate-password com --password-stdin para trocar"
        in lines
    )
    assert not re.search(r"^senha:", out2, re.M)
    assert _session_lines(out1)[2] in lines
    assert lines[-1].startswith("ATENÇÃO: a dashboard pública está FORA DO AR")


def test_D2280_1_15_rotate_password(env: Env) -> None:
    """Section 1: --rotate-password with --password-stdin hashes a new operator password."""
    rc, out1, _ = env.up()
    assert rc == 0
    rc, out2, err = env.cli(
        "up",
        "acme",
        "--rotate-password",
        "--password-stdin",
        stdin=f"{TEST_OPERATOR_PASSWORD_B}\n",
    )
    assert rc == 0, err
    assert _password_sent_to_hash(env, 0) == TEST_OPERATOR_PASSWORD
    assert _password_sent_to_hash(env, 1) == TEST_OPERATOR_PASSWORD_B
    assert not re.search(r"^senha: ", out1 + out2, re.M)
    assert len(env.admin.loads) == 2


@pytest.mark.parametrize("resto", ["failed", "vencido"])
def test_D2280_1_16_restos_do_mesmo_slug(env: Env, resto: str) -> None:
    """D2280.1-16: with leftovers of acme (failed unit or expired), teardown runs before and
    the creation is new."""
    rc, out1, _ = env.up()
    assert rc == 0
    if resto == "failed":
        env.host.units["demo-prospect@acme.service"] = "failed"
        env.host.containers.pop("prospect-acme")
    else:
        env.clock.advance(31 * 60)
    before = len(env.host.calls)
    rc, out2, err = env.up()
    assert rc == 0, err
    new = env.host.calls[before:]
    i_rm = next(i for i, c in enumerate(new) if c[:2] == ["podman", "rm"])
    i_start = next(
        i for i, c in enumerate(new) if c[2:] == ["start", "demo-prospect@acme.service"]
    )
    assert i_rm < i_start
    assert not re.search(r"^senha: ", out2, re.M)
    assert env.state("acme")["created_at"] == _z(env.clock.now())


def _assert_rollback(env: Env) -> None:
    assert [c for c in env.host.calls if c[:1] == ["systemd-run"]]
    env.assert_clean("acme")
    assert not env.slot_json().exists()


def test_D2280_1_17a_saude_sem_resposta_sai_7(env: Env) -> None:
    """D2280.1-17a: no pod health in 120 s -> 7 with teardown and restore_slot."""
    env.probe.pod = None
    rc, _, _ = env.up()
    assert rc == 7
    assert env.clock.now() - T0 >= timedelta(seconds=120)
    _assert_rollback(env)


def test_D2280_1_17b_load_400_sai_6(env: Env) -> None:
    """D2280.1-17b: /load 400 -> fragments deleted, /load again, exit 6, rollback."""
    env.admin.codes = [400]
    rc, _, _ = env.up()
    assert rc == 6
    assert len(env.admin.loads) >= 2
    assert not list(env.caddy_dir.iterdir())
    _assert_rollback(env)


def test_D2280_1_17c_rota_responde_200_sai_6(env: Env) -> None:
    """D2280.1-17c: the route check gets 200 instead of 401 -> exit 6, rollback."""
    env.probe.route_code = 200
    rc, _, _ = env.up()
    assert rc == 6
    assert not list(env.caddy_dir.iterdir())
    _assert_rollback(env)


def test_D2280_1_17d_systemctl_start_falha_sai_7(env: Env) -> None:
    """D2280.1-17d: systemctl start fails -> exit 7, rollback."""
    env.host.fail["start demo-prospect@acme.service"] = (1, "", "job failed")
    rc, _, _ = env.up()
    assert rc == 7
    _assert_rollback(env)


@pytest.mark.parametrize(
    ("change", "item"),
    [
        ("dropin", "10-host.conf"),
        ("socket", "prospect_caddy_admin_socket"),
        ("podman4", "Podman"),
        ("systemd-run", "systemd-run"),
        ("openssl", "openssl"),
    ],
)
def test_D2280_1_18_prerequisito_ausente_sai_5(
    env: Env, change: str, item: str
) -> None:
    """D2280.1-18: a missing prerequisite -> exit 5 naming the item, no podman stop."""
    if change == "dropin":
        (env.quadlet_dir / "demo-prospect@.container.d" / "10-host.conf").unlink()
    elif change == "socket":
        Path(env.inv["prospect_caddy_admin_socket"]).unlink()
    elif change == "podman4":
        env.host.podman_version = "4.9.3"
    else:
        env.which_missing.add(change)
    rc, _, err = env.up()
    assert rc == 5
    assert item in err
    assert not [c for c in env.host.calls if c[:2] == ["podman", "stop"]]


SECRET = "VALOR-QUE-NAO-PODE-SAIR"


@pytest.mark.parametrize(
    ("mutate", "key"),
    [
        ("absent", ""),
        ("mode644", ""),
        ("unknown", "prospect_dominio"),
        ("missing", "prospect_domain"),
        ("license", "prospect_license_file"),
        ("relative", "prospect_corpus_dir"),
        ("nonexistent", "prospect_profile_file"),
        ("colon", "prospect_corpus_dir"),
        ("comma", "prospect_corpus_dir"),
        ("newline", "prospect_corpus_dir"),
        ("type", "prospect_port"),
        ("notjson", ""),
    ],
)
def test_D2280_1_18_inventario_invalido_sai_5(env: Env, mutate: str, key: str) -> None:
    """D2280.1-18 (revision 1): inventory errors -> exit 5 with the key name, no value."""
    inv = env.inv
    if mutate == "unknown":
        inv[key] = SECRET
    elif mutate == "missing":
        del inv[key]
    elif mutate == "license":
        inv["prospect_license_mode"] = "enforced"
    elif mutate == "relative":
        inv[key] = f"srv/{SECRET}"
    elif mutate == "nonexistent":
        inv[key] = f"/nao/existe/{SECRET}"
    elif mutate in ("colon", "comma", "newline"):
        sep = {"colon": ":", "comma": ",", "newline": "\n"}[mutate]
        bad = env.tmp / f"x{sep}{SECRET}"
        bad.mkdir()
        inv[key] = str(bad)
    elif mutate == "type":
        inv[key] = "18100"
    env.write_inventory(0o644 if mutate == "mode644" else 0o600)
    if mutate == "absent":
        env.inventory_path.unlink()
    if mutate == "notjson":
        env.inventory_path.write_text("[1, 2]", encoding="utf-8")
    rc, out, err = env.up()
    assert rc == 5, (rc, err)
    assert SECRET not in out + err
    if key:
        assert key in err
    assert not [c for c in env.host.calls if c[:2] == ["podman", "stop"]]
    assert len(err.strip().splitlines()) == 1


def test_D2280_1_18_inventario_padrao_no_home(
    env: Env, monkeypatch: pytest.MonkeyPatch
) -> None:
    """D2280.1-18: without PROSPECT_INVENTORY, the CLI reads ~/demo/prospect/inventory.json."""
    monkeypatch.delenv("PROSPECT_INVENTORY")
    target = env.home / "demo" / "prospect" / "inventory.json"
    target.parent.mkdir(parents=True)
    env.inventory_path.rename(target)
    rc, out, err = env.cli("list")
    assert rc == 0, err
    assert "dashboard: no ar" in out
    target.unlink()
    rc, _, err = env.cli("list")
    assert rc == 5


@pytest.mark.parametrize(
    ("mode", "state", "ok"),
    [
        ("enforced", "MACHINE_MISMATCH", False),
        ("enforced", "REVOKED", False),
        ("enforced", "UNKNOWN", False),
        ("open", "VALID", False),
        ("enforced", "VALID", True),
        ("enforced", "GRACE", True),
        ("open", "OPEN", True),
    ],
)
def test_D2280_1_19_licenca_e_confianca(
    env: Env, mode: str, state: str, ok: bool
) -> None:
    """D2280.1-19: license_state outside the allowed list -> 7 with rollback."""
    env.inv["prospect_license_mode"] = mode
    if mode == "enforced":
        env.inv["prospect_license_file"] = str(env.tmp / "srv" / "demo.lic")
    env.write_inventory()
    env.probe.pod = {"trust_state": "trusted", "license": {"license_state": state}}
    rc, _, err = env.up()
    if ok:
        assert rc == 0, err
    else:
        assert rc == 7
        _assert_rollback(env)


def test_D2280_1_19_trust_degraded_sai_7(env: Env) -> None:
    """D2280.1-19: top-level trust_state degraded -> 7."""
    env.probe.pod = {"trust_state": "degraded", "license": {"license_state": "OPEN"}}
    rc, _, _ = env.up()
    assert rc == 7
    _assert_rollback(env)


def test_D2280_1_20_nunca_recria_a_dashboard(env: Env) -> None:
    """D2280.1-20: checked for every test by the ``env`` fixture; here a full cycle."""
    assert env.up()[0] == 0
    assert env.cli("down", "acme")[0] == 0
    starts = [c for c in env.host.calls if "start" in c and "podman" in c]
    assert starts and all(c[0] == "systemd-run" for c in starts)


# --------------------------------------------------------------------------- slot swap
def test_D2280_1_38_sem_flag_sai_2_so_leituras(env: Env) -> None:
    """D2280.1-38: without --stop-dashboard -> exit 2 with the message, reads only."""
    rc, out, err = env.cli("up", "acme")
    assert rc == 2
    assert (
        "a dashboard pública vai ficar fora do ar durante a sessão; "
        "para confirmar, repita com --stop-dashboard"
    ) in out + err
    assert env.host.writes() == []
    assert not (env.runtime / "demo-prospect" / "acme").exists()


def test_D2280_1_39_ordem_da_troca(env: Env) -> None:
    """D2280.1-39: slot.json, then stop demo-reset.timer if active, then podman stop."""
    env.host.timer_active = True
    rc, _, err = env.up()
    assert rc == 0, err
    h = env.host
    i_timer = h.index(lambda c: c[2:] == ["stop", "demo-reset.timer"])
    i_stop = h.index(lambda c: c[:2] == ["podman", "stop"])
    assert 0 <= i_timer < i_stop
    assert "demo-prospect/slot.json" in h.snaps[i_timer]
    slot = json.loads(env.slot_json().read_text("utf-8"))
    assert slot["slot"] == "dashboard"
    assert slot["taken_by"] == "acme"
    assert slot["reset_timer_was_active"] is True
    assert slot["mode"] == "podman"
    assert slot["taken_at"].endswith("Z")
    assert env.slot_json().stat().st_mode & 0o777 == 0o600


def test_D2280_1_40_tres_instancias_sai_4(env: Env) -> None:
    """D2280.1-40: three Data Boar instances running -> 4, no write."""
    env.host.add_container("outra", "localhost/data_boar:dev", "running")
    rc, _, _ = env.up()
    assert rc == 4
    assert env.host.writes() == []


def test_D2280_1_40_duas_sem_a_dashboard_sai_4(env: Env) -> None:
    """D2280.1-40: two running and none is the dashboard -> 4, no write."""
    env.host.containers["dashboard"]["State"] = "exited"
    env.host.add_container("outra", IMAGE, "running")
    rc, _, _ = env.up()
    assert rc == 4
    assert env.host.writes() == []


def test_D2280_1_40_dashboard_ja_parada(env: Env) -> None:
    """D2280.1-40: dashboard already stopped and only apresentacao -> no stop, and the
    slot record says dashboard_was_running false."""
    env.host.containers["dashboard"]["State"] = "exited"
    env.inv["prospect_image"] = "localhost/outra-imagem:1"
    env.write_inventory()
    rc, out, err = env.up("acme")
    assert rc == 0, err
    assert not [c for c in env.host.calls if c[:2] == ["podman", "stop"]]
    slot = json.loads(env.slot_json().read_text("utf-8"))
    assert slot["dashboard_was_running"] is False
    assert "ATENÇÃO: a dashboard pública está FORA DO AR" in out


def test_D2280_1_40_imagem_do_inventario_conta(env: Env) -> None:
    """Section 3: a container with prospect_image counts even without data_boar in the name."""
    env.inv["prospect_image"] = "registry.example/assinada@sha256:" + "0" * 64
    env.write_inventory()
    env.host.add_container("terceira", env.inv["prospect_image"], "running")
    rc, _, _ = env.up()
    assert rc == 4


def test_D2280_1_41_modo_systemd(env: Env) -> None:
    """D2280.1-41: systemd mode stops and starts dashboard.service, never podman stop/start."""
    env.inv["prospect_slot_mode"] = "systemd"
    env.write_inventory()
    assert env.up()[0] == 0
    assert env.cli("down", "acme")[0] == 0
    calls = env.host.calls
    assert ["systemctl", "--user", "stop", "dashboard.service"] in calls
    assert ["systemctl", "--user", "start", "dashboard.service"] in calls
    assert not [c for c in calls if c[:2] == ["podman", "stop"]]
    assert not [c for c in calls if c[:1] == ["systemd-run"]]


# --------------------------------------------------------------------------- restore, alert
def test_D2280_1_42_restore_slot_ok(env: Env) -> None:
    """D2280.1-42: restore_slot uses systemd-run --scope, restarts the timer if it was
    active, accepts trusted+integrity.validated, deletes slot.json and exits 0."""
    env.host.timer_active = True
    assert env.up()[0] == 0
    assert env.host.timer_active is False
    _pod_gone(env, "acme")  # revision 2: restore-slot only restarts a free slot
    before = len(env.host.calls)
    rc, out, err = env.cli("restore-slot")
    assert rc == 0, err
    new = env.host.calls[before:]
    run = [c for c in new if c[:1] == ["systemd-run"]]
    assert len(run) == 1
    assert re.fullmatch(r"--unit=databoar-slot-\d+", run[0][4])
    assert run[0][5:] == ["podman", "start", "dashboard"]
    i_run = new.index(run[0])
    i_timer = new.index(["systemctl", "--user", "start", "demo-reset.timer"])
    assert i_run < i_timer
    assert not env.slot_json().exists()
    assert "dashboard no ar" in out


def test_D2280_1_42_integrity_no_topo_nao_passa(env: Env) -> None:
    """D2280.1-42 (revision 1): integrity_state at top level without `integrity` fails."""
    assert env.up()[0] == 0
    _pod_gone(env, "acme")  # revision 2: restore-slot only restarts a free slot
    env.probe.slot = {"trust_state": "trusted", "integrity_state": "validated"}
    rc, _, _ = env.cli("restore-slot")
    assert rc == 8


def test_D2280_1_43_saude_nao_volta_alerta_uma_vez(env: Env) -> None:
    """D2280.1-43: no validated health in 180 s -> 8, one emit, ALERT, slot.json stays;
    the next reap retries without a second emit; recovery clears both."""
    assert env.up()[0] == 0
    env.probe.slot = {
        "trust_state": "trusted",
        "integrity": {"integrity_state": "tampered"},
    }
    t_before = env.clock.now()
    rc, _, err = env.cli("down", "acme")
    assert rc == 8
    assert env.clock.now() - t_before >= timedelta(seconds=180)
    assert len(env.alerter.emitted) == 1
    msg = env.alerter.emitted[0]
    assert msg.startswith("dashboard não voltou após a sessão de prospecto acme: ")
    alert = env.alert_path.read_text("utf-8").splitlines()
    assert len(alert) == 1
    assert re.match(r"ALERT \d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ sessão acme: \S", alert[0])
    assert env.alert_path.stat().st_mode & 0o777 == 0o600
    assert env.slot_json().exists()
    key_like = re.compile(r"[0-9a-f]{64}")
    assert not key_like.search(msg) and not key_like.search(alert[0])
    runs = len([c for c in env.host.calls if c[:1] == ["systemd-run"]])
    rc, _, _ = env.cli("reap")
    assert rc == 8
    assert len([c for c in env.host.calls if c[:1] == ["systemd-run"]]) == runs + 1
    assert len(env.alerter.emitted) == 1
    env.probe.slot = {
        "trust_state": "trusted",
        "integrity": {"integrity_state": "validated"},
    }
    rc, _, err = env.cli("reap")
    assert rc == 0, err
    assert not env.slot_json().exists()
    assert not env.alert_path.exists()
    assert [m for m in env.alerter.infos if "recuperada" in m]
    assert len(env.alerter.emitted) == 1


def test_D2280_1_43_start_falha_sai_8_na_hora(env: Env) -> None:
    """D2280.1-43 (revision 1): systemd-run ... podman start rc 125 -> 8 at once, no health
    probe, reason 'start falhou (rc=125)'."""
    assert env.up()[0] == 0
    env.host.dash_start_rc = 125
    probes = len(env.probe.calls)
    t_before = env.clock.now()
    rc, _, _ = env.cli("down", "acme")
    assert rc == 8
    assert len(env.probe.calls) == probes
    assert env.clock.now() - t_before < timedelta(seconds=5)
    assert env.alerter.emitted == [
        "dashboard não voltou após a sessão de prospecto acme: start falhou (rc=125)"
    ]
    assert "start falhou (rc=125)" in env.alert_path.read_text("utf-8")
    rc, out, _ = env.cli("list")
    assert "dashboard: FORA DO AR, restauração falhou às " in out


def _hold_lock_in_subprocess(path: Path) -> subprocess.Popen[str]:
    path.parent.mkdir(parents=True, exist_ok=True)
    code = (
        "import fcntl,sys\n"
        "f=open(sys.argv[1],'a')\n"
        "fcntl.flock(f,fcntl.LOCK_EX)\n"
        "print('ok',flush=True)\n"
        "sys.stdin.read()\n"
    )
    proc = subprocess.Popen(
        [sys.executable, "-c", code, str(path)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
    )
    assert proc.stdout is not None
    assert proc.stdout.readline().strip() == "ok"
    return proc


def _release(proc: subprocess.Popen[str]) -> None:
    assert proc.stdin is not None
    proc.stdin.close()
    proc.wait(10)
    if proc.stdout is not None:
        proc.stdout.close()


FORBIDDEN_FROM_UNIT = ("stop", "reset-failed")


def _assert_from_unit_safe(calls: list[list[str]]) -> None:
    for c in calls:
        if c[:2] == ["systemctl", "--user"] and c[2] in FORBIDDEN_FROM_UNIT:
            assert not c[-1].startswith("demo-prospect@acme"), c
        assert c[:2] != ["podman", "exec"], c
        assert not ("podman" in c and "start" in c), c


def test_D2280_1_44_from_unit_com_lock_ocupado(env: Env) -> None:
    """D2280.1-44: teardown --from-unit with the lock held by another process -> 0, no call."""
    assert env.up()[0] == 0
    before = len(env.host.calls)
    proc = _hold_lock_in_subprocess(env.lock_path())
    try:
        t = time.monotonic()
        rc, _, _ = env.cli("teardown", "acme", "--from-unit")
        assert time.monotonic() - t < 2
    finally:
        _release(proc)
    assert rc == 0
    assert env.host.calls[before:] == []
    assert env.slug_dir("acme").exists()


def test_D2280_1_44_from_unit_com_lock_livre(env: Env) -> None:
    """D2280.1-44: with the lock free: steps 1 to 7, release, then start --no-block of
    demo-slot-restore.service; never stop/reset-failed itself, exec or start."""
    assert env.up()[0] == 0
    env.host.containers.pop("prospect-acme")  # the unit already removed its container
    env.host.units["demo-prospect@acme.service"] = "deactivating"
    before = len(env.host.calls)
    rc, _, err = env.cli("teardown", "acme", "--from-unit")
    assert rc == 0, err
    new = env.host.calls[before:]
    _assert_from_unit_safe(new)
    assert new[-1] == [
        "systemctl", "--user", "start", "--no-block", "demo-slot-restore.service"
    ]  # fmt: skip
    assert not env.slug_dir("acme").exists()
    assert not list(env.caddy_dir.iterdir())
    assert "prospect-acme" not in env.host.networks
    import fcntl

    with env.lock_path().open("a") as f:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        fcntl.flock(f, fcntl.LOCK_UN)


# --------------------------------------------------------------------------- down, list, reap
def test_D2280_1_21_down_completo(env: Env) -> None:
    """D2280.1-21: down acme: stop, teardown (fragments, /load, drop-in, rm --filter label,
    network rm, state, reset-failed) and restore_slot; postconditions; exit 0."""
    assert env.up()[0] == 0
    loads = len(env.admin.loads)
    before = len(env.host.calls)
    rc, out, err = env.cli("down", "acme")
    assert rc == 0, err
    new = env.host.calls[before:]
    want = [
        ["systemctl", "--user", "stop", "demo-prospect@acme.service"],
        ["podman", "rm", "-f", "-i", "--filter", "label=databoar.prospect=acme"],
        ["podman", "network", "rm", "-f", "prospect-acme"],
        ["systemctl", "--user", "reset-failed", "demo-prospect@acme.service"],
    ]
    idx = [new.index(w) for w in want]
    assert idx == sorted(idx)
    assert len(env.admin.loads) == loads + 1
    i_run = next(i for i, c in enumerate(new) if c[:1] == ["systemd-run"])
    assert i_run > idx[-1]
    env.assert_clean("acme")
    assert not env.slot_json().exists()
    assert "removido: acme; dashboard no ar" in out


def test_D2280_1_22_down_sem_nada(env: Env) -> None:
    """D2280.1-22: unknown slug or a second down -> 0 and 'nada a remover', no /load."""
    rc, out, err = env.cli("down", "nunca")
    assert rc == 0, err
    assert "nada a remover: nunca" in out
    assert env.admin.loads == []
    assert env.host.writes() == []


def test_D2280_1_22_down_sem_nada_religa_slot(env: Env) -> None:
    """D2280.1-22 (revision 2): with no occupant and slot.json present (a crash mid-session),
    restore_slot restarts the dashboard: systemd-run ... podman start dashboard, slot.json
    deleted with good fake health, and stdout is only 'nada a remover: <slug>'."""
    assert env.up()[0] == 0
    assert env.cli("down", "acme")[0] == 0
    env.slot_json().write_text(
        json.dumps({"slot": "dashboard", "taken_by": "acme", "taken_at": _z(T0),
                    "mode": "podman", "reset_timer_was_active": False}),
        encoding="utf-8",
    )  # fmt: skip
    env.host.containers["dashboard"]["State"] = "exited"
    loads = len(env.admin.loads)
    before = len(env.host.calls)
    rc, out, err = env.cli("down", "acme")
    assert rc == 0, err
    assert _session_lines(out) == ["nada a remover: acme"]
    assert len(env.admin.loads) == loads
    run = [c for c in env.host.calls[before:] if c[:1] == ["systemd-run"]]
    assert len(run) == 1 and run[0][5:] == ["podman", "start", "dashboard"]
    assert env.host.state("dashboard") == "running"
    assert not env.slot_json().exists()


# -- occupancy guard of restore_slot (design revision 2, section 3 step 0, DEC-20)
def _acme_ativo(env: Env, mode: str = "podman") -> str:
    """acme active after a full up --stop-dashboard, with demo-reset.timer active before;
    returns the expires_at of acme."""
    if mode != "podman":
        env.inv["prospect_slot_mode"] = mode
        env.write_inventory()
    env.host.timer_active = True
    assert env.up()[0] == 0
    assert env.host.state("prospect-acme") == "running"
    assert env.host.units["demo-prospect@acme.service"] == "active"
    assert env.slot_json().exists()
    return str(env.state("acme")["expires_at"])


def _tree(path: Path) -> dict[str, bytes]:
    return {
        str(p.relative_to(path)): p.read_bytes() for p in path.rglob("*") if p.is_file()
    }


def _assert_nao_religou(env: Env, new: list[list[str]], occupant: str = "acme") -> None:
    """No restart of the slot and no write naming the occupant (D2280.1-45)."""
    for c in new:
        assert c[:1] != ["systemd-run"], c
        assert c[:2] != ["podman", "start"], c
        assert c != ["systemctl", "--user", "start", "dashboard.service"], c
        assert c != ["systemctl", "--user", "start", "demo-reset.timer"], c
        assert c[:1] != ["#probe"], c  # no health wait
        if not is_read(c):
            assert occupant not in " ".join(c), c
    assert not env.alert_path.exists()
    assert env.alerter.emitted == []


@pytest.mark.parametrize("mode", ["podman", "systemd"])
def test_D2280_1_45_down_de_outro_slug_nao_religa(env: Env, mode: str) -> None:
    """D2280.1-45: with acme active, `down bravo` exits 0 with two lines, never restarts
    the dashboard, keeps slot.json byte for byte and leaves acme intact."""
    exp = _acme_ativo(env, mode)
    slot = env.slot_json().read_bytes()
    acme = _tree(env.slug_dir("acme"))
    loads = len(env.admin.loads)
    before = len(env.host.calls)
    rc, out, err = env.cli("down", "bravo")
    assert rc == 0, err
    assert _session_lines(out) == [
        "nada a remover: bravo",
        f"dashboard não religada: slot ocupado por acme até {exp}",
    ]
    _assert_nao_religou(env, env.host.calls[before:])
    assert len(env.admin.loads) == loads
    assert env.slot_json().read_bytes() == slot
    assert _tree(env.slug_dir("acme")) == acme
    assert env.host.state("prospect-acme") == "running"


def test_D2280_1_45_down_de_outro_slug_com_restos(env: Env) -> None:
    """D2280.1-45: bravo with a leftover fragment is torn down (one /load and the rm of
    bravo's label, nothing names acme) and the single line says the slot is occupied."""
    exp = _acme_ativo(env)
    slot = env.slot_json().read_bytes()
    (env.caddy_dir / "bravo.caddy").write_text("x", encoding="utf-8")
    loads = len(env.admin.loads)
    before = len(env.host.calls)
    rc, out, err = env.cli("down", "bravo")
    assert rc == 0, err
    assert _session_lines(out) == [
        f"removido: bravo; dashboard não religada: slot ocupado por acme até {exp}"
    ]
    new = env.host.calls[before:]
    assert len(env.admin.loads) == loads + 1
    assert [
        "podman", "rm", "-f", "-i", "--filter", "label=databoar.prospect=bravo"
    ] in new  # fmt: skip
    _assert_nao_religou(env, new)
    assert env.slot_json().read_bytes() == slot
    assert not (env.caddy_dir / "bravo.caddy").exists()


def test_D2280_1_45_ocupante_so_pelo_conteiner(env: Env) -> None:
    """D2280.1-45: a running labelled container without state.json occupies the slot; the
    line ends in 'slot ocupado por acme', without 'até'."""
    env.host.add_container(
        "prospect-acme", IMAGE, "running", {"databoar.prospect": "acme"}
    )
    env.host.containers["dashboard"]["State"] = "exited"
    env.slot_json().parent.mkdir(parents=True, exist_ok=True)
    env.slot_json().write_text(
        json.dumps({"slot": "dashboard", "taken_by": "acme", "taken_at": _z(T0),
                    "mode": "podman", "reset_timer_was_active": False}),
        encoding="utf-8",
    )  # fmt: skip
    slot = env.slot_json().read_bytes()
    before = len(env.host.calls)
    rc, out, err = env.cli("down", "bravo")
    assert rc == 0, err
    assert _session_lines(out) == [
        "nada a remover: bravo",
        "dashboard não religada: slot ocupado por acme",
    ]
    _assert_nao_religou(env, env.host.calls[before:])
    assert env.slot_json().read_bytes() == slot
    assert env.host.state("dashboard") == "exited"


def test_D2280_1_46_restore_slot_ocupado(env: Env) -> None:
    """D2280.1-46: with acme active, `restore-slot` exits 0 with the single occupied line,
    no restart, slot.json byte for byte and no ALERT."""
    exp = _acme_ativo(env)
    slot = env.slot_json().read_bytes()
    before = len(env.host.calls)
    rc, out, err = env.cli("restore-slot")
    assert rc == 0, err
    assert _session_lines(out) == [
        f"dashboard não religada: slot ocupado por acme até {exp}"
    ]
    _assert_nao_religou(env, env.host.calls[before:])
    assert env.slot_json().read_bytes() == slot


def test_D2280_1_46_unidade_deactivating_nao_ocupa(env: Env) -> None:
    """D2280.1-46: unit deactivating and no running labelled container (TTL after the
    ExecStopPost) is no occupant: restore-slot restarts as in D2280.1-42."""
    _acme_ativo(env)
    _pod_gone(env, "acme", "deactivating")
    before = len(env.host.calls)
    rc, out, err = env.cli("restore-slot")
    assert rc == 0, err
    run = [c for c in env.host.calls[before:] if c[:1] == ["systemd-run"]]
    assert len(run) == 1 and run[0][5:] == ["podman", "start", "dashboard"]
    assert not env.slot_json().exists()
    assert _session_lines(out) == ["dashboard no ar"]


def test_D2280_1_47_corrida_do_ttl(env: Env) -> None:
    """D2280.1-47: TTL of acme, then up bravo before the restore runs: the restore finds
    bravo and does nothing; down bravo restarts the dashboard and the timer."""
    _acme_ativo(env)
    # 1. the TTL: the unit is deactivating while its ExecStopPost runs.
    env.host.units["demo-prospect@acme.service"] = "deactivating"
    before = len(env.host.calls)
    assert env.cli("teardown", "acme", "--from-unit")[0] == 0
    new = env.host.calls[before:]
    assert [
        "systemctl", "--user", "start", "--no-block", "demo-slot-restore.service"
    ] in new  # fmt: skip
    assert not [c for c in new if c[:1] == ["systemd-run"]]
    env.host.units["demo-prospect@acme.service"] = "failed"
    # 2. up bravo before the restore: the dashboard is already stopped.
    before = len(env.host.calls)
    rc, _, err = env.up("bravo")
    assert rc == 0, err
    assert not [c for c in env.host.calls[before:] if c[:2] == ["podman", "stop"]]
    record = json.loads(env.slot_json().read_text("utf-8"))
    assert record["taken_by"] == "bravo"
    assert record["reset_timer_was_active"] is True
    exp = str(env.state("bravo")["expires_at"])
    # 3. the delayed demo-slot-restore.service.
    slot = env.slot_json().read_bytes()
    before = len(env.host.calls)
    rc, out, err = env.cli("restore-slot")
    assert rc == 0, err
    assert _session_lines(out) == [
        f"dashboard não religada: slot ocupado por bravo até {exp}"
    ]
    _assert_nao_religou(env, env.host.calls[before:], occupant="bravo")
    assert env.slot_json().read_bytes() == slot
    # 4. down bravo restores the slot and the timer of the start of acme.
    before = len(env.host.calls)
    rc, out, err = env.cli("down", "bravo")
    assert rc == 0, err
    new = env.host.calls[before:]
    run = [c for c in new if c[:1] == ["systemd-run"]]
    assert len(run) == 1 and run[0][5:] == ["podman", "start", "dashboard"]
    assert ["systemctl", "--user", "start", "demo-reset.timer"] in new
    assert not env.slot_json().exists()
    assert _session_lines(out) == ["removido: bravo; dashboard no ar"]


def test_D2280_1_47_reap_com_bravo_ativo_nao_religa(env: Env) -> None:
    """D2280.1-47: with bravo active and slot.json present, reap does not restore."""
    _acme_ativo(env)
    env.host.timer_active = False
    assert env.cli("down", "acme")[0] == 0
    assert env.up("bravo")[0] == 0
    before = len(env.host.calls)
    assert env.cli("reap")[0] == 0
    _assert_nao_religou(env, env.host.calls[before:], occupant="bravo")
    assert env.slot_json().exists()


def test_D2280_1_47_reap_bravo_vencido_religa(env: Env) -> None:
    """D2280.1-47: with bravo past its deadline, reap tears it down and restores."""
    assert env.up("bravo", "--ttl", "5m")[0] == 0
    env.clock.t = T0 + timedelta(minutes=5, seconds=61)
    before = len(env.host.calls)
    rc, out, err = env.cli("reap")
    assert rc == 0, err
    run = [c for c in env.host.calls[before:] if c[:1] == ["systemd-run"]]
    assert len(run) == 1
    assert not env.slot_json().exists()
    env.assert_clean("bravo")


def test_D2280_1_47_reap_pod_sobrevive_nao_religa(env: Env) -> None:
    """D2280.1-47: bravo past its deadline whose container survives the teardown (the fake
    rm fails) -> reap exits 3, prints the occupied line without 'até', no podman start,
    slot.json stays."""
    assert env.up("bravo", "--ttl", "5m")[0] == 0
    env.clock.t = T0 + timedelta(minutes=5, seconds=61)
    env.host.fail["systemctl --user stop demo-prospect@bravo.service"] = (1, "", "x")
    env.host.fail["podman rm -f -i --filter label=databoar.prospect=bravo"] = (
        1, "", "x"
    )  # fmt: skip
    slot = env.slot_json().read_bytes()
    before = len(env.host.calls)
    rc, out, err = env.cli("reap")
    assert rc == 3, (out, err)
    assert "reap: dashboard não religada: slot ocupado por bravo" in _session_lines(out)
    new = env.host.calls[before:]
    assert not [c for c in new if c[:1] == ["systemd-run"]]
    assert not [c for c in new if c[:2] == ["podman", "start"]]
    assert env.host.state("prospect-bravo") == "running"
    assert env.slot_json().read_bytes() == slot


@pytest.mark.parametrize("resto", ["rede", "fragmento", "estado"])
def test_D2280_1_23_restos_parciais(env: Env, resto: str) -> None:
    """D2280.1-23: only the network, only the fragment or only the state left -> removed, 0."""
    if resto == "rede":
        env.host.networks["prospect-acme"] = {"databoar.prospect": "acme"}
    elif resto == "fragmento":
        (env.caddy_dir / "acme.caddy").write_text("x", encoding="utf-8")
    else:
        d = env.slug_dir("acme")
        d.mkdir(parents=True)
        (d / "state.json").write_text("{}", encoding="utf-8")
    rc, out, err = env.cli("down", "acme")
    assert rc == 0, err
    env.assert_clean("acme")
    assert "removido: acme" in out


def test_D2280_1_24_load_sem_conexao_sai_3(env: Env) -> None:
    """D2280.1-24: /load with a connection error -> fragment deleted, exit 3 'rota pode
    persistir'."""
    assert env.up()[0] == 0
    env.admin.default = 0
    rc, out, err = env.cli("down", "acme")
    assert rc == 3
    assert "rota pode persistir" in out + err
    assert not list(env.caddy_dir.glob("acme.*"))


def test_D2280_1_25_network_rm_falha_sai_3(env: Env) -> None:
    """D2280.1-25: network rm failing -> exit 3 naming 'rede prospect-acme'."""
    assert env.up()[0] == 0
    env.host.fail["network rm -f prospect-acme"] = (2, "", "busy")
    rc, out, err = env.cli("down", "acme")
    assert rc == 3
    assert "rede prospect-acme" in out + err


def test_D2280_1_26_down_pega_o_lock_antes_do_stop(env: Env) -> None:
    """D2280.1-26: down holds the lock before stop; the simulated ExecStopPost
    (teardown --from-unit, another descriptor) returns at once and down does not wait."""
    assert env.up()[0] == 0
    seen: dict[str, Any] = {}

    def exec_stop_post(unit: str) -> None:
        c = env.ctx()
        t = time.monotonic()
        n = len(env.host.calls)
        seen["rc"] = P.main(["teardown", "acme", "--from-unit"], c)
        seen["elapsed"] = time.monotonic() - t
        seen["calls"] = env.host.calls[n:]

    env.host.on_stop_unit = exec_stop_post
    t = time.monotonic()
    rc, _, err = env.cli("down", "acme")
    assert rc == 0, err
    assert seen["rc"] == 0
    assert seen["elapsed"] < 2
    assert seen["calls"] == []
    assert time.monotonic() - t < 10
    env.assert_clean("acme")


def test_D2280_1_27_list(env: Env) -> None:
    """D2280.1-27: list shows the prospect and the slot line in the three situations;
    --json has a stable schema; no key, hash or password in any output."""
    rc, out, _ = env.cli("list")
    assert rc == 0
    assert "dashboard: no ar" in out
    rc, up_out, _ = env.up()
    assert rc == 0
    senha = _password_sent_to_hash(env)
    assert not re.search(r"^senha: ", up_out, re.M)
    key = _pod_env(env)["PROSPECT_API_KEY"]
    env.clock.advance(60)
    rc, out, _ = env.cli("list")
    assert rc == 0
    st = env.state("acme")
    assert re.search(
        rf"^acme ativo {st['created_at']} {st['expires_at']} 29\b", out, re.M
    )
    assert f"dashboard: parada pela sessão acme desde {_z(T0)}" in out
    rc, jout, _ = env.cli("list", "--json")
    assert rc == 0
    data = json.loads(jout)
    assert set(data) == {"prospects", "slot"}
    assert data["prospects"] == [
        {
            "slug": "acme",
            "status": "ativo",
            "created_at": st["created_at"],
            "expires_at": st["expires_at"],
            "minutes_left": 29,
        }
    ]
    assert set(data["slot"]) == {"state", "taken_by", "since", "failed_at"}
    assert data["slot"]["state"] == "parada"
    env.clock.advance(30 * 60)
    rc, out, _ = env.cli("list")
    assert re.search(r"^acme vencido ", out, re.M)
    env.host.units["demo-prospect@acme.service"] = "failed"
    env.clock.t = T0 + timedelta(minutes=2)
    rc, out, _ = env.cli("list")
    assert re.search(r"^acme órfão ", out, re.M)
    env.host.dash_start_rc = 125
    assert env.cli("down", "acme")[0] == 8
    rc, out, _ = env.cli("list")
    assert "dashboard: FORA DO AR, restauração falhou às " in out
    rc, jout, _ = env.cli("list", "--json")
    assert json.loads(jout)["slot"]["state"] == "fora_do_ar"
    for text in (out, jout, up_out.replace(senha, "")):
        assert senha not in text and key not in text
        assert not re.search(r"\$2[aby]\$", text)


def test_D2280_1_28_reap_no_prazo(env: Env) -> None:
    """D2280.1-28: at expires_at - 1 s reap does nothing; at +61 s with the unit active:
    stop, teardown, reset-failed and restore_slot."""
    assert env.up("acme", "--ttl", "5m")[0] == 0
    env.clock.t = T0 + timedelta(minutes=5) - timedelta(seconds=1)
    before = len(env.host.calls)
    rc, _, _ = env.cli("reap")
    assert rc == 0
    assert [c for c in env.host.calls[before:] if not is_read(c)] == []
    env.clock.t = T0 + timedelta(minutes=5, seconds=61)
    before = len(env.host.calls)
    rc, out, err = env.cli("reap")
    assert rc == 0, err
    new = env.host.calls[before:]
    i_stop = new.index(["systemctl", "--user", "stop", "demo-prospect@acme.service"])
    i_reset = new.index(
        ["systemctl", "--user", "reset-failed", "demo-prospect@acme.service"]
    )
    i_run = next(i for i, c in enumerate(new) if c[:1] == ["systemd-run"])
    assert i_stop < i_reset < i_run
    env.assert_clean("acme")
    assert out.strip()


def test_D2280_1_28_reap_unidade_failed_sem_stop(env: Env) -> None:
    """D2280.1-28: with the unit failed, the same without the stop."""
    assert env.up()[0] == 0
    env.host.units["demo-prospect@acme.service"] = "failed"
    env.host.containers.pop("prospect-acme")
    before = len(env.host.calls)
    rc, _, err = env.cli("reap")
    assert rc == 0, err
    new = env.host.calls[before:]
    assert ["systemctl", "--user", "stop", "demo-prospect@acme.service"] not in new
    assert ["systemctl", "--user", "reset-failed", "demo-prospect@acme.service"] in new
    env.assert_clean("acme")


def test_D2280_1_29_reap_so_remove_o_rotulado(env: Env) -> None:
    """D2280.1-29: only prospect-orfao (labelled) and a fragment without state go away;
    the dashboard is only touched by restore_slot."""
    h = env.host
    for name in ("samba", "caddy-demo", "lab-db"):
        h.add_container(name, "docker.io/library/x:1", "running")
    h.add_container("prospect-orfao", IMAGE, "exited", {"databoar.prospect": "orfao"})
    for name in ("dashboard", "apresentacao", "samba", "lab-net"):
        h.networks[name] = {}
    h.networks["prospect-orfao"] = {"databoar.prospect": "orfao"}
    (env.caddy_dir / "bravo.caddy").write_text("x", encoding="utf-8")
    (env.caddy_dir / "bravo.crt").write_text("x", encoding="utf-8")
    rc, _, err = env.cli("reap")
    assert rc == 0, err
    assert "prospect-orfao" not in h.containers
    assert "prospect-orfao" not in h.networks
    assert {"dashboard", "apresentacao", "samba", "caddy-demo", "lab-db"} <= set(
        h.containers
    )
    assert {"dashboard", "apresentacao", "samba", "lab-net"} <= set(h.networks)
    assert not list(env.caddy_dir.iterdir())
    for c in h.writes():
        if "dashboard" in " ".join(c):
            assert c[0] == "systemd-run", c


def test_D2280_1_30_segundo_reap_sem_escrita(env: Env) -> None:
    """D2280.1-30: a second reap does no write."""
    env.host.add_container(
        "prospect-orfao", IMAGE, "exited", {"databoar.prospect": "orfao"}
    )
    (env.caddy_dir / "bravo.caddy").write_text("x", encoding="utf-8")
    assert env.cli("reap")[0] == 0
    before = len(env.host.calls)
    loads = len(env.admin.loads)
    assert env.cli("reap")[0] == 0
    assert [c for c in env.host.calls[before:] if not is_read(c)] == []
    assert len(env.admin.loads) == loads


# --------------------------------------------------------------------------- script shape
def test_cli_e_executavel_no_git_e_tem_shebang() -> None:
    """The units run prospect.py directly: shebang and mode 100755 in the git index."""
    listed = subprocess.run(
        ["git", "ls-files", "-s", "--", CLI.relative_to(REPO).as_posix()],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert listed.startswith("100755 "), listed
    assert CLI.read_text("utf-8").startswith("#!/usr/bin/env python3\n")


def test_cli_upload_recusado_na_fase_a(env: Env) -> None:
    """Section 1: --upload -> exit 2 'upload: fase B não habilitada'."""
    rc, _, err = env.cli("up", "acme", "--stop-dashboard", "--upload")
    assert rc == 2
    assert "upload: fase B não habilitada" in err
    assert env.host.calls == []


def test_cli_erro_de_uso_em_uma_linha(env: Env) -> None:
    """Section 1: usage errors go to stderr in one line with exit 2."""
    rc, _, err = env.cli("nao-existe")
    assert rc == 2
    assert len(err.strip().splitlines()) == 1


# --------------------------------------------------------------------------- extra cases
def test_reap_reseta_a_unidade_failed_depois_do_from_unit(env: Env) -> None:
    """Sections 11 and 12: after the TTL (or a killed pod) the ExecStopPost teardown leaves
    the unit `failed` and no state; the next reap resets it and brings the slot back."""
    assert env.up()[0] == 0
    env.host.containers.pop("prospect-acme")
    env.host.units["demo-prospect@acme.service"] = "failed"
    assert env.cli("teardown", "acme", "--from-unit")[0] == 0
    assert not env.slug_dir("acme").exists()
    assert env.host.units.get("demo-prospect@acme.service") == "failed"
    before = len(env.host.calls)
    rc, _, err = env.cli("reap")
    assert rc == 0, err
    new = env.host.calls[before:]
    assert ["systemctl", "--user", "reset-failed", "demo-prospect@acme.service"] in new
    assert "demo-prospect@acme.service" not in env.host.units
    env.assert_clean("acme")
    assert not env.slot_json().exists()
    before = len(env.host.calls)
    assert env.cli("reap")[0] == 0
    assert [c for c in env.host.calls[before:] if not is_read(c)] == []


def test_memoria_insuficiente_e_dashboard_nao_volta_sai_8(env: Env) -> None:
    """Section 1, exit codes: when the slot does not come back, 8 wins over 4."""
    env.mem_mib = 100
    env.host.dash_start_rc = 125
    rc, _, _ = env.up()
    assert rc == 8
    assert len(env.alerter.emitted) == 1


def test_falha_de_inicio_com_dashboard_que_nao_volta_sai_8(env: Env) -> None:
    """Section 1, exit codes: a failed up whose rollback cannot bring the slot back is 8."""
    env.host.fail["start demo-prospect@acme.service"] = (1, "", "job failed")
    env.host.dash_start_rc = 125
    rc, _, _ = env.up()
    assert rc == 8
    assert not env.slug_dir("acme").exists()


def test_rota_sem_resposta_e_tentada_de_novo(env: Env) -> None:
    """Section 10, step 11: no answer yet (0) is retried for a few seconds; 401 passes."""
    env.probe.route_codes = [0, 0, 401]
    rc, _, err = env.up()
    assert rc == 0, err
    assert len(env.probe.route_calls) == 3
