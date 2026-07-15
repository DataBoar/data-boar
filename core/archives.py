"""
Helpers for detecting and classifying compressed files (archives).

Detection by extension + magic bytes; optional iteration over members for scanning
inner content (Phase 4). Used by filesystem/share connectors when scan_compressed
is enabled.
"""

from __future__ import annotations

import contextlib
import math
import zipfile
from collections.abc import Callable
from pathlib import Path
from typing import Iterable, Iterator

import tarfile

# scan_failures reasons for unreadable archive members (#828; shared taxonomy with SQL sampling_error).
SCAN_FAILURE_REASON_ENCRYPTED_NO_PASSWORD = "encrypted_no_password"
SCAN_FAILURE_REASON_WRONG_PASSWORD = "wrong_password"
SCAN_FAILURE_REASON_ARCHIVE_READ_ERROR = "archive_read_error"
SCAN_FAILURE_REASON_ARCHIVE_BUDGET_EXCEEDED = "archive_budget_exceeded"

MemberReadFailureCallback = Callable[[str, str, str], None]


# Tier 1 – stdlib-backed formats (see PLAN_COMPRESSED_FILES.md)
_TIER1_EXTENSIONS: set[str] = {
    ".zip",
    ".tar",
    ".gz",
    ".tgz",
    ".bz2",
    ".tbz2",
    ".xz",
    ".txz",
    ".tar.gz",
    ".tar.bz2",
    ".tar.xz",
}

# Tier 2 – 7z (optional py7zr dependency for actual extraction)
_TIER2_EXTENSIONS: set[str] = {
    ".7z",
}


def default_compressed_extensions() -> set[str]:
    """Return the default set of extensions treated as candidate archives."""

    return set(_TIER1_EXTENSIONS | _TIER2_EXTENSIONS)


def normalize_compressed_extensions(exts: Iterable[str] | None) -> set[str]:
    """
    Normalise a list of extensions into a set of lowercase suffixes with leading dot.

    If exts is falsy, return the default Tier 1 + Tier 2 set.
    """

    if not exts:
        return default_compressed_extensions()
    norm: set[str] = set()
    for e in exts:
        if not e:
            continue
        s = str(e).strip().lower().lstrip("*")
        if not s:
            continue
        if not s.startswith("."):
            s = f".{s}"
        norm.add(s)
    return norm


def read_magic(path: Path, n: int = 8) -> bytes:
    """Read the first n bytes of a file (best-effort; returns b'' on error)."""

    try:
        with path.open("rb") as f:
            return f.read(n)
    except OSError:
        return b""


def _has_prefix(data: bytes, prefix: bytes) -> bool:
    return bool(data) and data.startswith(prefix)


def is_zip_magic(data: bytes) -> bool:
    """ZIP: PK\\x03\\x04 (files) or PK\\x05\\x06 (empty) or PK\\x07\\x08 (spanned)."""

    return (
        data.startswith(b"PK\x03\x04")
        or data.startswith(b"PK\x05\x06")
        or data.startswith(b"PK\x07\x08")
    )


def is_gzip_magic(data: bytes) -> bool:
    """Gzip: 0x1f 0x8b."""

    return _has_prefix(data, b"\x1f\x8b")


def is_bzip2_magic(data: bytes) -> bool:
    """Bzip2: ASCII 'BZh'."""

    return _has_prefix(data, b"BZh")


def is_xz_magic(data: bytes) -> bool:
    """XZ: FD 37 7A 58 5A 00."""

    return _has_prefix(data, b"\xfd7zXZ\x00")


def is_7z_magic(data: bytes) -> bool:
    """7z: 37 7A BC AF 27 1C."""

    return _has_prefix(data, b"7z\xbc\xaf'\x1c")


def detect_archive_type(path: Path) -> str | None:
    """
    Best-effort archive type detection using extension + magic bytes.

    Returns one of: "zip", "tar", "tar.gz", "tar.bz2", "tar.xz", "gz", "bz2", "xz", "7z", or None.
    """

    suffixes = [s.lower() for s in path.suffixes]
    magic = read_magic(path, 8)

    # Multi-suffix tar.* first
    if suffixes[-2:] == [".tar", ".gz"] and is_gzip_magic(magic):
        return "tar.gz"
    if suffixes[-2:] == [".tar", ".bz2"] and is_bzip2_magic(magic):
        return "tar.bz2"
    if suffixes[-2:] == [".tar", ".xz"] and is_xz_magic(magic):
        return "tar.xz"

    # Single-suffix cases
    if suffixes and suffixes[-1] in {".tgz"} and is_gzip_magic(magic):
        return "tar.gz"
    if suffixes and suffixes[-1] in {".tbz2"} and is_bzip2_magic(magic):
        return "tar.bz2"
    if suffixes and suffixes[-1] in {".txz"} and is_xz_magic(magic):
        return "tar.xz"

    ext = suffixes[-1] if suffixes else ""
    if ext == ".zip" and is_zip_magic(magic):
        return "zip"
    if ext == ".gz" and is_gzip_magic(magic):
        return "gz"
    if ext == ".bz2" and is_bzip2_magic(magic):
        return "bz2"
    if ext == ".xz" and is_xz_magic(magic):
        return "xz"
    if ext == ".tar":
        # tarfile can validate headers later; here we only check extension.
        return "tar"
    if ext == ".7z" and is_7z_magic(magic):
        return "7z"

    return None


def is_supported_archive(path: Path, exts: Iterable[str] | None = None) -> bool:
    """
    Return True if path looks like a supported archive (by extension + magic bytes).

    exts allows passing a custom compressed_extensions list from config; when None,
    the default Tier 1 + Tier 2 list is used.
    """

    allowed = normalize_compressed_extensions(exts)
    suffixes = [s.lower() for s in path.suffixes]
    full_suffix = (
        "".join(suffixes[-2:])
        if len(suffixes) >= 2
        else (suffixes[-1] if suffixes else "")
    )

    # Quick extension check (full suffix or single suffix)
    if full_suffix and full_suffix in allowed:
        return detect_archive_type(path) is not None
    if suffixes and suffixes[-1] in allowed:
        return detect_archive_type(path) is not None
    return False


def _norm_content_extensions(exts: Iterable[str] | set[str] | None) -> set[str]:
    """Normalise content extensions to lowercase set with leading dot."""
    if not exts:
        return set()
    out: set[str] = set()
    for e in exts:
        s = str(e).strip().lower().lstrip("*")
        if not s:
            continue
        if not s.startswith("."):
            s = f".{s}"
        out.add(s)
    return out


class ArchiveUnsupportedError(Exception):
    """Raised when archive format requires an optional dependency (e.g. py7zr)."""

    pass


def classify_zip_member_read_failure(
    exc: BaseException,
    *,
    encrypted: bool,
    password_provided: bool,
) -> str:
    """Map zipfile member read errors to scan_failures reason codes (#828)."""
    if encrypted and not password_provided:
        return SCAN_FAILURE_REASON_ENCRYPTED_NO_PASSWORD
    if encrypted and password_provided:
        msg = str(exc).lower()
        if (
            "bad password" in msg
            or "incorrect password" in msg
            or "bad crc-32" in msg
            or "bad crc" in msg
        ):
            return SCAN_FAILURE_REASON_WRONG_PASSWORD
    return SCAN_FAILURE_REASON_ARCHIVE_READ_ERROR


def classify_7z_member_read_failure(
    exc: BaseException,
    *,
    password_provided: bool,
) -> str:
    """Map py7zr member read errors to scan_failures reason codes (#828)."""
    try:
        from py7zr import exceptions as py7zr_exc
    except ImportError:
        py7zr_exc = None  # type: ignore[misc, assignment]
    if py7zr_exc is not None and isinstance(exc, py7zr_exc.PasswordRequired):
        return SCAN_FAILURE_REASON_ENCRYPTED_NO_PASSWORD
    if password_provided:
        if py7zr_exc is not None and isinstance(exc, py7zr_exc.CrcError):
            return SCAN_FAILURE_REASON_WRONG_PASSWORD
        msg = str(exc).lower()
        if "password" in msg or "wrong" in msg or "crc" in msg:
            return SCAN_FAILURE_REASON_WRONG_PASSWORD
    return SCAN_FAILURE_REASON_ARCHIVE_READ_ERROR


def iter_archive_members(
    path: Path,
    archive_type: str,
    max_inner_size: int,
    allowed_extensions: Iterable[str] | set[str],
    file_passwords: dict[str, str] | None = None,
    on_member_read_failure: MemberReadFailureCallback | None = None,
    *,
    max_members: int | None = None,
    max_total_uncompressed: int | None = None,
    max_expansion_ratio: float | None = None,
) -> Iterator[tuple[str, bytes]]:
    """
    Yield (member_name, content_bytes) for each file inside the archive whose
    extension is in allowed_extensions and uncompressed size <= max_inner_size.
    Skips directories. Member names use forward slashes.

    Aggregate budgets (#1233): optional ``max_members``, ``max_total_uncompressed``,
    and ``max_expansion_ratio`` are checked from declared sizes **before** materializing
    member bytes. Exceeding any limit invokes ``on_member_read_failure`` with
    ``archive_budget_exceeded`` and stops iteration (fail-closed).
    """
    allowed = _norm_content_extensions(allowed_extensions)
    if not allowed:
        return
    pw = file_passwords or {}

    try:
        compressed_size = max(int(path.stat().st_size), 0)
    except OSError:
        compressed_size = 0

    examined = 0
    total_uncompressed = 0

    def _budget_exceeded(member_label: str, detail: str) -> bool:
        """True when a budget was hit; caller must stop iteration without materializing."""
        if on_member_read_failure is not None:
            on_member_read_failure(
                SCAN_FAILURE_REASON_ARCHIVE_BUDGET_EXCEEDED,
                member_label,
                f"{path.name}|{member_label}: {detail}",
            )
        return True

    def _after_examine(member_label: str, declared_size: int) -> bool:
        """Increment counters; return True if iteration must stop (budget exceeded)."""
        nonlocal examined, total_uncompressed
        examined += 1
        total_uncompressed += max(int(declared_size), 0)
        if max_members is not None and examined > max_members:
            return _budget_exceeded(
                member_label,
                f"max_members exceeded (examined={examined} > {max_members})",
            )
        if (
            max_total_uncompressed is not None
            and total_uncompressed > max_total_uncompressed
        ):
            return _budget_exceeded(
                member_label,
                (
                    f"max_total_uncompressed exceeded "
                    f"(total={total_uncompressed} > {max_total_uncompressed})"
                ),
            )
        if (
            max_expansion_ratio is not None
            and compressed_size > 0
            and math.isfinite(float(max_expansion_ratio))
            and (total_uncompressed / compressed_size) > float(max_expansion_ratio)
        ):
            ratio = total_uncompressed / compressed_size
            return _budget_exceeded(
                member_label,
                (
                    f"max_expansion_ratio exceeded "
                    f"(ratio={ratio:.1f} > {max_expansion_ratio})"
                ),
            )
        return False

    if archive_type == "zip":
        pwd = (pw.get(".zip") or pw.get("default") or "").encode("utf-8") or None
        try:
            with zipfile.ZipFile(path, "r") as z:
                if pwd:
                    z.setpassword(pwd)
                for name in z.namelist():
                    if name.endswith("/"):
                        continue
                    try:
                        info = z.getinfo(name)
                    except KeyError:
                        continue
                    if _after_examine(name, info.file_size):
                        return
                    if info.file_size > max_inner_size:
                        continue
                    ext = Path(name).suffix.lower()
                    if ext not in allowed:
                        continue
                    try:
                        data = z.read(name)
                    except (RuntimeError, zipfile.BadZipFile) as e:
                        if on_member_read_failure is not None:
                            encrypted = bool(info.flag_bits & 0x1)
                            reason = classify_zip_member_read_failure(
                                e,
                                encrypted=encrypted,
                                password_provided=bool(pwd),
                            )
                            on_member_read_failure(
                                reason,
                                name,
                                f"{path.name}|{name}: {type(e).__name__}: {e}",
                            )
                        continue
                    yield (name, data)
        except (zipfile.BadZipFile, OSError):
            return

    elif archive_type in ("tar", "tar.gz", "tar.bz2", "tar.xz"):
        mode = "r"
        if archive_type == "tar.gz":
            mode = "r:gz"
        elif archive_type == "tar.bz2":
            mode = "r:bz2"
        elif archive_type == "tar.xz":
            mode = "r:xz"
        try:
            with tarfile.open(path, mode) as tar:
                for member in tar.getmembers():
                    if not member.isfile():
                        continue
                    declared = int(getattr(member, "size", 0) or 0)
                    if _after_examine(member.name, declared):
                        return
                    if declared > max_inner_size:
                        continue
                    ext = Path(member.name).suffix.lower()
                    if ext not in allowed:
                        continue
                    f = tar.extractfile(member)
                    data = f.read() if f else b""
                    yield (member.name, data)
        except (tarfile.ReadError, OSError):
            return

    elif archive_type == "7z":
        try:
            import py7zr
            from py7zr.io import BytesIOFactory
        except ImportError:
            raise ArchiveUnsupportedError(
                "7z support requires py7zr: `uv sync --extra compressed` (uv) "
                "or `pip install 'data-boar[compressed]'` (fallback); "
                "on a host without liblzma see issue #926"
            )
        pwd = pw.get(".7z") or pw.get("default") or None
        from py7zr.exceptions import PasswordRequired

        try:
            with py7zr.SevenZipFile(path, "r", password=pwd) as archive:
                # py7zr >= 0.22: use list(); older docs used files_list (removed in 1.x).
                # Collect desired members first, then ONE extract() — solid archives
                # re-decompress per extract call (#1250 / #1248).
                desired: list[str] = []
                for member in archive.list():
                    if member.is_directory:
                        continue
                    size = getattr(member, "uncompressed", 0) or 0
                    if _after_examine(member.filename, size):
                        # Stop collecting; still extract members already in desired
                        # (ZIP/TAR parity — do not discard the pre-budget queue).
                        break
                    if size > max_inner_size:
                        continue
                    ext = Path(member.filename).suffix.lower()
                    if ext not in allowed:
                        continue
                    desired.append(member.filename)

                if not desired:
                    return

                # SevenZipFile is stateful after list(); reset before extract.
                with contextlib.suppress(Exception):
                    archive.reset()

                try:
                    # Per-stream memory cap matches the per-member size filter above.
                    fac = BytesIOFactory(max_inner_size)
                    archive.extract(targets=desired, factory=fac)
                except PasswordRequired:
                    raise
                except (Exception, OSError) as e:
                    if on_member_read_failure is not None:
                        reason = classify_7z_member_read_failure(
                            e, password_provided=bool(pwd)
                        )
                        # Batch extract failed as a whole — record one failure per target
                        # so scan_failures still surfaces the reason for each member.
                        for name in desired:
                            on_member_read_failure(
                                reason,
                                name,
                                f"{path.name}|{name}: {type(e).__name__}: {e}",
                            )
                    return

                for name in desired:
                    bio = fac.products.get(name)
                    if bio is None:
                        continue
                    try:
                        bio.seek(0)
                        data = bio.read()
                    except (Exception, OSError) as e:
                        if on_member_read_failure is not None:
                            reason = classify_7z_member_read_failure(
                                e, password_provided=bool(pwd)
                            )
                            on_member_read_failure(
                                reason,
                                name,
                                f"{path.name}|{name}: {type(e).__name__}: {e}",
                            )
                        continue
                    yield (name, data)
        except PasswordRequired as e:
            if on_member_read_failure is not None:
                on_member_read_failure(
                    SCAN_FAILURE_REASON_ENCRYPTED_NO_PASSWORD,
                    path.name,
                    f"{path.name}: {type(e).__name__}: {e}",
                )
            return
        except (py7zr.Bad7zFile, OSError):
            return

    # Single-file compressed (gz/bz2/xz without tar): no member iteration in this phase
    elif archive_type in ("gz", "bz2", "xz"):
        return
