#!/usr/bin/env python3
"""Generate docs/hubs/OPS_HUB.md from tracked docs/ops/**/*.md (git ls-files)."""

from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_EN = REPO_ROOT / "docs" / "hubs" / "OPS_HUB.md"
OUT_PT = REPO_ROOT / "docs" / "hubs" / "OPS_HUB.pt_BR.md"
FINGERPRINT_RE = re.compile(r"<!-- ops-hub-fingerprint: ([a-f0-9]{64}) -->")

SUBDIR_TITLES = {
    "today-mode": "Today-mode (dated checklists)",
    "inspirations": "Inspirations",
    "lab_lessons_learned": "Lab lessons archive",
    "sre_audits": "SRE audits",
    "governance": "Governance diagrams",
    "dashboards": "Dashboards",
    "evidence": "Evidence",
}

# First matching prefix wins (root files only).
PREFIX_GROUPS: list[tuple[str, str]] = [
    ("CURSOR_", "Agent and Cursor"),
    ("OPERATOR_AGENT", "Agent and Cursor"),
    ("CLOUD_AGENTS", "Agent and Cursor"),
    ("LLM_AGENT", "Agent and Cursor"),
    ("PII_", "Integrity and PII"),
    ("INTEGRITY", "Integrity and PII"),
    ("RELEASE_", "Integrity and PII"),
    ("SECURE_", "Integrity and PII"),
    ("TOKEN_AWARE", "Scripts and automation"),
    ("SCRIPTS_", "Scripts and automation"),
    ("WINDOWS_FAST", "Scripts and automation"),
    ("REPO_", "Scripts and automation"),
    ("LAB_", "Lab-op and homelab"),
    ("HOMELAB", "Lab-op and homelab"),
    ("MAESTRO", "Lab-op and homelab"),
    ("COMPLETAO", "Lab-op and homelab"),
    ("PRIMARY_", "Lab-op and homelab"),
    ("WSL", "Lab-op and homelab"),
    ("WINDOWS_WSL", "Lab-op and homelab"),
    ("LMDE", "Lab-op and homelab"),
    ("T14_", "Lab-op and homelab"),
    ("UFW_", "Lab-op and homelab"),
    ("ZRAM_", "Lab-op and homelab"),
    ("USBGuard", "Lab-op and homelab"),
    ("LYNIS_", "Lab-op and homelab"),
    ("DOCKER_", "Lab-op and homelab"),
    ("OPERATOR_LAB", "Lab-op and homelab"),
    ("OPERATOR_SESSION_SHORTHAND", "Shorthands and quick reference"),
    ("LAB_OP_SHORTHAND", "Shorthands and quick reference"),
    ("SPRINT_", "Plans and retrospectives"),
    ("WRB_", "Plans and retrospectives"),
    ("PLANS_", "Plans and retrospectives"),
    ("THIN_SLICE", "Plans and retrospectives"),
    ("WORKFLOW_", "Plans and retrospectives"),
    ("ISSUE_QUEUE", "Plans and retrospectives"),
    ("OPERATOR_NEXT_DAY", "Plans and retrospectives"),
    ("OPERATOR_WORKFLOW", "Plans and retrospectives"),
]

GROUP_ORDER = [
    "Agent and Cursor",
    "Integrity and PII",
    "Scripts and automation",
    "Lab-op and homelab",
    "Shorthands and quick reference",
    "Plans and retrospectives",
    "Other ops docs (root)",
]


def _git_ops_md() -> list[str]:
    proc = subprocess.run(
        ["git", "ls-files", "docs/ops/**/*.md", "docs/ops/*.md"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return []
    return sorted(
        {
            line.strip().replace("\\", "/")
            for line in proc.stdout.splitlines()
            if line.strip()
        }
    )


def _fingerprint(paths: list[str]) -> str:
    return hashlib.sha256("\n".join(paths).encode("utf-8")).hexdigest()


def _stem_key(rel: str) -> tuple[str, bool]:
    """Return (group_key, is_pt_br). group_key is path without .pt_BR.md / .md."""
    if rel.endswith(".pt_BR.md"):
        return rel[: -len(".pt_BR.md")] + ".md", True
    return rel, False


def _group_root(filename: str) -> str:
    for prefix, group in PREFIX_GROUPS:
        if filename.startswith(prefix):
            return group
    return "Other ops docs (root)"


def _pair_rows(paths: list[str]) -> dict[str, dict[str, str | None]]:
    """Map canonical EN-ish path -> {en, pt}."""
    rows: dict[str, dict[str, str | None]] = {}
    for rel in paths:
        key, is_pt = _stem_key(rel)
        slot = rows.setdefault(key, {"en": None, "pt": None})
        if is_pt:
            slot["pt"] = rel
        else:
            slot["en"] = rel
    return rows


def _md_link(rel: str) -> str:
    href = "../" + rel[len("docs/") :]
    return f"[`{Path(rel).name}`]({href})"


def _role_cell(en: str | None, pt: str | None) -> str:
    parts: list[str] = []
    if en:
        parts.append(_md_link(en))
    if pt:
        parts.append(f"([pt-BR](../{pt[len('docs/') :]}))")
    return " ".join(parts) if parts else "—"


def _render_en(paths: list[str], fingerprint: str) -> str:
    pairs = _pair_rows(paths)
    by_group: dict[str, list[tuple[str, dict[str, str | None]]]] = defaultdict(list)
    subdir_groups: dict[str, list[tuple[str, dict[str, str | None]]]] = defaultdict(
        list
    )

    for key, slot in sorted(pairs.items()):
        rel = slot["en"] or slot["pt"] or key
        rest = rel[len("docs/ops/") :]
        if "/" in rest:
            sub = rest.split("/", 1)[0]
            subdir_groups[sub].append((key, slot))
        else:
            by_group[_group_root(Path(rel).name)].append((key, slot))

    n_files = len(paths)
    n_rows = len(pairs)
    lines = [
        "# Ops hub — index of `docs/ops/`",
        "",
        "**Português (Brasil):** [OPS_HUB.pt_BR.md](OPS_HUB.pt_BR.md)",
        "",
        f"<!-- ops-hub-fingerprint: {fingerprint} -->",
        "",
        "> **For agents:** this page is the **full index** of tracked operator docs under `docs/ops/`.",
        "> The cold-start ladder is the **session router**; it is not a complete catalogue.",
        "> Rows are generated from `git ls-files` — do not add files that are not on disk.",
        "",
        f"_Generated by `scripts/build_ops_hub.py` — **{n_files}** Markdown files, **{n_rows}** stems (EN/pt-BR pairs share a row)._",
        "",
        "Canonical prose stays in the linked files. This hub does not move or merge them ([ADR-0057](../adr/ADR-0057-lightweight-hub-index-co-located-links.md)).",
        "",
    ]

    for group in GROUP_ORDER:
        items = by_group.get(group, [])
        if not items:
            continue
        lines.extend([f"## {group}", "", "| Doc | Path |", "| --- | ---- |"])
        for _key, slot in items:
            name = Path(slot["en"] or slot["pt"] or "").name
            lines.append(f"| {name} | {_role_cell(slot['en'], slot['pt'])} |")
        lines.append("")

    for sub in sorted(subdir_groups):
        title = SUBDIR_TITLES.get(sub, sub)
        lines.extend(
            [
                f"## {title} (`docs/ops/{sub}/`)",
                "",
                "| Doc | Path |",
                "| --- | ---- |",
            ]
        )
        for _key, slot in sorted(subdir_groups[sub], key=lambda x: x[0]):
            name = Path(slot["en"] or slot["pt"] or "").name
            lines.append(f"| {name} | {_role_cell(slot['en'], slot['pt'])} |")
        lines.append("")

    lines.extend(
        [
            "## Related maps",
            "",
            "- Hub of hubs: [INDEX.md](INDEX.md)",
            "- Cold-start ladder: [`OPERATOR_AGENT_COLD_START_LADDER.md`](../ops/OPERATOR_AGENT_COLD_START_LADDER.md)",
            "- Master one-liners: [`DOCS_AND_HUBS_INDEX.md`](../ops/DOCS_AND_HUBS_INDEX.md)",
            "",
            "Regenerate: `uv run python scripts/build_ops_hub.py --write`.",
            "",
        ]
    )
    return "\n".join(lines)


def _render_pt(n_files: int, n_rows: int) -> str:
    return (
        "# Hub de ops — índice de `docs/ops/`\n\n"
        "**English (canonical tables):** [OPS_HUB.md](OPS_HUB.md)\n\n"
        "> **Para agentes:** este hub é o **índice completo** dos runbooks rastreados em `docs/ops/`.\n"
        "> O COLD_START_LADDER é o **roteador de sessão**, não o catálogo.\n"
        "> As linhas vêm de `git ls-files` — não invente entradas.\n\n"
        f"_Gerado por `scripts/build_ops_hub.py` — **{n_files}** arquivos Markdown, "
        f"**{n_rows}** stems (EN e pt-BR na mesma linha). Tabelas canônicas no arquivo em inglês "
        "(nomes de arquivo permanecem em inglês para bater com o disco)._\n\n"
        "Regenerar: `uv run python scripts/build_ops_hub.py --write`.\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    paths = _git_ops_md()
    fingerprint = _fingerprint(paths)
    pairs = _pair_rows(paths)
    en = _render_en(paths, fingerprint)
    pt = _render_pt(len(paths), len(pairs))

    if args.check:
        if not OUT_EN.is_file():
            print("build_ops_hub: missing OPS_HUB.md", file=sys.stderr)
            return 1
        got = OUT_EN.read_text(encoding="utf-8")
        m = FINGERPRINT_RE.search(got)
        if not m or m.group(1) != fingerprint:
            print(
                "build_ops_hub: stale fingerprint (run with --write)",
                file=sys.stderr,
            )
            return 1
        if got != en:
            print("build_ops_hub: OPS_HUB.md differs from generator", file=sys.stderr)
            return 1
        print(f"build_ops_hub: OK ({len(paths)} files)")
        return 0

    if args.write:
        OUT_EN.write_text(en, encoding="utf-8", newline="\n")
        OUT_PT.write_text(pt, encoding="utf-8", newline="\n")
        print(
            f"Wrote {OUT_EN.relative_to(REPO_ROOT)} and {OUT_PT.relative_to(REPO_ROOT)}"
        )
        return 0

    print(en[:1500])
    return 0


if __name__ == "__main__":
    sys.exit(main())
