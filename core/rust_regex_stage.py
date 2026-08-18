"""
Rust regex matching stage (#1414) — cached ``Regex`` loop, not ``RegexSet``.

Builds a per-detector engine from live YAML/built-in patterns after
``regex_translate.classify_pattern``. Community / missing wheel → pure Python.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from core.regex_translate import PatternRouting, RoutingKind, classify_pattern

logger = logging.getLogger(__name__)

_RUST_STAGE_FEATURE = "rust_regex_stage"


@dataclass
class RustRegexStageStatus:
    active: bool
    name: str | None
    backend: str | None
    tier: str | None
    reason: str | None
    engine: str
    rust_accelerator_installed: bool
    accelerated_count: int = 0
    translated_count: int = 0
    python_fallback_count: int = 0
    rust_only_count: int = 0
    python_fallback_reasons: dict[str, str] = field(default_factory=dict)
    rust_only_patterns: list[str] = field(default_factory=list)

    def to_prefilter_dict(self) -> dict[str, Any]:
        return {
            "active": self.active,
            "name": self.name,
            "backend": self.backend,
            "tier": self.tier,
            "reason": self.reason,
            "engine": self.engine,
            "rust_accelerator_installed": self.rust_accelerator_installed,
            "accelerated_count": self.accelerated_count,
            "translated_count": self.translated_count,
            "python_fallback_count": self.python_fallback_count,
            "rust_only_count": self.rust_only_count,
            "python_fallback_reasons": dict(self.python_fallback_reasons),
            "rust_only_patterns": list(self.rust_only_patterns),
        }

    @classmethod
    def inactive_python(
        cls, *, tier: str | None = None, reason: str = "inactive"
    ) -> RustRegexStageStatus:
        return cls(
            active=False,
            name="rust_regex_stage",
            backend="python",
            tier=tier,
            reason=reason,
            engine="core",
            rust_accelerator_installed=_rust_installed(),
        )


class RustRegexStage:
    """Per-detector cached Rust matcher + Python fallback pattern names."""

    def __init__(
        self,
        *,
        engine: Any,
        routings: list[PatternRouting],
        python_fallback_names: set[str],
    ) -> None:
        self._engine = engine
        self._routings = routings
        self.python_fallback_names = python_fallback_names

    def match_names(self, text: str) -> set[str]:
        if self._engine is None:
            return set()
        try:
            hits = self._engine.match_names(text)
        except Exception as exc:  # noqa: BLE001 — fail-soft per ADR-0083
            logger.warning("rust-regex-stage: match failed (fail-soft): %s", exc)
            return set()
        return set(hits or [])


def _rust_installed() -> bool:
    try:
        from boar_fast_filter import RegexStageEngine  # noqa: F401

        return True
    except Exception:  # noqa: BLE001
        return False


def _tier_allows_rust_stage(
    licensing_config: dict[str, Any] | None,
) -> tuple[bool, str | None, str | None]:
    try:
        from core.licensing.runtime_feature_tier import get_runtime_tier_for_features
        from core.licensing.tier_features import FEATURE_TIER_MAP, is_feature_available

        _ = FEATURE_TIER_MAP[_RUST_STAGE_FEATURE]
        tier = get_runtime_tier_for_features(licensing_config or {})
        tier_value = getattr(tier, "value", str(tier))
        if not is_feature_available(_RUST_STAGE_FEATURE, tier):
            return False, tier_value, "tier_below_pro_plus"
        return True, tier_value, None
    except Exception as exc:  # noqa: BLE001
        return False, None, f"tier_gate_error:{exc}"


def build_rust_regex_stage(
    patterns: dict[str, tuple[str, str]],
    *,
    licensing_config: dict[str, Any] | None = None,
) -> tuple[RustRegexStage | None, RustRegexStageStatus]:
    routings = [classify_pattern(name, pat) for name, (pat, _norm) in patterns.items()]
    accelerated = sum(1 for r in routings if r.kind is RoutingKind.DIRECT)
    translated = sum(1 for r in routings if r.kind is RoutingKind.TRANSLATED)
    fallback = [r for r in routings if r.kind is RoutingKind.PYTHON_FALLBACK]
    fallback_reasons = {r.name: r.reason for r in fallback}

    installed = _rust_installed()
    allowed, tier_value, tier_reason = _tier_allows_rust_stage(licensing_config)

    base_status = RustRegexStageStatus(
        active=False,
        name="rust_regex_stage",
        backend="python",
        tier=tier_value,
        reason=tier_reason or "inactive",
        engine="core",
        rust_accelerator_installed=installed,
        accelerated_count=accelerated,
        translated_count=translated,
        python_fallback_count=len(fallback),
        python_fallback_reasons=fallback_reasons,
    )

    if not allowed:
        return None, base_status
    if not installed:
        base_status.reason = "rust_extension_missing"
        return None, base_status

    rust_names: list[str] = []
    rust_patterns: list[str] = []
    python_fallback_names: set[str] = {r.name for r in fallback}
    for routing in routings:
        if routing.kind is RoutingKind.PYTHON_FALLBACK:
            continue
        assert routing.rust_pattern is not None
        rust_names.append(routing.name)
        rust_patterns.append(routing.rust_pattern)

    if not rust_names:
        base_status.reason = "no_rust_eligible_patterns"
        return None, base_status

    try:
        from boar_fast_filter import RegexStageEngine

        engine = RegexStageEngine.compile_patterns(rust_names, rust_patterns, None)
    except Exception as exc:  # noqa: BLE001
        logger.warning("rust-regex-stage: compile failed (fail-soft): %s", exc)
        base_status.reason = "rust_compile_failed"
        return None, base_status

    active_status = RustRegexStageStatus(
        active=True,
        name="rust_regex_stage",
        backend="rust",
        tier=tier_value,
        reason=None,
        engine="core",
        rust_accelerator_installed=True,
        accelerated_count=accelerated,
        translated_count=translated,
        python_fallback_count=len(fallback),
        python_fallback_reasons=fallback_reasons,
    )
    stage = RustRegexStage(
        engine=engine,
        routings=routings,
        python_fallback_names=python_fallback_names,
    )
    return stage, active_status
