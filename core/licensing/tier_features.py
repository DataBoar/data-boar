"""
tier_features.py
================
Feature-to-tier mapping for Data Boar.

STRATEGY (internal — not yet public):
  Community  — open source, self-hosted, core detectors, XLSX/HTML reports
  Std        — paid entry (Boar-Std; not Oracle Database Standard Edition): commercial right, support
  Pro        — PDF reports, corporate connectors, scheduled scans, fixed RBAC, support SLA
  Pro+       — custom RBAC, SARIF/SIEM push, RoPA export, deploy pack (claim-driven workers)
  Enterprise — plugin/partner arch, CMDB, sink, white-label, SSO, per-resource RBAC
  Partner    — channel / multi-client delivery (custom agreement; capability ≥ Pro+)

CONNECTOR BOUNDARY (operator decision, ratified 2026-06-11 — #843):
  Open-core stays useful: filesystem, self-hosted SQL/NoSQL (sqlite/postgres/
  mysql/mongo/redis), compressed files, and the generic REST connector are
  Community. The gate bites only on MANAGED CORPORATE infrastructure:
  PowerBI, SharePoint, Dataverse, WebDAV, SMB/CIFS, NFS, MSSQL, Oracle (plus
  the cloud connectors already mapped: Snowflake, SAP, S3, Azure Blob, GCS)
  are Pro. Gating only bites in licensing.mode: enforced — Tier.OPEN
  (enforcement off) stays free for dev and lab.

Do NOT expose tier names or pricing publicly until branding decision is made.

When adding a NEW FEATURE, add a row here FIRST, then implement the gate in the code.
Convention: check `is_feature_available("feature_name")` before activating feature.
"""

from __future__ import annotations

from enum import Enum


class Tier(str, Enum):
    COMMUNITY = "community"
    STD = "std"  # Boar-Std product tier — not Oracle DB "Standard Edition"
    PRO = "pro"
    PRO_PLUS = "pro_plus"
    ENTERPRISE = "enterprise"
    PARTNER = "partner"
    OPEN = "open"  # enforcement off (dev / unlicensed)


# ---------------------------------------------------------------------------
# Feature registry
# Feature name -> minimum tier required
# ---------------------------------------------------------------------------
FEATURE_TIER_MAP: dict[str, Tier] = {
    # Core scanning — always available
    "scan_filesystem": Tier.COMMUNITY,
    "scan_database_sql": Tier.COMMUNITY,
    "scan_database_nosql": Tier.COMMUNITY,
    "detector_cpf": Tier.COMMUNITY,
    "detector_rg": Tier.COMMUNITY,
    "detector_email": Tier.COMMUNITY,
    "detector_phone": Tier.COMMUNITY,
    "detector_name_heuristic": Tier.COMMUNITY,
    "detector_cnpj": Tier.COMMUNITY,
    "detector_address": Tier.COMMUNITY,
    "report_xlsx": Tier.COMMUNITY,
    "report_html": Tier.COMMUNITY,
    "api_rest": Tier.COMMUNITY,
    "dashboard_web": Tier.COMMUNITY,
    "docker_deploy": Tier.COMMUNITY,
    "ansible_deploy": Tier.COMMUNITY,
    "compressed_files": Tier.COMMUNITY,
    "content_type_detection": Tier.COMMUNITY,
    "synthetic_data_testing": Tier.COMMUNITY,
    # Generic REST stays open-core (#843) — explicit entry so the registry
    # gate records an allow decision instead of falling through silently.
    "connector_rest": Tier.COMMUNITY,
    # #854: explicit per-connector entries for EVERY registered connector.
    # The registry gate now fails CLOSED on a connector type without an
    # explicit tier decision — absence here means blocked (except Tier.OPEN),
    # never silently community.
    "connector_api": Tier.COMMUNITY,  # generic API/REST family (alias of rest)
    "connector_filesystem": Tier.COMMUNITY,
    "connector_mongodb": Tier.COMMUNITY,  # self-hosted NoSQL (open-core)
    "connector_redis": Tier.COMMUNITY,  # self-hosted NoSQL (open-core)
    "connector_postgresql": Tier.COMMUNITY,  # self-hosted SQL (open-core)
    "connector_mysql": Tier.COMMUNITY,
    "connector_mariadb": Tier.COMMUNITY,
    "connector_sqlite": Tier.COMMUNITY,
    # Pro features (PDF report, advanced connectors, scheduling)
    "ocr_images": Tier.PRO,
    "report_pdf": Tier.PRO,  # see PLAN_PDF_GRC_REPORT.md
    "report_pdf_custom_branding": Tier.ENTERPRISE,
    "compliance_grade_report": Tier.PRO,  # DPO A+→F score — see #697
    "connector_snowflake": Tier.PRO,
    "connector_sap": Tier.PRO,
    "connector_s3_object_storage": Tier.PRO,
    "connector_azure_blob": Tier.PRO,
    "connector_gcs": Tier.PRO,
    # Managed corporate infrastructure connectors (#843 boundary)
    "connector_powerbi": Tier.PRO,
    "connector_sharepoint": Tier.PRO,
    "connector_dataverse": Tier.PRO,
    "connector_webdav": Tier.PRO,
    "connector_smb": Tier.PRO,
    "connector_cifs": Tier.PRO,
    "connector_nfs": Tier.PRO,
    "connector_mssql": Tier.PRO,
    "connector_oracle": Tier.PRO,
    "scheduled_scans": Tier.PRO,
    # Aliases / upcoming gates (see GitHub #558, #544, #552, #551)
    "scan_scheduler_pro": Tier.PRO,
    "scan_scheduler_ui_enterprise": Tier.ENTERPRISE,
    "governance_lens_pro": Tier.PRO,
    "governance_lens_enterprise": Tier.ENTERPRISE,
    "findings_sink_sql": Tier.PRO,
    "scan_max_workers_pro": Tier.PRO,
    "scan_max_workers_enterprise": Tier.ENTERPRISE,
    "api_key_management_ui": Tier.PRO,
    "dashboard_rbac": Tier.PRO,
    # GRC-style org maturity questionnaire UI (POC); not open core — see PLAN_MATURITY_SELF_ASSESSMENT_GRC_QUESTIONNAIRE.md
    "maturity_self_assessment_poc": Tier.PRO,
    "notifications_email": Tier.PRO,
    "notifications_slack": Tier.PRO,
    "sbom_export": Tier.PRO,
    "build_integrity_verify": Tier.PRO,
    # Enterprise features
    "multi_tenant": Tier.ENTERPRISE,
    "sso_saml": Tier.ENTERPRISE,
    "pdf_digital_signature": Tier.ENTERPRISE,
    "scheduled_pdf_email": Tier.ENTERPRISE,
    "historical_comparison": Tier.ENTERPRISE,
    "audit_log_export": Tier.ENTERPRISE,
    "custom_detectors": Tier.ENTERPRISE,
    "vcs_connector": Tier.ENTERPRISE,  # files version control (VCS) scanner — see #677
    "plugin_partner_interface": Tier.ENTERPRISE,  # L1/L2/L3 plugin arch — see #695
    "partner_provider_driver": Tier.ENTERPRISE,  # stealthization via partner provider — see #696
}

# ---------------------------------------------------------------------------
# Tier ordering (for >= comparisons)
# ---------------------------------------------------------------------------
_TIER_ORDER = {
    Tier.COMMUNITY: 0,
    Tier.STD: 1,
    Tier.PRO: 2,
    Tier.PRO_PLUS: 3,
    Tier.ENTERPRISE: 4,
    Tier.PARTNER: 5,
    Tier.OPEN: 99,  # OPEN bypasses all checks
}


def is_feature_available(feature: str, current_tier: Tier = Tier.OPEN) -> bool:
    """
    Returns True if the feature is available for the given tier.
    In OPEN mode (default), all features are available.

    Usage:
        from core.licensing.tier_features import is_feature_available, Tier
        if is_feature_available("report_pdf", runtime_tier):
            generate_pdf_report(...)
        else:
            raise FeatureNotAvailableError("report_pdf", Tier.PRO)
    """
    if current_tier == Tier.OPEN:
        return True
    required = FEATURE_TIER_MAP.get(feature, Tier.COMMUNITY)
    return _TIER_ORDER[current_tier] >= _TIER_ORDER[required]


def get_required_tier(feature: str) -> Tier:
    """Return the minimum tier required for a feature."""
    return FEATURE_TIER_MAP.get(feature, Tier.COMMUNITY)


def features_for_tier(tier: Tier) -> list[str]:
    """Return all features available for a given tier (cumulative)."""
    return [
        name
        for name, required in FEATURE_TIER_MAP.items()
        if _TIER_ORDER.get(required, 0) <= _TIER_ORDER.get(tier, 0)
    ]
