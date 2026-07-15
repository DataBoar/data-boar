"""
Tests for config and pattern file encoding: UTF-8, auto-detect fallback, pattern_files_encoding.

Ensures we do not regress when config or compliance samples use different character sets
(UTF-8, UTF-8 BOM, cp1252, Latin-1) in production.
"""

import tempfile
from pathlib import Path

import yaml

from config.loader import load_config, normalize_config


def test_load_config_utf8_with_unicode():
    """load_config loads YAML with Unicode comments and values (UTF-8)."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", encoding="utf-8", delete=False
    ) as f:
        yaml.dump(
            {
                "targets": [
                    {
                        "name": "Test",
                        "type": "filesystem",
                        "path": ".",
                        "recursive": True,
                    }
                ],
                "report": {"output_dir": "."},
                "file_scan": {},
                # Comment in content: 日本語 and café
            },
            f,
            default_flow_style=False,
            allow_unicode=True,
        )
        path = Path(f.name)
    try:
        # Overwrite with content that has Unicode in key/comment
        path.write_text(
            "# Config with 日本語 and café\n"
            "targets:\n  - name: Test\n    type: filesystem\n    path: .\n    recursive: true\n"
            "report:\n  output_dir: .\n"
            "pattern_files_encoding: utf-8\n",
            encoding="utf-8",
        )
        config = load_config(path)
        assert config.get("targets")
        assert config.get("pattern_files_encoding", "").lower() in ("utf-8", "")
    finally:
        path.unlink(missing_ok=True)


def test_load_config_auto_encoding_latin1_content():
    """load_config loads YAML saved as Latin-1 (auto-detection fallback)."""
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".yaml", delete=False) as f:
        # Minimal valid config with one Latin-1 character in comment
        f.write(
            b"# Caf\xe9\n"
            b"targets:\n  - name: Test\n    type: filesystem\n    path: .\n    recursive: true\n"
            b"report:\n  output_dir: .\n"
        )
        path = Path(f.name)
    try:
        config = load_config(path)
        assert config.get("targets")
        assert config.get("report", {}).get("output_dir") == "."
    finally:
        path.unlink(missing_ok=True)


def test_normalize_config_includes_pattern_files_encoding():
    """normalize_config sets pattern_files_encoding (default utf-8)."""
    out = normalize_config(
        {
            "targets": [],
            "report": {"output_dir": "."},
        }
    )
    assert out.get("pattern_files_encoding") == "utf-8"

    out2 = normalize_config(
        {
            "targets": [],
            "report": {"output_dir": "."},
            "pattern_files_encoding": "cp1252",
        }
    )
    assert out2.get("pattern_files_encoding") == "cp1252"


def test_normalize_config_max_inner_size_validation():
    """max_inner_size is clamped to 1 MB–500 MB; invalid or missing -> None."""
    out = normalize_config({"targets": [], "report": {"output_dir": "."}})
    assert out["file_scan"].get("max_inner_size") is None

    out2 = normalize_config(
        {
            "targets": [],
            "report": {"output_dir": "."},
            "file_scan": {"max_inner_size": 50_000_000},
        }
    )
    assert out2["file_scan"]["max_inner_size"] == 50_000_000

    out3 = normalize_config(
        {
            "targets": [],
            "report": {"output_dir": "."},
            "file_scan": {"max_inner_size": 500},  # below 1 MB
        }
    )
    assert out3["file_scan"]["max_inner_size"] == 1_000_000

    out4 = normalize_config(
        {
            "targets": [],
            "report": {"output_dir": "."},
            "file_scan": {"max_inner_size": 999_000_000},  # above 500 MB
        }
    )
    assert out4["file_scan"]["max_inner_size"] == 500_000_000

    out5 = normalize_config(
        {
            "targets": [],
            "report": {"output_dir": "."},
            "file_scan": {"max_inner_size": "not a number"},
        }
    )
    assert out5["file_scan"]["max_inner_size"] is None


def test_normalize_config_archive_budget_validation():
    """max_members / max_total_uncompressed / max_expansion_ratio clamp; invalid -> None."""
    out = normalize_config({"targets": [], "report": {"output_dir": "."}})
    assert out["file_scan"].get("max_members") is None
    assert out["file_scan"].get("max_total_uncompressed") is None
    assert out["file_scan"].get("max_expansion_ratio") is None

    out2 = normalize_config(
        {
            "targets": [],
            "report": {"output_dir": "."},
            "file_scan": {
                "max_members": 500,
                "max_total_uncompressed": 50_000_000,
                "max_expansion_ratio": 100,
            },
        }
    )
    assert out2["file_scan"]["max_members"] == 500
    assert out2["file_scan"]["max_total_uncompressed"] == 50_000_000
    assert out2["file_scan"]["max_expansion_ratio"] == 100.0

    out3 = normalize_config(
        {
            "targets": [],
            "report": {"output_dir": "."},
            "file_scan": {
                "max_members": 0,
                "max_total_uncompressed": 100,
                "max_expansion_ratio": 0.5,
            },
        }
    )
    assert out3["file_scan"]["max_members"] == 1
    assert out3["file_scan"]["max_total_uncompressed"] == 1_000_000
    assert out3["file_scan"]["max_expansion_ratio"] == 1.0

    out4 = normalize_config(
        {
            "targets": [],
            "report": {"output_dir": "."},
            "file_scan": {
                "max_members": "nope",
                "max_total_uncompressed": "x",
                "max_expansion_ratio": "y",
            },
        }
    )
    assert out4["file_scan"]["max_members"] is None
    assert out4["file_scan"]["max_total_uncompressed"] is None
    assert out4["file_scan"]["max_expansion_ratio"] is None


def test_normalize_config_file_sample_max_chars_default():
    """file_scan.file_sample_max_chars defaults for plain-text read budget; clamped when invalid."""
    out = normalize_config({"targets": [], "report": {"output_dir": "."}})
    assert out["file_scan"].get("file_sample_max_chars") == 12000

    out2 = normalize_config(
        {
            "targets": [],
            "report": {"output_dir": "."},
            "file_scan": {"file_sample_max_chars": 50_000},
        }
    )
    assert out2["file_scan"]["file_sample_max_chars"] == 50_000


def test_normalize_config_use_content_type():
    """file_scan.use_content_type is normalized (default False); engine/connectors receive it via target file_scan."""
    out = normalize_config({"targets": [], "report": {"output_dir": "."}})
    assert out["file_scan"].get("use_content_type") is False

    out2 = normalize_config(
        {
            "targets": [],
            "report": {"output_dir": "."},
            "file_scan": {"use_content_type": True},
        }
    )
    assert out2["file_scan"]["use_content_type"] is True

    out3 = normalize_config(
        {
            "targets": [],
            "report": {"output_dir": "."},
            "file_scan": {"use_content_type": False},
        }
    )
    assert out3["file_scan"]["use_content_type"] is False


def test_normalize_config_rich_media_and_ocr_keys():
    """file_scan rich-media flags and ocr_max_dimension clamp (256–8000)."""
    out = normalize_config({"targets": [], "report": {"output_dir": "."}})
    fs = out["file_scan"]
    assert fs.get("scan_rich_media_metadata") is False
    assert fs.get("scan_image_ocr") is False
    assert fs.get("ocr_lang") == "eng"
    assert fs.get("ocr_max_dimension") == 2000

    out2 = normalize_config(
        {
            "targets": [],
            "report": {"output_dir": "."},
            "file_scan": {
                "scan_rich_media_metadata": True,
                "scan_image_ocr": True,
                "ocr_lang": "por",
                "ocr_max_dimension": 99999,
            },
        }
    )
    fs2 = out2["file_scan"]
    assert fs2["scan_rich_media_metadata"] is True
    assert fs2["scan_image_ocr"] is True
    assert fs2["ocr_lang"] == "por"
    assert fs2["ocr_max_dimension"] == 8000

    out3 = normalize_config(
        {
            "targets": [],
            "report": {"output_dir": "."},
            "file_scan": {"ocr_max_dimension": 100},
        }
    )
    assert out3["file_scan"]["ocr_max_dimension"] == 256
