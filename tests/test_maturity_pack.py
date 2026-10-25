"""Maturity assessment YAML pack loader (architecture A)."""

from __future__ import annotations

from pathlib import Path

import pytest

from core.maturity_assessment.pack import load_maturity_pack


def test_load_sample_pack():
    p = (
        Path(__file__).resolve().parent
        / "fixtures"
        / "maturity_assessment"
        / "sample_pack.yaml"
    )
    pack = load_maturity_pack(p)
    assert pack.version == 1
    assert len(pack.sections) == 1
    assert pack.sections[0].id == "governance"
    assert len(pack.sections[0].questions) == 2
    q0, q1 = pack.sections[0].questions
    assert q0.score_yes == 2.0 and q0.score_no == 0.0
    assert q1.score_no == 1.0


def test_load_pack_rejects_duplicate_question_ids(tmp_path):
    bad = tmp_path / "dup.yaml"
    bad.write_text(
        "version: 1\n"
        "sections:\n"
        "  - id: a\n"
        '    title: "A"\n'
        "    questions:\n"
        "      - id: q1\n"
        '        prompt: "p1"\n'
        "  - id: b\n"
        '    title: "B"\n'
        "    questions:\n"
        "      - id: q1\n"
        '        prompt: "p2"\n',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="duplicate question id"):
        load_maturity_pack(bad)


def test_load_pack_rejects_empty_sections(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("version: 1\nsections: []\n", encoding="utf-8")
    with pytest.raises(ValueError, match="no valid sections"):
        load_maturity_pack(bad)
