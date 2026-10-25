"""Tests for optional sql_sampling_file / sql_sampling_files config fragments."""

from pathlib import Path

import pytest
import yaml

from config.loader import load_config, normalize_config


def test_load_config_merges_sql_sampling_fragment_inline_wins(tmp_path: Path) -> None:
    frag = tmp_path / "sampling_extra.yaml"
    frag.write_text(
        yaml.dump(
            {
                "overrides": {
                    "targets": {"db_a": {"sample_limit": 3}},
                    "patterns": {"*_logs": 40},
                }
            },
            default_flow_style=False,
        ),
        encoding="utf-8",
    )
    root = tmp_path / "config.yaml"
    root.write_text(
        yaml.dump(
            {
                "targets": [],
                "report": {"output_dir": "."},
                "sql_sampling_file": "sampling_extra.yaml",
                "sql_sampling": {
                    "overrides": {
                        "targets": {"db_a": {"sample_limit": 9}},
                        "patterns": {"*_audit": 77},
                    }
                },
            },
            default_flow_style=False,
        ),
        encoding="utf-8",
    )
    cfg = load_config(root)
    sql = cfg["sql_sampling"]["overrides"]
    assert sql["targets"]["db_a"]["sample_limit"] == 9
    assert sql["patterns"]["*_audit"] == 77
    assert sql["patterns"]["*_logs"] == 40


def test_sql_sampling_files_order_later_file_wins(tmp_path: Path) -> None:
    (tmp_path / "a.yaml").write_text(
        yaml.dump({"overrides": {"patterns": {"t_*": 1}}}),
        encoding="utf-8",
    )
    (tmp_path / "b.yaml").write_text(
        yaml.dump({"overrides": {"patterns": {"t_*": 2}}}),
        encoding="utf-8",
    )
    root = tmp_path / "config.yaml"
    root.write_text(
        yaml.dump(
            {
                "targets": [],
                "report": {"output_dir": "."},
                "sql_sampling_files": ["a.yaml", "b.yaml"],
            }
        ),
        encoding="utf-8",
    )
    cfg = load_config(root)
    assert cfg["sql_sampling"]["overrides"]["patterns"]["t_*"] == 2


def test_normalize_config_without_path_does_not_expand_file(tmp_path: Path) -> None:
    """Programmatic normalize without config_path leaves paths as references only."""
    frag = tmp_path / "only_in_file.yaml"
    frag.write_text(yaml.dump({"overrides": {"patterns": {"x": 1}}}), encoding="utf-8")
    out = normalize_config(
        {
            "targets": [],
            "report": {"output_dir": "."},
            "sql_sampling_file": str(frag.name),
        }
    )
    assert out["sql_sampling"]["overrides"]["patterns"] == {}


def test_sql_sampling_file_path_escape_rejected(tmp_path: Path) -> None:
    root = tmp_path / "config.yaml"
    root.write_text(
        yaml.dump(
            {
                "targets": [],
                "report": {"output_dir": "."},
                "sql_sampling_file": "../evil.yaml",
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="escapes"):
        load_config(root)


def test_sql_sampling_file_absolute_path_outside_config_dir_rejected(
    tmp_path: Path,
) -> None:
    """#1550: absolute paths must still resolve under the config directory."""
    outside = tmp_path / "outside.yaml"
    outside.write_text(
        yaml.dump({"overrides": {"patterns": {"x": 1}}}), encoding="utf-8"
    )
    cfg_dir = tmp_path / "cfg"
    cfg_dir.mkdir()
    root = cfg_dir / "config.yaml"
    root.write_text(
        yaml.dump(
            {
                "targets": [],
                "report": {"output_dir": "."},
                "sql_sampling_file": str(outside),
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="escapes"):
        load_config(root)


def test_sql_sampling_file_absolute_path_inside_config_dir_ok(tmp_path: Path) -> None:
    frag = tmp_path / "sampling_extra.yaml"
    frag.write_text(
        yaml.dump({"overrides": {"patterns": {"inside_*": 2}}}),
        encoding="utf-8",
    )
    root = tmp_path / "config.yaml"
    root.write_text(
        yaml.dump(
            {
                "targets": [],
                "report": {"output_dir": "."},
                "sql_sampling_file": str(frag.resolve()),
            }
        ),
        encoding="utf-8",
    )
    cfg = load_config(root)
    assert cfg["sql_sampling"]["overrides"]["patterns"]["inside_*"] == 2


def test_sql_sampling_invalid_yaml_error_omits_file_snippet(tmp_path: Path) -> None:
    """Parse failures must not echo fragment body (YAML context / HTTP banner leak)."""
    sentinel = "DB_SQL_SAMPLING_PARSE_SENTINEL"
    frag = tmp_path / "broken.yaml"
    frag.write_text(f"{sentinel}: [unclosed\n", encoding="utf-8")
    root = tmp_path / "config.yaml"
    root.write_text(
        yaml.dump(
            {
                "targets": [],
                "report": {"output_dir": "."},
                "sql_sampling_file": "broken.yaml",
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="not valid YAML") as ei:
        load_config(root)
    msg = str(ei.value)
    assert sentinel not in msg
    assert ei.value.__cause__ is None


def test_get_effective_limit_alias() -> None:
    from core.sampling import SamplingProvider

    p = SamplingProvider.from_config(
        {
            "sql_sampling": {
                "overrides": {"targets": {"t": {"sample_limit": 4}}, "patterns": {}}
            }
        }
    )
    assert p.get_effective_limit("t", "any", global_limit=10) == 4
