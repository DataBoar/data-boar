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


def test_published_sync_cites_release_tag_for_pyproject_version() -> None:
    """Docs must name ``v{pyproject.version}`` when that tag exists locally."""
    version, _ = _pyproject()
    expected_tag = f"v{version}"
    local_tags = {
        ln.strip()
        for ln in subprocess.run(
            ["git", "tag", "-l", "v*"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.splitlines()
        if ln.strip()
    }
    if expected_tag not in local_tags:
        pytest.skip(f"tag {expected_tag} not present locally (bump ritual in progress)")
    for path in (SYNC_EN, SYNC_PT):
        text = path.read_text(encoding="utf-8")
        assert expected_tag in text, (
            f"{path.name} must cite GitHub Release tag {expected_tag}"
        )
    # Newest local v* should not silently leap ahead of the sync table.
    latest = _latest_v_tag()
    if latest != expected_tag:
        pytest.fail(
            f"latest local tag is {latest} but pyproject is {version}; "
            "refresh PUBLISHED_SYNC or finish the tag ritual"
        )


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
    assert version in body, f"PyPI simple index missing {version}"

    hub_url = (
        f"https://hub.docker.com/v2/repositories/fabioleitao/data_boar/tags/{version}"
    )
    try:
        with urllib.request.urlopen(hub_url, timeout=20) as resp:  # noqa: S310
            hub_body = resp.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError) as exc:
        pytest.skip(f"Docker Hub unreachable: {exc}")
    assert "name" in hub_body and version in hub_body
