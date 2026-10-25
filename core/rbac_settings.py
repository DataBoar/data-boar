"""RBAC feature gate (GitHub #86 Phase 2).

A configured ``api.rbac.enabled`` stays fail-closed when the enforced tier
drops below Pro (#2092). Turning the flag off is what disables the gate.
"""

from __future__ import annotations

from typing import Any


def rbac_enforcement_active(config: dict[str, Any]) -> bool:
    """True when ``api.rbac.enabled`` is set.

    The tier does not turn a configured gate off. A Community or degraded
    license keeps denying unauthenticated calls instead of widening access.
    """
    api = config.get("api") if isinstance(config.get("api"), dict) else {}
    raw = api.get("rbac")
    if not isinstance(raw, dict) or not raw.get("enabled"):
        return False
    return True
