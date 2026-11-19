"""Black-box acceptance for prospect-up/down, phase A (task 2280.4, epic #2280, issue #2285).

Source of truth: ``docs/desenho/2280.1.md``, section "Especificação para a aceitação do QA"
(A-1 to A-18) and section 15 (test seams). Phase B (A-B1 to A-B3) belongs to task 2280.10.

How it talks to the system (only what an operator would use):
- the CLI ``deploy/demo/prospect/prospect.py <sub>`` as a subprocess (``up``, ``down``,
  ``list``, ``reap``), configured by a private inventory file named in ``PROSPECT_INVENTORY``;
- ``podman`` / ``systemctl --user`` / ``journalctl --user`` to look at the outside effects;
- HTTPS to a throwaway ``caddy:2`` proxy in a high port, with ``curl --resolve``.

Harness (session scope): throwaway proxy, a test ``dashboard`` (``--restart=always``) and a
test ``apresentacao``, both from ``PROSPECT_TEST_IMAGE`` with license mode ``open``, domain
``prospect.test``. Skipped without ``podman``/``systemd-run --user``/the image variable.
A preparation failure is an ERROR, never an expected failure.

Pending marker: every test is ``xfail(strict=True, raises=CliAusente)``. ``CliAusente`` is
raised only while the phase-A artifacts do not exist in the repo, so a harness mistake can
never pass as "expected failure". When 2280.2/2280.3 land, the dev removes ``pendente``.

Placeholders only: ``acme`` and ``bravo`` are synthetic slugs; no real prospect, vault,
host or secret appears here. Time-dependent waits are polls with a deadline (the design
fixes the reaper cycle, so there is no clock to inject from outside).
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
CLI = REPO / "deploy" / "demo" / "prospect" / "prospect.py"
QUADLET = REPO / "deploy" / "demo" / "quadlet"
TEMPLATE = QUADLET / "demo-prospect@.container"
DOMAIN = "prospect.test"
LICENSE_HOSTNAME = "pod.prospect.test"
USER = "prospect"


class CliAusente(Exception):
    """The phase-A artifacts are not in the repo yet (task 2280.2/2280.3 pending)."""


pendente = pytest.mark.xfail(
    strict=True,
    raises=CliAusente,
    reason="pendente: tarefa 2280.2/2280.3 implementa o prospect-up/down (#2285)",
)


# --------------------------------------------------------------------------- helpers
def _run(
    argv: list[str], *, env: dict[str, str] | None = None, timeout: float = 120.0
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def _esperar(
    cond: Callable[[], bool], timeout: float, passo: float = 2.0, *, msg: str = ""
) -> None:
    """Poll ``cond`` until true or ``timeout`` (deadline polling, no fixed sleep)."""
    limite = time.monotonic() + timeout
    pausa = threading.Event()
    while time.monotonic() < limite:
        if cond():
            return
        pausa.wait(passo)
    if not cond():
        raise AssertionError(f"timeout de {timeout:.0f}s: {msg}")


def _esperar_estavel(
    segundos: float, cond: Callable[[], bool], passo: float = 5.0
) -> None:
    """Hold for ``segundos`` while ``cond`` stays true (A-15 and A-17 'still there later')."""
    fim = time.monotonic() + segundos
    pausa = threading.Event()
    while time.monotonic() < fim:
        assert cond(), "a condição deixou de valer durante a espera"
        pausa.wait(passo)
    assert cond()


def _porta_livre() -> int:
    import socket

    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _cpf_sintetico(base: str) -> str:
    """Valid-checksum CPF built at runtime from 9 digits (no literal in the repo)."""
    d = [int(c) for c in base]
    for n in (10, 11):
        s = sum(v * (n - i) for i, v in enumerate(d))
        d.append((s * 10 % 11) % 10)
    t = "".join(map(str, d))
    return f"{t[:3]}.{t[3:6]}.{t[6:9]}-{t[9:]}"


@dataclass
class Sessao:
    slug: str
    url: str
    senha: str
    expires_at: str
    saida: str


@dataclass
class Monitor:
    """Polls control URLs in a thread and records every non-200 (A-10)."""

    urls: list[tuple[str, Callable[[], int]]]
    falhas: list[str] = field(default_factory=list)
    _parar: threading.Event = field(default_factory=threading.Event)
    _t: threading.Thread | None = None

    def __enter__(self) -> Monitor:
        def laco() -> None:
            while not self._parar.is_set():
                for nome, sonda in self.urls:
                    codigo = sonda()
                    if codigo != 200:
                        self.falhas.append(f"{nome}={codigo}")
                self._parar.wait(1.0)

        self._t = threading.Thread(target=laco, daemon=True)
        self._t.start()
        return self

    def __exit__(self, *exc: object) -> None:
        self._parar.set()
        if self._t:
            self._t.join(timeout=10)


class Harness:
    def __init__(self, image: str) -> None:
        self.image = image
        self.sufixo = f"{os.getpid():x}"
        self.dash = f"qa-dashboard-{self.sufixo}"
        self.apres = f"qa-apresentacao-{self.sufixo}"
        self.proxy = f"qa-proxy-{self.sufixo}"
        self.porta_dash = _porta_livre()
        self.porta_apres = _porta_livre()
        self.porta_proxy = _porta_livre()
        self.porta_pod = _porta_livre()
        self.runtime = Path(os.environ["XDG_RUNTIME_DIR"])
        self.raiz = Path(tempfile.mkdtemp(prefix="pq", dir=self.runtime))
        self.caddy_dir = self.raiz / "frag"
        self.admin_sock = self.raiz / "a.sock"
        self.alerta_chamadas = self.raiz / "alert-calls.txt"
        self.alerta_arquivo = self.raiz / "ALERT"
        self.inventario = self.raiz / "inventory.json"
        self.instalados: list[Path] = []
        self.inicio_journal = time.strftime("%Y-%m-%d %H:%M:%S")

    # -- processes
    def podman(
        self, *args: str, timeout: float = 120.0
    ) -> subprocess.CompletedProcess[str]:
        return _run(["podman", *args], timeout=timeout)

    def systemctl(self, *args: str) -> subprocess.CompletedProcess[str]:
        return _run(["systemctl", "--user", *args])

    def cli(
        self, *args: str, timeout: float = 400.0
    ) -> subprocess.CompletedProcess[str]:
        env = {**os.environ, "PROSPECT_INVENTORY": str(self.inventario)}
        return _run([sys.executable, str(CLI), *args], env=env, timeout=timeout)

    def inspecionar(self, nome: str) -> dict:
        r = self.podman("inspect", nome)
        assert r.returncode == 0, f"podman inspect {nome}: {r.stderr[-200:]}"
        return json.loads(r.stdout)[0]

    def existe(self, nome: str) -> bool:
        return self.podman("container", "exists", nome).returncode == 0

    def estado(self, nome: str) -> str:
        return str(self.inspecionar(nome)["State"]["Status"])

    # -- http
    def http(
        self,
        host: str,
        caminho: str,
        *,
        auth: tuple[str, str] | None = None,
        metodo: str = "GET",
        porta: int | None = None,
    ) -> tuple[int, str]:
        porta = porta or self.porta_proxy
        cmd = [
            "curl", "-sk", "-m", "10", "-X", metodo,
            "--resolve", f"{host}:{porta}:127.0.0.1",
            "-o", "-", "-w", "\n%{http_code}",
        ]  # fmt: skip
        if auth:
            cmd += ["-u", f"{auth[0]}:{auth[1]}"]
        r = _run([*cmd, f"https://{host}:{porta}{caminho}"], timeout=30)
        corpo, _, codigo = r.stdout.rpartition("\n")
        return (int(codigo) if codigo.isdigit() else 0), corpo

    def host(self, slug: str) -> str:
        return f"{slug}.{DOMAIN}"

    def status_direto(self, porta: int) -> dict | None:
        r = _run(
            ["curl", "-sk", "-m", "5", f"https://127.0.0.1:{porta}/status"], timeout=15
        )
        try:
            return json.loads(r.stdout)
        except ValueError:
            return None

    def dash_saudavel(self) -> bool:
        s = self.status_direto(self.porta_dash)
        return bool(s and s.get("trust_state") == "trusted")

    # -- build
    def _certificado(self) -> Path:
        certs = self.raiz / "certs"
        certs.mkdir(exist_ok=True)
        r = _run(
            ["openssl", "req", "-x509", "-newkey", "ec", "-pkeyopt", "ec_paramgen_curve:prime256v1",
             "-nodes", "-keyout", str(certs / "tls.key"), "-out", str(certs / "tls.crt"),
             "-days", "2", "-subj", "/CN=localhost",
             "-addext", "subjectAltName=DNS:localhost,IP:127.0.0.1"],
        )  # fmt: skip
        assert r.returncode == 0, r.stderr
        for p in certs.iterdir():
            p.chmod(0o644)
        return certs

    def _instancia(self, nome: str, porta: int, *, restart: str) -> None:
        dados = self.raiz / f"data-{nome}"
        dados.mkdir(exist_ok=True)
        (dados / "config.yaml").write_text(
            "targets:\n  - name: Corpus sintetico\n    type: filesystem\n    path: /corpus\n"
            f"scan:\n  max_workers: 1\napi:\n  port: {porta}\n  host: 127.0.0.1\n"
            "sqlite_path: /data/audit_results.db\nreport:\n  output_dir: /data\n",
            encoding="utf-8",
        )
        certs = self.raiz / "certs"
        r = self.podman(
            "run", "-d", "--name", nome, "--network", "host", "--user", "0",
            f"--restart={restart}", "-e", "DATA_BOAR_LICENSE_MODE=open",
            "-v", f"{dados}:/data", "-v", f"{self.raiz / 'corpus'}:/corpus:ro",
            "-v", f"{certs}:/certs:ro", self.image,
            "main.py", "--config", "/data/config.yaml", "--web", "--host", "127.0.0.1",
            "--port", str(porta), "--https-cert-file", "/certs/tls.crt",
            "--https-key-file", "/certs/tls.key",
        )  # fmt: skip
        assert r.returncode == 0, f"preparação: {nome}: {r.stderr[-300:]}"

    def _corpus(self) -> None:
        pasta = self.raiz / "corpus"
        pasta.mkdir(exist_ok=True)
        for i in range(300):
            cpf = _cpf_sintetico(f"{(i * 7919 + 123456789) % 10**9:09d}")
            (pasta / f"ficha-{i:03d}.txt").write_text(
                f"Cliente ficticio {i}\nCPF: {cpf}\nE-mail: cliente{i}@exemplo.com\n",
                encoding="utf-8",
            )

    def subir(self) -> None:
        self._corpus()
        self._certificado()
        self.caddy_dir.mkdir(exist_ok=True)
        (self.raiz / "Caddyfile").write_text(
            f"{{\n\tadmin unix/{self.admin_sock}\n\thttps_port {self.porta_proxy}\n"
            "\tskip_install_trust\n\tauto_https disable_redirects\n}\n"
            f'ctrl.{DOMAIN}:{self.porta_proxy} {{\n\ttls internal\n\trespond "ok" 200\n}}\n'
            f"import {self.caddy_dir}/*.caddy\n",
            encoding="utf-8",
        )
        for nome, porta, restart in (
            (self.dash, self.porta_dash, "always"),
            (self.apres, self.porta_apres, "no"),
        ):
            self._instancia(nome, porta, restart=restart)
        r = self.podman(
            "run", "-d", "--name", self.proxy, "--network", "host",
            "-v", f"{self.raiz}:{self.raiz}",
            "docker.io/library/caddy:2", "caddy", "run", "--config", f"{self.raiz}/Caddyfile",
        )  # fmt: skip
        assert r.returncode == 0, f"preparação: proxy: {r.stderr[-300:]}"
        _esperar(
            lambda: self.http(f"ctrl.{DOMAIN}", "/")[0] == 200,
            90,
            msg="proxy de teste no ar",
        )
        _esperar(self.dash_saudavel, 120, msg="dashboard de teste trusted")
        _esperar(
            lambda: bool(
                (self.status_direto(self.porta_apres) or {}).get("trust_state")
            ),
            120,
            msg="apresentacao de teste no ar",
        )
        self._inventario()
        self._instalar_unidades()

    def _inventario(self) -> None:
        alerta = self.raiz / "alert.sh"
        alerta.write_text(
            f'#!/bin/sh\necho "$1" >> {self.alerta_chamadas}\n', encoding="utf-8"
        )
        alerta.chmod(0o755)
        (self.raiz / "profile.yaml").write_text("{}\n", encoding="utf-8")
        (self.raiz / "recommendations.yaml").write_text("{}\n", encoding="utf-8")
        base_env = self.raiz / "base.env"
        base_env.write_text("", encoding="utf-8")
        base_env.chmod(0o600)
        inv = {
            "prospect_slot_container": self.dash,
            "prospect_slot_mode": "podman",
            "prospect_slot_health_url": f"https://127.0.0.1:{self.porta_dash}/status",
            "prospect_protected_containers": [self.apres],
            "prospect_alert_cmd": str(alerta),
            "prospect_alert_path": str(self.alerta_arquivo),
            "prospect_port": self.porta_pod,
            "prospect_domain": DOMAIN,
            "prospect_proxy_port": self.porta_proxy,
            "prospect_proxy_container": self.proxy,
            "prospect_tls_line": "tls internal",
            "prospect_caddy_dir": str(self.caddy_dir),
            "prospect_caddy_dir_in_proxy": str(self.caddy_dir),
            "prospect_caddy_admin_socket": str(self.admin_sock),
            "prospect_caddyfile": str(self.raiz / "Caddyfile"),
            "prospect_base_env": str(base_env),
            "prospect_corpus_dir": str(self.raiz / "corpus"),
            "prospect_profile_file": str(self.raiz / "profile.yaml"),
            "prospect_recommendations_file": str(self.raiz / "recommendations.yaml"),
            "prospect_license_mode": "open",
            "prospect_license_hostname": LICENSE_HOSTNAME,
            "prospect_image": self.image,
            "prospect_reserved_slugs": [],
        }
        self.inventario.write_text(json.dumps(inv), encoding="utf-8")
        self.inventario.chmod(0o600)

    def _instalar_unidades(self) -> None:
        home = Path.home()
        quad = home / ".config" / "containers" / "systemd"
        usr = home / ".config" / "systemd" / "user"
        alvo_cli = home / "demo" / "prospect" / "bin" / "prospect.py"
        for p in (quad / TEMPLATE.name, alvo_cli.parent.parent):
            if p.exists() or p.is_symlink():
                pytest.skip(
                    f"{p} já existe: host com o recurso instalado, não sobrescrevo"
                )
        env_dropin = f"[Service]\nEnvironment=PROSPECT_INVENTORY={self.inventario}\n"
        quad.mkdir(parents=True, exist_ok=True)
        usr.mkdir(parents=True, exist_ok=True)
        alvo_cli.parent.mkdir(parents=True)
        alvo_cli.symlink_to(CLI)
        self.instalados += [alvo_cli.parent.parent]
        shutil.copy(TEMPLATE, quad / TEMPLATE.name)
        host_d = quad / f"{TEMPLATE.name}.d"
        host_d.mkdir()
        (host_d / "10-host.conf").write_text(
            f"[Container]\nImage={self.image}\nHostName={LICENSE_HOSTNAME}\n"
            + env_dropin
            + "[Container]\nEnvironment=DATA_BOAR_LICENSE_MODE=open\n",
            encoding="utf-8",
        )
        self.instalados += [quad / TEMPLATE.name, host_d]
        fixas = ["demo-slot-restore.service", "demo-prospect-reap.service",
                 "demo-prospect-reap.timer"]  # fmt: skip
        for nome in fixas:
            origem = QUADLET / nome
            shutil.copy(origem, usr / nome)
            self.instalados.append(usr / nome)
            if nome.endswith(".service"):
                d = usr / f"{nome}.d"
                d.mkdir()
                (d / "10-test.conf").write_text(env_dropin, encoding="utf-8")
                self.instalados.append(d)
        slice_ = next(
            iter((REPO / "deploy" / "demo").rglob("demo-prospect.slice")), None
        )
        assert slice_ is not None, (
            "preparação: demo-prospect.slice não encontrada em deploy/demo"
        )
        shutil.copy(slice_, usr / slice_.name)
        self.instalados.append(usr / slice_.name)
        self.systemctl("daemon-reload")

    # -- state between tests
    def zerar(self) -> None:
        self.systemctl("stop", "demo-prospect-reap.timer")
        self.systemctl("stop", "demo-prospect@*.service")
        self.systemctl("reset-failed")
        ids = self.podman(
            "ps", "-aq", "--filter", "label=databoar.prospect"
        ).stdout.split()
        if ids:
            self.podman("rm", "-f", "-i", *ids)
        redes = self.podman(
            "network", "ls", "-q", "--filter", "label=databoar.prospect"
        )
        for rede in redes.stdout.split():
            self.podman("network", "rm", "-f", rede)
        for f in self.caddy_dir.glob("*"):
            f.unlink()
        shutil.rmtree(self.runtime / "demo-prospect", ignore_errors=True)
        for d in (self.runtime / "systemd" / "user").glob("demo-prospect@*.service.d"):
            shutil.rmtree(d, ignore_errors=True)
        for f in (self.alerta_chamadas, self.alerta_arquivo):
            f.unlink(missing_ok=True)
        self.systemctl("daemon-reload")
        self.podman(
            "exec", self.proxy, "caddy", "reload", "--config", f"{self.raiz}/Caddyfile"
        )
        self.garantir_dashboard()

    def garantir_dashboard(self) -> None:
        if not self.existe(self.dash) or self.estado(self.dash) == "created":
            self.podman("rm", "-f", self.dash)
            self._instancia(self.dash, self.porta_dash, restart="always")
        elif self.estado(self.dash) != "running":
            self.podman("start", self.dash)
        if self.estado(self.apres) != "running":
            self.podman("start", self.apres)
        _esperar(self.dash_saudavel, 120, msg="dashboard de teste voltou ao baseline")

    def desmontar(self) -> None:
        self.systemctl("stop", "demo-prospect-reap.timer")
        self.systemctl("stop", "demo-prospect@*.service")
        for nome in (self.proxy, self.dash, self.apres):
            self.podman("rm", "-f", "-t", "0", nome)
        ids = self.podman(
            "ps", "-aq", "--filter", "label=databoar.prospect"
        ).stdout.split()
        if ids:
            self.podman("rm", "-f", "-i", *ids)
        for p in reversed(self.instalados):
            if p.is_dir():
                shutil.rmtree(p, ignore_errors=True)
            else:
                p.unlink(missing_ok=True)
        self.systemctl("daemon-reload")
        shutil.rmtree(self.raiz, ignore_errors=True)

    # -- operator view
    def subir_prospecto(self, slug: str = "acme", ttl: str = "10m") -> Sessao:
        r = self.cli("up", slug, "--stop-dashboard", "--ttl", ttl)
        assert r.returncode == 0, f"up {slug}: rc={r.returncode} {r.stderr[-300:]}"
        return self.ler_sessao(slug, r.stdout)

    def ler_sessao(self, slug: str, saida: str) -> Sessao:
        url = re.search(rf"https://{slug}\.{re.escape(DOMAIN)}\S*", saida)
        senha = re.search(r"senha(?! já)[^:\n]*:\s*(\S+)", saida, re.IGNORECASE)
        prazo = re.search(r"\d{4}-\d\d-\d\dT[\d:.]+Z", saida)
        assert url and prazo, f"saída do up sem URL ou prazo: {saida[-300:]!r}"
        return Sessao(
            slug, url.group(0), senha.group(1) if senha else "", prazo.group(0), saida
        )

    def auth(self, s: Sessao, senha: str | None = None) -> tuple[str, str]:
        return (USER, s.senha if senha is None else senha)

    def pod_status(self, s: Sessao) -> dict:
        codigo, corpo = self.http(self.host(s.slug), "/status", auth=self.auth(s))
        assert codigo == 200, f"/status do pod {s.slug}: {codigo}"
        return json.loads(corpo)

    def scan_concluido(self, s: Sessao) -> dict:
        codigo, _ = self.http(
            self.host(s.slug), "/scan", auth=self.auth(s), metodo="POST"
        )
        assert codigo in (200, 202), f"POST /scan: {codigo}"

        def pronto() -> bool:
            st = self.pod_status(s)
            return not st.get("running") and int(st.get("findings_count") or 0) > 0

        _esperar(pronto, 240, 3.0, msg="scan do corpus sintético concluído")
        return self.pod_status(s)

    def assert_limpo(self, slug: str) -> None:
        """Postconditions of A-5."""
        nomes = self.podman("ps", "-a", "--format", "{{.Names}}").stdout
        assert f"prospect-{slug}" not in nomes.split()
        assert (
            f"prospect-{slug}"
            not in self.podman("network", "ls", "--format", "{{.Name}}").stdout
        )
        assert (
            f"prospect-{slug}"
            not in self.podman("volume", "ls", "--format", "{{.Name}}").stdout
        )
        unidades = self.systemctl(
            "list-units", "--all", "--no-legend", f"demo-prospect@{slug}*"
        )
        assert unidades.stdout.strip() == "", unidades.stdout
        codigo, _ = self.http(self.host(slug), "/en/")
        assert codigo not in (200, 401), f"host do slug ainda é servido ({codigo})"
        assert not (self.runtime / "demo-prospect" / slug).exists()
        assert not list(self.caddy_dir.glob(f"{slug}.*"))

    def assert_slot_ok(self, id_antes: str) -> None:
        """Postconditions of A-17 (the dashboard is back, same container, trusted)."""
        info = self.inspecionar(self.dash)
        assert info["Id"] == id_antes
        assert info["State"]["Status"] == "running"
        assert self.dash_saudavel()
        assert not (self.runtime / "demo-prospect" / "slot.json").exists()


# --------------------------------------------------------------------------- fixtures
@pytest.fixture(scope="session")
def harness() -> Iterator[Harness]:
    if not shutil.which("podman") or not shutil.which("systemd-run"):
        pytest.skip("sem podman ou systemd-run")
    if _run(["systemd-run", "--user", "--scope", "true"]).returncode != 0:
        pytest.skip("systemd-run --user indisponível")
    image = os.environ.get("PROSPECT_TEST_IMAGE", "")
    if not image:
        pytest.skip("defina PROSPECT_TEST_IMAGE (imagem Data Boar de teste)")
    faltam = [p for p in (CLI, TEMPLATE) if not p.exists()]
    if faltam:
        raise CliAusente(
            f"ainda não existem: {[str(p.relative_to(REPO)) for p in faltam]}"
        )
    assert "data_boar" in image, (
        "preparação: a imagem de teste precisa ter data_boar no nome"
    )
    em_uso = _run(["podman", "ps", "--format", "{{.Names}} {{.Image}}"]).stdout
    assert "data_boar" not in em_uso, "preparação: há outro Data Boar rodando no Podman"
    h = Harness(image)
    try:
        h.subir()
        yield h
    finally:
        h.desmontar()


@pytest.fixture
def cenario(harness: Harness) -> Iterator[Harness]:
    harness.zerar()
    try:
        yield harness
    finally:
        harness.zerar()


# --------------------------------------------------------------------------- A-1 .. A-18
@pendente
def test_A1_up_imprime_credenciais_e_exige_senha(cenario: Harness) -> None:
    """A-1: up exits 0 with URL/user/password/warning; 401, 401, 200 on /en/; pod trusted."""
    h = cenario
    r = h.cli("up", "acme", "--stop-dashboard", "--ttl", "10m")
    assert r.returncode == 0, r.stderr
    s = h.ler_sessao("acme", r.stdout)
    assert s.senha and USER in r.stdout
    assert "dashboard" in r.stdout and "FORA DO AR" in r.stdout
    host = h.host("acme")
    assert h.http(host, "/en/")[0] == 401
    assert h.http(host, "/en/", auth=h.auth(s, "senha-errada"))[0] == 401
    assert h.http(host, "/en/", auth=h.auth(s))[0] == 200
    assert h.pod_status(s)["trust_state"] == "trusted"


@pendente
def test_A2_up_repetido_e_idempotente(cenario: Harness) -> None:
    """A-2: second up exits 0, no new password, same URL and deadline, one container."""
    h = cenario
    s1 = h.subir_prospecto()
    r = h.cli("up", "acme")
    assert r.returncode == 0, r.stderr
    s2 = h.ler_sessao("acme", r.stdout)
    assert (s2.url, s2.expires_at) == (s1.url, s1.expires_at)
    assert s1.senha not in r.stdout and not s2.senha
    nomes = h.podman("ps", "-a", "--format", "{{.Names}}").stdout.split()
    assert nomes.count("prospect-acme") == 1


@pendente
def test_A3_pod_nao_alcanca_nada_fora(cenario: Harness) -> None:
    """A-3: from inside the pod, no public IP, LAN IP, host.containers.internal, host loopback
    ports or external name resolution."""
    import socket

    h = cenario
    h.subir_prospecto()
    with socket.socket() as ouvinte:  # stands in for a database port on the host
        ouvinte.bind(("127.0.0.1", 0))
        ouvinte.listen(1)
        porta_banco = ouvinte.getsockname()[1]
        rota = _run(["ip", "-4", "route", "get", "1.1.1.1"]).stdout
        lan = re.search(r"src (\S+)", rota)
        alvos = [("1.1.1.1", 443), ("host.containers.internal", h.porta_apres),
                 ("127.0.0.1", h.porta_apres), ("127.0.0.1", porta_banco)]  # fmt: skip
        if lan:
            alvos.append((lan.group(1), h.porta_apres))
        script = (
            "import socket,sys\n"
            "for h,p in [a.split(':') for a in sys.argv[1:]]:\n"
            "    try:\n"
            "        socket.create_connection((h,int(p)),timeout=4).close(); print('CONECTOU',h,p)\n"
            "    except OSError: pass\n"
            "try:\n"
            "    socket.getaddrinfo('example.com',443); print('RESOLVEU')\n"
            "except OSError: pass\n"
        )
        r = h.podman("exec", "prospect-acme", "python3", "-c", script,
                     *[f"{a}:{b}" for a, b in alvos])  # fmt: skip
        assert r.returncode == 0, r.stderr[-300:]
        assert r.stdout.strip() == "", f"o pod alcançou algo fora: {r.stdout}"


@pendente
def test_A4_isolamento_entre_prospectos(cenario: Harness) -> None:
    """A-4: other processes reach the pod port but get 401 without the key; after
    scan(acme)/down/up(bravo), bravo has no finding or session from acme."""
    h = cenario
    s = h.subir_prospecto("acme")
    for porta_origem in (h.porta_pod,):
        r = _run(["curl", "-sk", "-m", "10", "-o", "/dev/null", "-w", "%{http_code}",
                  f"https://127.0.0.1:{porta_origem}/en/"])  # fmt: skip
        assert r.stdout == "401", f"pod sem chave devia dar 401, deu {r.stdout}"
    antes = h.scan_concluido(s)
    assert antes["findings_count"] > 0
    sessao_acme = antes["current_session_id"]
    assert h.cli("down", "acme").returncode == 0
    s2 = h.subir_prospecto("bravo")
    st = h.pod_status(s2)
    assert int(st["findings_count"]) == 0
    assert st["current_session_id"] != sessao_acme


@pendente
def test_A5_down_remove_tudo(cenario: Harness) -> None:
    """A-5: down exits 0 and leaves nothing of acme (podman, unit, route, state, fragment)."""
    h = cenario
    h.subir_prospecto()
    r = h.cli("down", "acme")
    assert r.returncode == 0, r.stderr
    h.assert_limpo("acme")


@pendente
def test_A6_down_repetido_ou_inexistente(cenario: Harness) -> None:
    """A-6: down twice, and down of an unknown slug, exit 0 with 'nada a remover'."""
    h = cenario
    h.subir_prospecto()
    assert h.cli("down", "acme").returncode == 0
    for slug in ("acme", "nunca"):
        r = h.cli("down", slug)
        assert r.returncode == 0, r.stderr
        assert "nada a remover" in r.stdout


@pendente
def test_A7_ttl_vence_e_reaper_limpa(cenario: Harness) -> None:
    """A-7: after the TTL plus one reaper cycle, A-5 and A-17 hold with no manual command."""
    h = cenario
    id_dash = h.inspecionar(h.dash)["Id"]
    h.subir_prospecto("acme", "5m")
    h.systemctl("start", "demo-prospect-reap.timer")
    _esperar(
        lambda: not h.existe("prospect-acme") and h.dash_saudavel(),
        8 * 60,
        10.0,
        msg="TTL de 5m + 1 ciclo do reaper",
    )
    h.assert_limpo("acme")
    h.assert_slot_ok(id_dash)


@pendente
def test_A8_pod_morto_nao_volta_e_slot_volta(cenario: Harness) -> None:
    """A-8: podman kill on the pod: it does not come back; A-5 and A-17 hold within 3 min."""
    h = cenario
    id_dash = h.inspecionar(h.dash)["Id"]
    h.subir_prospecto()
    h.systemctl("start", "demo-prospect-reap.timer")
    assert h.podman("kill", "prospect-acme").returncode == 0
    _esperar(
        lambda: not h.existe("prospect-acme") and h.dash_saudavel(),
        3 * 60,
        5.0,
        msg="limpeza em até 3 min",
    )
    h.assert_limpo("acme")
    h.assert_slot_ok(id_dash)


@pendente
@pytest.mark.parametrize("slug", ["Acme.com", "dashboard"])
def test_A9_slug_invalido_ou_reservado(cenario: Harness, slug: str) -> None:
    """A-9: invalid or reserved slug exits 2, creates nothing, does not stop the dashboard."""
    h = cenario
    id_dash = h.inspecionar(h.dash)["Id"]
    r = h.cli("up", slug, "--stop-dashboard")
    assert r.returncode == 2, (r.returncode, r.stderr)
    assert not [n for n in h.podman("ps", "-a", "--format", "{{.Names}}").stdout.split()
                if n.startswith("prospect-")]  # fmt: skip
    assert not list(h.caddy_dir.glob("*"))
    h.assert_slot_ok(id_dash)


@pendente
def test_A10_nada_cai_durante_o_ciclo(cenario: Harness) -> None:
    """A-10: control site and the test apresentacao answer 200 throughout a full cycle, and the
    apresentacao keeps the same StartedAt."""
    h = cenario
    inicio = h.inspecionar(h.apres)["State"]["StartedAt"]
    sondas = [
        ("controle", lambda: h.http(f"ctrl.{DOMAIN}", "/")[0]),
        ("apresentacao", lambda: (h.status_direto(h.porta_apres) is not None) and 200),
    ]
    with Monitor(sondas) as mon:  # type: ignore[arg-type]
        h.subir_prospecto()
        assert h.cli("down", "acme").returncode == 0
    assert mon.falhas == []
    assert h.inspecionar(h.apres)["State"]["StartedAt"] == inicio


@pendente
def test_A11_endurecimento_do_pod(cenario: Harness) -> None:
    """A-11: limits and hardening in `podman inspect` of the pod."""
    h = cenario
    h.subir_prospecto()
    i = h.inspecionar("prospect-acme")
    hc = i["HostConfig"]
    assert hc["Memory"] == 700 * 1024 * 1024
    assert hc["MemorySwap"] == hc["Memory"]
    assert hc["NanoCpus"] == 10**9 or hc.get("CpuQuota") == hc.get("CpuPeriod")
    assert hc["PidsLimit"] == 256
    assert hc["ReadonlyRootfs"] is True
    assert hc["CapAdd"] in (None, []) and "ALL" in [c.upper() for c in hc["CapDrop"]]
    assert "no-new-privileges" in " ".join(hc["SecurityOpt"] or [])
    assert hc["LogConfig"]["Type"] == "none"
    assert i["Config"]["Hostname"] == LICENSE_HOSTNAME
    tmpfs = {m["Destination"] for m in i["Mounts"] if m["Type"] == "tmpfs"} | set(
        (hc.get("Tmpfs") or {}).keys()
    )
    assert {"/data", "/tmp"} <= tmpfs  # noqa: S108


@pendente
def test_A12_segredos_nao_vazam(cenario: Harness) -> None:
    """A-12: printed password and the API key (read from pod.env) are not in the journal, the
    proxy logs, ~/.local/share/containers or $XDG_RUNTIME_DIR after A-5."""
    h = cenario
    s = h.subir_prospecto()
    pod_env = h.runtime / "demo-prospect" / "acme" / "pod.env"
    chave = re.search(
        r"PROSPECT_API_KEY=([0-9a-f]{64})", pod_env.read_text(encoding="utf-8")
    )
    assert chave and s.senha
    assert h.cli("down", "acme").returncode == 0
    segredos = [s.senha, chave.group(1)]
    journal = _run(
        ["journalctl", "--user", "--no-pager", "--since", h.inicio_journal]
    ).stdout
    logs_proxy = h.podman("logs", h.proxy)
    for seg in segredos:
        assert seg not in journal
        assert seg not in logs_proxy.stdout + logs_proxy.stderr
        for raiz in (Path.home() / ".local" / "share" / "containers", h.runtime):
            r = _run(
                ["grep", "-rlsaF", "--exclude-dir=qa-*", seg, str(raiz)], timeout=600
            )
            achados = [a for a in r.stdout.split() if not a.startswith(str(h.raiz))]
            assert achados == [], f"segredo em {achados}"


@pendente
def test_A14_segundo_scan_recebe_409(cenario: Harness) -> None:
    """A-14: two POST /scan in a row through the proxy: the second gets 409."""
    h = cenario
    s = h.subir_prospecto()
    host = h.host("acme")
    primeiro = h.http(host, "/scan", auth=h.auth(s), metodo="POST")[0]
    segundo = h.http(host, "/scan", auth=h.auth(s), metodo="POST")[0]
    assert primeiro in (200, 202)
    assert segundo == 409


@pendente
def test_A15_troca_de_slot(cenario: Harness) -> None:
    """A-15: without the flag exit 2 and the dashboard keeps running; with it the dashboard is
    exited (same id, restart=always), stays so 30 s later, apresentacao untouched, pod up."""
    h = cenario
    info = h.inspecionar(h.dash)
    id_dash = info["Id"]
    inicio_apres = h.inspecionar(h.apres)["State"]["StartedAt"]
    r = h.cli("up", "acme")
    assert r.returncode == 2, (r.returncode, r.stderr)
    assert h.estado(h.dash) == "running"
    assert not h.existe("prospect-acme")
    s = h.subir_prospecto()

    def parada() -> bool:
        i = h.inspecionar(h.dash)
        return (
            i["Id"] == id_dash
            and i["State"]["Status"] == "exited"
            and i["HostConfig"]["RestartPolicy"]["Name"] == "always"
        )

    assert parada()
    _esperar_estavel(30, parada, 5.0)
    assert h.inspecionar(h.apres)["State"]["StartedAt"] == inicio_apres
    assert h.pod_status(s)["trust_state"] == "trusted"


@pendente
def test_A16_outro_prospecto_ativo(cenario: Harness) -> None:
    """A-16: with acme active, up bravo exits 4 naming acme, and bravo has nothing."""
    h = cenario
    h.subir_prospecto("acme")
    r = h.cli("up", "bravo", "--stop-dashboard")
    assert r.returncode == 4, (r.returncode, r.stderr)
    assert "acme" in r.stdout + r.stderr
    h.assert_limpo("bravo")


@pendente
def test_A17_dashboard_volta_e_continua_viva(cenario: Harness) -> None:
    """A-17: after down, the dashboard is running (same id), trusted, and 60 s later it is
    still running with a live conmon (the old scar does not come back)."""
    h = cenario
    id_dash = h.inspecionar(h.dash)["Id"]
    h.subir_prospecto()
    assert h.cli("down", "acme").returncode == 0
    h.assert_slot_ok(id_dash)

    def viva() -> bool:
        st = h.inspecionar(h.dash)["State"]
        return st["Status"] == "running" and Path(f"/proc/{st['ConmonPid']}").exists()

    assert viva()
    _esperar_estavel(60, viva, 5.0)
    assert h.dash_saudavel()


@pendente
def test_A18_dashboard_nao_volta_gera_alerta_unico(cenario: Harness) -> None:
    """A-18: with a dashboard that cannot start, down exits 8, removes the pod, writes ALERT and
    an err line in the journal, calls the alert command once, list shows FORA DO AR, and two
    reaper cycles do not repeat the alert.

    Deviation from the design text: the dashboard is made unstartable by a bind mount whose
    source is removed (an image with a missing tag cannot be forced after `create`)."""
    h = cenario
    h.subir_prospecto()
    fonte = h.raiz / "sumira"
    fonte.mkdir()
    h.podman("rm", "-f", "-t", "0", h.dash)
    r = h.podman(
        "create", "--name", h.dash, "--restart=always", "-v", f"{fonte}:/x:ro", h.image
    )
    assert r.returncode == 0, f"preparação: {r.stderr[-300:]}"
    fonte.rmdir()
    assert h.podman("start", h.dash).returncode != 0, (
        "preparação: a dashboard devia não subir"
    )
    try:
        r = h.cli("down", "acme")
        assert r.returncode == 8, (r.returncode, r.stderr)
        assert not h.existe("prospect-acme")
        assert h.alerta_arquivo.exists() and "ALERT" in h.alerta_arquivo.read_text(
            encoding="utf-8"
        )
        err = _run(["journalctl", "--user", "--no-pager", "-t", "databoar-prospect", "-p", "err",
                    "--since", h.inicio_journal]).stdout  # fmt: skip
        assert "dashboard não voltou" in err
        chamadas = h.alerta_chamadas.read_text(encoding="utf-8").splitlines()
        assert len(chamadas) == 1
        assert "FORA DO AR" in h.cli("list").stdout
        for _ in range(2):
            h.cli("reap")
        assert len(h.alerta_chamadas.read_text(encoding="utf-8").splitlines()) == 1
    finally:
        h.podman("rm", "-f", "-t", "0", h.dash)
