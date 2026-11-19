"""Real adapters of ``deploy/demo/prospect/prospect.py`` against local stdlib servers.

Task 2280.2 (epic #2280, issue #2283). The D2280.1-* tests use fakes for every seam of
section 15; these extra tests run the real ``Runner``, ``AdminClient`` (HTTP over a unix
socket in ``tmp_path``), ``HealthProbe`` (HTTPS on 127.0.0.1 with the pod certificate
made by ``openssl_argv``) and ``Alerter``, so the code the host runs is executed at least
once off the host. Linux host script: skipped as a module on Windows.
"""

from __future__ import annotations

import http.server
import json
import os
import shutil
import socket
import socketserver
import ssl
import subprocess
import sys
import threading
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

if os.name == "nt":
    pytest.skip("prospect.py is a Linux host script (fcntl)", allow_module_level=True)

from tests.test_deploy_demo_prospect_cli import P  # noqa: E402


class _Recorder(http.server.BaseHTTPRequestHandler):
    seen: list[dict[str, Any]] = []
    reply: tuple[int, bytes] = (200, b"{}")

    def log_message(self, format: str, *args: Any) -> None:  # silence stderr
        return

    def _answer(self, body: bytes = b"") -> None:
        type(self).seen.append(
            {
                "method": self.command,
                "path": self.path,
                "headers": {k.lower(): v for k, v in self.headers.items()},
                "body": body,
            }
        )
        code, payload = type(self).reply
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:  # noqa: N802
        self._answer()

    def do_POST(self) -> None:  # noqa: N802
        n = int(self.headers.get("Content-Length") or 0)
        self._answer(self.rfile.read(n))


def _handler(reply: tuple[int, bytes]) -> type[_Recorder]:
    return type("H", (_Recorder,), {"seen": [], "reply": reply})


class _UnixHTTPServer(socketserver.ThreadingMixIn, socketserver.UnixStreamServer):
    daemon_threads = True

    def get_request(self):  # type: ignore[no-untyped-def]
        request, _ = super().get_request()
        return request, ("local", 0)


@pytest.fixture
def unix_admin(tmp_path: Path) -> Iterator[tuple[str, type[_Recorder]]]:
    # Short path: AF_UNIX paths stop at 108 bytes (design, section 10).
    d = Path(os.environ.get("XDG_RUNTIME_DIR") or "/tmp")  # noqa: S108
    sock = d / f"pt-{os.getpid()}-{threading.get_ident() % 10000}.sock"
    sock.unlink(missing_ok=True)
    h = _handler((400, b'{"error":"bad"}'))
    srv = _UnixHTTPServer(str(sock), h)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    try:
        yield str(sock), h
    finally:
        srv.shutdown()
        srv.server_close()
        t.join(5)
        sock.unlink(missing_ok=True)


def test_runner_executa_sem_shell_e_repassa_stdin() -> None:
    rc, out, err = P.Runner().run(
        [sys.executable, "-c", "import sys; print(sys.stdin.read().upper())"],
        input="ab",
    )
    assert (rc, out.strip(), err) == (0, "AB", "")
    rc, _out, _err = P.Runner().run(["/caminho/que/nao/existe"])
    assert rc == 127


def test_admin_client_post_load_no_socket(unix_admin: tuple[str, Any]) -> None:
    path, h = unix_admin
    code = P.AdminClient(path).load("site {\n}\n")
    assert code == 400
    assert h.seen == [
        {
            "method": "POST",
            "path": "/load",
            "headers": h.seen[0]["headers"],
            "body": b"site {\n}\n",
        }
    ]
    assert h.seen[0]["headers"]["content-type"] == "text/caddyfile"


def test_admin_client_sem_conexao_devolve_0(tmp_path: Path) -> None:
    assert P.AdminClient(str(tmp_path / "nao-ha.sock")).load("x") == 0


def test_alerter_journal_e_comando(tmp_path: Path) -> None:
    calls: list[tuple[list[str], str | None]] = []

    class R:
        def run(self, argv: list[str], input: str | None = None):
            calls.append((argv, input))
            return 0, "", ""

    a = P.Alerter(R(), "/opt/notificar")
    a.emit("dashboard não voltou após a sessão de prospecto acme: x")
    a.info("dashboard recuperada")
    assert calls == [
        (
            ["systemd-cat", "-t", "databoar-prospect", "-p", "err"],
            "dashboard não voltou após a sessão de prospecto acme: x\n",
        ),
        (
            [
                "/opt/notificar",
                "dashboard não voltou após a sessão de prospecto acme: x",
            ],
            None,
        ),
        (
            ["systemd-cat", "-t", "databoar-prospect", "-p", "info"],
            "dashboard recuperada\n",
        ),
    ]


if os.name != "nt" and shutil.which("openssl"):

    @pytest.fixture
    def pod_https(
        tmp_path: Path,
    ) -> Iterator[tuple[int, Path, type[_Recorder]]]:
        """HTTPS on 127.0.0.1 with the pod certificate made by the real openssl argv."""
        certs = tmp_path / "pod"
        certs.mkdir()
        r = subprocess.run(
            P.openssl_argv("acme", certs), capture_output=True, text=True, check=False
        )
        assert r.returncode == 0, r.stderr[-300:]
        body = json.dumps(
            {"trust_state": "trusted", "license": {"license_state": "OPEN"}}
        ).encode()
        h = _handler((200, body))
        srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h)
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(str(certs / "tls.crt"), str(certs / "tls.key"))
        srv.socket = ctx.wrap_socket(srv.socket, server_side=True)
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        try:
            yield srv.server_address[1], certs, h
        finally:
            srv.shutdown()
            srv.server_close()
            t.join(5)

    def test_openssl_argv_gera_ec_p256_com_san(pod_https: Any) -> None:
        _port, certs, _h = pod_https
        text = subprocess.run(
            ["openssl", "x509", "-in", str(certs / "tls.crt"), "-noout", "-text"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        assert "prime256v1" in text or "P-256" in text
        assert "DNS:prospect-acme" in text

    def test_health_probe_fixa_o_certificado_do_pod(pod_https: Any) -> None:
        port, certs, h = pod_https
        url = f"https://127.0.0.1:{port}/status"
        st = P.HealthProbe().status(url, "k" * 64, str(certs / "tls.crt"))
        assert st == {"trust_state": "trusted", "license": {"license_state": "OPEN"}}
        assert h.seen[-1]["headers"]["x-api-key"] == "k" * 64
        other = certs.parent / "outro"
        other.mkdir()
        subprocess.run(P.openssl_argv("bravo", other), capture_output=True, check=True)
        assert P.HealthProbe().status(url, None, str(other / "tls.crt")) is None

    def test_health_probe_slot_sem_verificacao_so_no_loopback(pod_https: Any) -> None:
        port, _certs, h = pod_https
        assert P.HealthProbe().status(f"https://127.0.0.1:{port}/status") is not None
        h.reply = (503, b"{}")
        assert P.HealthProbe().status(f"https://127.0.0.1:{port}/status") is None
        with pytest.raises(ValueError):
            P.HealthProbe().status(f"https://localhost:{port}/status")

    def test_route_status_com_sni_e_host(pod_https: Any) -> None:
        port, _certs, h = pod_https
        h.reply = (401, b"{}")
        assert P.HealthProbe().route_status("acme.prospect.test", port) == 401
        assert h.seen[-1]["headers"]["host"] == "acme.prospect.test"
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            closed = s.getsockname()[1]
        assert P.HealthProbe().route_status("acme.prospect.test", closed) == 0
