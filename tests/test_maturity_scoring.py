"""Rubric scoring for maturity YAML packs."""

from __future__ import annotations

from pathlib import Path

import pytest

from core.maturity_assessment.pack import load_maturity_pack
from core.maturity_assessment.scoring import (
    compute_rubric_score,
    rubric_result_to_summary_dict,
)


def test_compute_rubric_score_matches_sample_pack():
    p = (
        Path(__file__).resolve().parent
        / "fixtures"
        / "maturity_assessment"
        / "sample_pack.yaml"
    )
    pack = load_maturity_pack(p)
    # yes=2 + no=1 => 3; max per question 2+2=4 => 75%
    r = compute_rubric_score(
        pack,
        {"sample_dpo": "yes", "sample_policy": "no"},
    )
    assert r.has_rubric is True
    assert r.total == pytest.approx(3.0)
    assert r.maximum == pytest.approx(4.0)
    assert r.percentage == pytest.approx(75.0)
    assert len(r.lines) == 2


def test_unset_answer_uses_unset_weight():
    p = (
        Path(__file__).resolve().parent
        / "fixtures"
        / "maturity_assessment"
        / "sample_pack.yaml"
    )
    pack = load_maturity_pack(p)
    r = compute_rubric_score(pack, {"sample_dpo": "", "sample_policy": "na"})
    # unset+na: 0 + 1 = 1
    assert r.total == pytest.approx(1.0)


def test_rubric_result_to_summary_dict_percent_format():
    p = (
        Path(__file__).resolve().parent
        / "fixtures"
        / "maturity_assessment"
        / "sample_pack.yaml"
    )
    pack = load_maturity_pack(p)
    r = compute_rubric_score(pack, {"sample_dpo": "yes", "sample_policy": "yes"})
    d = rubric_result_to_summary_dict(r)
    assert d["has_rubric"] is True
    assert d["percentage_display"] == "100.0"
    assert d["total_display"] == "4"
    assert d["maximum_display"] == "4"


def test_all_zero_scores_has_no_rubric_percentage():
    from core.maturity_assessment.pack import (
        MaturityPack,
        MaturityQuestion,
        MaturitySection,
    )

    pack = MaturityPack(
        version=1,
        sections=(
            MaturitySection(
                id="s",
                title="T",
                questions=(MaturityQuestion(id="q1", prompt="p"),),
            ),
        ),
    )
    r = compute_rubric_score(pack, {"q1": "yes"})
    assert r.has_rubric is False
    assert r.percentage is None
    d = rubric_result_to_summary_dict(r)
    assert d["percentage_display"] == ""
