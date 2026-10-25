"""#1876: OCR / rich-media / data-soup extras are Pro-gated on the scan path."""

from __future__ import annotations

from pathlib import Path

import pytest

from connectors.filesystem_connector import FilesystemConnector, _read_text_sample
from core.licensing.guard import get_license_guard, reset_license_guard_for_tests
from core.licensing.tier_features import FEATURE_TIER_MAP, Tier, is_feature_available


@pytest.fixture(autouse=True)
def _clean_guard():
    reset_license_guard_for_tests()
    yield
    reset_license_guard_for_tests()


def _lab_tier(tier: str) -> None:
    get_license_guard({"licensing": {"mode": "open", "effective_tier": tier}})


def test_map_augmented_extras_are_pro() -> None:
    assert FEATURE_TIER_MAP["ocr_images"] is Tier.PRO
    assert FEATURE_TIER_MAP["rich_media_metadata"] is Tier.PRO
    assert FEATURE_TIER_MAP["data_soup_formats"] is Tier.PRO
    assert not is_feature_available("ocr_images", Tier.COMMUNITY)
    assert not is_feature_available("rich_media_metadata", Tier.COMMUNITY)
    assert not is_feature_available("data_soup_formats", Tier.COMMUNITY)
    assert is_feature_available("ocr_images", Tier.PRO)
    assert is_feature_available("data_soup_formats", Tier.OPEN)


def test_community_connector_drops_rich_media_flags() -> None:
    _lab_tier("community")
    c = FilesystemConnector(
        {
            "name": "fs",
            "path": ".",
            "file_scan": {
                "scan_rich_media_metadata": True,
                "scan_image_ocr": True,
            },
        },
        scanner=None,
        db_manager=None,
    )
    assert c.scan_rich_media_metadata is False
    assert c.scan_image_ocr is False


def test_pro_connector_keeps_rich_media_flags() -> None:
    _lab_tier("pro")
    c = FilesystemConnector(
        {
            "name": "fs",
            "path": ".",
            "file_scan": {
                "scan_rich_media_metadata": True,
                "scan_image_ocr": True,
            },
        },
        scanner=None,
        db_manager=None,
    )
    assert c.scan_rich_media_metadata is True
    assert c.scan_image_ocr is True


def test_community_skips_parquet_extract_via_read_text_sample(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _lab_tier("community")
    called = {"n": 0}

    def _boom(*_a, **_k):
        called["n"] += 1
        return "secret-column"

    monkeypatch.setattr(
        "connectors.data_soup_formats.sample_parquet_text",
        _boom,
    )
    p = tmp_path / "t.parquet"
    p.write_bytes(b"PAR1")
    assert _read_text_sample(p, ".parquet", 4000, {}) == ""
    assert called["n"] == 0


def test_pro_calls_parquet_extract(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _lab_tier("pro")
    monkeypatch.setattr(
        "connectors.data_soup_formats.sample_parquet_text",
        lambda *_a, **_k: "col_a alice",
    )
    p = tmp_path / "t.parquet"
    p.write_bytes(b"PAR1")
    assert "alice" in _read_text_sample(p, ".parquet", 4000, {})


def test_community_skips_ocr_extractor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _lab_tier("community")
    called = {"n": 0}

    def _boom(*_a, **_k):
        called["n"] += 1
        return "OCR-SECRET"

    monkeypatch.setattr(
        "connectors.rich_media_sample.build_rich_media_text_sample",
        _boom,
    )
    p = tmp_path / "x.png"
    p.write_bytes(b"\x89PNG\r\n")
    out = _read_text_sample(p, ".png", 4000, {}, scan_image_ocr=True)
    assert called["n"] == 0
    assert "OCR-SECRET" not in out


def test_epub_stays_community(tmp_path: Path) -> None:
    """EPUB is stdlib ZIP, not the dataformats extra."""
    _lab_tier("community")
    import io
    import zipfile

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr(
            "OEBPS/c.xhtml",
            '<?xml version="1.0"?><html xmlns="http://www.w3.org/1999/xhtml">'
            "<body><p>keep-epub</p></body></html>",
        )
    p = tmp_path / "b.epub"
    p.write_bytes(buf.getvalue())
    assert "keep-epub" in _read_text_sample(p, ".epub", 4000, {})
