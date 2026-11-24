"""Pure helpers for image/blob column detection (issue #2362, D2362-1..D2362-9)."""

from __future__ import annotations

import base64
import random

import pytest

from core.image_blob import (
    IMAGE_BASE64_PATTERN,
    IMAGE_BLOB_PATTERN,
    PROBE_PREFIX_BYTES,
    cell_to_bytes,
    column_name_suggests_image,
    column_type_family,
    decode_base64_prefix,
    image_finding_fields,
    normalize_image_blob_config,
    sniff_image_kind,
)


@pytest.mark.parametrize(
    ("type_str", "expected"),
    [
        ("BLOB", "binary"),
        ("longblob", "binary"),
        ("MEDIUMBLOB", "binary"),
        ("TINYBLOB", "binary"),
        ("BYTEA", "binary"),
        ("VARBINARY(max)", "binary"),
        ("VARBINARY(8000)", "binary"),
        ("IMAGE", "binary"),
        ("RAW(2000)", "binary"),
        ("BINARY(255)", "binary"),
        ("BINARY(16)", "other"),
        ("RAW(16)", "other"),
        ("VARBINARY(32)", "other"),
        ("LONG RAW", "other"),
        ("NUMERIC(16)", "other"),
        ("NULL", "other"),
        ("INTEGER", "other"),
        ("DATETIME", "other"),
        ("TEXT", "text"),
        ("VARCHAR(255)", "text"),
        ("NVARCHAR(max)", "text"),
        ("CLOB", "text"),
        ("NCLOB", "text"),
        ("VARCHAR2(4000 CHAR)", "text"),
        ("LONGTEXT", "text"),
        ("NTEXT", "text"),
        ("CHARACTER VARYING(100)", "text"),
    ],
)
def test_D2362_1_column_type_family(type_str: str, expected: str) -> None:
    assert column_type_family(type_str) == expected


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("foto_documento", True),
        ("fotoDocumento", True),
        ("AVATAR", True),
        ("img", True),
        ("attachments", True),
        ("anexo", True),
        ("scan_frente", True),
        ("documentos", True),
        ("status", False),
        ("photographer", False),
        ("imagination", False),
        ("description", False),
        ("doc_id", False),
    ],
)
def test_D2362_2_column_name_suggests_image(name: str, expected: bool) -> None:
    assert column_name_suggests_image(name) is expected


def test_D2362_3_sniff_image_kind_positive() -> None:
    assert sniff_image_kind(bytes.fromhex("ffd8ffe0") + b"\x00" * 4) == "jpeg"
    assert sniff_image_kind(b"\x89PNG\r\n\x1a\n") == "png"
    assert sniff_image_kind(b"GIF87a") == "gif"
    assert sniff_image_kind(b"GIF89a") == "gif"
    assert sniff_image_kind(b"RIFF\x00\x00\x00\x00WEBP") == "webp"
    assert sniff_image_kind(b"II*\x00") == "tiff"
    assert sniff_image_kind(b"MM\x00*") == "tiff"
    assert sniff_image_kind(b"\x00\x00\x00\x18ftypheic\x00\x00") == "heic"
    assert sniff_image_kind(b"%PDF-1.7\n") == "pdf"
    bmp = bytearray(b"BM")
    bmp += (54 + 40).to_bytes(4, "little")
    bmp += b"\0\0\0\0"
    bmp += (54).to_bytes(4, "little")
    bmp += (40).to_bytes(4, "little")
    bmp += b"\0" * 8
    assert sniff_image_kind(bytes(bmp)) == "bmp"


@pytest.mark.parametrize(
    "prefix",
    [
        b"BM",
        b"BM" + b"\x01" * 16,
        b"ID3" + b"\x00" * 4,
        b"fLaC" + b"\x00",
        b"OggS" + b"\x00",
        b"\x00\x00\x00\x18ftypisom\x00",
        b"",
        b"\x00" * 3,
        bytes(random.Random(1729).randrange(256) for _ in range(64)),
        b"\x00" * 64,
    ],
)
def test_D2362_4_sniff_image_kind_negative(prefix: bytes) -> None:
    assert sniff_image_kind(prefix) is None


def _jpeg_b64(n: int = 120) -> str:
    raw = bytes.fromhex("ffd8ffe0") + b"\x00" * 20
    return base64.b64encode(raw).decode("ascii")[:n].ljust(n, "A")


@pytest.mark.parametrize(
    "value",
    [
        "data:image/png;base64," + _jpeg_b64(120),
        "DATA:Image/PNG;BASE64," + _jpeg_b64(120),
        "data:image/png;base64,"
        + "\r\n".join(_jpeg_b64(152)[i : i + 76] for i in range(0, 152, 76)),
        base64.urlsafe_b64encode(bytes.fromhex("ffd8ffe0") + b"\x00" * 80).decode(
            "ascii"
        ),
        _jpeg_b64(200)[:200],
    ],
)
def test_D2362_5_decode_base64_prefix_positive(value: str) -> None:
    decoded = decode_base64_prefix(value, min_chars=100)
    assert decoded is not None
    assert sniff_image_kind(decoded) == "jpeg"


@pytest.mark.parametrize(
    "value",
    [
        "short",
        "data:image/png;base64," + "A" * 50,
        "AAAA " + "A" * 100,
        "Ab+c-d_e" * 20,
        "AAAA=" + "A" * 100,
        "data:text/plain,hello",
        base64.b64encode(b"hello world").decode(),
        "ffd8ffe0" + "00" * 50,
    ],
)
def test_D2362_6_decode_base64_prefix_negative(value: str) -> None:
    decoded = decode_base64_prefix(value, min_chars=100)
    if decoded is not None:
        assert sniff_image_kind(decoded) is None
    else:
        assert decoded is None


class _FakeLob:
    def __init__(self) -> None:
        self.calls: list[tuple[int, int]] = []

    def read(self, offset: int, amount: int) -> bytes:
        self.calls.append((offset, amount))
        return b"\xff\xd8\xff\xe0"


class _StrRaises:
    def __str__(self) -> str:
        raise RuntimeError("no str")

    def __repr__(self) -> str:
        raise RuntimeError("no repr")


def test_D2362_7_cell_to_bytes() -> None:
    assert cell_to_bytes(b"abc") == b"abc"
    assert cell_to_bytes(bytearray(b"x")) == b"x"
    assert cell_to_bytes(memoryview(b"y")) == b"y"
    lob = _FakeLob()
    assert cell_to_bytes(lob) == b"\xff\xd8\xff\xe0"
    assert lob.calls == [(1, PROBE_PREFIX_BYTES)]
    assert cell_to_bytes("x") is None
    assert cell_to_bytes(1) is None
    assert cell_to_bytes(None) is None
    assert cell_to_bytes(_StrRaises()) is None


def test_D2362_8_image_finding_fields() -> None:
    kinds = {"png", "jpeg"}
    fields = image_finding_fields(kinds, base64=False, name_hint=False)
    assert fields["pattern_detected"] == IMAGE_BLOB_PATTERN
    assert fields["sensitivity_level"] == "MEDIUM"
    assert "jpeg,png" in fields["norm_tag"]
    fields_b64 = image_finding_fields(kinds, base64=True, name_hint=True)
    assert fields_b64["pattern_detected"] == IMAGE_BASE64_PATTERN
    assert "column name suggests image" in fields_b64["norm_tag"]
    all_kinds = {"jpeg", "png", "gif", "bmp", "webp", "tiff", "heic", "pdf"}
    long_tag = image_finding_fields(all_kinds, base64=True, name_hint=True)["norm_tag"]
    assert len(long_tag) < 200


@pytest.mark.parametrize(
    ("raw", "expected_enabled", "expected_rows", "expected_min_chars"),
    [
        (None, False, 5, 100),
        ([], False, 5, 100),
        ({}, False, 5, 100),
        ({"enabled": "false"}, False, 5, 100),
        ({"enabled": "ON"}, True, 5, 100),
        ({"sampling_rows": 0}, False, 1, 100),
        ({"sampling_rows": 999}, False, 50, 100),
        ({"sampling_rows": "abc"}, False, 5, 100),
        ({"base64_min_chars": 10}, False, 5, 64),
        ({"base64_min_chars": 500}, False, 5, 150),
    ],
)
def test_D2362_9_normalize_image_blob_config(
    raw: object, expected_enabled: bool, expected_rows: int, expected_min_chars: int
) -> None:
    out = normalize_image_blob_config(raw)
    assert out["enabled"] is expected_enabled
    assert out["sampling_rows"] == expected_rows
    assert out["base64_min_chars"] == expected_min_chars
    assert set(out) == {"enabled", "sampling_rows", "base64_min_chars"}
