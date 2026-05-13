"""
One-shot script: add ADR-0050 metadata header to PLAN_*.md files that lack it.

Skips files that already have all four fields: Status, Date, Authors, Priority.
Uses git log for creation date. Reads existing **Status:** if present.
Maps priorities from PLANS_TODO H-tags; defaults to H3 when not found.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PLANS_DIR = REPO_ROOT / "docs" / "plans"
AUTHORS = "Fabio Leitao"

# Known depends-on for specific plans (explicit, not auto-detected)
KNOWN_DEPS: dict[str, str] = {
    "PLAN_SCAN_RUN_MANIFEST_AND_EXECUTION_SUMMARY.md": "ADR-0037, ADR-0048, ADR-0049",
    "PLAN_SQL_SAMPLING_SRE_AND_AUDIT_EVIDENCE.md": "ADR-0043",
    "PLAN_BANDIT_SECURITY_LINTER.md": "ADR-0037",
    "PLAN_SYNTHETIC_DATA_LAB.pt_BR.md": "ADR-0007",
    "PLAN_SYNTHETIC_DATA_AND_CONFIDENCE_VALIDATION.md": "ADR-0007",
    "PLAN_PRODUCT_TIERS_AND_OPEN_CORE.md": "ADR-0025",
    "PLAN_COMPLIANCE_EVIDENCE_MAPPING.md": "ADR-0025, ADR-0037",
    "PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md": "ADR-0034",
    "PLAN_ADDITIONAL_DETECTION_TECHNIQUES_AND_FN_REDUCTION.md": "ADR-0043",
    "PLAN_PDF_GRC_REPORT.md": "ADR-0048",
    "PLAN_FINDINGS_CORPORATE_REPOSITORY_EXPORT.md": "ADR-0048",
    "PLAN_MATURITY_SELF_ASSESSMENT_GRC_QUESTIONNAIRE.md": "ADR-0025",
    "PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md": "ADR-0025",
    "PLAN_SECRETS_VAULT.md": "ADR-0005",
    "PLAN_ENGINEERING_DOCTRINE_CONSOLIDATION.md": "ADR-0046, ADR-0047",
}

# Priority overrides derived from PLANS_TODO H-tags (non-H3 exceptions)
PRIORITY_OVERRIDES: dict[str, str] = {
    # H0 - critical path / now
    "PLAN_READINESS_AND_OPERATIONS.md": "H0",
    "PLAN_REPAIR_COMPLETAO_ORQUESTRATOR_RESILIENCE.md": "H0",
    "PLAN_BANDIT_SECURITY_LINTER.md": "H0",
    "PLAN_TWO_WEEK_EXECUTION_NO_REGRESSION.md": "H0",
    "PLAN_ENGINEERING_DOCTRINE_CONSOLIDATION.md": "H0",
    "PLAN_GRC_INSPIRED_ENTERPRISE_TRUST_ACCELERATORS.md": "H0",
    "PLAN_MATURITY_SELF_ASSESSMENT_GRC_QUESTIONNAIRE.md": "H0",
    "PLAN_COMPLIANCE_EVIDENCE_MAPPING.md": "H0",
    "PLAN_PRIORITY_MATRIX_ADJUSTMENTS_2026-03-25.md": "H0",
    # H1 - short-term
    "PLAN_PRODUCT_TIERS_AND_OPEN_CORE.md": "H1",
    "PLAN_NEXT_WAVE_PLATFORM_AND_GTM.md": "H1",
    "PLAN_FOUNDER_SRE_CAREER_AND_PRODUCT_ALIGNMENT.md": "H1",
    "PLAN_FOUNDER_CAREER_AND_BRANDING.pt_BR.md": "H1",
    "PLAN_MARKET_ALIGNMENT_AND_WABBIX_REVIEW_TIMING.md": "H1",
    "PLAN_PDF_GRC_REPORT.md": "H1",
    "PLAN_ACTION_PLAN_GENERATOR_POST_SCAN.md": "H1",
    "PLAN_SCAN_RUN_MANIFEST_AND_EXECUTION_SUMMARY.md": "H2",
    # H2 - medium-term
    "PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md": "H2",
    "PLAN_DASHBOARD_HTTPS_BY_DEFAULT_AND_HTTP_EXPLICIT_RISK.md": "H2",
    "PLAN_DATABRICKS_UNITY_LAKEHOUSE_SCOPE_AND_SCAN.md": "H2",
    "PLAN_FINDINGS_CORPORATE_REPOSITORY_EXPORT.md": "H2",
    "PLAN_LAB_FIREWALL_ACCESS_AND_OBSERVABILITY.md": "H2",
    "PLAN_LAB_FIREWALL_ACCESS_AND_OBSERVABILITY.pt_BR.md": "H2",
    "PLAN_LAB_OP_CAPEX_OPEX_AND_PROCUREMENT.md": "H2",
    "PLAN_LAB_OP_CAPEX_OPEX_PROCUREMENT.md": "H2",
    "PLAN_LAB_OP_CAPEX_OPEX_PROCUREMENT.pt_BR.md": "H2",
    "PLAN_LAB_OP_OBSERVABILITY_STACK.md": "H2",
    "PLAN_LAB_OP_OBSERVABILITY_STACK.pt_BR.md": "H2",
    "PLAN_SCOPE_IMPORT_FROM_EXPORTS.md": "H2",
    "PLAN_NOTIFICATIONS_OFFBAND_AND_SCAN_COMPLETE.md": "H2",
    "PLAN_OPERATOR_API_KEY_FIRST_AUTH_UX.md": "H2",
    "PLAN_OBJECT_STORAGE_CLOUD_CONNECTORS.md": "H2",
    "PLAN_DASHBOARD_MOBILE_RESPONSIVE.md": "H2",
    "PLAN_ADDITIONAL_DATA_SOUP_FORMATS.md": "H2",
    "PLAN_SQL_SAMPLING_SRE_AND_AUDIT_EVIDENCE.md": "H2",
    "PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md": "H2",
    "PLAN_ADDITIONAL_DETECTION_TECHNIQUES_AND_FN_REDUCTION.md": "H2",
    "PLAN_EXTENDED_SENSITIVE_DISCOVERY_POSITIONING.md": "H2",
    "PLAN_OPT_IN_NETWORK_PORT_SERVICE_HINTS.md": "H2",
    # H3 - long-term (these are default, listed explicitly for clarity)
    "PLAN_ENTERPRISE_HR_SST_ERP_CONNECTORS.md": "H3",
    "PLAN_SAP_CONNECTOR.md": "H3",
    "PLAN_SELENIUM_QA_TEST_SUITE.md": "H3",
    "PLAN_SELF_UPGRADE_AND_VERSION_CHECK.md": "H3",
    "PLAN_SYNTHETIC_DATA_LAB.pt_BR.md": "H3",
    "PLAN_SYNTHETIC_DATA_AND_CONFIDENCE_VALIDATION.md": "H3",
    "PLAN_SECRETS_VAULT.md": "H3",
    "PLAN_CLOJURE_AUGMENTATION.md": "H3",
    "PLAN_CLOJURE_AUGMENTATION.pt_BR.md": "H3",
    "PLAN_OPTIONAL_STRONG_CRYPTO_AND_CONTROLS_VALIDATION.md": "H3",
    "PLAN_IMAGE_SENSITIVE_DATA_DETECTION.pt_BR.md": "H3",
    "PLAN_STRICTO_SENSU_RESEARCH_PATH.md": "H3",
    "PLAN_LATO_SENSU_THESIS.md": "H3",
    "PLAN_WEBSITE_AND_DOCS_I18N_FUTURE.md": "H3",
    "PLAN_DATA_SOURCE_VERSIONS_AND_HARDENING.md": "H3",
    "PLAN_CNPJ_ALPHANUMERIC_FORMAT_VALIDATION.md": "H3",
    "PLAN_GEMINI_FEEDBACK_TRIAGE.md": "H3",
}

STATUS_KEYWORDS_COMPLETED = re.compile(
    r"shipped|completed|done|all slices.*shipped|merged|closed", re.IGNORECASE
)
STATUS_KEYWORDS_DEFERRED = re.compile(
    r"deferred|backlog.*parked|paused|on hold|not started|future", re.IGNORECASE
)
STATUS_KEYWORDS_ACTIVE = re.compile(
    r"in.progress|in.flight|active|partially shipped|slice [12].*shipped",
    re.IGNORECASE,
)


def git_creation_date(path: Path) -> str:
    result = subprocess.run(
        [
            "git",
            "log",
            "--diff-filter=A",
            "--format=%ad",
            "--date=short",
            "--",
            str(path),
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    date = result.stdout.strip()
    if not date:
        # fallback: earliest log entry for the file
        result2 = subprocess.run(
            ["git", "log", "--format=%ad", "--date=short", "--", str(path)],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        lines = result2.stdout.strip().splitlines()
        date = lines[-1] if lines else "2026-01-01"
    return date


def extract_existing_status(lines: list[str]) -> str | None:
    for line in lines[:15]:
        m = re.match(r"^\*\*Status:\*\*\s*(.+)", line.strip())
        if m:
            raw = m.group(1).strip()
            # Normalize to ADR-0050 vocabulary
            if STATUS_KEYWORDS_COMPLETED.search(raw):
                return "Completed"
            if STATUS_KEYWORDS_DEFERRED.search(raw):
                return "Deferred"
            if STATUS_KEYWORDS_ACTIVE.search(raw):
                return "Active"
            return "Pending"
    return None


def has_full_header(lines: list[str]) -> bool:
    """Return True if file already has Status+Date+Authors+Priority header."""
    text = "\n".join(lines[:20])
    return "**Date:**" in text and "**Authors:**" in text and "**Priority:**" in text


def build_header(name: str, status: str, date: str, priority: str) -> str:
    deps = KNOWN_DEPS.get(name)
    header = f"\n**Status:** {status}\n**Date:** {date}\n**Authors:** {AUTHORS}\n**Priority:** {priority}\n"
    if deps:
        header += f"**Depends on:** {deps}\n"
    return header


def process_file(path: Path) -> bool:
    """Insert header if missing. Returns True if file was modified."""
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    if has_full_header(lines):
        return False

    name = path.name
    date = git_creation_date(path)
    status = extract_existing_status([line.rstrip() for line in lines]) or "Pending"
    priority = PRIORITY_OVERRIDES.get(name, "H3")

    # Find insertion point: after the first `# ` heading line (title)
    insert_after = 0
    for i, line in enumerate(lines):
        if line.startswith("# "):
            insert_after = i
            break

    # Build header block
    header_block = build_header(name, status, date, priority)
    header_lines = [line + "\n" for line in header_block.splitlines()]

    # Remove any existing standalone **Status:** line to avoid duplication
    cleaned = []
    skip_next_blank = False
    for i, line in enumerate(lines):
        if i <= insert_after:
            cleaned.append(line)
            continue
        stripped = line.strip()
        if re.match(r"^\*\*Status:\*\*", stripped) and "**Date:**" not in stripped:
            skip_next_blank = True
            continue
        if skip_next_blank and stripped == "":
            skip_next_blank = False
            continue
        skip_next_blank = False
        cleaned.append(line)

    # Insert header after title
    result = cleaned[: insert_after + 1] + header_lines + cleaned[insert_after + 1 :]

    # Ensure blank line after header block before next content
    path.write_text("".join(result), encoding="utf-8")
    return True


def main() -> None:
    plan_files = sorted(PLANS_DIR.glob("PLAN_*.md"))
    modified = 0
    for p in plan_files:
        if process_file(p):
            print(f"  updated: {p.name}")
            modified += 1
        else:
            print(f"  skipped (already has header): {p.name}")
    print(f"\nDone. {modified}/{len(plan_files)} files updated.")


if __name__ == "__main__":
    main()
