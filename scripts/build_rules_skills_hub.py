#!/usr/bin/env python3
"""Generate docs/hubs/RULES_AND_SKILLS_HUB.md from .cursor/rules and .cursor/skills."""

from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RULES_DIR = REPO_ROOT / ".cursor" / "rules"
SKILLS_DIR = REPO_ROOT / ".cursor" / "skills"
OUT_EN = REPO_ROOT / "docs" / "hubs" / "RULES_AND_SKILLS_HUB.md"
OUT_PT = REPO_ROOT / "docs" / "hubs" / "RULES_AND_SKILLS_HUB.pt_BR.md"

FRONTMATTER = re.compile(r"^---\s*\r?\n(.*?)\r?\n---\s*\r?\n", re.DOTALL)
SESSION_KEYWORD = re.compile(r"\|\s*\*\*([a-z0-9-]+)\*\*\s*\|", re.I)
FINGERPRINT_RE = re.compile(r"<!-- rules-skills-fingerprint: ([a-f0-9]{64}) -->")


def _parse_frontmatter(text: str) -> dict[str, str]:
    m = FRONTMATTER.match(text)
    if not m:
        return {}
    block = m.group(1)
    out: dict[str, str] = {}
    for line in block.splitlines():
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        out[key.strip()] = val.strip()
    return out


def _first_heading_or_line(text: str, fallback: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
        if line.strip() and not line.startswith("---"):
            s = line.strip()
            if len(s) > 120:
                s = s[:117] + "..."
            return s
    return fallback


def _fingerprint(rules: list[dict], skills: list[dict]) -> str:
    parts = [
        f"r:{r['file']}:{int(r['always'])}"
        for r in sorted(rules, key=lambda x: x["file"])
    ]
    parts.extend(f"s:{s['folder']}" for s in sorted(skills, key=lambda x: x["folder"]))
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


def _load_session_keywords() -> list[str]:
    path = RULES_DIR / "session-mode-keywords.mdc"
    if not path.is_file():
        return []
    return SESSION_KEYWORD.findall(path.read_text(encoding="utf-8"))


def _git_tracked_paths(glob_pattern: str) -> list[Path]:
    proc = subprocess.run(
        ["git", "ls-files", glob_pattern],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return []
    out: list[Path] = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if line:
            out.append((REPO_ROOT / line).resolve())
    return out


def _collect_rules() -> list[dict]:
    rows: list[dict] = []
    paths = _git_tracked_paths(".cursor/rules/*.mdc")
    if not paths:
        paths = sorted(RULES_DIR.glob("*.mdc"))
    for path in sorted(paths, key=lambda p: p.name):
        raw = path.read_text(encoding="utf-8")
        fm = _parse_frontmatter(raw)
        always = fm.get("alwaysApply", "").lower() == "true"
        desc = fm.get("description", "") or _first_heading_or_line(raw, path.stem)
        globs = fm.get("globs", "")
        rows.append(
            {
                "file": path.name,
                "path": f"`.cursor/rules/{path.name}`",
                "always": always,
                "description": desc.replace("|", "\\|"),
                "globs": globs,
            }
        )
    return rows


def _collect_skills() -> list[dict]:
    rows: list[dict] = []
    paths = _git_tracked_paths(".cursor/skills/**/SKILL.md")
    if not paths:
        paths = sorted(SKILLS_DIR.glob("**/SKILL.md"))
    for path in sorted(paths, key=lambda p: p.as_posix()):
        rel = path.relative_to(SKILLS_DIR)
        folder = rel.parent.as_posix() if rel.parent != Path(".") else rel.parent.name
        raw = path.read_text(encoding="utf-8")
        fm = _parse_frontmatter(raw)
        desc = fm.get("description", "") or _first_heading_or_line(raw, folder)
        rows.append(
            {
                "folder": folder,
                "path": f"`.cursor/skills/{rel.as_posix()}`",
                "description": desc.replace("|", "\\|"),
            }
        )
    return rows


def _render_en(
    rules: list[dict], skills: list[dict], keywords: list[str], fingerprint: str
) -> str:
    always = [r for r in rules if r["always"]]
    situational = [r for r in rules if not r["always"]]
    kw_hint = ", ".join(f"`{k}`" for k in keywords[:12])
    if len(keywords) > 12:
        kw_hint += f", ... ({len(keywords)} total in session-mode-keywords)"

    lines = [
        "# Rules and Skills Hub",
        "",
        "**Português (Brasil):** [RULES_AND_SKILLS_HUB.pt_BR.md](RULES_AND_SKILLS_HUB.pt_BR.md)",
        "",
        (
            "> **For agents:** consult this hub before duplicating behavior in chat. "
            + "Rules with `alwaysApply: true` are already active — do not re-load them unless debugging. "
            + "Situational rules attach via **globs** or **session keywords** (see "
            + "[session-mode-keywords.mdc](../../.cursor/rules/session-mode-keywords.mdc)). "
            + "Skills are invoked when the task matches the skill description or a session keyword."
        ),
        "",
        f"_Generated by `scripts/build_rules_skills_hub.py` — {len(rules)} rules, "
        f"{len(skills)} skills. Session keyword sample: {kw_hint}._",
        "",
        "## Rules (`.cursor/rules/*.mdc`)",
        "",
        "### Always-on (`alwaysApply: true`)",
        "",
        "| Rule | What it does |",
        "| ---- | ------------ |",
    ]
    for r in always:
        lines.append(f"| {r['path']} | {r['description']} |")
    lines.extend(
        [
            "",
            "### Situational (globs and/or session keywords)",
            "",
            "| Rule | Activation | What it does |",
            "| ---- | ---------- | ------------ |",
        ]
    )
    for r in situational:
        act = r["globs"] if r["globs"] else "keyword / `@rule` / plan globs"
        lines.append(f"| {r['path']} | {act} | {r['description']} |")
    lines.extend(
        [
            "",
            "## Skills (`.cursor/skills/*/SKILL.md`)",
            "",
            "| Skill | Path | What it does |",
            "| ----- | ---- | ------------ |",
        ]
    )
    for s in skills:
        lines.append(f"| `{s['folder']}` | {s['path']} | {s['description']} |")
    lines.extend(
        [
            "",
            "## Maintenance",
            "",
            "- Regenerate after adding or renaming rules/skills: "
            + "`uv run python scripts/build_rules_skills_hub.py --write`.",
            "- Hub pattern: [ADR-0057](../adr/ADR-0057-lightweight-hub-index-co-located-links.md).",
            "- Cross-cutting map: [INDEX.md](INDEX.md).",
            "",
            f"<!-- rules-skills-fingerprint: {fingerprint} -->",
            "",
        ]
    )
    return "\n".join(lines)


def _render_pt(rules: list[dict], skills: list[dict], keywords: list[str]) -> str:
    intro = (
        "# Hub de regras e skills\n\n"
        "**English (canonical tables):** [RULES_AND_SKILLS_HUB.md](RULES_AND_SKILLS_HUB.md)\n\n"
        "> **Para agentes:** consulte o hub em inglês para tabelas atualizadas (nomes de arquivo "
        "e descrições técnicas permanecem em inglês). Use "
        "[session-mode-keywords.mdc](../../.cursor/rules/session-mode-keywords.mdc) para tokens "
        "de sessão. Regenerar: `uv run python scripts/build_rules_skills_hub.py --write`.\n\n"
    )
    # pt-BR file = intro + pointer; full tables stay in EN (issue allows synced structure)
    return intro + (
        "## Resumo\n\n"
        f"- **Regras:** {len(rules)} arquivos `.mdc` "
        f"({sum(1 for r in rules if r['always'])} always-on, "
        f"{sum(1 for r in rules if not r['always'])} situacionais).\n"
        f"- **Skills:** {len(skills)} pastas com `SKILL.md`.\n"
        f"- **Keywords de sessão:** {len(keywords)} tokens em `session-mode-keywords.mdc`.\n\n"
        "Abra o arquivo em inglês para a tabela completa (evita drift entre dois corpos grandes).\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="Write hub files")
    parser.add_argument("--check", action="store_true", help="Fail if hubs differ")
    args = parser.parse_args()
    rules = _collect_rules()
    skills = _collect_skills()
    keywords = _load_session_keywords()
    fingerprint = _fingerprint(rules, skills)
    en = _render_en(rules, skills, keywords, fingerprint)
    pt = _render_pt(rules, skills, keywords)

    if args.check:
        ok = True
        if not OUT_EN.is_file():
            print(
                "build_rules_skills_hub: missing RULES_AND_SKILLS_HUB.md",
                file=sys.stderr,
            )
            ok = False
        else:
            got = OUT_EN.read_text(encoding="utf-8")
            m = FINGERPRINT_RE.search(got)
            if not m or m.group(1) != fingerprint:
                print(
                    "build_rules_skills_hub: stale fingerprint "
                    f"(run with --write; {len(rules)} rules, {len(skills)} skills)",
                    file=sys.stderr,
                )
                ok = False
        if ok:
            print(
                f"build_rules_skills_hub: OK ({len(rules)} rules, {len(skills)} skills)"
            )
            return 0
        return 1

    if args.write:
        OUT_EN.write_text(en, encoding="utf-8", newline="\n")
        OUT_PT.write_text(pt, encoding="utf-8", newline="\n")
        print(
            f"Wrote {OUT_EN.relative_to(REPO_ROOT)} and {OUT_PT.relative_to(REPO_ROOT)}"
        )
        return 0

    print(en[:2000])
    print("\n... (use --write to save)\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
