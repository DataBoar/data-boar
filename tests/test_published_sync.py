"""Guard PUBLISHED_SYNC docs against version / org-path drift (#1392).

Offline core: pyproject version + maturity_build must appear in both language
files; GitHub links must use DataBoar/data-boar; local latest v* tag must be
cited. Optional network probes for PyPI / Docker Hub are skipif-gated so the
local gate (ADR-0080) never depends on the network.
"""

from __future__ import annotations

import os
import subprocess
import tomllib
import urllib.error
import urllib.request
from pathlib import Path

import pytest
from packaging.version import InvalidVersion, Version

REPO_ROOT = Path(__file__).resolve().parents[1]
SYNC_EN = REPO_ROOT / "docs" / "ops" / "today-mode" / "PUBLISHED_SYNC.md"
SYNC_PT = REPO_ROOT / "docs" / "ops" / "today-mode" / "PUBLISHED_SYNC.pt_BR.md"
DEAD_ORG = "FabioLeitao/data-boar"
LIVE_ORG = "DataBoar/data-boar"


def _pyproject() -> tuple[str, int]:
    with (REPO_ROOT / "pyproject.toml").open("rb") as f:
        data = tomllib.load(f)
    version = str(data["project"]["version"])
    maturity = int(data["tool"]["databoar"]["maturity_build"])
    return version, maturity


def _latest_v_tag() -> str:
    proc = subprocess.run(
        ["git", "tag", "-l", "v*", "--sort=-version:refname"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    tags = [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]
    assert tags, "expected at least one local v* tag"
    return tags[0]


@pytest.mark.parametrize("path", [SYNC_EN, SYNC_PT], ids=["en", "pt_BR"])
def test_published_sync_matches_pyproject_and_live_org(path: Path) -> None:
    assert path.is_file(), f"missing {path}"
    text = path.read_text(encoding="utf-8")
    version, maturity = _pyproject()

    assert version in text, f"{path.name} must cite pyproject version {version}"
    assert (
        f"maturity_build={maturity}" in text or f"maturity_build = {maturity}" in text
    ), f"{path.name} must cite maturity_build={maturity}"
    assert DEAD_ORG not in text, (
        f"{path.name} still links dead org path {DEAD_ORG!r}; use {LIVE_ORG}"
    )
    assert LIVE_ORG in text, f"{path.name} must link {LIVE_ORG}"


def _tag_key(tag: str) -> Version:
    return Version(tag.removeprefix("v"))


def _release_tags(tags: list[str]) -> list[str]:
    """Keep only PEP 440 release tags (ignores labels such as ``v1.7.2-safe``)."""
    out: list[str] = []
    for tag in tags:
        try:
            _tag_key(tag)
        except InvalidVersion:
            continue
        out.append(tag)
    return out


def _release_tag_sync_problems(
    version: str, local_tags: list[str], docs: dict[str, str]
) -> list[str]:
    """Return drift problems between pyproject, local ``v*`` tags and the sync docs.

    * Tag ``v{version}`` exists: both docs cite it and it is the newest tag.
    * Tag missing (bump ritual in progress: the tag is cut with the release): the
      newest existing tag must be older than ``version`` and both docs must cite it.
      The condition is asserted, not skipped, so it never eats the CI skip ceiling.
    """
    expected = f"v{version}"
    tags = sorted(_release_tags(local_tags), key=_tag_key)
    latest = tags[-1]
    problems: list[str] = []
    if expected in tags:
        cited = expected
        if latest != expected:
            problems.append(
                f"latest local tag is {latest} but pyproject is {version}; "
                "refresh PUBLISHED_SYNC or finish the tag ritual"
            )
    else:
        cited = latest
        if _tag_key(latest) > _tag_key(expected):
            problems.append(
                f"latest local tag {latest} is newer than pyproject {version} "
                f"and tag {expected} does not exist; pyproject is behind the tags"
            )
    for name, text in docs.items():
        if cited not in text:
            problems.append(f"{name} must cite GitHub Release tag {cited}")
    return problems


def test_published_sync_cites_release_tag_for_pyproject_version() -> None:
    """Docs cite ``v{pyproject.version}``, or the newest tag while the bump is in progress."""
    version, _ = _pyproject()
    local_tags = [
        ln.strip()
        for ln in subprocess.run(
            ["git", "tag", "-l", "v*"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.splitlines()
        if ln.strip()
    ]
    if not _release_tags(local_tags):
        pytest.skip(
            "no local PEP 440 v* tags (shallow clone without tags); nothing to compare"
        )
    docs = {path.name: path.read_text(encoding="utf-8") for path in (SYNC_EN, SYNC_PT)}
    problems = _release_tag_sync_problems(version, local_tags, docs)
    assert not problems, "\n".join(problems)


@pytest.mark.skipif(
    os.environ.get("DATABOAR_PUBLISHED_SYNC_NETWORK") != "1",
    reason="set DATABOAR_PUBLISHED_SYNC_NETWORK=1 to probe PyPI/Hub",
)
def test_published_sync_optional_network_py_pi_and_hub() -> None:
    version, _ = _pyproject()
    # PyPI simple API — confirm the project lists this version.
    req = urllib.request.Request(
        "https://pypi.org/simple/data-boar/",
        headers={"Accept": "application/vnd.pypi.simple.v1+json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:  # noqa: S310
            body = resp.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError) as exc:
        pytest.skip(f"PyPI unreachable: {exc}")
    else:
        assert version in body, f"PyPI simple index missing {version}"

    hub_url = (
        f"https://hub.docker.com/v2/repositories/fabioleitao/data_boar/tags/{version}"
    )
    try:
        with urllib.request.urlopen(hub_url, timeout=20) as resp:  # noqa: S310
            hub_body = resp.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError) as exc:
        pytest.skip(f"Docker Hub unreachable: {exc}")
    else:
        assert "name" in hub_body and version in hub_body


# --- release-tag sync rules (#2240): the bump ritual must be asserted, not skipped ---------


def _docs_citing(*tags: str) -> dict[str, str]:
    body = " ".join(
        f"[{t}](https://github.com/{LIVE_ORG}/releases/tag/{t})" for t in tags
    )
    return {"PUBLISHED_SYNC.md": body, "PUBLISHED_SYNC.pt_BR.md": body}


def test_tag_sync_tag_exists_and_cited_is_clean() -> None:
    assert (
        _release_tag_sync_problems(
            "1.8.1", ["v1.8.0", "v1.8.1"], _docs_citing("v1.8.1")
        )
        == []
    )


def test_tag_sync_tag_exists_but_not_cited_is_a_problem() -> None:
    problems = _release_tag_sync_problems(
        "1.8.1", ["v1.8.0", "v1.8.1"], _docs_citing("v1.8.0")
    )
    assert any("v1.8.1" in p and "PUBLISHED_SYNC.md" in p for p in problems)


def test_tag_sync_tag_exists_but_newer_tag_leaps_ahead() -> None:
    problems = _release_tag_sync_problems(
        "1.8.1", ["v1.8.1", "v1.8.2"], _docs_citing("v1.8.1")
    )
    assert any("v1.8.2" in p for p in problems)


def test_tag_sync_bump_in_progress_checks_latest_existing_tag() -> None:
    """pyproject 1.8.1 ahead of the newest tag v1.8.0: verified, not skipped."""
    assert (
        _release_tag_sync_problems(
            "1.8.1", ["v1.7.4", "v1.8.0"], _docs_citing("v1.8.0")
        )
        == []
    )


def test_tag_sync_bump_in_progress_docs_must_cite_latest_existing_tag() -> None:
    problems = _release_tag_sync_problems("1.8.1", ["v1.8.0"], _docs_citing("v1.7.4"))
    assert any("v1.8.0" in p and "PUBLISHED_SYNC" in p for p in problems)


def test_tag_sync_bump_in_progress_tag_ahead_of_pyproject_is_a_problem() -> None:
    """A tag newer than pyproject while the pyproject tag is missing is drift."""
    problems = _release_tag_sync_problems("1.8.1", ["v1.8.2"], _docs_citing("v1.8.2"))
    assert any("v1.8.2" in p and "1.8.1" in p for p in problems)
