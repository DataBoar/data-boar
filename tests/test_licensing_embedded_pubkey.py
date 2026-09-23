"""#1331 — embedded official license pubkey default + override precedence."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from core.licensing.fingerprint import compute_machine_fingerprint
from core.licensing.guard import LicenseGuard
from core.licensing.verify import load_embedded_official_public_key_pem

REPO_ROOT = Path(__file__).resolve().parents[1]
OFFICIAL_PEM = REPO_ROOT / "core" / "licensing" / "license-pub-v1.pem"


def _pem_public(priv: Ed25519PrivateKey) -> str:
    pub = priv.public_key()
    return (
        pub.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode("ascii")
        .strip()
    )


def _make_token(
    priv: Ed25519PrivateKey,
    *,
    extra: dict | None = None,
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": "lic-embedded-1",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=7)).timestamp()),
        "dbcid": "cust-1",
        "dbcname": "Embedded Key Customer",
        "dbenv": "qa",
        "dbissuer": "test-issuer",
        "dbkid": "k1",
        "dbtier": "enterprise",
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, priv, algorithm="EdDSA")


@pytest.fixture
def ed25519_priv() -> Ed25519PrivateKey:
    return Ed25519PrivateKey.generate()


@pytest.fixture(autouse=True)
def _clear_license_env(monkeypatch: pytest.MonkeyPatch):
    from core.licensing import reset_license_guard_for_tests

    reset_license_guard_for_tests()
    for k in (
        "DATA_BOAR_LICENSE_MODE",
        "DATA_BOAR_LICENSE_PATH",
        "DATA_BOAR_LICENSE_PUBLIC_KEY_PEM",
        "DATA_BOAR_LICENSE_PUBLIC_KEY_PATH",
        "DATA_BOAR_LICENSE_REVOCATION_PATH",
        "DATA_BOAR_EXPECTED_BUILD_DIGEST",
        "DATA_BOAR_RELEASE_MANIFEST_PATH",
    ):
        monkeypatch.delenv(k, raising=False)
    yield
    reset_license_guard_for_tests()


def test_embedded_loader_returns_committed_official_pem() -> None:
    loaded = load_embedded_official_public_key_pem()
    assert loaded is not None
    assert loaded == OFFICIAL_PEM.read_text(encoding="utf-8").strip()
    assert "BEGIN PUBLIC KEY" in loaded


def test_enforced_embedded_default_validates_matching_token(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    ed25519_priv: Ed25519PrivateKey,
) -> None:
    """Source-tree stand-in for a .lic signed by the official issuer key."""
    pem = _pem_public(ed25519_priv)
    monkeypatch.setattr(
        "core.licensing.guard.load_embedded_official_public_key_pem",
        lambda: pem,
    )
    mfp = compute_machine_fingerprint()
    lic = tmp_path / "bound.lic"
    lic.write_text(
        _make_token(ed25519_priv, extra={"dbmfp": mfp, "dbtier": "enterprise"}),
        encoding="utf-8",
    )
    g = LicenseGuard({"licensing": {"mode": "enforced", "license_path": str(lic)}})
    assert g.context.state == "VALID"
    assert g.context.dbtier == "enterprise"
    assert g.allows_scan() is True


def test_enforced_embedded_default_not_missing_public_key(
    tmp_path: Path,
    ed25519_priv: Ed25519PrivateKey,
) -> None:
    """A .lic with no pubkey env must use the packaged key, not fail missing_public_key."""
    lic = tmp_path / "foreign.lic"
    lic.write_text(_make_token(ed25519_priv), encoding="utf-8")
    g = LicenseGuard({"licensing": {"mode": "enforced", "license_path": str(lic)}})
    assert g.context.detail != "missing_public_key"
    assert g.context.state == "INVALID"
    assert "jwt_error" in g.context.detail


def test_pem_env_is_untrusted_key_override(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    winner = Ed25519PrivateKey.generate()
    monkeypatch.setenv("DATA_BOAR_LICENSE_PUBLIC_KEY_PEM", _pem_public(winner))
    lic = tmp_path / "t.lic"
    lic.write_text(_make_token(winner), encoding="utf-8")
    g = LicenseGuard({"licensing": {"mode": "enforced", "license_path": str(lic)}})
    assert g.context.state == "INVALID"
    assert g.context.detail == "untrusted_key_override"


def test_path_env_is_untrusted_key_override(
    tmp_path: Path,
    ed25519_priv: Ed25519PrivateKey,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    env_pem = tmp_path / "env.pem"
    env_pem.write_text(_pem_public(ed25519_priv), encoding="utf-8")
    monkeypatch.setenv("DATA_BOAR_LICENSE_PUBLIC_KEY_PATH", str(env_pem))
    lic = tmp_path / "t.lic"
    lic.write_text(_make_token(ed25519_priv), encoding="utf-8")
    g = LicenseGuard({"licensing": {"mode": "enforced", "license_path": str(lic)}})
    assert g.context.state == "INVALID"
    assert g.context.detail == "untrusted_key_override"


def test_config_public_key_path_is_untrusted_key_override(
    tmp_path: Path,
    ed25519_priv: Ed25519PrivateKey,
) -> None:
    pem_path = tmp_path / "k.pem"
    pem_path.write_text(_pem_public(ed25519_priv), encoding="utf-8")
    lic = tmp_path / "t.lic"
    lic.write_text(_make_token(ed25519_priv), encoding="utf-8")
    g = LicenseGuard(
        {
            "licensing": {
                "mode": "enforced",
                "license_path": str(lic),
                "public_key_path": str(pem_path),
            }
        }
    )
    assert g.context.state == "INVALID"
    assert g.context.detail == "untrusted_key_override"


def _venv_python(venv: Path) -> Path:
    if os.name == "nt":
        return venv / "Scripts" / "python.exe"
    return venv / "bin" / "python"


_WHEEL_PROBE = r"""
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from importlib.resources import files
from pathlib import Path

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from core.licensing.fingerprint import compute_machine_fingerprint
from core.licensing.guard import LicenseGuard
from core.licensing.verify import load_embedded_official_public_key_pem

venv_root = Path(sys.argv[1]).resolve()
lic_path = sys.argv[2]
import core.licensing.guard as guard_mod

guard_file = Path(guard_mod.__file__).resolve()
assert venv_root in guard_file.parents, guard_file

pem = load_embedded_official_public_key_pem()
assert pem and "BEGIN PUBLIC KEY" in pem
packaged = files("core.licensing").joinpath("license-pub-v1.pem").read_text(
    encoding="utf-8"
)
assert pem == packaged.strip()

priv = Ed25519PrivateKey.generate()
now = datetime.now(timezone.utc)
payload = {
    "sub": "lic-wheel-1",
    "iat": int(now.timestamp()),
    "exp": int((now + timedelta(days=7)).timestamp()),
    "dbcid": "cust-wheel",
    "dbcname": "Wheel Customer",
    "dbenv": "qa",
    "dbissuer": "test-issuer",
    "dbkid": "k1",
    "dbtier": "enterprise",
    "dbmfp": compute_machine_fingerprint(),
}
token = jwt.encode(payload, priv, algorithm="EdDSA")
Path(lic_path).write_text(token, encoding="utf-8")

for k in (
    "DATA_BOAR_LICENSE_PUBLIC_KEY_PEM",
    "DATA_BOAR_LICENSE_PUBLIC_KEY_PATH",
    "DATA_BOAR_LICENSE_PATH",
    "DATA_BOAR_LICENSE_MODE",
):
    os.environ.pop(k, None)

g = LicenseGuard({"licensing": {"mode": "enforced", "license_path": lic_path}})
assert g.context.detail != "missing_public_key", g.context.detail
assert g.context.state == "INVALID"
assert "jwt_error" in g.context.detail

pub = (
    priv.public_key()
    .public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    .decode("ascii")
    .strip()
)
os.environ["DATA_BOAR_LICENSE_PUBLIC_KEY_PEM"] = pub
from core.licensing import reset_license_guard_for_tests
import core.licensing.guard as guard_mod

reset_license_guard_for_tests()
g_env = LicenseGuard({"licensing": {"mode": "enforced", "license_path": lic_path}})
assert g_env.context.state == "INVALID", (g_env.context.state, g_env.context.detail)
assert g_env.context.detail == "untrusted_key_override"
os.environ.pop("DATA_BOAR_LICENSE_PUBLIC_KEY_PEM", None)
guard_mod.load_embedded_official_public_key_pem = lambda: pub
reset_license_guard_for_tests()
g2 = LicenseGuard({"licensing": {"mode": "enforced", "license_path": lic_path}})
assert g2.context.state == "VALID", (g2.context.state, g2.context.detail)
assert g2.context.dbtier == "enterprise"

print(
    json.dumps(
        {
            "ok": True,
            "embedded_has_official_marker": "Ark71OUyF78XTwvywt+9HLr7odY" in pem,
        }
    )
)
"""


def test_wheel_install_embedded_pubkey_default(tmp_path: Path) -> None:
    """Install the built wheel (not the source tree) and exercise the packaged PEM.

    A VALID token against the *official* pubkey needs the issuer private key,
    which is not in this repo. The probe asserts: official PEM is in the wheel,
    importlib.resources loads it, missing_public_key is gone, a raw PEM env
    override is rejected, and pinning the embedded loader (test stand-in for
    the issuer key) still yields VALID + dbtier from a bound .lic.
    """
    if shutil.which("uv") is None:
        pytest.skip("uv is required to build and install the wheel")

    dist = tmp_path / "dist"
    dist.mkdir()
    build = subprocess.run(
        ["uv", "build", "--wheel", "--out-dir", str(dist)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if build.returncode != 0:
        pytest.fail(f"uv build failed:\n{build.stdout}\n{build.stderr}")
    wheels = list(dist.glob("data_boar-*.whl")) + list(dist.glob("data-boar-*.whl"))
    assert wheels, f"no wheel in {dist}: {list(dist.iterdir())}"

    venv = tmp_path / "venv"
    subprocess.run(
        ["uv", "venv", str(venv)],
        check=True,
        capture_output=True,
        text=True,
    )
    py = _venv_python(venv)
    for args in (
        ["uv", "pip", "install", "--python", str(py), "--no-deps", str(wheels[0])],
        ["uv", "pip", "install", "--python", str(py), "pyjwt", "cryptography"],
    ):
        inst = subprocess.run(args, capture_output=True, text=True, check=False)
        if inst.returncode != 0:
            pytest.fail(f"{args} failed:\n{inst.stdout}\n{inst.stderr}")

    probe_path = tmp_path / "probe_wheel_license.py"
    probe_path.write_text(_WHEEL_PROBE, encoding="utf-8")
    lic = tmp_path / "wheel.lic"
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONHOME", None)
    result = subprocess.run(
        [str(py), str(probe_path), str(venv.resolve()), str(lic)],
        cwd=str(tmp_path),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        pytest.fail(
            f"wheel probe failed ({result.returncode}):\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    payload = json.loads(result.stdout.strip().splitlines()[-1])
    assert payload["ok"] is True
    assert payload["embedded_has_official_marker"] is True
