"""
tier_features.py
================
Feature-to-tier mapping for Data Boar.

STRATEGY (internal — not yet public):
  Community  — open source, self-hosted, unlimited scans, core detectors, XLSX/HTML reports
  Pro        — PDF reports, advanced connectors, scheduled scans, API key management, support SLA
  Enterprise — custom branding, digital signatures, multi-tenant, SSO, priority support

CURRENT STATUS: stub — enforcement not yet implemented.
All features default to OPEN (no restriction) until licensing contracts are finalized.
Do NOT expose tier names or pricing publicly until branding decision is made.

When adding a NEW FEATURE, add a row here FIRST, then implement the gate in the code.
Convention: check `is_feature_available("feature_name")` before activating feature.
"""

from __future__ import annotations

from enum import Enum


class Tier(str, Enum):
    COMMUNITY = "community"
    PRO = "pro"
    ENTERPRISE = "enterprise"
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
    "ocr_images": Tier.COMMUNITY,
    "synthetic_data_testing": Tier.COMMUNITY,
    # Pro features (PDF report, advanced connectors, scheduling)
    "report_pdf": Tier.PRO,  # see PLAN_PDF_GRC_REPORT.md
    "report_pdf_custom_branding": Tier.ENTERPRISE,
    "connector_snowflake": Tier.PRO,
    "connector_sap": Tier.PRO,
    "connector_s3_object_storage": Tier.PRO,
    "connector_azure_blob": Tier.PRO,
    "connector_gcs": Tier.PRO,
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
}

# ---------------------------------------------------------------------------
# Tier ordering (for >= comparisons)
# ---------------------------------------------------------------------------
_TIER_ORDER = {
    Tier.COMMUNITY: 0,
    Tier.PRO: 1,
    Tier.ENTERPRISE: 2,
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
