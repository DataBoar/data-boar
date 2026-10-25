"""
Heuristic NIST CSF 2.0 *function hints* for GRC findings (CISO/DPO-facing).

Maps finding ``norm_tag`` strings to short NIST CSF 2.0 codes (e.g. ``"GV"``,
``"ID.AM"``, ``"PR.DS"``) using a **versioned, shipped** mapping table
(``report/nist_csf_mapping.yaml``) — never hard-coded "truth" in code.

These are **hints**, not a compliance determination, control attestation, or legal
conclusion (ADR-0025). The CISO/DPO validates applicability and maturity. The mapping
complements the article hints documented in ``docs/GRC_EXECUTIVE_REPORT_SCHEMA.md`` and
the tri-level positioning discussion in issue #749 (NIST CSF / SANS / ISO 27035).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

_MAPPING_PATH = Path(__file__).resolve().parent / "nist_csf_mapping.yaml"

# Fallbacks used only when the YAML cannot be read; keep behaviour safe (no hints)
# rather than raising into the report pipeline.
_FALLBACK_MAPPING_VERSION = "nist_csf_2_0_hint_v1"
_FALLBACK_DISCLAIMER = (
    "NIST CSF 2.0 function codes are heuristic hints derived from finding norm tags, "
    "not a compliance determination or control attestation (ADR-0025). "
    "CISO/DPO validates applicability and maturity."
)

# Canonical CSF 2.0 Function ordering for stable, reviewable output.
_FUNCTION_ORDER = {"GV": 0, "ID": 1, "PR": 2, "DE": 3, "RS": 4, "RC": 5}


def _csf_sort_key(code: str) -> tuple[int, str]:
    """Sort CSF codes by Function order (GV, ID, PR, DE, RS, RC), then alphabetically."""
    function = code.split(".", 1)[0].upper()
    return (_FUNCTION_ORDER.get(function, 99), code.upper())


@lru_cache(maxsize=1)
def _load_mapping() -> dict[str, Any]:
    """Load and cache the shipped YAML mapping table (safe defaults on failure)."""
    try:
        raw = _MAPPING_PATH.read_text(encoding="utf-8")
        data = yaml.safe_load(raw)
    except (OSError, yaml.YAMLError):
        return {
            "mapping_version": _FALLBACK_MAPPING_VERSION,
            "disclaimer": "",
            "rules": [],
        }
    if not isinstance(data, dict):
        return {
            "mapping_version": _FALLBACK_MAPPING_VERSION,
            "disclaimer": "",
            "rules": [],
        }

    rules_out: list[tuple[str, list[str]]] = []
    for item in data.get("rules") or []:
        if not isinstance(item, dict):
            continue
        match = str(item.get("match", "")).strip().lower()
        codes = item.get("csf")
        if not match or not isinstance(codes, list):
            continue
        clean_codes = [str(c).strip() for c in codes if str(c).strip()]
        if clean_codes:
            rules_out.append((match, clean_codes))

    version = str(data.get("mapping_version") or _FALLBACK_MAPPING_VERSION)
    disclaimer = str(data.get("disclaimer") or _FALLBACK_DISCLAIMER).strip()
    return {"mapping_version": version, "disclaimer": disclaimer, "rules": rules_out}


def mapping_version() -> str:
    """Return the shipped mapping table version (e.g. ``nist_csf_2_0_hint_v1``)."""
    return str(_load_mapping()["mapping_version"])


def disclaimer() -> str:
    """Return the ADR-0025 heuristic disclaimer for the CSF hint block."""
    text = str(_load_mapping()["disclaimer"]).strip()
    return text or _FALLBACK_DISCLAIMER


def csf_functions_for_norm_tags(norm_tags: list[str] | None) -> list[str]:
    """
    Return heuristic NIST CSF 2.0 codes for the given ``norm_tags`` (sorted, de-duplicated).

    Returns an empty list when no norm_tag matches a mapping rule — callers should then
    **omit** the ``nist_csf_function_hint`` field rather than emit an empty array.
    """
    if not norm_tags:
        return []
    rules = _load_mapping()["rules"]
    if not rules:
        return []
    found: set[str] = set()
    for tag in norm_tags:
        norm = str(tag or "").strip().lower()
        if not norm:
            continue
        for match, codes in rules:
            if match in norm:
                found.update(codes)
    return sorted(found, key=_csf_sort_key)
