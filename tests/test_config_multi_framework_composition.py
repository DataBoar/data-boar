"""#1319: regex_overrides_files / ml_patterns_files / compliance_frameworks composition."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from config.loader import load_config, normalize_config
from core.detector import SensitivityDetector, _load_regex_overrides

_SAMPLES = Path(__file__).resolve().parent.parent / "docs" / "compliance-samples"
_LGPD = _SAMPLES / "compliance-sample-lgpd.yaml"
_PCI = _SAMPLES / "compliance-sample-pci_dss.yaml"


def _manual_recommendation_merge(*files: Path) -> list[dict]:
    by_key: dict[str, dict] = {}
    order: list[str] = []
    for path in files:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for row in data.get("recommendation_overrides") or []:
            if not isinstance(row, dict):
                continue
            key = str(row.get("norm_tag_pattern") or "").strip()
            if not key:
                continue
            if key not in by_key:
                order.append(key)
            by_key[key] = dict(row)
    return [by_key[k] for k in order]


def test_singular_regex_overrides_file_still_loads(tmp_path: Path) -> None:
    sample = tmp_path / "one.yaml"
    sample.write_text(
        yaml.dump(
            {
                "regex": [
                    {
                        "name": "SOLO_ID",
                        "pattern": "solo[0-9]+",
                        "norm_tag": "Solo",
                    }
                ],
                "recommendation_overrides": [
                    {
                        "norm_tag_pattern": "Solo",
                        "base_legal": "solo-base",
                        "risk": "r",
                        "recommendation": "rec",
                        "priority": "P2",
                        "relevant_for": "test",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    root = tmp_path / "config.yaml"
    root.write_text(
        yaml.dump(
            {
                "targets": [],
                "report": {"output_dir": "."},
                "regex_overrides_file": "one.yaml",
            }
        ),
        encoding="utf-8",
    )
    cfg = load_config(root)
    assert cfg["regex_overrides_file"] == "one.yaml"
    assert len(cfg["regex_overrides_files"]) == 1
    assert Path(cfg["regex_overrides_files"][0]).name == "one.yaml"
    recs = cfg["report"]["recommendation_overrides"]
    assert recs[0]["norm_tag_pattern"] == "Solo"
    assert recs[0]["base_legal"] == "solo-base"
    det = SensitivityDetector(regex_overrides_path=cfg["regex_overrides_files"])
    assert "SOLO_ID" in det.patterns


def test_regex_overrides_files_later_name_wins(tmp_path: Path) -> None:
    (tmp_path / "a.yaml").write_text(
        yaml.dump(
            {
                "regex": [
                    {"name": "SAME", "pattern": "aaa", "norm_tag": "A"},
                    {"name": "ONLY_A", "pattern": "aaa2", "norm_tag": "A2"},
                ]
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "b.yaml").write_text(
        yaml.dump(
            {
                "regex": [
                    {"name": "SAME", "pattern": "bbb", "norm_tag": "B"},
                    {"name": "ONLY_B", "pattern": "bbb2", "norm_tag": "B2"},
                ]
            }
        ),
        encoding="utf-8",
    )
    root = tmp_path / "config.yaml"
    root.write_text(
        yaml.dump(
            {
                "targets": [],
                "report": {"output_dir": "."},
                "regex_overrides_files": ["a.yaml", "b.yaml"],
            }
        ),
        encoding="utf-8",
    )
    cfg = load_config(root)
    det = SensitivityDetector(regex_overrides_path=cfg["regex_overrides_files"])
    assert det.patterns["SAME"] == ("bbb", "B")
    assert det.patterns["ONLY_A"][1] == "A2"
    assert det.patterns["ONLY_B"][1] == "B2"


def test_two_frameworks_match_manual_yaml_merge() -> None:
    """Composed LGPD + PCI-DSS equals concatenating the two sample files by hand."""
    assert _LGPD.is_file() and _PCI.is_file()
    cfg = normalize_config(
        {
            "targets": [],
            "report": {"output_dir": "."},
            "compliance_frameworks": ["lgpd", "pci_dss"],
        }
    )
    expected_rec = _manual_recommendation_merge(_LGPD, _PCI)
    assert cfg["report"]["recommendation_overrides"] == expected_rec
    manual_regex = {}
    manual_regex.update(_load_regex_overrides(str(_LGPD)))
    manual_regex.update(_load_regex_overrides(str(_PCI)))
    det = SensitivityDetector(regex_overrides_path=cfg["regex_overrides_files"])
    for name, pair in manual_regex.items():
        assert det.patterns[name] == pair
    assert cfg["compliance_frameworks"] == ["lgpd", "pci_dss"]


def test_inline_recommendation_overrides_win_on_same_pattern(tmp_path: Path) -> None:
    sample = tmp_path / "fw.yaml"
    sample.write_text(
        yaml.dump(
            {
                "regex": [{"name": "X", "pattern": "x+", "norm_tag": "TagX"}],
                "recommendation_overrides": [
                    {
                        "norm_tag_pattern": "TagX",
                        "base_legal": "from-file",
                        "risk": "r",
                        "recommendation": "file",
                        "priority": "P3",
                        "relevant_for": "file",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    root = tmp_path / "config.yaml"
    root.write_text(
        yaml.dump(
            {
                "targets": [],
                "regex_overrides_file": "fw.yaml",
                "report": {
                    "output_dir": ".",
                    "recommendation_overrides": [
                        {
                            "norm_tag_pattern": "TagX",
                            "base_legal": "from-inline",
                            "risk": "r",
                            "recommendation": "inline",
                            "priority": "P1",
                            "relevant_for": "inline",
                        }
                    ],
                },
            }
        ),
        encoding="utf-8",
    )
    cfg = load_config(root)
    recs = [
        r
        for r in cfg["report"]["recommendation_overrides"]
        if r["norm_tag_pattern"] == "TagX"
    ]
    assert len(recs) == 1
    assert recs[0]["base_legal"] == "from-inline"


def test_unknown_compliance_framework_fails_closed() -> None:
    with pytest.raises(ValueError, match="Unknown compliance framework"):
        normalize_config(
            {
                "targets": [],
                "report": {"output_dir": "."},
                "compliance_frameworks": ["not_a_real_framework_zz"],
            }
        )


def test_invalid_framework_slug_rejected() -> None:
    with pytest.raises(ValueError, match="Invalid compliance_frameworks"):
        normalize_config(
            {
                "targets": [],
                "report": {"output_dir": "."},
                "compliance_frameworks": ["../etc"],
            }
        )
