"""Tests for core.learned_patterns: collect_learned_entries and write_learned_patterns."""

from core.learned_patterns import collect_learned_entries, write_learned_patterns


def test_collect_includes_high_with_pattern():
    db = [
        {
            "column_name": "cpf_cliente",
            "sensitivity_level": "HIGH",
            "pattern_detected": "LGPD_CPF",
            "norm_tag": "LGPD",
            "ml_confidence": 85,
        },
    ]
    entries = collect_learned_entries(
        db, [], min_sensitivity="HIGH", min_confidence=70, require_pattern=True
    )
    assert len(entries) == 1
    assert entries[0]["text"] == "cpf_cliente"
    assert entries[0]["label"] == "sensitive"


def test_collect_excludes_low():
    db = [
        {
            "column_name": "item_count",
            "sensitivity_level": "LOW",
            "pattern_detected": "GENERAL",
            "norm_tag": "",
            "ml_confidence": 10,
        },
    ]
    entries = collect_learned_entries(db, [], min_sensitivity="HIGH")
    assert len(entries) == 0


def test_collect_excludes_generic_term():
    db = [
        {
            "column_name": "id",
            "sensitivity_level": "HIGH",
            "pattern_detected": "ML_DETECTED",
            "norm_tag": "LGPD",
            "ml_confidence": 80,
        },
    ]
    entries = collect_learned_entries(
        db, [], min_sensitivity="HIGH", exclude_generic=True
    )
    assert len(entries) == 0


def test_collect_excludes_when_require_pattern_and_general():
    db = [
        {
            "column_name": "custom_field",
            "sensitivity_level": "HIGH",
            "pattern_detected": "GENERAL",
            "norm_tag": "",
            "ml_confidence": 90,
        },
    ]
    entries = collect_learned_entries(
        db, [], min_sensitivity="HIGH", require_pattern=True
    )
    assert len(entries) == 0
    entries2 = collect_learned_entries(
        db, [], min_sensitivity="HIGH", require_pattern=False
    )
    assert len(entries2) == 1


def test_collect_medium_when_min_sensitivity_medium():
    db = [
        {
            "column_name": "possible_pii",
            "sensitivity_level": "MEDIUM",
            "pattern_detected": "ML_POTENTIAL",
            "norm_tag": "Potential",
            "ml_confidence": 55,
        },
    ]
    entries = collect_learned_entries(
        db, [], min_sensitivity="MEDIUM", min_confidence=50, require_pattern=True
    )
    assert len(entries) == 1
    assert entries[0]["text"] == "possible_pii"


def test_collect_filesystem_extracts_table_column():
    fs = [
        {
            "file_name": "/path/to/data.db | users.cpf",
            "sensitivity_level": "HIGH",
            "pattern_detected": "LGPD_CPF",
            "norm_tag": "LGPD",
            "ml_confidence": 82,
        },
    ]
    entries = collect_learned_entries([], fs, min_sensitivity="HIGH")
    assert len(entries) == 1
    assert entries[0]["text"] == "users.cpf"


def test_collect_filesystem_skips_bare_filename():
    """#1259: generic filenames must not become learned ML terms."""
    fs = [
        {
            "file_name": "/repo/main.yml",
            "sensitivity_level": "HIGH",
            "pattern_detected": "DOB_POSSIBLE_MINOR",
            "norm_tag": "Minor",
            "ml_confidence": 82,
        },
        {
            "file_name": "CONTRIBUTORS.txt",
            "sensitivity_level": "HIGH",
            "pattern_detected": "ML_POTENTIAL_ENTERTAINMENT",
            "norm_tag": "",
            "ml_confidence": 90,
        },
    ]
    entries = collect_learned_entries([], fs, min_sensitivity="HIGH")
    assert entries == []


def test_write_learned_patterns_disabled_returns_none(tmp_path):
    class MockDB:
        def get_findings(self, session_id):
            return (
                [
                    {
                        "column_name": "cpf",
                        "sensitivity_level": "HIGH",
                        "pattern_detected": "CPF",
                        "norm_tag": "LGPD",
                        "ml_confidence": 90,
                    }
                ],
                [],
                [],
            )

    config = {"learned_patterns": {"enabled": False}, "ml_patterns_file": ""}
    out = write_learned_patterns(MockDB(), "s1", config)
    assert out is None


def test_write_learned_patterns_writes_yaml(tmp_path):
    class MockDB:
        def get_findings(self, session_id):
            return (
                [
                    {
                        "column_name": "cpf_cliente",
                        "sensitivity_level": "HIGH",
                        "pattern_detected": "LGPD_CPF",
                        "norm_tag": "LGPD",
                        "ml_confidence": 88,
                    }
                ],
                [],
                [],
            )

    out_file = tmp_path / "learned.yaml"
    config = {
        "learned_patterns": {
            "enabled": True,
            "output_file": str(out_file),
            "append": False,
        },
        "ml_patterns_file": "",
    }
    out = write_learned_patterns(MockDB(), "s1", config)
    assert out == str(out_file)
    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "cpf_cliente" in content
    assert "sensitive" in content


def test_write_learned_patterns_resolves_relative_output_against_report_dir(tmp_path):
    """#1260: relative output_file lands under report.output_dir, not cwd."""

    class MockDB:
        def get_findings(self, session_id):
            return (
                [
                    {
                        "column_name": "cpf_cliente",
                        "sensitivity_level": "HIGH",
                        "pattern_detected": "LGPD_CPF",
                        "norm_tag": "LGPD",
                        "ml_confidence": 88,
                    }
                ],
                [],
                [],
            )

    report_dir = tmp_path / "reports" / "demo"
    report_dir.mkdir(parents=True)
    config = {
        "report": {"output_dir": str(report_dir)},
        "learned_patterns": {
            "enabled": True,
            "output_file": "learned_patterns.yaml",
            "append": False,
        },
        "ml_patterns_file": "",
    }
    out = write_learned_patterns(MockDB(), "s1", config)
    expected = report_dir / "learned_patterns.yaml"
    assert out == str(expected)
    assert expected.exists()


def test_write_learned_patterns_keeps_absolute_output_path(tmp_path):
    """#1260: explicit absolute output_file is not rewritten under report.output_dir."""

    class MockDB:
        def get_findings(self, session_id):
            return (
                [
                    {
                        "column_name": "cpf_cliente",
                        "sensitivity_level": "HIGH",
                        "pattern_detected": "LGPD_CPF",
                        "norm_tag": "LGPD",
                        "ml_confidence": 88,
                    }
                ],
                [],
                [],
            )

    absolute_out = tmp_path / "custom" / "learned.yaml"
    config = {
        "report": {"output_dir": str(tmp_path / "reports")},
        "learned_patterns": {
            "enabled": True,
            "output_file": str(absolute_out),
            "append": False,
        },
        "ml_patterns_file": "",
    }
    out = write_learned_patterns(MockDB(), "s1", config)
    assert out == str(absolute_out)
    assert absolute_out.exists()
