"""#2168 — signed CRITICAL_MODULES manifest is the integrity trust root."""

from __future__ import annotations

import json

from tests.integrity_manifest_helpers import (
    generate_test_signing_key,
    install_matching_signed_manifest,
    reset_signed_manifest_pins,
    write_signed_manifest,
)

from core.integrity_anchor import (
    compute_module_hashes,
    ensure_integrity_anchor,
    reconcile_integrity_anchor,
    reset_integrity_anchor_for_tests,
)
from core.integrity_signed_manifest import (
    evaluate_signed_manifest,
    set_manifest_path_for_tests,
    set_verify_pem_for_tests,
    sign_manifest_body,
)


def _cfg(tmp_path) -> dict:
    return {"sqlite_path": str(tmp_path / "audit.db")}


def test_matching_signed_manifest_validates(tmp_path) -> None:
    install_matching_signed_manifest(tmp_path, release_label="1.8.0")
    snap = ensure_integrity_anchor(_cfg(tmp_path))
    assert snap["integrity_state"] == "validated"
    assert snap["trust_level"] == "expected"
    assert snap["mismatched_files"] == []


def test_absent_signed_manifest_is_tampered(tmp_path) -> None:
    reset_signed_manifest_pins()
    snap = ensure_integrity_anchor(_cfg(tmp_path))
    assert snap["integrity_state"] == "tampered"
    assert snap["trust_level"] == "adulterated"


def test_unsigned_manifest_is_tampered(tmp_path) -> None:
    path = tmp_path / "integrity_manifest.json"
    path.write_text(
        json.dumps(
            {
                "schema": "data-boar.integrity-manifest.v1",
                "release_label": "1.8.0",
                "files": compute_module_hashes(),
            }
        ),
        encoding="utf-8",
    )
    set_manifest_path_for_tests(str(path))
    private_key, public_pem = generate_test_signing_key()
    set_verify_pem_for_tests(public_pem)
    verdict = evaluate_signed_manifest(compute_module_hashes(), "1.8.0", None)
    assert verdict["integrity_state"] == "tampered"
    assert verdict["detail"] == "signed_manifest_unsigned"


def test_invalid_signature_is_tampered(tmp_path) -> None:
    private_key, _public_pem = generate_test_signing_key()
    _other_key, other_pem = generate_test_signing_key()
    path = write_signed_manifest(
        tmp_path / "integrity_manifest.json",
        compute_module_hashes(),
        "1.8.0",
        private_key,
    )
    set_manifest_path_for_tests(str(path))
    set_verify_pem_for_tests(other_pem)
    verdict = evaluate_signed_manifest(compute_module_hashes(), "1.8.0", None)
    assert verdict["integrity_state"] == "tampered"
    assert verdict["detail"] == "signed_manifest_signature_invalid"


def test_adulterated_manifest_body_is_tampered(tmp_path) -> None:
    private_key, public_pem = generate_test_signing_key()
    body = sign_manifest_body(compute_module_hashes(), "1.8.0", private_key)
    body["files"]["main.py"] = "0" * 64
    path = tmp_path / "integrity_manifest.json"
    path.write_text(json.dumps(body), encoding="utf-8")
    set_manifest_path_for_tests(str(path))
    set_verify_pem_for_tests(public_pem)
    verdict = evaluate_signed_manifest(compute_module_hashes(), "1.8.0", None)
    assert verdict["integrity_state"] == "tampered"
    assert verdict["detail"] == "signed_manifest_signature_invalid"


def test_critical_module_changed_after_install_stays_tampered_after_reconcile(
    tmp_path, monkeypatch
) -> None:
    install_matching_signed_manifest(tmp_path, release_label="1.8.0")
    monkeypatch.setattr("core.integrity_anchor._release_label", lambda: "1.8.0")
    cfg = _cfg(tmp_path)
    assert ensure_integrity_anchor(cfg)["integrity_state"] == "validated"
    drifted = compute_module_hashes()
    drifted["core/detector.py"] = "c" * 64
    monkeypatch.setattr("core.integrity_anchor.compute_module_hashes", lambda: drifted)
    reset_integrity_anchor_for_tests()
    assert ensure_integrity_anchor(cfg)["integrity_state"] == "tampered"
    snap = reconcile_integrity_anchor(cfg, "1.8.0")
    assert snap["integrity_state"] == "tampered"
    assert "core/detector.py" in snap["mismatched_files"]


def test_downgrade_is_tampered(tmp_path, monkeypatch) -> None:
    install_matching_signed_manifest(tmp_path, release_label="1.8.0")
    monkeypatch.setattr("core.integrity_anchor._release_label", lambda: "1.8.0")
    cfg = _cfg(tmp_path)
    assert ensure_integrity_anchor(cfg)["integrity_state"] == "validated"
    monkeypatch.setattr("core.integrity_anchor._release_label", lambda: "1.7.4")
    reset_integrity_anchor_for_tests()
    snap = ensure_integrity_anchor(cfg)
    assert snap["integrity_state"] == "tampered"


def test_upgrade_2162_unsigned_published_to_signed_candidate(
    tmp_path, monkeypatch
) -> None:
    """#2162 upgrade smoke: previous published unsigned tree → signed candidate."""
    reset_signed_manifest_pins()
    monkeypatch.setattr("core.integrity_anchor._release_label", lambda: "1.7.4")
    cfg = _cfg(tmp_path)
    assert ensure_integrity_anchor(cfg)["integrity_state"] == "tampered"
    monkeypatch.setattr("core.integrity_anchor._release_label", lambda: "1.8.0")
    install_matching_signed_manifest(tmp_path, release_label="1.8.0")
    reset_integrity_anchor_for_tests()
    snap = ensure_integrity_anchor(cfg)
    assert snap["integrity_state"] == "validated"
    assert snap["trust_level"] == "expected"
