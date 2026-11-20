"""Registry, engine and tier of the ``object_storage`` reader (epic #2306, task 2306.2).

Source: ``docs/desenho/2306.md``, section 4 (revision 4: tier by driver name, DEC-15 and
DEC-16) and section 2a. Cases ``D2306-22``, ``D2306-23``, ``D2306-79`` and ``D2306-80``.

The tier gate uses the lab simulation of ``tests/test_connector_tier_gating.py``
(``licensing.mode: open`` plus ``effective_tier``); the signed-licence path is A2306-17.
"""

from __future__ import annotations

import importlib
from collections.abc import Iterator
from typing import Any

import pytest

from connectors import object_storage_driver
from core.licensing.errors import FeatureTierBlockedError
from core.licensing.guard import reset_license_guard_for_tests
from core.licensing.tier_features import FEATURE_TIER_MAP, Tier
from tests.object_storage_dev_harness import MINIO_ENDPOINT, connector_module

DRIVER_TIER_KEYS = {
    "s3": "connector_s3_object_storage",
    "s3_compatible": "connector_s3_compatible",
}


@pytest.fixture(autouse=True)
def _clean_guard() -> Iterator[None]:
    reset_license_guard_for_tests()
    yield
    reset_license_guard_for_tests()


def _lab(tier: str | None) -> dict[str, Any]:
    lc: dict[str, Any] = {"mode": "open"}
    if tier:
        lc["effective_tier"] = tier
    return {"licensing": lc}


def _gate(cfg: dict[str, Any], target: dict[str, Any]) -> Exception | None:
    from core.connector_registry import require_connector_allowed

    reset_license_guard_for_tests()
    try:
        require_connector_allowed(cfg, target)
    except FeatureTierBlockedError as exc:
        return exc
    return None


def test_D2306_22_tier_por_driver_enterprise_e_falha_fechada() -> None:
    """D2306-22: s3 -> connector_s3_object_storage, s3_compatible -> connector_s3_compatible,
    both ENTERPRISE; no driver / unknown -> None; azure_blob stays PRO; the old key
    connector_object_storage does not exist; Pro is blocked, Enterprise and Tier.OPEN pass."""
    from core.connector_registry import tier_feature_for_target

    for driver, feature in DRIVER_TIER_KEYS.items():
        assert (
            tier_feature_for_target({"type": "object_storage", "driver": driver})
            == feature
        ), driver
        assert FEATURE_TIER_MAP.get(feature) == Tier.ENTERPRISE, feature
    assert tier_feature_for_target({"type": "object_storage"}) is None
    assert tier_feature_for_target({"type": "object_storage", "driver": "ftp"}) is None
    assert (
        tier_feature_for_target({"type": "object_storage", "driver": "azure_blob"})
        == "connector_azure_blob"
    )
    assert FEATURE_TIER_MAP.get("connector_azure_blob") == Tier.PRO
    assert "connector_object_storage" not in FEATURE_TIER_MAP
    # Normalised driver name (lower case, no surrounding spaces).
    assert (
        tier_feature_for_target({"type": "object_storage", "driver": " S3 "})
        == "connector_s3_object_storage"
    )

    for driver in DRIVER_TIER_KEYS:
        target = {"type": "object_storage", "driver": driver, "name": "b"}
        assert _gate(_lab("enterprise"), target) is None, driver
        assert _gate(_lab(None), target) is None, driver
        assert isinstance(_gate(_lab("pro"), target), FeatureTierBlockedError), driver
    # Unknown driver: fail closed outside Tier.OPEN, even for Enterprise.
    unknown = {"type": "object_storage", "driver": "ftp", "name": "b"}
    assert isinstance(_gate(_lab("enterprise"), unknown), FeatureTierBlockedError)
    assert _gate(_lab(None), unknown) is None


def test_D2306_23_registro_resolve_o_conector_nos_dois_drivers() -> None:
    """D2306-23 (part 1): connector_for_target returns ObjectStorageConnector for s3 and
    s3_compatible, with the generic required keys (revision 6, R6-8)."""
    importlib.import_module("core.engine")  # the engine imports the connector modules
    from core.connector_registry import connector_for_target

    for driver in DRIVER_TIER_KEYS:
        resolved = connector_for_target({"type": "object_storage", "driver": driver})
        assert resolved is not None, driver
        assert resolved[0] is connector_module().ObjectStorageConnector, driver
        assert resolved[1] == ["name", "driver"], driver


def test_D2306_23_engine_passa_os_parametros_de_arquivo(monkeypatch, tmp_path) -> None:
    """D2306-23 (part 2): the engine instantiates the connector with the file parameters and
    without ``detection_config`` (the file-connector branch of ``_run_target_inner``)."""
    engine_mod = importlib.import_module("core.engine")
    from core import connector_registry as reg

    seen: dict[str, Any] = {}

    class Spy:
        def __init__(self, target: Any, scanner: Any, db: Any, **kw: Any) -> None:
            seen.update(kw)

        def run(self) -> None:
            seen["ran"] = True

    monkeypatch.setitem(reg._REGISTRY, "object_storage", (Spy, ["name", "driver"]))
    cfg = {
        "licensing": {"mode": "open"},
        "sqlite_path": str(tmp_path / "audit.db"),
        "targets": [],
    }
    engine = engine_mod.AuditEngine(cfg, db_path=str(tmp_path / "audit.db"))
    try:
        engine._run_target(
            {"type": "object_storage", "driver": "s3", "name": "x", "bucket": "b"}
        )
    finally:
        engine.db_manager.dispose()
    assert seen.get("ran") is True, seen
    assert set(seen) - {"ran"} == {
        "extensions",
        "scan_sqlite_as_db",
        "sample_limit",
        "file_sample_max_chars",
        "file_passwords",
    }


class _NoUrlTarget(dict):
    """A target that fails the test if the tier lookup reads any host or URL key."""

    _FORBIDDEN = frozenset({"endpoint_url", "host", "url", "base_url", "endpoint"})

    def __getitem__(self, key: Any) -> Any:
        assert key not in self._FORBIDDEN, key
        return super().__getitem__(key)

    def get(self, key: Any, default: Any = None) -> Any:
        assert key not in self._FORBIDDEN, key
        return super().get(key, default)


def test_D2306_79_tier_nao_depende_da_url() -> None:
    """D2306-79: the same s3_compatible target pointing at a lab host or at AWS gives
    connector_s3_compatible; an s3 target always gives connector_s3_object_storage. The
    lookup never reads endpoint_url nor any host key (DEC-15)."""
    from core.connector_registry import tier_feature_for_target

    for endpoint in (MINIO_ENDPOINT, "https://s3.sa-east-1.amazonaws.com"):
        target = _NoUrlTarget(
            type="object_storage", driver="s3_compatible", endpoint_url=endpoint
        )
        assert tier_feature_for_target(target) == "connector_s3_compatible", endpoint
    for extra in ({}, {"endpoint_url": MINIO_ENDPOINT}, {"host": "minio.lab.example"}):
        target = _NoUrlTarget(type="object_storage", driver="s3", **extra)
        assert tier_feature_for_target(target) == "connector_s3_object_storage", extra


def test_D2306_80_todo_driver_implementado_tem_tier() -> None:
    """D2306-80: every driver of the registry that has an implemented connector (s3,
    s3_compatible) has a key in _CONNECTOR_TIER_FEATURES and a value in FEATURE_TIER_MAP;
    the claims check keeps passing with the alias object_storage -> s3_object_storage."""
    from core.connector_registry import _CONNECTOR_TIER_FEATURES
    from tests.test_claims_consistency import connectors_without_tier

    implemented = sorted(
        n
        for n in object_storage_driver._REGISTRY
        if n not in object_storage_driver.NOT_AVAILABLE_YET
    )
    assert implemented == ["s3", "s3_compatible"]
    for name in implemented:
        assert name in _CONNECTOR_TIER_FEATURES, name
        assert _CONNECTOR_TIER_FEATURES[name] == DRIVER_TIER_KEYS[name], name
        assert _CONNECTOR_TIER_FEATURES[name] in FEATURE_TIER_MAP, name
    assert connectors_without_tier() == []
    # The connector type itself is registered (the claims check sees it).
    importlib.import_module("core.engine")
    from core.connector_registry import list_connector_types

    assert "object_storage" in list_connector_types()
