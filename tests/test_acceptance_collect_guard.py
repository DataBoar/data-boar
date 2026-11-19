"""The prospect acceptance suite is not collected without ``PROSPECT_TEST_IMAGE``.

Its tests skip when the image is missing, and 18 skips push the ``test-extras`` job past the
skip ceiling (60). ``tests/acceptance/conftest.py`` ignores that one file at collection time,
so nothing is counted as skipped. An explicit path on the command line is still collected.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ACCEPTANCE = "tests/acceptance/test_demo_prospect_acceptance.py"


def _collect(*args: str, image: str | None) -> str:
    env = {k: v for k, v in os.environ.items() if k != "PROSPECT_TEST_IMAGE"}
    if image is not None:
        env["PROSPECT_TEST_IMAGE"] = image
    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "--collect-only",
            "-q",
            "-o",
            "addopts=",
            "-p",
            "no:cacheprovider",
            *args,
        ],
        cwd=REPO,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
    )
    return res.stdout


def test_acceptance_file_is_not_collected_without_the_image() -> None:
    assert "test_demo_prospect_acceptance" not in _collect(
        "tests/acceptance", image=None
    )


def test_acceptance_file_is_collected_with_the_image() -> None:
    out = _collect("tests/acceptance", image="localhost/data_boar:test")
    assert out.count("test_demo_prospect_acceptance.py::") >= 17


def test_explicit_path_is_still_collected_without_the_image() -> None:
    out = _collect(ACCEPTANCE, image=None)
    assert out.count("test_demo_prospect_acceptance.py::") >= 17
