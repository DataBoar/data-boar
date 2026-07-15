"""
SMB/CIFS connector: connect to Windows or Samba shares by host (FQDN or IP), list files,
download to temp, run same text extraction and sensitivity detection as filesystem.
Requires optional dependency: pip install smbprotocol (or uv pip install -e ".[shares]").
"""

import os
import tempfile
from pathlib import Path
from typing import Any

from core.connector_registry import register
from core.archives import (
    default_compressed_extensions,
    is_supported_archive,
    normalize_compressed_extensions,
)

from connectors.filesystem_connector import (
    SUPPORTED_EXTENSIONS,
    _read_text_sample,
    _scan_sqlite_file_as_db,
    scan_archive_at_path,
)
from core.content_type import (
    choose_effective_pdf_extension,
    choose_effective_rich_media_extension,
)

try:
    import smbclient

    _SMB_AVAILABLE = True
except ImportError:
    _SMB_AVAILABLE = False
    smbclient = None

SQLITE_EXTENSIONS = {".sqlite", ".sqlite3", ".db"}


def _normalize_extensions(extensions: Any) -> set[str]:
    if not extensions:
        return set(SUPPORTED_EXTENSIONS)
    exts = list(extensions) if isinstance(extensions, (list, set)) else [extensions]
    use_all = any(str(x).strip().lower() in ("*", "all", ".*") for x in exts)
    if use_all:
        return set(SUPPORTED_EXTENSIONS)
    return {e if e.startswith(".") else f".{e.lstrip('*')}" for e in exts}


class SMBConnector:
    """
    Connect to SMB/CIFS share (host FQDN or IP, share name, path). Credentials: user, password, optional domain.
    List files recursively, download to temp, run filesystem-style text extraction and scanner, save findings.
    """

    def __init__(
        self,
        target_config: dict[str, Any],
        scanner: Any,
        db_manager: Any,
        extensions: set[str] | list[str] | None = None,
        scan_sqlite_as_db: bool = True,
        sample_limit: int = 5,
        file_sample_max_chars: int = 12_000,
        file_passwords: dict[str, str] | None = None,
    ):
        self.config = target_config
        self.scanner = scanner
        self.db_manager = db_manager
        self.scan_sqlite_as_db = scan_sqlite_as_db
        self.sample_limit = sample_limit
        self.file_sample_max_chars = int(file_sample_max_chars)
        self.extensions = _normalize_extensions(extensions)
        self.file_passwords = file_passwords or {}
        self._session_registered = False
        fs_opts = target_config.get("file_scan") or {}
        self.scan_compressed = bool(fs_opts.get("scan_compressed"))
        self.max_inner_size = fs_opts.get("max_inner_size")
        self.max_members = fs_opts.get("max_members")
        self.max_total_uncompressed = fs_opts.get("max_total_uncompressed")
        self.max_expansion_ratio = fs_opts.get("max_expansion_ratio")
        self.compressed_extensions = normalize_compressed_extensions(
            fs_opts.get("compressed_extensions") or default_compressed_extensions()
        )
        # Planned: optional content-based type detection (magic bytes) to help
        # with renamed/cloaked files. Currently just wired from config; behaviour
        # remains extension-based until a future opt-in phase.
        self.use_content_type = bool(fs_opts.get("use_content_type", False))
        self.scan_rich_media_metadata = bool(
            fs_opts.get("scan_rich_media_metadata", False)
        )
        self.scan_image_ocr = bool(fs_opts.get("scan_image_ocr", False))
        try:
            self.ocr_max_dimension = int(fs_opts.get("ocr_max_dimension", 2000))
        except (TypeError, ValueError):
            self.ocr_max_dimension = 2000
        self.ocr_max_dimension = max(256, min(8000, self.ocr_max_dimension))
        self.ocr_lang = str(fs_opts.get("ocr_lang") or "eng").strip() or "eng"
        self.scan_for_stego = bool(fs_opts.get("scan_for_stego", False))
        from core.rich_media_magic import IMAGE_EXTENSIONS, RICH_MEDIA_SCAN_EXTENSIONS

        if self.scan_rich_media_metadata:
            self.extensions = set(self.extensions) | set(RICH_MEDIA_SCAN_EXTENSIONS)
        elif self.scan_image_ocr:
            self.extensions = set(self.extensions) | set(IMAGE_EXTENSIONS)

    def _unc_path(self, *parts: str) -> str:
        host = self.config.get("host", "").strip()
        share = (self.config.get("share", "") or "").strip().replace("/", "\\")
        path = "\\".join(p for p in parts if p).replace("/", "\\")
        base = f"\\\\{host}\\{share}"
        if path:
            return base + "\\" + path.lstrip("\\")
        return base

    def run(self) -> None:
        if not _SMB_AVAILABLE:
            self.db_manager.save_failure(
                self.config.get("name", "SMB"),
                "error",
                'smbprotocol not installed. Install with: pip install smbprotocol or uv pip install -e ".[shares]"',
            )
            return
        target_name = self.config.get("name", "SMB")
        from utils.audit_log_display import audit_log_target_label

        audit_name = audit_log_target_label(self.config, default="SMB")
        host = self.config.get("host", "").strip()
        if not host:
            self.db_manager.save_failure(
                target_name, "error", "Missing host (FQDN or IP)"
            )
            return
        user = self.config.get("user", self.config.get("username", ""))
        password = self.config.get("pass", self.config.get("password", ""))
        domain = self.config.get("domain", "")
        if domain and user and "\\" not in user:
            user = f"{domain}\\{user}"
        port = int(self.config.get("port", 445))
        share = (self.config.get("share", "") or "").strip()
        if not share:
            self.db_manager.save_failure(target_name, "error", "Missing share name")
            return
        path_in_share = (
            (self.config.get("path", "") or "").strip().replace("/", "\\").strip("\\")
        )
        recursive = self.config.get("recursive", True)
        try:
            smbclient.register_session(
                host, username=user, password=password, port=port
            )
            self._session_registered = True
        except Exception as e:
            self.db_manager.save_failure(target_name, "auth_failed", str(e))
            return
        root_unc = (
            self._unc_path(path_in_share) if path_in_share else self._unc_path("")
        )
        try:
            if recursive:
                walker = smbclient.walk(root_unc)
            else:
                entries = list(smbclient.scandir(root_unc))
                files = [e.name for e in entries if e.is_file()]
                walker = [(root_unc, [], files)]
        except Exception as e:
            self.db_manager.save_failure(target_name, "unreachable", str(e))
            return
        for dirpath, _dirnames, filenames in walker:
            for filename in filenames:
                ext = Path(filename).suffix.lower()
                if ext not in self.extensions and not (
                    self.scan_compressed and ext in self.compressed_extensions
                ):
                    continue
                unc_file = dirpath + "\\" + filename
                try:
                    with smbclient.open_file(unc_file, mode="rb") as f:
                        content = f.read()
                except Exception as e:
                    self.db_manager.save_failure(
                        target_name, "permission_denied", f"{unc_file}: {e}"
                    )
                    continue
                if self.scan_sqlite_as_db and ext in SQLITE_EXTENSIONS:
                    fd, temp_path = tempfile.mkstemp(suffix=ext)
                    try:
                        os.write(fd, content)
                        os.close(fd)
                        for finding in _scan_sqlite_file_as_db(
                            Path(temp_path), self.scanner, self.sample_limit
                        ):
                            self.db_manager.save_finding(
                                "filesystem",
                                target_name=target_name,
                                path=dirpath,
                                file_name=finding["file_name"],
                                data_type=finding["data_type"],
                                sensitivity_level=finding["sensitivity_level"],
                                pattern_detected=finding["pattern_detected"],
                                norm_tag=finding["norm_tag"],
                                ml_confidence=finding["ml_confidence"],
                            )
                    finally:
                        try:
                            os.unlink(temp_path)
                        except Exception:
                            pass
                    continue
                if self.scan_compressed and ext in self.compressed_extensions:
                    fd, temp_path = tempfile.mkstemp(suffix=ext)
                    try:
                        os.write(fd, content)
                        os.close(fd)
                        p = Path(temp_path)
                        if is_supported_archive(p, exts=self.compressed_extensions):
                            scan_archive_at_path(
                                archive_path=p,
                                archive_display_name=filename,
                                target_name=target_name,
                                path_display=dirpath,
                                scanner=self.scanner,
                                db_manager=self.db_manager,
                                extensions=self.extensions,
                                max_inner_size=self.max_inner_size,
                                max_members=self.max_members,
                                max_total_uncompressed=self.max_total_uncompressed,
                                max_expansion_ratio=self.max_expansion_ratio,
                                file_passwords=self.file_passwords,
                                file_sample_max_chars=self.file_sample_max_chars,
                                rich_media_metadata=self.scan_rich_media_metadata,
                                scan_image_ocr=self.scan_image_ocr,
                                ocr_max_dimension=self.ocr_max_dimension,
                                ocr_lang=self.ocr_lang,
                                scan_for_stego=self.scan_for_stego,
                                use_content_type=self.use_content_type,
                                audit_log_name=audit_name,
                            )
                    finally:
                        try:
                            os.unlink(temp_path)
                        except Exception:
                            pass
                    continue
                fd, temp_path = tempfile.mkstemp(suffix=ext)
                try:
                    os.write(fd, content)
                    os.close(fd)
                    # Optional: when use_content_type is enabled, use shared helper for the narrow
                    # PDF-only slice (mirrors filesystem behaviour for renamed PDFs on shares).
                    effective_ext = choose_effective_pdf_extension(
                        ext, self.use_content_type, Path(temp_path)
                    )
                    effective_ext = choose_effective_rich_media_extension(
                        effective_ext, self.use_content_type, Path(temp_path)
                    )
                    text = _read_text_sample(
                        Path(temp_path),
                        effective_ext,
                        self.file_sample_max_chars,
                        self.file_passwords,
                        rich_media_metadata=self.scan_rich_media_metadata,
                        scan_image_ocr=self.scan_image_ocr,
                        ocr_max_dimension=self.ocr_max_dimension,
                        ocr_lang=self.ocr_lang,
                        scan_for_stego=self.scan_for_stego,
                    )
                    res = self.scanner.scan_file_content(text, Path(unc_file))
                    if res is None:
                        continue
                    self.db_manager.save_finding(
                        "filesystem",
                        target_name=target_name,
                        path=dirpath,
                        file_name=filename,
                        data_type=ext.replace(".", "").upper(),
                        sensitivity_level=res["sensitivity_level"],
                        pattern_detected=res["pattern_detected"],
                        norm_tag=res.get("norm_tag", ""),
                        ml_confidence=res.get("ml_confidence", 0),
                    )
                finally:
                    try:
                        os.unlink(temp_path)
                    except Exception:
                        pass


if _SMB_AVAILABLE:
    register("smb", SMBConnector, ["name", "host", "share"])
    register("cifs", SMBConnector, ["name", "host", "share"])
