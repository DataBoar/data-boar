"""Guardrail: external-tier Markdown must not link into planning/PMO paths.

Plans remain in the public tree under docs/plans/, but buyer-facing, legal,
and integrator docs should not offer one-click navigation into execution
detail. Allowed entry points stay in docs/README (Internal and reference),
docs/ops/, CONTRIBUTING, and plan files themselves.

See: .cursor/rules/audience-segmentation-docs.mdc
Architecture record: docs/adr/ADR-0004-external-docs-no-markdown-links-to-plans.md
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

# Workflow / maintainer-contract Markdown may link into plans (e.g. PLANS_HUB); still
# excluded from *buyer / integrator / product-guide* tier. See ADR 0004.
_ROOT_MD_SKIP_PLAN_LINK_GUARD: frozenset[str] = frozenset(
    ("CONTRIBUTING.md", "CONTRIBUTING.pt_BR.md", "AGENTS.md")
)


def _docs_path_skips_plan_link_guard(rel_posix: str) -> bool:
    return rel_posix.startswith("docs/COLLABORATION_TEAM") or rel_posix.startswith(
        "docs/TALENT_POOL_LEARNING_PATHS"
    )


# Markdown inline links: [text](target) — strip optional title after space
MD_LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")


def _forbidden_plan_url(url: str) -> bool:
    raw = url.strip().split()[0].strip("<>")
    low = raw.lower()
    if ".cursor/plans" in low:
        return True
    if "/plans/" in low or low.startswith("plans/"):
        return True
    return False


def _iter_strict_markdown_files() -> list[Path]:
    """Product / external-tier docs; excludes hub, ops, plans, ADR tree."""
    allowlist_docs = {
        REPO_ROOT / "docs" / "README.md",
        REPO_ROOT / "docs" / "README.pt_BR.md",
    }
    out: list[Path] = []
    docs_root = REPO_ROOT / "docs"
    if docs_root.is_dir():
        for path in sorted(docs_root.rglob("*.md")):
            if path in allowlist_docs:
                continue
            rel = path.relative_to(REPO_ROOT)
            parts = rel.parts
            if len(parts) >= 2 and parts[1] in ("ops", "plans"):
                continue
            if len(parts) >= 2 and parts[:2] == ("docs", "adr"):
                continue
            if len(parts) >= 2 and parts[:2] == ("docs", "private.example"):
                continue
            if len(parts) >= 2 and parts[:2] == ("docs", "private"):
                continue
            # feedbacks/reviews inbox is gitignored operator material; ARCHIVE_* copies
            # of tracked docs may legitimately link into plans — skip entire subtree.
            if len(parts) >= 2 and parts[1].startswith("feedbacks"):
                continue
            rel_posix = rel.as_posix()
            if _docs_path_skips_plan_link_guard(rel_posix):
                continue
            out.append(path)
    for name in (
        "README.md",
        "README.pt_BR.md",
        "SECURITY.md",
        "SECURITY.pt_BR.md",
    ):
        if name in _ROOT_MD_SKIP_PLAN_LINK_GUARD:
            continue
        p = REPO_ROOT / name
        if p.is_file():
            out.append(p)
    return sorted(set(out))


@pytest.mark.parametrize(
    "md_path",
    _iter_strict_markdown_files(),
    ids=lambda p: str(p.relative_to(REPO_ROOT)).replace("\\", "/"),
)
def test_external_tier_markdown_has_no_plan_links(md_path: Path) -> None:
    text = md_path.read_text(encoding="utf-8")
    violations: list[str] = []
    for _m in MD_LINK_RE.finditer(text):
        target = _m.group(2)
        if _forbidden_plan_url(target):
            violations.append(target.strip().split()[0])
        assert not violations, (
            f"{md_path.relative_to(REPO_ROOT)} links into plans/ or .cursor/plans - "
            f"replace with product docs or plain text. Targets: {violations!r}"
        )


def test_workflow_docs_excluded_from_external_tier_scan() -> None:
    paths = {p.resolve() for p in _iter_strict_markdown_files()}
    assert REPO_ROOT / "CONTRIBUTING.md" not in paths
    assert REPO_ROOT / "AGENTS.md" not in paths
    assert REPO_ROOT / "docs" / "COLLABORATION_TEAM.pt_BR.md" not in paths
    assert REPO_ROOT / "docs" / "TALENT_POOL_LEARNING_PATHS.md" not in paths
    assert REPO_ROOT / "docs" / "TALENT_POOL_LEARNING_PATHS.pt_BR.md" not in paths


def test_forbidden_url_detector() -> None:
    assert _forbidden_plan_url("plans/PLAN_X.md")
    assert _forbidden_plan_url("../plans/PLANS_TODO.md")
    assert _forbidden_plan_url("docs/plans/foo.md")
    assert _forbidden_plan_url(".cursor/plans/foo.md")
    assert not _forbidden_plan_url("README.md")
    assert not _forbidden_plan_url("ops/COMMIT_AND_PR.md")
