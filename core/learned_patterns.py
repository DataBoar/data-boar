"""
Learned patterns: extract terms from scan findings that were classified sensitive,
write to a YAML file compatible with ml_patterns_file for use in future runs.
Balances: (1) reducing false positives via thresholds and blocklist,
(2) surfacing compliance-relevant terms that may be missing from default ML patterns.
"""

from pathlib import Path
from typing import Any

# Terms that are too generic to learn (would cause false positives if added to ML)
_GENERIC_TERMS = frozenset(
    {
        "id",
        "name",
        "key",
        "value",
        "data",
        "type",
        "date",
        "code",
        "num",
        "nr",
        "no",
        "n",
        "x",
        "val",
        "txt",
        "desc",
        "comment",
        "remarks",
        "status",
        "flag",
    }
)


def _normalize_term(raw: str) -> str:
    """Lowercase, strip; for dedupe and blocklist check."""
    return (raw or "").strip().lower()


def _extract_term(row: dict, source: str) -> str | None:
    """Get a single term from a finding (column name or file/context)."""
    if source == "database":
        term = (row.get("column_name") or "").strip()
    else:
        # Filesystem: only learn structured db-like locations ("path | table.column").
        # Bare filenames (e.g. main.yml) do not generalize across projects (#1259).
        fn = (row.get("file_name") or "").strip()
        if " | " not in fn:
            return None
        term = fn.split(" | ")[-1].strip()  # e.g. table.column
    return term if term else None


def _sensitivity_rank(level: str) -> int:
    """Higher = stricter; HIGH=2, MEDIUM=1, LOW=0."""
    return {"HIGH": 2, "MEDIUM": 1, "LOW": 0}.get((level or "").upper(), 0)


def collect_learned_entries(
    db_rows: list[dict],
    fs_rows: list[dict],
    *,
    min_sensitivity: str = "HIGH",
    min_confidence: int = 70,
    min_term_length: int = 3,
    require_pattern: bool = True,
    exclude_generic: bool = True,
) -> list[dict]:
    """
    Build list of learned entries from findings.
    - min_sensitivity: only include findings with this level or higher (HIGH or MEDIUM).
    - min_confidence: minimum ml_confidence (0-100).
    - min_term_length: skip terms shorter than this (reduces noise).
    - require_pattern: if True, skip findings where pattern_detected is empty or "GENERAL" (learn only when something concrete was detected).
    - exclude_generic: if True, skip terms in _GENERIC_TERMS.
    Returns list of dicts with keys: text, label, pattern_detected, norm_tag, count (for dedupe).
    """
    min_rank = _sensitivity_rank(min_sensitivity)
    seen: dict[str, dict] = {}  # normalized_term -> entry (with count)

    for row, src in [(r, "database") for r in db_rows] + [
        (r, "filesystem") for r in fs_rows
    ]:
        level = (row.get("sensitivity_level") or "").strip()
        if _sensitivity_rank(level) < min_rank:
            continue
        conf = row.get("ml_confidence")
        if conf is not None and (isinstance(conf, int) and conf < min_confidence):
            continue
        pattern = (row.get("pattern_detected") or "").strip()
        if require_pattern and (not pattern or pattern == "GENERAL"):
            continue
        term = _extract_term(row, src)
        if not term or len(term) < min_term_length:
            continue
        norm = (row.get("norm_tag") or "").strip()
        key = _normalize_term(term)
        if exclude_generic and key in _GENERIC_TERMS:
            continue
        if key in seen:
            seen[key]["count"] = seen[key].get("count", 1) + 1
            # Prefer higher confidence / stronger pattern
            if (conf or 0) > (seen[key].get("ml_confidence") or 0):
                seen[key]["pattern_detected"] = pattern
                seen[key]["norm_tag"] = norm
                seen[key]["ml_confidence"] = conf
        else:
            seen[key] = {
                "text": term,
                "label": "sensitive",
                "pattern_detected": pattern,
                "norm_tag": norm,
                "ml_confidence": conf,
                "count": 1,
            }
    return list(seen.values())


def _load_existing_ml_texts(path: str | Path | None) -> set[str]:
    """Load existing text values from ml_patterns file for dedupe (optional)."""
    if not path:
        return set()
    p = Path(path)
    if not p.exists():
        return set()
    raw = p.read_text(encoding="utf-8")
    if p.suffix.lower() in (".yaml", ".yml"):
        import yaml

        data = yaml.safe_load(raw)
    else:
        import json

        data = json.loads(raw)
    if not isinstance(data, (list, dict)):
        return set()
    items = (
        data if isinstance(data, list) else data.get("patterns", data.get("terms", []))
    )
    out = set()
    for item in items:
        if isinstance(item, dict) and item.get("text"):
            out.add(_normalize_term(item["text"]))
    return out


def _resolve_learned_patterns_output_path(lp: dict, config: dict[str, Any]) -> Path:
    """Resolve learned_patterns.output_file; relative paths anchor to report.output_dir (#1260)."""
    out_path = Path(lp.get("output_file", "learned_patterns.yaml"))
    if out_path.is_absolute():
        return out_path
    output_dir = str((config.get("report") or {}).get("output_dir") or "").strip()
    if output_dir:
        return Path(output_dir) / out_path
    return out_path


def write_learned_patterns(
    db_manager: Any,
    session_id: str | None,
    config: dict[str, Any],
) -> str | None:
    """
    Collect learned entries from session findings, merge with existing file if configured,
    write YAML. Returns path to written file or None if disabled / no entries.
    Config under config["learned_patterns"]:
      enabled: bool (default True if key present)
      output_file: str (default "learned_patterns.yaml"; relative paths resolve under report.output_dir)
      min_sensitivity: "HIGH" | "MEDIUM" (default "HIGH")
      min_confidence: int (default 70)
      min_term_length: int (default 3)
      require_pattern: bool (default True – only learn when a pattern was detected)
      append: bool (default True – merge with existing file)
      exclude_if_in_ml_patterns: bool (default True – skip terms already in ml_patterns_file)
    """
    lp = config.get("learned_patterns") or {}
    if not lp.get("enabled", False):
        return None
    out_path = _resolve_learned_patterns_output_path(lp, config)
    min_sensitivity = lp.get("min_sensitivity", "HIGH")
    min_confidence = int(lp.get("min_confidence", 70))
    min_term_length = int(lp.get("min_term_length", 3))
    require_pattern = lp.get("require_pattern", True)
    append = lp.get("append", True)
    exclude_in_ml = lp.get("exclude_if_in_ml_patterns", True)

    db_rows, fs_rows, _ = db_manager.get_findings(session_id)
    entries = collect_learned_entries(
        db_rows,
        fs_rows,
        min_sensitivity=min_sensitivity,
        min_confidence=min_confidence,
        min_term_length=min_term_length,
        require_pattern=require_pattern,
        exclude_generic=True,
    )
    if exclude_in_ml and config.get("ml_patterns_file"):
        existing = _load_existing_ml_texts(config["ml_patterns_file"])
        entries = [e for e in entries if _normalize_term(e["text"]) not in existing]
    if not entries:
        return None

    # Optional merge with existing learned file
    if append and out_path.exists():
        raw = out_path.read_text(encoding="utf-8")
        if out_path.suffix.lower() in (".yaml", ".yml"):
            import yaml

            existing_data = yaml.safe_load(raw) or []
        else:
            import json

            existing_data = json.loads(raw) if raw.strip() else []
        existing_list = (
            existing_data
            if isinstance(existing_data, list)
            else existing_data.get("patterns", [])
        )
        existing_by_text = {
            _normalize_term(item.get("text", "")): item
            for item in existing_list
            if isinstance(item, dict) and item.get("text")
        }
        for e in entries:
            key = _normalize_term(e["text"])
            if key not in existing_by_text:
                existing_by_text[key] = {
                    "text": e["text"],
                    "label": "sensitive",
                    "pattern_detected": e.get("pattern_detected"),
                    "norm_tag": e.get("norm_tag"),
                    "count": e.get("count", 1),
                }
        entries = list(existing_by_text.values())

    # Write YAML compatible with ml_patterns_file: list of { text, label } plus optional fields
    out_list = []
    for e in entries:
        item = {"text": e["text"], "label": "sensitive"}
        if e.get("pattern_detected"):
            item["pattern_detected"] = e["pattern_detected"]
        if e.get("norm_tag"):
            item["norm_tag"] = e["norm_tag"]
        if e.get("count", 1) > 1:
            item["count"] = e["count"]
        out_list.append(item)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    import yaml

    with open(out_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(
            out_list, f, default_flow_style=False, allow_unicode=True, sort_keys=False
        )
    return str(out_path)
