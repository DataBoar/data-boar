"""
CLI ↔ scan-path readiness (#1411 observability; product mother #1414).

Resolves paid-tier status for ``--prefilter-status``, ``--validate-config``,
and ``GET /status`` → ``detection_prefilter`` / scan evidence.

**Product direction (#1414 / ADR-0083):** Rust runs the **same regex stage** as
``SensitivityDetector`` (no skip of non-suspects → no zero-regression latch).
The ``ProScanner`` + ``filter_batch`` skip path and
``PRO_SCAN_PATH_ZERO_REGRESSION_LATCH`` below are **discarded framing** retained
only until PLAN §0 retirement — do not document them as shipping behaviour.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)

# Discarded skip/latch design (PLAN_RUST_REGEX_STAGE §0 / #1414). Kept True so
# CLI never activates the old ProScanner skip path; retire with the WIP, not by
# "lifting" a product latch.
PRO_SCAN_PATH_ZERO_REGRESSION_LATCH = True


def resolve_pro_scan_path(
    cfg: dict[str, Any] | None,
    *,
    deep_scan_fn: Callable[[list[str]], Any] | None = None,
    legacy_scan_fn: Callable[[list[str]], Any] | None = None,
) -> tuple[Any | None, dict[str, Any]]:
    """
    Resolve paid-tier scan-path readiness (observability + fail-soft).

    Returns ``(scanner_or_None, status)``. Status keys:
    ``active``, ``name``, ``backend`` (``rust``|``python``|None), ``tier``,
    ``reason``, ``engine`` (``pro``|``core``).
    With the discarded latch ON, always returns ``None`` + reason code for status.
    """
    status: dict[str, Any] = {
        "active": False,
        "name": None,
        "backend": None,
        "tier": None,
        "reason": None,
        "engine": "core",
    }
    if os.environ.get("DATA_BOAR_PREFILTER", "").strip().lower() in (
        "0",
        "off",
        "false",
    ):
        status["reason"] = "env_off"
        logger.info("pro-scan-path: inactive (DATA_BOAR_PREFILTER off) [#1411]")
        return None, status

    try:
        from core.licensing.runtime_feature_tier import get_runtime_tier_for_features
        from core.licensing.tier_features import FEATURE_TIER_MAP, Tier
        from pro.engine import RUST_AVAILABLE, ProScanner

        _ = FEATURE_TIER_MAP["pro_prefilter_accel"]
        tier = get_runtime_tier_for_features(cfg or {})
        status["tier"] = getattr(tier, "value", str(tier))
        # Explicit paid set — never check_feature (OPEN bypasses that API).
        if tier not in (Tier.PRO_PLUS, Tier.ENTERPRISE, Tier.PARTNER):
            status["reason"] = "tier_below_pro_plus"
            logger.info(
                "pro-scan-path: inactive (tier=%s requires Pro+/Enterprise/Partner) [#1411]",
                status["tier"],
            )
            return None, status

        backend = "rust" if RUST_AVAILABLE else "python"
        status["name"] = "ProScanner"
        status["backend"] = backend

        if PRO_SCAN_PATH_ZERO_REGRESSION_LATCH:
            status["reason"] = "zero_regression_latch"
            status["engine"] = "core"
            logger.warning(
                "pro-scan-path: inactive (zero-regression latch; tier=%s backend=%s) [#1411]",
                status["tier"],
                backend,
            )
            return None, status

        pro = ProScanner(
            deep_scan_fn=deep_scan_fn,
            legacy_scan_fn=legacy_scan_fn or deep_scan_fn,
        )
        # Prefer live FastFilter presence over import-time RUST_AVAILABLE.
        live_backend = (
            "rust" if getattr(pro, "fast_filter", None) is not None else "python"
        )
        status["backend"] = live_backend
        status["active"] = True
        status["engine"] = "pro"
        status["reason"] = None
        logger.info(
            "pro-scan-path: ACTIVE name=ProScanner backend=%s tier=%s [#1411]",
            live_backend,
            status["tier"],
        )
        return pro, status
    except Exception as exc:  # noqa: BLE001 — fail-soft: keep core path
        status["reason"] = "fail_soft"
        logger.warning("pro-scan-path: disabled (fail-soft): %s [#1411]", exc)
        return None, status


def rust_accelerator_installed() -> bool:
    """True when ``boar_fast_filter`` imports (wheelhouse channel; not on PyPI)."""
    try:
        from pro.engine import RUST_AVAILABLE

        return bool(RUST_AVAILABLE)
    except Exception:  # noqa: BLE001
        return False
