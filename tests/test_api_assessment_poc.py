"""Gated dashboard route: organizational self-assessment POC placeholder (PLAN_MATURITY_*)."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from fastapi.testclient import TestClient

from core.database import LocalDBManager
from core.licensing.guard import reset_license_guard_for_tests


def _csrf_token_from_html(html: str) -> str:
    m = re.search(r'name="csrf_token"\s+value="([^"]+)"', html)
    assert m is not None, "expected csrf_token on assessment GET HTML"
    return m.group(1)


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


def _make_license_token(
    priv: Ed25519PrivateKey,
    *,
    extra: dict | None = None,
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": "assessment-jwt-tier-test",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=7)).timestamp()),
        "dbcid": "cust-test",
        "dbcname": "Tier Test",
        "dbenv": "qa",
        "dbissuer": "pytest",
        "dbkid": "k1",
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, priv, algorithm="EdDSA")


@pytest.fixture
def ed25519_priv() -> Ed25519PrivateKey:
    return Ed25519PrivateKey.generate()


def _setup_routes(tmp_path: Path, api_extra: str = "", licensing_block: str = ""):
    """Point api.routes at a temp config.yaml. Avoid duplicate YAML ``api:`` keys (merge bugs)."""
    out_dir = str(tmp_path).replace("\\", "/")
    config_yaml = f"""targets: []
report:
  output_dir: {out_dir}
api:
  port: 8088
{api_extra}sqlite_path: {out_dir}/audit_results.db
scan:
  max_workers: 1
{licensing_block}"""
    config_path = tmp_path / "config.yaml"
    config_path.write_text(config_yaml, encoding="utf-8")

    import api.routes as routes

    original_config_path = routes._config_path
    original_config = routes._config
    original_engine = routes._audit_engine
    routes._config_path = str(config_path)
    routes._config = None
    routes._audit_engine = None
    client = TestClient(routes.app)
    return routes, client, original_config_path, original_config, original_engine


def _teardown_routes(routes, original_config_path, original_config, original_engine):
    routes._config_path = original_config_path
    routes._config = original_config
    routes._audit_engine = original_engine
    routes._maturity_pack_cache = None


def _setup_enforced_assessment_routes(
    tmp_path: Path,
    ed25519_priv: Ed25519PrivateKey,
    monkeypatch: pytest.MonkeyPatch,
    *,
    jwt_dbtier: str,
    yaml_effective_tier_line: str = "  effective_tier: pro\n",
):
    """
    ``licensing.mode: enforced`` + JWT file with ``dbtier`` claim.

    When ``yaml_effective_tier_line`` is empty, YAML omits ``effective_tier`` (tier from JWT only).
    """
    pem = _pem_public(ed25519_priv)
    monkeypatch.setenv("DATA_BOAR_LICENSE_PUBLIC_KEY_PEM", pem)
    lic = tmp_path / "license.lic"
    lic.write_text(
        _make_license_token(ed25519_priv, extra={"dbtier": jwt_dbtier}),
        encoding="utf-8",
    )
    reset_license_guard_for_tests()
    pack_src = (
        Path(__file__).resolve().parent
        / "fixtures"
        / "maturity_assessment"
        / "sample_pack.yaml"
    )
    pack_dst = tmp_path / "pack.yaml"
    pack_dst.write_text(pack_src.read_text(encoding="utf-8"), encoding="utf-8")
    pack_path = str(pack_dst).replace("\\", "/")
    lic_path = str(lic).replace("\\", "/")
    licensing_block = f"""licensing:
  mode: enforced
  license_path: {lic_path}
{yaml_effective_tier_line}"""
    extra = f"""  maturity_self_assessment_poc_enabled: true
  maturity_assessment_pack_path: {pack_path}
"""
    return _setup_routes(tmp_path, api_extra=extra, licensing_block=licensing_block)


def test_assessment_placeholder_404_when_flag_off(tmp_path):
    routes, client, orig_path, orig_cfg, orig_engine = _setup_routes(tmp_path)
    try:
        r = client.get("/en/assessment")
        assert r.status_code == 404
    finally:
        _teardown_routes(routes, orig_path, orig_cfg, orig_engine)


def test_assessment_placeholder_200_when_flag_on_open_tier(tmp_path):
    routes, client, orig_path, orig_cfg, orig_engine = _setup_routes(
        tmp_path,
        api_extra="  maturity_self_assessment_poc_enabled: true\n",
    )
    try:
        r = client.get("/en/assessment")
        assert r.status_code == 200
        assert "PLAN_MATURITY_SELF_ASSESSMENT_GRC_QUESTIONNAIRE" in r.text
        r2 = client.get("/pt-br/assessment")
        assert r2.status_code == 200
    finally:
        _teardown_routes(routes, orig_path, orig_cfg, orig_engine)


def test_assessment_placeholder_404_when_community_tier_with_flag(tmp_path):
    routes, client, orig_path, orig_cfg, orig_engine = _setup_routes(
        tmp_path,
        api_extra="  maturity_self_assessment_poc_enabled: true\n",
        licensing_block="licensing:\n  effective_tier: community\n",
    )
    try:
        r = client.get("/en/assessment")
        assert r.status_code == 404
    finally:
        _teardown_routes(routes, orig_path, orig_cfg, orig_engine)


def test_assessment_placeholder_200_when_pro_tier_with_flag(tmp_path):
    routes, client, orig_path, orig_cfg, orig_engine = _setup_routes(
        tmp_path,
        api_extra="  maturity_self_assessment_poc_enabled: true\n",
        licensing_block="licensing:\n  effective_tier: pro\n",
    )
    try:
        r = client.get("/en/assessment")
        assert r.status_code == 200
    finally:
        _teardown_routes(routes, orig_path, orig_cfg, orig_engine)


def test_assessment_post_400_without_pack(tmp_path):
    routes, client, orig_path, orig_cfg, orig_engine = _setup_routes(
        tmp_path,
        api_extra="  maturity_self_assessment_poc_enabled: true\n",
        licensing_block="licensing:\n  effective_tier: pro\n",
    )
    try:
        r = client.post(
            "/en/assessment",
            data={
                "assessment_batch_id": "a" * 32,
                "pack_version": "1",
            },
        )
        assert r.status_code == 400
    finally:
        _teardown_routes(routes, orig_path, orig_cfg, orig_engine)


def test_assessment_post_404_when_community_tier(tmp_path):
    routes, client, orig_path, orig_cfg, orig_engine = _setup_routes(
        tmp_path,
        api_extra="  maturity_self_assessment_poc_enabled: true\n",
        licensing_block="licensing:\n  effective_tier: community\n",
    )
    try:
        r = client.post(
            "/en/assessment",
            data={"assessment_batch_id": "b" * 32},
        )
        assert r.status_code == 404
    finally:
        _teardown_routes(routes, orig_path, orig_cfg, orig_engine)


def test_assessment_post_persists_answers_with_integrity_secret(tmp_path, monkeypatch):
    """When DATA_BOAR_MATURITY_INTEGRITY_SECRET is set, rows get HMAC and /status reports integrity."""
    monkeypatch.setenv("DATA_BOAR_MATURITY_INTEGRITY_SECRET", "poc-test-hmac-key")
    pack_src = (
        Path(__file__).resolve().parent
        / "fixtures"
        / "maturity_assessment"
        / "sample_pack.yaml"
    )
    pack_dst = tmp_path / "pack.yaml"
    pack_dst.write_text(pack_src.read_text(encoding="utf-8"), encoding="utf-8")
    pack_path = str(pack_dst).replace("\\", "/")
    extra = f"""  maturity_self_assessment_poc_enabled: true
  maturity_assessment_pack_path: {pack_path}
"""
    routes, client, orig_path, orig_cfg, orig_engine = _setup_routes(
        tmp_path,
        api_extra=extra,
        licensing_block="licensing:\n  effective_tier: pro\n",
    )
    try:
        r = client.get("/en/assessment")
        assert r.status_code == 200
        m = re.search(r'name="assessment_batch_id" value="([^"]+)"', r.text)
        assert m is not None
        bid = m.group(1)
        r2 = client.post(
            "/en/assessment",
            data={
                "assessment_batch_id": bid,
                "pack_version": "1",
                "csrf_token": _csrf_token_from_html(r.text),
                "answer__sample_dpo": "yes",
                "answer__sample_policy": "no",
            },
            follow_redirects=False,
        )
        assert r2.status_code == 303
        loc = r2.headers.get("location") or ""
        assert f"batch={bid}" in loc
        r3 = client.get(loc)
        assert r3.status_code == 200
        assert "2 verified" in r3.text
        assert "Integrity (POC" in r3.text
        assert "75.0" in r3.text
        db = LocalDBManager(str(tmp_path / "audit_results.db"))
        try:
            rows = db.maturity_assessment_rows_for_integrity()
            assert len(rows) == 2
            assert all((row.get("row_hmac") or "").strip() for row in rows)
            st = client.get("/status")
            assert st.status_code == 200
            body = st.json()
            assert "maturity_assessment_integrity" in body
            mi = body["maturity_assessment_integrity"]
            assert mi.get("secret_configured") is True
            assert mi.get("rows_ok") == 2
            assert mi.get("rows_mismatch") == 0
        finally:
            db.dispose()
    finally:
        _teardown_routes(routes, orig_path, orig_cfg, orig_engine)


def test_assessment_post_persists_answers(tmp_path):
    pack_src = (
        Path(__file__).resolve().parent
        / "fixtures"
        / "maturity_assessment"
        / "sample_pack.yaml"
    )
    pack_dst = tmp_path / "pack.yaml"
    pack_dst.write_text(pack_src.read_text(encoding="utf-8"), encoding="utf-8")
    pack_path = str(pack_dst).replace("\\", "/")
    extra = f"""  maturity_self_assessment_poc_enabled: true
  maturity_assessment_pack_path: {pack_path}
"""
    routes, client, orig_path, orig_cfg, orig_engine = _setup_routes(
        tmp_path,
        api_extra=extra,
        licensing_block="licensing:\n  effective_tier: pro\n",
    )
    try:
        r = client.get("/en/assessment")
        assert r.status_code == 200
        m = re.search(r'name="assessment_batch_id" value="([^"]+)"', r.text)
        assert m is not None
        bid = m.group(1)
        r2 = client.post(
            "/en/assessment",
            data={
                "assessment_batch_id": bid,
                "pack_version": "1",
                "csrf_token": _csrf_token_from_html(r.text),
                "answer__sample_dpo": "yes",
                "answer__sample_policy": "no",
            },
            follow_redirects=False,
        )
        assert r2.status_code == 303
        loc = r2.headers.get("location") or ""
        assert "saved=1" in loc
        assert f"batch={bid}" in loc
        r3 = client.get(loc)
        assert r3.status_code == 200
        assert "Recent submissions" in r3.text
        assert "assessment-history" in r3.text
        assert f"assessment?saved=1&amp;batch={bid}" in r3.text
        assert "Submission summary" in r3.text
        assert "Stored 2 answer row" in r3.text
        assert "Rubric score" in r3.text
        assert "75.0" in r3.text
        assert "Download CSV" in r3.text
        ex = client.get(
            f"/en/assessment/export?batch={bid}&format=csv",
        )
        assert ex.status_code == 200
        assert ex.headers.get("content-disposition", "").startswith("attachment")
        assert "sample_dpo" in ex.text
        assert "disclaimer" in ex.text.lower()
        exm = client.get(f"/en/assessment/export?batch={bid}&format=md")
        assert exm.status_code == 200
        assert "# Maturity self-assessment export" in exm.text
        db = LocalDBManager(str(tmp_path / "audit_results.db"))
        try:
            assert db.count_maturity_assessment_answers() == 2
        finally:
            db.dispose()
    finally:
        _teardown_routes(routes, orig_path, orig_cfg, orig_engine)


def test_assessment_export_404_when_batch_has_no_rows(tmp_path):
    routes, client, orig_path, orig_cfg, orig_engine = _setup_routes(
        tmp_path,
        api_extra=(
            "  maturity_self_assessment_poc_enabled: true\n"
            "  maturity_assessment_pack_path: "
            + str(
                Path(__file__).resolve().parent
                / "fixtures"
                / "maturity_assessment"
                / "sample_pack.yaml"
            ).replace("\\", "/")
            + "\n"
        ),
        licensing_block="licensing:\n  effective_tier: pro\n",
    )
    try:
        ghost = "c" * 32
        r = client.get(f"/en/assessment/export?batch={ghost}&format=csv")
        assert r.status_code == 404
    finally:
        _teardown_routes(routes, orig_path, orig_cfg, orig_engine)


def test_assessment_history_section_absent_without_submissions(tmp_path):
    """No empty history card: table is omitted until at least one batch exists in SQLite."""
    pack_src = (
        Path(__file__).resolve().parent
        / "fixtures"
        / "maturity_assessment"
        / "sample_pack.yaml"
    )
    pack_dst = tmp_path / "pack.yaml"
    pack_dst.write_text(pack_src.read_text(encoding="utf-8"), encoding="utf-8")
    pack_path = str(pack_dst).replace("\\", "/")
    extra = f"""  maturity_self_assessment_poc_enabled: true
  maturity_assessment_pack_path: {pack_path}
"""
    routes, client, orig_path, orig_cfg, orig_engine = _setup_routes(
        tmp_path,
        api_extra=extra,
        licensing_block="licensing:\n  effective_tier: pro\n",
    )
    try:
        r = client.get("/en/assessment")
        assert r.status_code == 200
        assert "Recent submissions" not in r.text
        assert "assessment-history" not in r.text
    finally:
        _teardown_routes(routes, orig_path, orig_cfg, orig_engine)


def test_assessment_renders_yaml_pack_when_configured(tmp_path):
    pack_src = (
        Path(__file__).resolve().parent
        / "fixtures"
        / "maturity_assessment"
        / "sample_pack.yaml"
    )
    pack_dst = tmp_path / "pack.yaml"
    pack_dst.write_text(pack_src.read_text(encoding="utf-8"), encoding="utf-8")
    pack_path = str(pack_dst).replace("\\", "/")
    extra = f"""  maturity_self_assessment_poc_enabled: true
  maturity_assessment_pack_path: {pack_path}
"""
    routes, client, orig_path, orig_cfg, orig_engine = _setup_routes(
        tmp_path, api_extra=extra
    )
    try:
        r = client.get("/en/assessment")
        assert r.status_code == 200
        assert "Governance (sample)" in r.text
        assert "privacy governance" in r.text.lower()
    finally:
        _teardown_routes(routes, orig_path, orig_cfg, orig_engine)


def test_assessment_enforced_jwt_dbtier_community_overrides_yaml_pro_returns_404(
    tmp_path, ed25519_priv, monkeypatch
):
    """JWT ``dbtier: community`` wins over ``licensing.effective_tier: pro``; POC needs Pro+ -> 404."""
    routes, client, orig_path, orig_cfg, orig_engine = (
        _setup_enforced_assessment_routes(
            tmp_path,
            ed25519_priv,
            monkeypatch,
            jwt_dbtier="community",
            yaml_effective_tier_line="  effective_tier: pro\n",
        )
    )
    try:
        r = client.get("/en/assessment")
        assert r.status_code == 404
        r2 = client.post(
            "/en/assessment",
            data={"assessment_batch_id": "a" * 32, "pack_version": "1"},
        )
        assert r2.status_code == 404
        r3 = client.get("/en/assessment/export?batch=" + "b" * 32 + "&format=csv")
        assert r3.status_code == 404
    finally:
        _teardown_routes(routes, orig_path, orig_cfg, orig_engine)
        reset_license_guard_for_tests()


def test_assessment_enforced_jwt_dbtier_pro_returns_200(
    tmp_path, ed25519_priv, monkeypatch
):
    routes, client, orig_path, orig_cfg, orig_engine = (
        _setup_enforced_assessment_routes(
            tmp_path,
            ed25519_priv,
            monkeypatch,
            jwt_dbtier="pro",
            yaml_effective_tier_line="",
        )
    )
    try:
        r = client.get("/en/assessment")
        assert r.status_code == 200
        assert "PLAN_MATURITY_SELF_ASSESSMENT_GRC_QUESTIONNAIRE" in r.text
    finally:
        _teardown_routes(routes, orig_path, orig_cfg, orig_engine)
        reset_license_guard_for_tests()
