"""Pro-floor gates for optional scan extras (#854 remaining / #1876).

OCR, rich-media extras, and data-soup extras follow ``docs/SUBSCRIPTION_TIERS.md``
(Pro or higher). OPEN (enforcement off) still bypasses via ``is_feature_available``.
Computer-vision beyond OCR is not in the product; do not add keys for it.
"""

from __future__ import annotations

from core.licensing.guard import get_license_guard
from core.licensing.tier_features import is_feature_available

# Extra-backed columnar/binary formats in ``connectors.data_soup_formats``
# (pyarrow / fastavro / dbfread). EPUB stays Community (stdlib ZIP).
DATA_SOUP_EXTRA_EXTENSIONS = frozenset(
    {".parquet", ".feather", ".orc", ".avro", ".dbf"}
)


def ocr_images_allowed() -> bool:
    return is_feature_available(
        "ocr_images", get_license_guard().product_tier_for_features()
    )


def rich_media_metadata_allowed() -> bool:
    return is_feature_available(
        "rich_media_metadata", get_license_guard().product_tier_for_features()
    )


def data_soup_formats_allowed() -> bool:
    return is_feature_available(
        "data_soup_formats", get_license_guard().product_tier_for_features()
    )


def effective_rich_media_flags(metadata: bool, image_ocr: bool) -> tuple[bool, bool]:
    """Return config flags only when the runtime tier allows those extras."""
    return (
        bool(metadata) and rich_media_metadata_allowed(),
        bool(image_ocr) and ocr_images_allowed(),
    )
