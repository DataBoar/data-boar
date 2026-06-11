"""
Connector registry: map target type (postgresql, mysql, filesystem, etc.) to connector class.
Each connector implements: connect(), discover(), sample() where applicable, close(),
and reports findings via a callback (save_finding/save_failure) passed by the engine.
"""

from typing import Any, Type

# Registry: type string -> (connector_class, requires_config_keys)
_REGISTRY: dict[str, tuple[Type[Any], list[str]]] = {}


def register(
    connector_type: str,
    connector_class: Type[Any],
    required_keys: list[str] | None = None,
):
    """Register a connector class for a given type (e.g. postgresql, mysql, filesystem)."""
    _REGISTRY[connector_type] = (connector_class, required_keys or [])


def get_connector(connector_type: str) -> tuple[Type[Any], list[str]]:
    """Return (connector_class, required_config_keys) for type. Raises KeyError if unknown."""
    return _REGISTRY[connector_type]


def list_connector_types() -> list[str]:
    """Return registered connector types."""
    return list(_REGISTRY.keys())


def _try_get_connector(connector_type: str) -> tuple[Type[Any], list[str]] | None:
    """Return (connector_class, required_keys) for type, or None if not registered."""
    try:
        return get_connector(connector_type)
    except KeyError:
        return None


def _resolve_database_connector(
    target: dict[str, Any],
) -> tuple[Type[Any], list[str]] | None:
    """Resolve SQL connector from target with type='database' and driver."""
    driver = target.get("driver", "")
    engine = driver.split("+")[0].lower() if driver else ""
    if engine in _REGISTRY:
        return get_connector(engine)
    if driver and driver in _REGISTRY:
        return get_connector(driver)
    for alias in ("postgresql", "mysql", "sqlite", "mssql", "oracle"):
        if alias in driver or driver in (
            alias,
            f"{alias}+psycopg2",
            f"{alias}+pymysql",
        ):
            if alias in _REGISTRY:
                return get_connector(alias)
    return None


# Connector tier boundary (#843, operator-ratified 2026-06-11):
# - Open-core (Community): filesystem, self-hosted SQL/NoSQL (sqlite/postgres/
#   mysql/mongo/redis), compressed files, generic REST. Filesystem and
#   self-hosted DB engines are intentionally ABSENT from this map — never gated.
# - Pro: managed corporate infrastructure (PowerBI, SharePoint, Dataverse,
#   WebDAV, SMB/CIFS, NFS, MSSQL, Oracle) + cloud connectors.
# The gate only bites in licensing.mode: enforced; Tier.OPEN stays free.
_CONNECTOR_TIER_FEATURES: dict[str, str] = {
    # Community baseline (explicit so the gate records an allow decision)
    "api": "connector_rest",
    "rest": "connector_rest",
    # Cloud connectors (Pro)
    "snowflake": "connector_snowflake",
    "s3": "connector_s3_object_storage",
    "azure_blob": "connector_azure_blob",
    "gcs": "connector_gcs",
    # Managed corporate infrastructure (Pro)
    "powerbi": "connector_powerbi",
    "sharepoint": "connector_sharepoint",
    "dataverse": "connector_dataverse",
    "powerapps": "connector_dataverse",  # same connector family as dataverse
    "webdav": "connector_webdav",
    "smb": "connector_smb",
    "cifs": "connector_cifs",
    "nfs": "connector_nfs",
    # Corporate DB engines via type=database + driver (Pro)
    "mssql": "connector_mssql",
    "oracle": "connector_oracle",
}


def tier_feature_for_target(target: dict[str, Any]) -> str | None:
    """Return the tier feature name for a target, or None when never gated.

    None means open-core by design (filesystem, self-hosted SQL/NoSQL) —
    see the boundary comment on ``_CONNECTOR_TIER_FEATURES``.
    """
    t = (target.get("type") or "").strip().lower()
    if t in _CONNECTOR_TIER_FEATURES:
        return _CONNECTOR_TIER_FEATURES[t]
    if t == "database":
        driver = (target.get("driver") or "").split("+")[0].strip().lower()
        return _CONNECTOR_TIER_FEATURES.get(driver)
    return None


def require_connector_allowed(cfg: dict[str, Any], target: dict[str, Any]) -> None:
    """Tier gate at connector instantiation (#843).

    Raises :class:`core.licensing.errors.FeatureTierBlockedError` with an
    actionable message when the runtime tier denies this connector in
    enforced mode. Free in ``Tier.OPEN`` (enforcement off) and for open-core
    connectors (no map entry).
    """
    feature = tier_feature_for_target(target)
    if not feature:
        return
    from core.licensing.errors import FeatureTierBlockedError
    from core.licensing.feature_gate import require_feature

    try:
        require_feature(cfg, feature)
    except FeatureTierBlockedError as exc:
        ttype = (target.get("type") or "?").strip().lower()
        raise FeatureTierBlockedError(
            exc.feature,
            (
                f"connector '{ttype}' requires {exc.required_tier} tier "
                f"(licensing.mode=enforced; current tier: {exc.current_tier}). "
                f"{exc.reason}"
            ),
            required_tier=exc.required_tier,
            current_tier=exc.current_tier,
        ) from exc


def connector_for_target(target: dict[str, Any]) -> tuple[Type[Any], list[str]] | None:
    """
    Resolve connector from target config. Target may have type='database' with driver='postgresql+psycopg2'.
    Returns (connector_class, required_keys) or None if not supported.
    """
    t = target.get("type", "")
    if t == "filesystem":
        return get_connector("filesystem")
    if t in ("api", "rest"):
        return _try_get_connector("api")
    if t in ("sharepoint", "webdav", "smb", "cifs", "nfs"):
        return _try_get_connector(t)
    if t in ("powerbi", "dataverse", "powerapps"):
        return _try_get_connector(t)
    if t == "database":
        return _resolve_database_connector(target)
    return None
