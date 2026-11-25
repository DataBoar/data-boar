"""Pure helpers for image/blob column presence detection (#2362); no I/O."""

from __future__ import annotations

import base64
import binascii
import re
from typing import Final, Iterable, Literal

from core.rich_media_magic import infer_rich_media_suffix

ImageKind = Literal["jpeg", "png", "gif", "bmp", "webp", "tiff", "heic", "pdf"]
TypeFamily = Literal["binary", "text", "other"]

PROBE_PREFIX_BYTES: Final = 64
BASE64_PREFIX_CHARS: Final = 88
IMAGE_BLOB_PATTERN: Final = "IMAGE_BLOB_IN_COLUMN"
IMAGE_BASE64_PATTERN: Final = "IMAGE_BASE64_IN_COLUMN"
IMAGE_FINDING_LEVEL: Final = "MEDIUM"

_DEFAULT_ENABLED = False
_DEFAULT_SAMPLING_ROWS = 5
_DEFAULT_BASE64_MIN_CHARS = 100
_SAMPLING_ROWS_RANGE = (1, 50)
_BASE64_MIN_CHARS_RANGE = (64, 150)

_BINARY_TOKENS = frozenset(
    {
        "BLOB",
        "TINYBLOB",
        "MEDIUMBLOB",
        "LONGBLOB",
        "BYTEA",
        "VARBINARY",
        "BINARY",
        "IMAGE",
        "RAW",
    }
)

_NAME_TOKENS = frozenset(
    {
        "foto",
        "imagem",
        "photo",
        "image",
        "img",
        "picture",
        "thumbnail",
        "avatar",
        "documento",
        "attachment",
        "anexo",
        "scan",
        "selfie",
    }
)

_SUFFIX_TO_KIND: dict[str, ImageKind] = {
    ".jpg": "jpeg",
    ".jpeg": "jpeg",
    ".png": "png",
    ".gif": "gif",
    ".webp": "webp",
    ".tif": "tiff",
    ".tiff": "tiff",
    ".heic": "heic",
    ".heif": "heic",
}

_BMP_DIB_SIZES = frozenset({12, 40, 52, 56, 64, 108, 124})


def column_type_token(type_str: str) -> str:
    s = type_str.strip().upper()
    paren = s.find("(")
    if paren >= 0:
        s = s[:paren]
    return re.sub(r"\s+", " ", s).strip()


def _type_arg0(type_str: str) -> str | None:
    m = re.search(r"\(([^)]*)\)", type_str.strip(), re.IGNORECASE)
    if not m:
        return None
    return m.group(1).strip()


def column_type_family(type_str: str) -> TypeFamily:
    token = column_type_token(type_str)
    if token == "LONG RAW":
        return "other"
    arg0 = _type_arg0(type_str)
    if token in _BINARY_TOKENS:
        if arg0 is not None and arg0.isdigit() and int(arg0) < PROBE_PREFIX_BYTES:
            return "other"
        return "binary"
    if any(part in token for part in ("CHAR", "TEXT", "CLOB")):
        return "text"
    return "other"


def column_name_suggests_image(column_name: str) -> bool:
    s = re.sub(r"([a-z])([A-Z])", r"\1 \2", column_name)
    for raw in re.split(r"[^A-Za-z0-9]+", s):
        if not raw:
            continue
        tok = raw.lower()
        if tok.endswith("s") and len(tok) > 1:
            tok = tok[:-1]
        if tok in _NAME_TOKENS:
            return True
    return False


def sniff_image_kind(prefix: bytes) -> ImageKind | None:
    if len(prefix) >= 5 and prefix[:5] == b"%PDF-":
        return "pdf"
    suffix = infer_rich_media_suffix(prefix)
    if suffix == ".bmp":
        if len(prefix) < 18:
            return None
        if prefix[6:10] != b"\0\0\0\0":
            return None
        dib_size = int.from_bytes(prefix[14:18], "little")
        if dib_size not in _BMP_DIB_SIZES:
            return None
        return "bmp"
    if suffix in (".mp3", ".flac", ".ogg", ".mp4"):
        return None
    if suffix is None:
        return None
    return _SUFFIX_TO_KIND.get(suffix)


def decode_base64_prefix(value: str, *, min_chars: int) -> bytes | None:
    s = value.strip()
    if s[:5].lower() == "data:":
        head = s[:128]
        marker = ";base64,"
        pos = head.lower().find(marker)
        if pos < 0:
            return None
        s = s[pos + len(marker) :]
    s = s.replace("\r", "").replace("\n", "")
    if len(s) < min_chars:
        return None
    std_alphabet = set(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
    )
    url_alphabet = set(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_="
    )
    chars = set(s)
    if chars <= std_alphabet:
        decoder = base64.b64decode
    elif chars <= url_alphabet:
        decoder = base64.urlsafe_b64decode
    else:
        return None
    if "=" in s.rstrip("="):
        return None
    head = s[:BASE64_PREFIX_CHARS]
    head = head[: len(head) - (len(head) % 4)]
    if not head:
        return None
    try:
        if decoder is base64.b64decode:
            return decoder(head, validate=True)
        return decoder(head)
    except binascii.Error:
        return None


def cell_to_bytes(cell: object) -> bytes | None:
    if isinstance(cell, bytes):
        return cell
    if isinstance(cell, bytearray):
        return bytes(cell)
    if isinstance(cell, memoryview):
        return bytes(cell)
    read = getattr(cell, "read", None)
    if callable(read):
        data = read(1, PROBE_PREFIX_BYTES)
        if isinstance(data, bytes):
            return data
        return None
    return None


def image_finding_fields(
    kinds: Iterable[str], *, base64: bool, name_hint: bool
) -> dict[str, str]:
    joined = ",".join(sorted(set(kinds)))
    tag = f"Image/document stored in column ({joined}); content not read; confirm manually"
    if name_hint:
        tag += "; column name suggests image"
    return {
        "pattern_detected": IMAGE_BASE64_PATTERN if base64 else IMAGE_BLOB_PATTERN,
        "sensitivity_level": IMAGE_FINDING_LEVEL,
        "norm_tag": tag,
    }


def _truthy_enabled(raw: object) -> bool:
    if raw is True:
        return True
    if isinstance(raw, str) and raw.strip().lower() in {"1", "true", "yes", "on"}:
        return True
    return False


def _clamp_int(value: object, default: int, low: int, high: int) -> int:
    if not isinstance(value, (int, str)) or isinstance(value, bool):
        return default
    try:
        n = int(value)
    except ValueError:
        return default
    return max(low, min(high, n))


def normalize_image_blob_config(raw: object) -> dict[str, object]:
    if not isinstance(raw, dict):
        raw = {}
    low, high = _SAMPLING_ROWS_RANGE
    b_low, b_high = _BASE64_MIN_CHARS_RANGE
    return {
        "enabled": _truthy_enabled(raw.get("enabled")),
        "sampling_rows": _clamp_int(
            raw.get("sampling_rows"), _DEFAULT_SAMPLING_ROWS, low, high
        ),
        "base64_min_chars": _clamp_int(
            raw.get("base64_min_chars"), _DEFAULT_BASE64_MIN_CHARS, b_low, b_high
        ),
    }
