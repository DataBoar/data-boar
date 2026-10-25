"""Structural consistency audit for compliance samples (#412).

Does not edit tests/test_compliance_samples.py (platitude / seed-gate file).
The issue's required keys ``regex_patterns`` / ``ml_patterns`` are the plugin
schema names — samples use ``regex`` / ``terms`` (detector + report contract).
"""

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLES_DIR = REPO_ROOT / "docs" / "compliance-samples"
_ALLOWED_PRIORITIES = frozenset({"CRÍTICA", "ALTA", "MÉDIA", "INFORMATIVO"})


def _sample_paths() -> list[Path]:
    return sorted(SAMPLES_DIR.glob("compliance-sample-*.yaml"))


@pytest.mark.parametrize("sample_path", _sample_paths(), ids=lambda p: p.name)
def test_sample_has_header_comment(sample_path: Path):
    first = next(
        (
            ln
            for ln in sample_path.read_text(encoding="utf-8").splitlines()
            if ln.strip()
        ),
        "",
    )
    assert first.startswith("#"), f"{sample_path.name}: missing leading header comment"


@pytest.mark.parametrize("sample_path", _sample_paths(), ids=lambda p: p.name)
def test_sample_has_all_three_sections(sample_path: Path):
    data = yaml.safe_load(sample_path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    for key in ("regex", "terms", "recommendation_overrides"):
        assert data.get(key), f"{sample_path.name}: missing non-empty {key}"


@pytest.mark.parametrize("sample_path", _sample_paths(), ids=lambda p: p.name)
def test_sample_override_priorities_are_canonical(sample_path: Path):
    data = yaml.safe_load(sample_path.read_text(encoding="utf-8"))
    for i, row in enumerate(data.get("recommendation_overrides") or []):
        pri = row.get("priority")
        assert pri in _ALLOWED_PRIORITIES, (
            f"{sample_path.name}[{i}] priority={pri!r} "
            f"(expected one of {sorted(_ALLOWED_PRIORITIES)})"
        )
