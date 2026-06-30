"""Close-approval contract for operator-gated GitHub issues (#990, ADR-0072).

Mirrors `.github/workflows/operator-gated-reopen.yml` (github-script).

Only the **latest** close comment (trailer at line start) or label ``gate-close-approved``
counts. Scanning issue body or full comment history would match protocol doc cites
(e.g. trailer in backticks on #406) and disable the guard.
"""

from __future__ import annotations

import re
from pathlib import Path

from scripts.gate_trailer_attest import (
    extract_signature_pem,
    extract_trailer_line,
    verify_trailer_signature,
)

OPERATOR_GATED_LABEL = "operator-gated"
APPROVED_CLOSE_LABEL = "gate-close-approved"
DEFAULT_ALLOWED_SIGNERS = (
    Path(__file__).resolve().parents[1] / "docs" / "adr" / "allowed_signers"
)

# Must open the close comment — not a doc line citing the trailer in backticks.
CLOSE_MARKER_RE = re.compile(
    r"^\s*Gate-Close-Approved-By:\s*@?FabioLeitao\b",
    re.I | re.MULTILINE,
)


def close_trailer_in_latest_comment(text: str) -> bool:
    """True when the latest comment is a deliberate close approval."""
    return bool(CLOSE_MARKER_RE.search(text or ""))


def close_trailer_has_valid_sshsig(
    text: str,
    *,
    allowed_signers: Path | None = None,
) -> bool:
    """True when the comment carries a verified file-namespace SSHSIG for the trailer."""
    body = text or ""
    trailer = extract_trailer_line(body)
    sig_pem = extract_signature_pem(body)
    if not trailer or not sig_pem:
        return False
    signers = allowed_signers or DEFAULT_ALLOWED_SIGNERS
    ok, _msg = verify_trailer_signature(
        trailer,
        sig_pem,
        allowed_signers=signers,
    )
    return ok


def close_allowed(labels: list[str], latest_comment_body: str | None) -> bool:
    """Whether an operator-gated issue may stay closed."""
    if APPROVED_CLOSE_LABEL in labels:
        return True
    if latest_comment_body and close_trailer_in_latest_comment(latest_comment_body):
        return close_trailer_has_valid_sshsig(latest_comment_body)
    return False
