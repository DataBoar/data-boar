"""
SharePoint connector: connect to SharePoint (on-prem or URL) by site_url (FQDN), list files in a folder,
download to temp, run same text extraction and sensitivity detection as filesystem.
Uses REST API with NTLM or basic auth. Requires optional: requests_ntlm (or uv pip install -e ".[shares]").
"""

import os
import tempfile
from pathlib import Path
from typing import Any

from core.about import get_http_user_agent
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
    import requests
    from requests_ntlm import HttpNtlmAuth

    _REQUESTS_NTLM_AVAILABLE = True
except ImportError:
    _REQUESTS_NTLM_AVAILABLE = False
    requests = None
    HttpNtlmAuth = None

SQLITE_EXTENSIONS = {".sqlite", ".sqlite3", ".db"}


def _normalize_extensions(extensions: Any) -> set[str]:
    if not extensions:
        return set(SUPPORTED_EXTENSIONS)
    exts = list(extensions) if isinstance(extensions, (list, set)) else [extensions]
    use_all = any(str(x).strip().lower() in ("*", "all", ".*") for x in exts)
    if use_all:
        return set(SUPPORTED_EXTENSIONS)
    return {e if e.startswith(".") else f".{e.lstrip('*')}" for e in exts}


class SharePointConnector:
    """
    Connect to SharePoint site (site_url = FQDN or host with path). Credentials: user, password; auth NTLM or basic.
    List files in folder (path_in_site), download via REST GetFileByServerRelativeUrl/.../$value, scan, save findings.
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
        fs_opts = target_config.get("file_scan") or {}
        self.scan_compressed = bool(fs_opts.get("scan_compressed"))
        self.max_inner_size = fs_opts.get("max_inner_size")
        self.max_members = fs_opts.get("max_members")
        self.max_total_uncompressed = fs_opts.get("max_total_uncompressed")
        self.max_expansion_ratio = fs_opts.get("max_expansion_ratio")
        self.compressed_extensions = normalize_compressed_extensions(
            fs_opts.get("compressed_extensions") or default_compressed_extensions()
        )
        # Planned: optional content-based type detection (magic bytes) for renamed/cloaked files.
        # Wiring only; actual use in extraction will be controlled by a future opt-in toggle.
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

    def run(self) -> None:
        if not _REQUESTS_NTLM_AVAILABLE:
            self.db_manager.save_failure(
                self.config.get("name", "SharePoint"),
                "error",
                'requests and requests_ntlm required. Install with: pip install requests requests_ntlm or uv pip install -e ".[shares]"',
            )
            return
        target_name = self.config.get("name", "SharePoint")
        from utils.audit_log_display import audit_log_target_label

        audit_name = audit_log_target_label(self.config, default="SharePoint")
        site_url = (
            self.config.get("site_url")
            or self.config.get("base_url")
            or self.config.get("url", "")
        ).rstrip("/")
        if not site_url:
            self.db_manager.save_failure(
                target_name,
                "error",
                "Missing site_url (e.g. https://host/sites/sitename)",
            )
            return
        # SSRF guard (#832): reject link-local/private/loopback hosts unless the
        # target config opts in with allow_private_networks: true.
        from .url_guard import target_allows_private, validate_outbound_url

        err = validate_outbound_url(
            site_url,
            allow_private=target_allows_private(self.config),
            label="site_url",
        )
        if err:
            self.db_manager.save_failure(target_name, "error", err)
            return
        user = self.config.get("user", self.config.get("username", ""))
        password = self.config.get("pass", self.config.get("password", ""))
        path_in_site = (
            self.config.get("path", "")
            or self.config.get("path_in_site", "Shared Documents")
        ).strip("/")
        use_ntlm = self.config.get("auth", {}).get("type", "ntlm").lower() in (
            "ntlm",
            "",
        )
        verify_ssl = self.config.get("verify_ssl", True)
        session = requests.Session()
        session.headers["User-Agent"] = get_http_user_agent()
        session.verify = verify_ssl
        if use_ntlm and user and password:
            session.auth = HttpNtlmAuth(user, password)
        elif user and password:
            session.auth = (user, password)
        session.headers["Accept"] = "application/json;odata=verbose"
        list_files_url = (
            f"{site_url}/_api/web/GetFolderByServerRelativeUrl('{path_in_site}')/Files"
        )
        try:
            r = session.get(list_files_url)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            self.db_manager.save_failure(target_name, "unreachable", str(e))
            return
        results = data.get("d", {}).get("results", data.get("results", []))
        if not results:
            return
        for item in results:
            name = item.get("Name", item.get("name", ""))
            if not name:
                continue
            ext = Path(name).suffix.lower()
            if ext not in self.extensions and not (
                self.scan_compressed and ext in self.compressed_extensions
            ):
                continue
            server_relative_url = item.get(
                "ServerRelativeUrl", item.get("serverRelativeUrl", "")
            )
            if not server_relative_url:
                server_relative_url = f"/{path_in_site}/{name}".replace("//", "/")
            file_value_url = f"{site_url}/_api/web/GetFileByServerRelativeUrl('{server_relative_url}')/$value"
            try:
                r2 = session.get(file_value_url)
                r2.raise_for_status()
                content = r2.content
            except Exception as e:
                self.db_manager.save_failure(
                    target_name, "permission_denied", f"{name}: {e}"
                )
                continue
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                tmp.write(content)
                temp_path = tmp.name
            try:
                if (
                    self.scan_compressed
                    and ext in self.compressed_extensions
                    and is_supported_archive(
                        Path(temp_path), exts=self.compressed_extensions
                    )
                ):
                    scan_archive_at_path(
                        archive_path=Path(temp_path),
                        archive_display_name=name,
                        target_name=target_name,
                        path_display=server_relative_url,
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
                elif self.scan_sqlite_as_db and ext in SQLITE_EXTENSIONS:
                    for finding in _scan_sqlite_file_as_db(
                        Path(temp_path), self.scanner, self.sample_limit
                    ):
                        self.db_manager.save_finding(
                            "filesystem",
                            target_name=target_name,
                            path=server_relative_url,
                            file_name=finding["file_name"],
                            data_type=finding["data_type"],
                            sensitivity_level=finding["sensitivity_level"],
                            pattern_detected=finding["pattern_detected"],
                            norm_tag=finding["norm_tag"],
                            ml_confidence=finding["ml_confidence"],
                        )
                else:
                    # Optional: when use_content_type is enabled, mirror the filesystem narrow
                    # PDF-only slice to SharePoint downloads so PDFs renamed as .txt are still
                    # treated as PDF for extraction. Default remains extension-only.
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
                    res = self.scanner.scan_file_content(text, Path(name))
                    if res is not None:
                        self.db_manager.save_finding(
                            "filesystem",
                            target_name=target_name,
                            path=server_relative_url,
                            file_name=name,
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


if _REQUESTS_NTLM_AVAILABLE:
    register("sharepoint", SharePointConnector, ["name", "site_url"])
