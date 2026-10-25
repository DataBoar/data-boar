"""
License enforcement Audit Trail (#719).

Every enforcement decision (allow / deny / clamp / expire) emits a structured
record on the dedicated ``data_boar.licensing.audit`` logger with the stable
prefix ``LICENSE_AUDIT`` so SIEM pipelines and operators can filter it.

Level policy:

- **CRITICAL** — denial while ``mode=enforced`` (scan blocked, fail-closed
  tier clamp, env downgrade attempt). These must never be silent (#719).
- **WARNING** — clamps and denials outside enforced mode (lab tier
  simulation, trial row cap).
- **INFO** — allow decisions (scan permitted, license evaluated VALID/GRACE).
- **DEBUG** — high-frequency allow decisions (per-feature checks).
"""

from __future__ import annotations

import logging

audit_logger = logging.getLogger("data_boar.licensing.audit")

AUDIT_PREFIX = "LICENSE_AUDIT"


def audit_enforcement_event(
    action: str,
    *,
    mode: str,
    state: str = "",
    allowed: bool,
    feature: str = "",
    tier: str = "",
    detail: str = "",
    level: int | None = None,
) -> None:
    """Record one enforcement decision on the audit logger.

    *level* overrides the default policy (e.g. DEBUG for per-feature allows).
    """
    if level is None:
        if allowed:
            level = logging.INFO
        elif mode == "enforced":
            level = logging.CRITICAL
        else:
            level = logging.WARNING
    parts = [
        AUDIT_PREFIX,
        f"action={action}",
        f"mode={mode}",
        f"allowed={str(allowed).lower()}",
    ]
    if state:
        parts.append(f"state={state}")
    if tier:
        parts.append(f"tier={tier}")
    if feature:
        parts.append(f"feature={feature}")
    if detail:
        parts.append(f"detail={detail}")
    audit_logger.log(level, " ".join(parts))
