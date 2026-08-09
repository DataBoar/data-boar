"""
Excel report trust tint (S2a wave-2c / M-TRUST-02 thin).

Applies canonical ``trust_state`` / ``output_confidence`` to Excel workbooks:
- ``degraded``: Report info watermark + full findings sheets.
- ``untrusted``: Report info watermark + detail sheets present as stubs
  (0 finding rows + retention notice). Does **not** force ``-alpha`` from
  transport alone (integrity adulteration remains the -alpha path).
"""

from __future__ import annotations

from typing import Any

_WATERMARK_DEGRADED = (
    "TINTED / REDUCED CONFIDENCE — runtime trust_state=degraded. "
    "Do not treat this workbook as complete regulatory evidence. "
    "Findings sheets are included for operator triage."
)
_WATERMARK_UNTRUSTED = (
    "TINTED / MINIMAL OUTPUT — runtime trust_state=untrusted. "
    "Detail findings are withheld from this workbook (stub sheets only). "
    "Do not treat this workbook as complete regulatory evidence."
)


def resolve_excel_trust_tint(config: dict[str, Any] | None) -> dict[str, Any]:
    """
    Resolve Excel tint policy from the canonical trust snapshot.

    Keys: trust_state, trust_reasons, output_confidence, show_watermark,
    detail_sheets_stub, watermark_message.
    """
    from core.canonical_trust import get_canonical_trust_snapshot

    snap = get_canonical_trust_snapshot(config or {})
    state = str(snap.get("trust_state") or "degraded")
    confidence = str(snap.get("output_confidence") or "reduced")
    reasons = list(snap.get("trust_reasons") or [])
    show = state in ("degraded", "untrusted")
    stub = state == "untrusted"
    if state == "untrusted":
        message = _WATERMARK_UNTRUSTED
    elif state == "degraded":
        message = _WATERMARK_DEGRADED
    else:
        message = ""
    return {
        "trust_state": state,
        "trust_reasons": reasons,
        "output_confidence": confidence,
        "show_watermark": show,
        "detail_sheets_stub": stub,
        "watermark_message": message,
    }


def trust_tint_report_info_rows(tint: dict[str, Any]) -> list[dict[str, Any]]:
    """Rows prepended to Report info when trust is not clean."""
    if not tint.get("show_watermark"):
        return []
    reasons = tint.get("trust_reasons") or []
    reasons_s = ", ".join(str(r) for r in reasons) if reasons else "—"
    return [
        {"Field": "TRUST WATERMARK", "Value": tint.get("watermark_message") or ""},
        {"Field": "Trust state", "Value": tint.get("trust_state") or "unknown"},
        {"Field": "Trust reasons", "Value": reasons_s},
        {
            "Field": "Output confidence",
            "Value": tint.get("output_confidence") or "reduced",
        },
        {
            "Field": "Regulatory completeness",
            "Value": (
                "Not claimed — trust markers indicate degraded or untrusted runtime."
            ),
        },
    ]


def stub_detail_sheet_rows(
    *,
    sheet_label: str,
    retained_count: int,
    tint: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Stub rows for a detail sheet under untrusted tint (0 finding rows + notice).

    Sheet remains present so the workbook does not look truncated by accident.
    """
    reasons = tint.get("trust_reasons") or []
    reasons_s = ", ".join(str(r) for r in reasons) if reasons else "—"
    return [
        {
            "Field": "Output withheld",
            "Value": (
                f"{sheet_label} detail withheld: trust_state="
                f"{tint.get('trust_state')} "
                f"(output_confidence={tint.get('output_confidence')}). "
                "Rows remain in the audit database; regenerate when trust is restored."
            ),
        },
        {
            "Field": "Findings retained (not exported)",
            "Value": str(int(retained_count)),
        },
        {"Field": "Trust reasons", "Value": reasons_s},
    ]
