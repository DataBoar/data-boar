"""Pillow image round-trip, uv.lock Pillow floor, and the API health request.

The published extra floor stays on Pillow 12.x (#2116). The audited tree records
Pillow 13 in ``uv.lock``. This module reads that pin from the lock file and
keeps the image round-trip independent of whichever Pillow a pip install resolved.
"""

from __future__ import annotations

import io
import tomllib
from pathlib import Path

from PIL import Image

_REPO = Path(__file__).resolve().parents[1]
_LICENSE_ENV = (
    "CONFIG_PATH",
    "DATA_BOAR_LICENSE_PATH",
    "DATA_BOAR_LICENSE_PUBLIC_KEY_PATH",
    "DATA_BOAR_LICENSE_PUBLIC_KEY_PEM",
    "DATA_BOAR_LICENSE_MLDSA_PUBLIC_KEY_PATH",
    "DATA_BOAR_LICENSE_MLDSA_PUBLIC_KEY_PEM",
    "DATA_BOAR_LICENSE_MODE",
)


def _locked_package_version(name: str) -> str:
    lock = tomllib.loads((_REPO / "uv.lock").read_bytes().decode())
    versions = [pkg["version"] for pkg in lock["package"] if pkg["name"] == name]
    assert versions, f"{name} missing from uv.lock"
    return versions[0]


def test_uv_lock_resolves_pillow_13() -> None:
    """The uv override installs Pillow 13 even though the public floor does not."""
    version = _locked_package_version("pillow")
    major = int(version.split(".", 1)[0])
    assert major >= 13, version


def test_pillow_opens_saved_png() -> None:
    """Image.new → PNG bytes → Image.open is the path report and sample code use."""
    image = Image.new("RGB", (8, 4), color=(12, 34, 56))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    opened = Image.open(buffer)
    assert opened.size == (8, 4)
    assert opened.getpixel((0, 0)) == (12, 34, 56)


def test_pillow_heif_opener_still_opens_png() -> None:
    """Registering the HEIF opener must not break a normal PNG open."""
    import pytest

    pillow_heif = pytest.importorskip("pillow_heif")
    pillow_heif.register_heif_opener()
    image = Image.new("RGB", (4, 4), color=(1, 2, 3))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    opened = Image.open(buffer)
    assert opened.size == (4, 4)


def test_health_request_returns_ok(monkeypatch) -> None:
    """GET /health stays 200 with the status body on the Starlette request path."""
    import starlette
    from starlette.testclient import TestClient

    for name in _LICENSE_ENV:
        monkeypatch.delenv(name, raising=False)
    major = int(starlette.__version__.split(".", 1)[0])
    assert major >= 1

    from api.routes import app

    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
