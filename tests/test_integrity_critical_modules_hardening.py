"""#1298 — expanded behaviour-critical allowlist + CLI integrity surfacing."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from core.integrity_anchor import (
    CRITICAL_MODULES,
    alpha_version_suffix,
    compute_module_hashes,
    ensure_integrity_anchor,
    is_tampered,
    reset_integrity_anchor_for_tests,
    resolve_critical_modules,
)
from tests.integrity_persistence_criterion import (
    imports_legacy_db,
    is_persistence_source,
    runtime_modules_importing_legacy_db,
    runtime_persistence_modules,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]

_TAMPER_CLASS_PATHS = (
    "connectors/sql_connector.py",
    "core/licensing/verify.py",
    "connectors/sql_sampling.py",
    "core/database.py",
)

_PERSISTENCE_MODULE = "core/database.py"


@pytest.fixture(autouse=True)
def _clean_snapshot():
    reset_integrity_anchor_for_tests()
    yield
    reset_integrity_anchor_for_tests()


def _cfg(tmp_path) -> dict:
    return {"sqlite_path": str(tmp_path / "audit_results.db")}


def test_resolve_critical_modules_includes_globs_and_extras():
    modules = resolve_critical_modules()
    assert modules == CRITICAL_MODULES
    assert len(modules) >= 40
    for rel in (
        "connectors/sql_connector.py",
        "connectors/sql_sampling.py",
        "connectors/url_guard.py",
        "core/licensing/verify.py",
        "core/licensing/tier_features.py",
        "core/connector_registry.py",
        "core/validation.py",
        "utils/logger.py",
        "api/webauthn_routes.py",
        "api/webauthn_html_gate.py",
        "core/integrity_signed_manifest.py",
    ):
        assert rel in modules
    hashes = compute_module_hashes()
    assert all(hashes[rel] != "missing" for rel in modules)


@pytest.mark.parametrize("rel_path", _TAMPER_CLASS_PATHS)
def test_tamper_on_critical_class_detected_on_scan_startup(
    tmp_path, monkeypatch, rel_path: str
):
    """Simulates scan startup re-verify after tamper on each representative class."""
    cfg = _cfg(tmp_path)
    ensure_integrity_anchor(cfg)
    drifted = compute_module_hashes()
    drifted[rel_path] = "0" * 64
    monkeypatch.setattr("core.integrity_anchor.compute_module_hashes", lambda: drifted)
    reset_integrity_anchor_for_tests()
    snap = ensure_integrity_anchor(cfg)
    assert snap["integrity_state"] == "tampered"
    assert rel_path in snap["mismatched_files"]
    assert is_tampered()
    assert alpha_version_suffix() == "-alpha"


def test_cli_version_line_shows_alpha_when_tampered(tmp_path, monkeypatch):
    """--version path: integrity preflight + public version suffix when tampered."""
    cfg = _cfg(tmp_path)
    ensure_integrity_anchor(cfg)
    drifted = compute_module_hashes()
    drifted["connectors/sql_connector.py"] = "f" * 64
    monkeypatch.setattr("core.integrity_anchor.compute_module_hashes", lambda: drifted)
    reset_integrity_anchor_for_tests()
    from main import _cli_public_version_line, _run_startup_integrity_check

    snap = _run_startup_integrity_check(cfg)
    assert snap["integrity_state"] == "tampered"
    assert "-alpha" in _cli_public_version_line()
    assert "connectors/sql_connector.py" in snap["mismatched_files"]


def test_validate_config_emits_runtime_trust_line(tmp_path):
    """--validate-config pre-flight surfaces runtime-trust after integrity check."""
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(
        "targets:\n  - type: filesystem\n    name: fs1\n    path: .\n",
        encoding="utf-8",
    )
    db = tmp_path / "audit_results.db"
    ensure_integrity_anchor({"sqlite_path": str(db)})
    r = subprocess.run(
        [
            sys.executable,
            str(_REPO_ROOT / "main.py"),
            "--config",
            str(cfg_path),
            "--validate-config",
        ],
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
        timeout=60,
        check=False,
    )
    assert r.returncode == 0, r.stderr + r.stdout
    assert "runtime-trust:" in r.stdout
    assert "Validating config:" in r.stdout


# --- #2253: the scan persistence module is covered by the signed manifest ---------------------


def test_d2253_1_persistence_module_is_in_the_signed_list():
    """D2253-1: the module is listed and hashed (never 'missing')."""
    assert _PERSISTENCE_MODULE in CRITICAL_MODULES
    hashes = compute_module_hashes()
    assert _PERSISTENCE_MODULE in hashes
    assert hashes[_PERSISTENCE_MODULE] != "missing"


def test_d2253_2_change_in_the_persistence_module_is_tampered(tmp_path, monkeypatch):
    """D2253-2: a change in the module makes the signed manifest report tampered.

    The key must already be in the computed hashes before the mutation: the
    test must not pass by adding a key the manifest never had.
    """
    cfg = _cfg(tmp_path)
    ensure_integrity_anchor(cfg)
    drifted = compute_module_hashes()
    assert _PERSISTENCE_MODULE in drifted
    drifted[_PERSISTENCE_MODULE] = "0" * 64
    monkeypatch.setattr("core.integrity_anchor.compute_module_hashes", lambda: drifted)
    reset_integrity_anchor_for_tests()
    snap = ensure_integrity_anchor(cfg)
    assert snap["integrity_state"] == "tampered"
    assert _PERSISTENCE_MODULE in snap["mismatched_files"]
    assert alpha_version_suffix() == "-alpha"


def test_d2253_3_every_runtime_persistence_module_is_signed():
    """D2253-3: the criterion finds no persistence module outside the signed list,
    and no runtime module imports the legacy ``db`` package."""
    found = runtime_persistence_modules(_REPO_ROOT)
    assert found, "the criterion found no persistence module at all"
    assert found <= set(CRITICAL_MODULES), sorted(found - set(CRITICAL_MODULES))
    assert runtime_modules_importing_legacy_db(_REPO_ROOT) == set()


def test_d2253_4_criterion_classifies_tables_and_writers():
    """D2253-4: self-test of the criterion on synthetic sources."""
    assert is_persistence_source('class X:\n    __tablename__ = "t"\n') is True
    assert is_persistence_source('class X:\n    __tablename__: str = "t"\n') is True
    assert is_persistence_source("def save_failure(a, b, c):\n    pass\n") is True
    assert (
        is_persistence_source("class M:\n    def save_finding(self):\n        pass\n")
        is True
    )
    assert is_persistence_source("def save(a):\n    pass\n") is False
    assert is_persistence_source('TABLE = "__tablename__"\n') is False
    assert imports_legacy_db("import db\n") is True
    assert imports_legacy_db("from db.database import X\n") is True
    assert imports_legacy_db("from core.db_utils import X\nimport dbm\n") is False
