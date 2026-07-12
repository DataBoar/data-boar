"""ADR governance Phase 1 anti-regression tests (issue #1162, ADR-0045).

T1 lifecycle · T2 locale/structure · T5 anti-deletion (rename-aware) · T6 date immutability.

Does not duplicate test_adr_inventory_sync or test_adr_readme_index_sync.
"""

from __future__ import annotations

import subprocess

import pytest

from tests.adr_governance_support import (
    ADR_DIR,
    GENESIS_FIXTURE,
    H1_RE,
    ISO_DATE_IN_DATE_LINE_RE,
    META_AUTHORS_RE,
    META_DATE_RE,
    META_DECIDERS_RE,
    NEW_ADR_ALLOWED_STATUSES,
    PT_BR_HEADING_DENYLIST,
    REPO_ROOT,
    extract_date_line,
    git_is_repo,
    governance_override_present,
    iter_adr_files,
    load_genesis_fixture,
    parse_status,
    read_adr_text,
    staged_adr_paths,
    staged_name_status_with_renames,
)


def test_t2_h1_uses_em_dash_title_form() -> None:
    """T2: H1 must be '# ADR NNNN — Title' (space + em dash), not filename hyphen."""
    violations: list[str] = []
    for path in iter_adr_files():
        lines = read_adr_text(path).split("\n")
        first = lines[0] if lines else ""
        if not H1_RE.match(first):
            violations.append(f"{path.name}: {first!r}")
    assert not violations, "ADR H1 violations:\n" + "\n".join(violations)


def test_t2_metadata_labels_exact_anchored() -> None:
    """T2: metadata labels are exact anchored tokens (not a loose 'Data*' prefix)."""
    violations: list[str] = []
    for path in iter_adr_files():
        text = read_adr_text(path)
        if not META_DATE_RE.search(text):
            violations.append(f"{path.name}: missing '- **Date (UTC):**'")
        if not META_AUTHORS_RE.search(text):
            violations.append(f"{path.name}: missing '- **Authors:**'")
        if not META_DECIDERS_RE.search(text):
            violations.append(f"{path.name}: missing '- **Deciders:**'")
    assert not violations, "ADR metadata label violations:\n" + "\n".join(violations)


def test_t2_headings_free_of_pt_br_denylist() -> None:
    """T2: ## / ### headings must not use pt-BR section titles (ADR-0045 §7)."""
    violations: list[str] = []
    for path in iter_adr_files():
        for line in read_adr_text(path).split("\n"):
            if not (line.startswith("##") or line.startswith("###")):
                continue
            for label, pattern in PT_BR_HEADING_DENYLIST:
                if pattern.search(line):
                    violations.append(f"{path.name}: {label} in {line!r}")
    assert not violations, "pt-BR heading violations:\n" + "\n".join(violations)


def test_t6_genesis_date_lines_immutable_against_fixture() -> None:
    """T6: '- **Date (UTC):**' line must not change on later edits (frozen corpus)."""
    assert GENESIS_FIXTURE.is_file(), f"missing fixture: {GENESIS_FIXTURE}"
    baseline = load_genesis_fixture()
    adrs = {p.name for p in iter_adr_files()}
    violations: list[str] = []
    for name in sorted(adrs):
        path = ADR_DIR / name
        current = extract_date_line(read_adr_text(path))
        expected = baseline.get(name)
        if expected is None:
            violations.append(
                f"{name}: not in genesis fixture (add row when materializing)"
            )
            continue
        if current != expected:
            violations.append(f"{name}: expected {expected!r}, got {current!r}")
    extra = sorted(set(baseline) - adrs)
    if extra:
        violations.append(f"fixture lists removed ADRs: {extra}")
    assert not violations, "genesis Date (UTC) immutability violations:\n" + "\n".join(
        violations
    )


@pytest.mark.skipif(not git_is_repo(), reason="git required for incremental ADR gates")
def test_t1_new_staged_adrs_born_proposed_or_reserved() -> None:
    """T1: newly added ADRs in the index must have Status Proposed or Reserved."""
    if governance_override_present():
        pytest.skip("operator override marker present")
    violations: list[str] = []
    for rel in staged_adr_paths(diff_filter="A"):
        path = ADR_DIR / rel.split("/")[-1]
        if not path.is_file():
            path = REPO_ROOT / rel
        status = parse_status(read_adr_text(path))
        if status not in NEW_ADR_ALLOWED_STATUSES:
            violations.append(f"{rel}: Status={status!r} (want Proposed or Reserved)")
    assert not violations, "new ADR lifecycle violations:\n" + "\n".join(violations)


@pytest.mark.skipif(not git_is_repo(), reason="git required for incremental ADR gates")
def test_t5_staged_adr_deletions_blocked_rename_aware() -> None:
    """T5: true ADR erasure in the index is forbidden; renames/reformats are allowed."""
    if governance_override_present():
        pytest.skip("operator override marker present")
    renamed_sources = {
        old
        for status, old, new in staged_name_status_with_renames()
        if status.startswith("R") and new
    }
    violations: list[str] = []
    for status, old, _new in staged_name_status_with_renames():
        if status != "D":
            continue
        if old in renamed_sources:
            continue
        violations.append(old)
    assert not violations, (
        "ADR deletion blocked (ADR-0045 §1). True erasures in index:\n"
        + "\n".join(violations)
        + "\nUse status transition or rename (git mv); override only with "
        "ADR-Governance-Override-Approved-By: trailer."
    )


@pytest.mark.skipif(not git_is_repo(), reason="git required for incremental ADR gates")
def test_t6_staged_date_line_unchanged_for_existing_adrs() -> None:
    """T6: staged edits must not mutate '- **Date (UTC):**' on existing ADRs."""
    if governance_override_present():
        pytest.skip("operator override marker present")
    violations: list[str] = []
    for rel in staged_adr_paths():
        if rel in staged_adr_paths(diff_filter="A"):
            continue
        path = REPO_ROOT / rel
        if not path.is_file():
            continue
        proc_old = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "show", f"HEAD:{rel}"],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc_old.returncode != 0:
            continue
        old_line = extract_date_line(proc_old.stdout)
        new_line = extract_date_line(read_adr_text(path))
        if old_line and new_line and old_line != new_line:
            violations.append(f"{rel}: {old_line!r} -> {new_line!r}")
    assert not violations, "Date (UTC) immutability violations in index:\n" + "\n".join(
        violations
    )


@pytest.mark.skipif(not git_is_repo(), reason="git required for incremental ADR gates")
def test_t6_new_staged_adrs_have_parseable_iso_date() -> None:
    """T6: new ADRs must declare a parseable YYYY-MM-DD in the Date (UTC) line."""
    violations: list[str] = []
    for rel in staged_adr_paths(diff_filter="A"):
        path = REPO_ROOT / rel
        text = read_adr_text(path)
        if not ISO_DATE_IN_DATE_LINE_RE.search(text):
            violations.append(f"{rel}: no YYYY-MM-DD in '- **Date (UTC):**' line")
    assert not violations, "new ADR date violations:\n" + "\n".join(violations)


def test_phase1_corpus_file_count_matches_fixture() -> None:
    """Sanity: genesis fixture stays aligned with docs/adr/ADR-*.md count."""
    baseline = load_genesis_fixture()
    adrs = [p.name for p in iter_adr_files()]
    assert len(baseline) == len(adrs), (
        f"fixture rows={len(baseline)} adr files={len(adrs)}; "
        "regenerate tests/fixtures/adr_genesis_date_lines.json"
    )
