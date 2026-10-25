from core.archives import (
    default_compressed_extensions,
    detect_archive_type,
    is_7z_magic,
    is_bzip2_magic,
    is_gzip_magic,
    is_supported_archive,
    is_xz_magic,
    is_zip_magic,
    normalize_compressed_extensions,
    read_magic,
)


def test_default_and_normalize_extensions_cover_tier1_and_tier2():
    exts = default_compressed_extensions()
    # A few key extensions we expect to be present
    for expected in (".zip", ".tar", ".gz", ".tgz", ".bz2", ".xz", ".7z"):
        assert expected in exts

    custom = normalize_compressed_extensions(["zip", "*.tar.gz", ".TGZ", ""])
    assert ".zip" in custom
    assert ".tar.gz" in custom
    assert ".tgz" in custom


def test_magic_helpers_match_known_signatures():
    assert is_zip_magic(b"PK\x03\x04rest")
    assert is_zip_magic(b"PK\x05\x06rest")
    assert is_zip_magic(b"PK\x07\x08rest")
    assert is_gzip_magic(b"\x1f\x8brest")
    assert is_bzip2_magic(b"BZhrest")
    assert is_xz_magic(b"\xfd7zXZ\x00rest")
    assert is_7z_magic(b"7z\xbc\xaf'\x1crest")


def test_read_magic_and_detection_roundtrip(tmp_path):
    # ZIP (PK\x03\x04)
    zip_path = tmp_path / "test.zip"
    zip_path.write_bytes(b"PK\x03\x04dummy")
    assert is_zip_magic(read_magic(zip_path))
    assert detect_archive_type(zip_path) == "zip"

    # Gzip
    gz_path = tmp_path / "test.gz"
    gz_path.write_bytes(b"\x1f\x8brest")
    assert is_gzip_magic(read_magic(gz_path))
    assert detect_archive_type(gz_path) == "gz"

    # Bzip2
    bz2_path = tmp_path / "test.bz2"
    bz2_path.write_bytes(b"BZhrest")
    assert is_bzip2_magic(read_magic(bz2_path))
    assert detect_archive_type(bz2_path) == "bz2"

    # XZ
    xz_path = tmp_path / "test.xz"
    xz_path.write_bytes(b"\xfd7zXZ\x00rest")
    assert is_xz_magic(read_magic(xz_path))
    assert detect_archive_type(xz_path) == "xz"

    # 7z
    seven_path = tmp_path / "test.7z"
    seven_path.write_bytes(b"7z\xbc\xaf'\x1crest")
    assert is_7z_magic(read_magic(seven_path))
    assert detect_archive_type(seven_path) == "7z"


def test_tar_multi_suffix_detection(tmp_path):
    # tar.gz
    tgz = tmp_path / "archive.tar.gz"
    tgz.write_bytes(b"\x1f\x8brest")
    assert detect_archive_type(tgz) == "tar.gz"

    # tar.bz2
    tbz2 = tmp_path / "archive.tar.bz2"
    tbz2.write_bytes(b"BZhrest")
    assert detect_archive_type(tbz2) == "tar.bz2"

    # tar.xz
    txz = tmp_path / "archive.tar.xz"
    txz.write_bytes(b"\xfd7zXZ\x00rest")
    assert detect_archive_type(txz) == "tar.xz"

    # plain .tar: extension-based only
    tar_path = tmp_path / "archive.tar"
    tar_path.write_bytes(b"0" * 512)
    assert detect_archive_type(tar_path) == "tar"


def test_is_supported_archive_respects_extensions_and_magic(tmp_path):
    # Valid zip by both extension and magic
    zip_path = tmp_path / "good.zip"
    zip_path.write_bytes(b"PK\x03\x04rest")
    assert is_supported_archive(zip_path)

    # Wrong magic: looks like .zip but magic does not match
    bad_zip = tmp_path / "bad.zip"
    bad_zip.write_bytes(b"NOTZIP")
    assert not is_supported_archive(bad_zip)

    # Custom extension allow-list
    only_zip = [".zip"]
    assert is_supported_archive(zip_path, exts=only_zip)
    tar_path = tmp_path / "x.tar.gz"
    tar_path.write_bytes(b"\x1f\x8brest")
    assert not is_supported_archive(tar_path, exts=only_zip)
