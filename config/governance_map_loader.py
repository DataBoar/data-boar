"""
Load Governance Lens framework mapping YAML (structure per governance_framework_map.schema.yaml).

Curated commercial maps may live outside the public tree; OSS ships
``governance_framework_map_pro.example.yaml`` for lab and tests.
"""

from __future__ import annotations

import fnmatch
from pathlib import Path
from typing import Any

import yaml

DEFAULT_GOVERNANCE_MAP_FILE = "config/governance_framework_map_pro.example.yaml"


def resolve_governance_map_path(
    map_file: str, config_path: Path | str | None = None
) -> Path:
    """Resolve ``governance.map_file`` relative to the main config directory when needed."""
    p = Path(map_file)
    if p.is_absolute():
        return p
    if config_path:
        base = Path(config_path).resolve().parent
        candidate = base / p
        if candidate.is_file():
            return candidate
    repo_candidate = Path.cwd() / p
    if repo_candidate.is_file():
        return repo_candidate
    return (Path(config_path).resolve().parent if config_path else Path.cwd()) / p


def load_governance_map_entries(
    map_path: Path,
) -> list[dict[str, Any]]:
    """Parse and validate the minimum shape of a governance framework map file."""
    if not map_path.is_file():
        raise FileNotFoundError(f"Governance map file not found: {map_path}")
    raw = yaml.safe_load(map_path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"Governance map root must be a mapping: {map_path}")
    entries = raw.get("entries")
    if not isinstance(entries, list):
        raise ValueError(f"Governance map missing 'entries' list: {map_path}")
    out: list[dict[str, Any]] = []
    for idx, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ValueError(f"Governance map entry {idx} must be a mapping")
        pattern_name = str(entry.get("pattern_name") or "").strip()
        if not pattern_name:
            raise ValueError(f"Governance map entry {idx} missing pattern_name")
        frameworks = entry.get("frameworks")
        if not isinstance(frameworks, list) or not frameworks:
            raise ValueError(
                f"Governance map entry {pattern_name!r} needs a non-empty frameworks list"
            )
        tc = entry.get("target_context")
        if tc is not None and tc != "":
            tc = str(tc).strip()
        else:
            tc = None
        fw_norm: list[dict[str, Any]] = []
        for fw in frameworks:
            if not isinstance(fw, dict):
                continue
            fw_id = str(fw.get("id") or "").strip()
            if not fw_id:
                continue
            fw_norm.append(
                {
                    "id": fw_id,
                    "name": str(fw.get("name") or fw_id).strip(),
                    "tier": str(fw.get("tier") or "pro").strip().lower(),
                    "control_gap_title": str(fw.get("control_gap_title") or "").strip(),
                    "control_gap_body": str(fw.get("control_gap_body") or "").strip(),
                    "recommendation": str(fw.get("recommendation") or "").strip(),
                    "deadline_days": fw.get("deadline_days"),
                }
            )
        if not fw_norm:
            raise ValueError(
                f"Governance map entry {pattern_name!r} has no valid framework rows"
            )
        out.append(
            {
                "pattern_name": pattern_name,
                "target_context": tc,
                "frameworks": fw_norm,
            }
        )
    return out


def pattern_name_matches(entry_pattern: str, detected_pattern: str) -> bool:
    """Match detector pattern names (supports ``*`` / ``?`` wildcards)."""
    ep = (entry_pattern or "").strip()
    dp = (detected_pattern or "").strip()
    if not ep or not dp:
        return False
    if ep in ("*", "any", "ANY"):
        return True
    if "*" in ep or "?" in ep:
        return fnmatch.fnmatchcase(dp, ep)
    return dp == ep


def target_context_matches(entry_context: str | None, row_context: str) -> bool:
    if entry_context is None or str(entry_context).strip().lower() in (
        "",
        "null",
        "any",
    ):
        return True
    return str(entry_context).strip() == row_context
