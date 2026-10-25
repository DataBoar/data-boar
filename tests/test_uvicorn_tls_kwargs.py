"""
Regression: uvicorn>=0.52 removed run(..., ssl=SSLContext).

Native HTTPS in main.py must pass ssl_context_factory (keeps TLS >= 1.2).
Found during S2a demo bar after Order -1 uvicorn bump (#1491).
"""

from __future__ import annotations

import inspect
import ssl
from pathlib import Path

import uvicorn
from uvicorn.config import Config


REPO_ROOT = Path(__file__).resolve().parents[1]
MAIN_PY = REPO_ROOT / "main.py"


def test_uvicorn_run_accepts_ssl_context_factory_not_ssl_kwarg():
    """Installed uvicorn must match the kwargs main.py uses for HTTPS."""
    params = inspect.signature(uvicorn.run).parameters
    assert "ssl_context_factory" in params, (
        "uvicorn.run missing ssl_context_factory — main.py HTTPS wiring needs an update"
    )
    assert "ssl" not in params, (
        "uvicorn.run unexpectedly accepts ssl= again; revisit main.py if API reverts"
    )


def test_ssl_context_factory_kwargs_load_into_uvicorn_config():
    """Build the same kwarg shape as main.py and load Config (no network bind)."""
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2

    def _ssl_context_factory(config, create_default_context, _ctx=ctx):
        return _ctx

    # Minimal ASGI app string — Config.load resolves SSL without serving.
    config = Config(
        "tests.test_uvicorn_tls_kwargs:_asgi_noop",
        host="127.0.0.1",
        port=0,
        ssl_context_factory=_ssl_context_factory,
    )
    config.load()
    assert isinstance(config.ssl, ssl.SSLContext)
    assert config.ssl.minimum_version == ssl.TLSVersion.TLSv1_2


async def _asgi_noop(scope, receive, send):
    """Placeholder ASGI app for Config construction only."""
    if scope["type"] != "http":
        return
    await send({"type": "http.response.start", "status": 204, "headers": []})
    await send({"type": "http.response.body", "body": b""})


def test_main_py_uses_ssl_context_factory_for_https():
    """Source guard: do not regress to uvicorn_kwargs['ssl'] = ctx."""
    text = MAIN_PY.read_text(encoding="utf-8")
    assert 'uvicorn_kwargs["ssl_context_factory"]' in text
    assert 'uvicorn_kwargs["ssl"]' not in text
    assert "ssl_context_factory" in text
    # Keep TLS 1.2 floor on the context we hand to the factory.
    assert "TLSVersion.TLSv1_2" in text
