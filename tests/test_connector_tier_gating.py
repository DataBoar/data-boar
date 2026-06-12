"""
Connector tier gating at the registry (#843) + FEATURE_TIER_MAP completion (#705).

Boundary (operator-ratified): open-core keeps filesystem, self-hosted SQL/
NoSQL, compressed files, and generic REST; managed corporate infrastructure
(PowerBI, SharePoint, Dataverse, WebDAV, SMB/CIFS, NFS, MSSQL, Oracle) is
Pro. The gate bites only in enforced mode (or lab tier simulation) — never
in ``Tier.OPEN``.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from core.connector_registry import (
    require_connector_allowed,
    tier_feature_for_target,
)
from core.licensing.errors import FeatureTierBlockedError
from core.licensing.guard import reset_license_guard_for_tests
from core.licensing.tier_features import FEATURE_TIER_MAP, Tier


@pytest.fixture(autouse=True)
def _clean_guard():
    reset_license_guard_for_tests()
    yield
    reset_license_guard_for_tests()
    os.environ.pop("DATA_BOAR_LICENSE_PUBLIC_KEY_PEM", None)


# --- FEATURE_TIER_MAP completion (#705 + #843) ----------------------------


@pytest.mark.parametrize(
    ("feature", "tier"),
    [
        # #843 — connectors
        ("connector_rest", Tier.COMMUNITY),
        ("connector_powerbi", Tier.PRO),
        ("connector_sharepoint", Tier.PRO),
        ("connector_dataverse", Tier.PRO),
        ("connector_webdav", Tier.PRO),
        ("connector_smb", Tier.PRO),
        ("connector_cifs", Tier.PRO),
        ("connector_nfs", Tier.PRO),
        ("connector_mssql", Tier.PRO),
        ("connector_oracle", Tier.PRO),
        # #705 — features with open PLANs/issues
        ("compliance_grade_report", Tier.PRO),
        ("vcs_connector", Tier.ENTERPRISE),
        ("plugin_partner_interface", Tier.ENTERPRISE),
        ("partner_provider_driver", Tier.ENTERPRISE),
    ],
)
def test_feature_tier_map_entries(feature, tier):
    assert FEATURE_TIER_MAP.get(feature) == tier


# --- tier_feature_for_target resolution -----------------------------------


@pytest.mark.parametrize(
    ("target", "expected"),
    [
        ({"type": "powerbi"}, "connector_powerbi"),
        ({"type": "sharepoint"}, "connector_sharepoint"),
        ({"type": "dataverse"}, "connector_dataverse"),
        ({"type": "powerapps"}, "connector_dataverse"),
        ({"type": "webdav"}, "connector_webdav"),
        ({"type": "smb"}, "connector_smb"),
        ({"type": "cifs"}, "connector_cifs"),
        ({"type": "nfs"}, "connector_nfs"),
        ({"type": "api"}, "connector_api"),
        ({"type": "rest"}, "connector_rest"),
        ({"type": "database", "driver": "mssql+pyodbc"}, "connector_mssql"),
        ({"type": "database", "driver": "oracle+oracledb"}, "connector_oracle"),
        # open-core — explicit Community entries since #854 (fail-closed map)
        ({"type": "filesystem"}, "connector_filesystem"),
        ({"type": "database", "driver": "postgresql+psycopg2"}, "connector_postgresql"),
        ({"type": "database", "driver": "sqlite"}, "connector_sqlite"),
        ({"type": "database", "driver": "mysql+pymysql"}, "connector_mysql"),
        ({"type": "database", "driver": "mongodb"}, "connector_mongodb"),
        ({"type": "redis"}, "connector_redis"),
        # unknown — no tier decision: gate fails closed outside Tier.OPEN
        ({"type": "carrier_pigeon"}, None),
        ({"type": "database", "driver": "duckdb"}, None),
    ],
)
def test_tier_feature_for_target(target, expected):
    assert tier_feature_for_target(target) == expected


@pytest.mark.parametrize(
    ("feature", "tier"),
    [
        ("connector_api", Tier.COMMUNITY),
        ("connector_filesystem", Tier.COMMUNITY),
        ("connector_mongodb", Tier.COMMUNITY),
        ("connector_redis", Tier.COMMUNITY),
        ("connector_postgresql", Tier.COMMUNITY),
        ("connector_mysql", Tier.COMMUNITY),
        ("connector_mariadb", Tier.COMMUNITY),
        ("connector_sqlite", Tier.COMMUNITY),
    ],
)
def test_feature_tier_map_explicit_open_core_entries(feature, tier):
    """#854: every registered connector has an explicit map entry."""
    assert FEATURE_TIER_MAP.get(feature) == tier


# --- gate behaviour (lab simulation: mode open + effective_tier) -----------


def _cfg(tier: str | None) -> dict:
    lc: dict = {"mode": "open"}
    if tier:
        lc["effective_tier"] = tier
    return {"licensing": lc}


def test_community_blocked_on_pro_connector():
    with pytest.raises(FeatureTierBlockedError) as exc_info:
        require_connector_allowed(_cfg("community"), {"type": "powerbi"})
    msg = str(exc_info.value)
    assert "connector 'powerbi'" in msg
    assert "pro" in msg.lower()


def test_community_allowed_on_rest_and_open_core():
    require_connector_allowed(_cfg("community"), {"type": "rest"})
    require_connector_allowed(_cfg("community"), {"type": "filesystem"})
    require_connector_allowed(
        _cfg("community"), {"type": "database", "driver": "postgresql+psycopg2"}
    )
    require_connector_allowed(
        _cfg("community"), {"type": "database", "driver": "mongodb"}
    )
    require_connector_allowed(_cfg("community"), {"type": "redis"})


# --- #854: unknown connector type fails CLOSED ------------------------------


def test_unknown_connector_blocked_at_community():
    """#854 anti-leak: no FEATURE_TIER_MAP entry → blocked, not community."""
    with pytest.raises(FeatureTierBlockedError) as exc_info:
        require_connector_allowed(_cfg("community"), {"type": "carrier_pigeon"})
    msg = str(exc_info.value)
    assert "fail-closed" in msg
    assert "carrier_pigeon" in msg


def test_unknown_database_driver_blocked_at_pro():
    """#854: unknown driver under type=database also fails closed."""
    with pytest.raises(FeatureTierBlockedError):
        require_connector_allowed(_cfg("pro"), {"type": "database", "driver": "duckdb"})


def test_unknown_connector_free_in_open_tier():
    """Tier.OPEN (enforcement off) never gates — including unknown types."""
    require_connector_allowed(_cfg(None), {"type": "carrier_pigeon"})


def test_pro_allowed_on_corporate_connectors():
    for ttype in ("powerbi", "sharepoint", "webdav", "smb", "nfs"):
        reset_license_guard_for_tests()
        require_connector_allowed(_cfg("pro"), {"type": ttype})


def test_open_tier_free_for_everything():
    """Tier.OPEN (enforcement off, no simulation) never gates connectors."""
    require_connector_allowed(_cfg(None), {"type": "powerbi"})
    require_connector_allowed(
        _cfg(None), {"type": "database", "driver": "oracle+oracledb"}
    )


# --- enforced mode with signed JWT (end-to-end) ----------------------------


def _signed_license(tmp_path, dbtier: str) -> dict:
    priv = Ed25519PrivateKey.generate()
    pub_pem = (
        priv.public_key()
        .public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode("ascii")
    )
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "sub": "lic-gating",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(days=1)).timestamp()),
            "dbtier": dbtier,
        },
        priv,
        algorithm="EdDSA",
    )
    lic = tmp_path / "t.lic"
    lic.write_text(token, encoding="utf-8")
    os.environ["DATA_BOAR_LICENSE_PUBLIC_KEY_PEM"] = pub_pem
    return {"licensing": {"mode": "enforced", "license_path": str(lic)}}


def test_enforced_community_license_blocks_pro_connector(tmp_path):
    cfg = _signed_license(tmp_path, "community")
    with pytest.raises(FeatureTierBlockedError):
        require_connector_allowed(cfg, {"type": "sharepoint"})


def test_enforced_pro_license_allows_pro_connector(tmp_path):
    cfg = _signed_license(tmp_path, "pro")
    require_connector_allowed(cfg, {"type": "sharepoint"})


def test_enforced_unknown_connector_blocked_even_for_enterprise(tmp_path):
    """#854: fail-closed has no tier escape — unmapped means blocked."""
    cfg = _signed_license(tmp_path, "enterprise")
    with pytest.raises(FeatureTierBlockedError) as exc_info:
        require_connector_allowed(cfg, {"type": "carrier_pigeon"})
    assert "fail-closed" in str(exc_info.value)


# --- engine integration: blocked connector -> scan_failures row ------------


def test_engine_records_tier_blocked_failure(tmp_path, monkeypatch):
    from core.engine import AuditEngine

    cfg = {
        "licensing": {"mode": "open", "effective_tier": "community"},
        "sqlite_path": str(tmp_path / "audit.db"),
        "targets": [],
    }
    engine = AuditEngine(cfg, db_path=str(tmp_path / "audit.db"))
    failures: list[tuple[str, str, str]] = []
    monkeypatch.setattr(
        engine.db_manager,
        "save_failure",
        lambda name, step, err, **kw: failures.append((name, step, err)),
    )
    engine._run_target({"type": "powerbi", "name": "bi-corp"})
    assert failures, "blocked connector must record a scan_failures row"
    name, step, err = failures[0]
    assert name == "bi-corp"
    assert step == "tier_blocked"
    assert "connector 'powerbi'" in err
