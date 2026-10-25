"""CI guard: situational Cursor rule ``globs`` still resolve to existing files (#409).

Stale globs mean a rule with ``alwaysApply: false`` never attaches — silent miss
(ADR-0049). Pytest in ``ci.yml`` is the CI check; no extra workflow.

Gitignored trees (``docs/private/**``, ``.cursor/private/**``) are skipped when
absent (fresh CI clone). When the tree exists locally, those patterns must still
match a file.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
RULES_DIR = REPO_ROOT / ".cursor" / "rules"
# Gitignored workspace trees — not present on a fresh CI clone.
_GITIGNORED_GLOB_PREFIXES = ("docs/private/", ".cursor/private/")


def _parse_mdc_frontmatter(path: Path) -> dict[str, Any] | None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    data = yaml.safe_load(parts[1])
    if data is None:
        return {}
    if not isinstance(data, dict):
        return None
    return data


def _normalize_globs(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, str):
        return [p.strip() for p in raw.split(",") if p.strip()]
    if isinstance(raw, list):
        out: list[str] = []
        for item in raw:
            if item is None:
                continue
            if isinstance(item, str) and "," in item:
                out.extend(_normalize_globs(item))
            else:
                stripped = str(item).strip()
                if stripped:
                    out.append(stripped)
        return out
    return []


def _posix_rel_pattern(pattern: str) -> str:
    rel = pattern.replace("\\", "/")
    if rel.startswith("./"):
        rel = rel[2:]
    return rel


def _is_gitignored_workspace_glob(pattern: str) -> bool:
    normalized = _posix_rel_pattern(pattern)
    return any(normalized.startswith(prefix) for prefix in _GITIGNORED_GLOB_PREFIXES)


def _gitignored_tree_present(root: Path, pattern: str) -> bool:
    normalized = _posix_rel_pattern(pattern)
    for prefix in _GITIGNORED_GLOB_PREFIXES:
        if normalized.startswith(prefix):
            return (root / prefix.rstrip("/")).is_dir()
    return False


def _glob_has_file(root: Path, pattern: str) -> bool:
    rel = _posix_rel_pattern(pattern)
    try:
        hits = root.glob(rel)
    except ValueError:
        return False
    for hit in hits:
        if hit.is_file():
            return True
        if hit.is_dir() and any(child.is_file() for child in hit.rglob("*")):
            return True
    if "*" not in rel and "?" not in rel and "[" not in rel:
        return (root / rel).is_file()
    if rel.endswith("/**"):
        base = root / rel[:-3]
        return base.is_dir() and any(child.is_file() for child in base.rglob("*"))
    return False


def test_normalize_globs_accepts_yaml_list_and_comma_string() -> None:
    assert _normalize_globs(["a.md", "b.md"]) == ["a.md", "b.md"]
    assert _normalize_globs("a.md,b.md") == ["a.md", "b.md"]
    assert _normalize_globs(None) == []


def test_posix_rel_pattern_keeps_dotfiles() -> None:
    assert _posix_rel_pattern("./.github/workflows/*.yml") == ".github/workflows/*.yml"
    assert _posix_rel_pattern(".cursor/rules/**") == ".cursor/rules/**"


def test_situational_rule_globs_resolve() -> None:
    assert RULES_DIR.is_dir(), f"missing rules dir: {RULES_DIR}"
    stale: list[str] = []
    scanned = 0

    for mdc in sorted(RULES_DIR.glob("*.mdc")):
        meta = _parse_mdc_frontmatter(mdc)
        if meta is None:
            continue
        if meta.get("alwaysApply") is True:
            continue
        patterns = _normalize_globs(meta.get("globs"))
        if not patterns:
            continue
        scanned += 1
        for pattern in patterns:
            if _is_gitignored_workspace_glob(pattern) and not _gitignored_tree_present(
                REPO_ROOT, pattern
            ):
                continue
            if not _glob_has_file(REPO_ROOT, pattern):
                stale.append(f"{mdc.name}: glob {pattern!r} matches no files")

    assert scanned >= 1, "expected at least one situational rule with globs"
    assert not stale, "stale situational globs (files moved?):\n" + "\n".join(stale)
