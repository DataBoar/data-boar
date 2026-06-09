"""
Filesystem connector: recursive walk, permission check before read, extensions filter,
extract text (pypdf, docx, openpyxl, etc.), run detector, save filesystem_findings only.
On permission error: save_failure with reason permission_denied.
Scans all compatible/supported file types by extension; unknown types get path/name-only analysis.
"""

import hashlib
import os
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from core.connector_registry import register
from core.archives import (
    ArchiveUnsupportedError,
    default_compressed_extensions,
    detect_archive_type,
    iter_archive_members,
    is_supported_archive,
    normalize_compressed_extensions,
)
from core.content_type import (
    choose_effective_pdf_extension,
    choose_effective_rich_media_extension,
)
from utils.subtitle_text import SUBTITLE_EXTENSIONS, normalize_subtitle_sample

# Default cap for total uncompressed bytes per member when scanning inside archives.
DEFAULT_MAX_INNER_SIZE = 10_000_000
# Clamp range for max_inner_size (config may be validated in loader; this is defense-in-depth).
MIN_MAX_INNER_SIZE = 1_000_000  # 1 MB
MAX_MAX_INNER_SIZE = 500_000_000  # 500 MB


def _file_content_fingerprint(raw_bytes: bytes | None) -> str | None:
    """Return blake2s(raw_bytes, digest_size=8).hexdigest() for change detection.

    Returns None when raw_bytes is None or empty. Not a cryptographic commitment
    (see ADR-0051): used only as a fast equality probe between scan runs.
    """
    if not raw_bytes:
        return None
    return hashlib.blake2s(raw_bytes, digest_size=8).hexdigest()


# Plain text and markup (read as text with errors=replace)
_TEXT_EXTENSIONS = {
    ".txt",
    ".csv",
    ".tsv",
    ".tab",
    ".json",
    ".jsonl",
    ".ndjson",
    ".xml",
    ".html",
    ".htm",
    ".xhtml",
    ".md",
    ".markdown",
    ".rst",
    ".log",
    ".ini",
    ".cfg",
    ".conf",
    ".config",
    ".yml",
    ".yaml",
    ".toml",
    ".env",
    ".properties",
    ".sql",
    ".sh",
    ".bat",
    ".ps1",
    ".py",
    ".js",
    ".ts",
    ".mjs",
    ".cjs",
    ".vue",
    ".rb",
    ".php",
    ".pl",
    ".pm",
    ".java",
    ".kt",
    ".kts",
    ".scala",
    ".go",
    ".rs",
    ".c",
    ".h",
    ".cpp",
    ".hpp",
    ".cs",
    ".vb",
    ".r",
    ".R",
    ".graphql",
    ".gql",
    ".tex",
    ".bib",
    ".rtf",
    ".rtfd",
    ".rdf",
    ".owl",
    ".ttl",
    ".n3",
    ".svg",
    ".svgz",
    ".diff",
    ".patch",
    # Sidecar subtitles / captions (timing stripped before sensitivity scan; see utils/subtitle_text.py)
    ".srt",
    ".vtt",
    ".ass",
    ".ssa",
}

# Binary/document formats with dedicated extractors
_DOCUMENT_EXTENSIONS = {
    ".pdf",
    ".doc",
    ".docx",
    ".odt",
    ".ods",
    ".odp",
    ".odm",
    ".odg",
    ".odf",
    ".odb",
    ".xls",
    ".xlsx",
    ".xlsm",
    ".xlsb",
    ".ppt",
    ".pptx",
    ".pps",
    ".ppsx",
    ".msg",
    ".eml",
    ".mht",
    ".mhtml",
    ".epub",
}

# Database / structured (sample or path-only)
_DATA_EXTENSIONS = {
    ".sqlite",
    ".sqlite3",
    ".db",
    ".accdb",
    ".mdb",
    ".parquet",
    ".feather",
    ".orc",
    ".avro",
    ".dbf",
}

# Supported extensions = all of the above (recursive scan uses this when config does not override)
SUPPORTED_EXTENSIONS = _TEXT_EXTENSIONS | _DOCUMENT_EXTENSIONS | _DATA_EXTENSIONS

# Optional: extension -> MIME (for reference; scanning is extension-based)
EXTENSION_MIME = {
    ".txt": "text/plain",
    ".csv": "text/csv",
    ".json": "application/json",
    ".pdf": "application/pdf",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xls": "application/vnd.ms-excel",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".odt": "application/vnd.oasis.opendocument.text",
    ".ods": "application/vnd.oasis.opendocument.spreadsheet",
    ".odp": "application/vnd.oasis.opendocument.presentation",
    ".xml": "application/xml",
    ".html": "text/html",
    ".htm": "text/html",
    ".eml": "message/rfc822",
    ".msg": "application/vnd.ms-outlook",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".rtf": "application/rtf",
    ".sqlite": "application/vnd.sqlite3",
    ".yml": "text/yaml",
    ".yaml": "text/yaml",
}


def _read_text_sample(
    path: Path,
    ext: str,
    max_chars: int = 10000,
    file_passwords: dict[str, str] | None = None,
    *,
    rich_media_metadata: bool = False,
    scan_image_ocr: bool = False,
    ocr_max_dimension: int = 2000,
    ocr_lang: str = "eng",
    scan_for_stego: bool = False,
) -> str:
    """Extract text from file for sensitivity scan; return empty on error. No content stored after return.

    ``max_chars`` is a **character budget** for plain-text-like types (``.txt``, ``.md``, …).
    It comes from ``file_scan.file_sample_max_chars`` (not ``sample_limit``, which is still used
    for SQL row caps and similar).
    When file_passwords is provided (e.g. {'.pdf': 'secret', 'default': 'fallback'}), use it to open
    password-protected PDF and ZIP-based (e.g. .pptx) files. Unsupported or wrong password yields empty string.

    When *rich_media_metadata* or *scan_image_ocr* is true, image/audio/video extensions invoke
    ``connectors.rich_media_sample.build_rich_media_text_sample`` (optional mutagen, ffprobe, tesseract).

    When *scan_for_stego* is true, rich-media containers may receive a short entropy-based hint line
    (heuristic only; see ``connectors.stego_hint``).
    """
    pw = file_passwords or {}

    def finalize(text: str) -> str:
        text = text if len(text) <= max_chars else text[:max_chars]
        if not scan_for_stego:
            return text[:max_chars]
        from connectors.stego_hint import append_stego_hint

        return append_stego_hint(path, ext, text, max_chars)

    try:
        from connectors.rich_media_sample import build_rich_media_text_sample
        from core.rich_media_magic import IMAGE_EXTENSIONS, RICH_MEDIA_SCAN_EXTENSIONS

        if ext.lower() in RICH_MEDIA_SCAN_EXTENSIONS and (
            rich_media_metadata or scan_image_ocr
        ):
            return finalize(
                build_rich_media_text_sample(
                    path,
                    ext,
                    max_chars,
                    metadata=rich_media_metadata,
                    image_ocr=bool(scan_image_ocr and ext.lower() in IMAGE_EXTENSIONS),
                    ocr_max_dimension=ocr_max_dimension,
                    ocr_lang=ocr_lang,
                )
            )

        # Plain text and markup: read as text
        if ext in _TEXT_EXTENSIONS:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                raw = f.read(max_chars)
            if ext in SUBTITLE_EXTENSIONS:
                return finalize(normalize_subtitle_sample(raw, ext)[:max_chars])
            return finalize(raw)

        if ext == ".pdf":
            from pypdf import PdfReader

            reader = PdfReader(path)
            if reader.is_encrypted:
                password = pw.get(ext) or pw.get("default")
                if password:
                    reader.decrypt(password)
                else:
                    return finalize("")
            return finalize(
                " ".join(p.extract_text() or "" for p in reader.pages[:5])[:max_chars]
            )
        if ext == ".docx":
            from docx import Document

            doc = Document(path)
            return finalize(" ".join(p.text for p in doc.paragraphs[:50])[:max_chars])
        if ext == ".doc":
            # Extension ".doc" may be OOXML (ZIP) readable like .docx, or legacy Word 97-2003 (OLE binary).
            # Optional mammoth handles OOXML; OLE binary typically fails at zip open — path/name still analyzed.
            try:
                import mammoth
            except ImportError:
                return finalize("")
            try:
                with path.open("rb") as fh:
                    result = mammoth.extract_raw_text(fh)
                raw = result.value or ""
            except Exception:
                return finalize("")
            return finalize(raw)
        if ext == ".odt":
            try:
                from odf.opendocument import load
                from odf import text as odf_text, teletype

                doc = load(path)
                parts = [
                    teletype.extractText(el) for el in doc.getElementsByType(odf_text.P)
                ]
                return finalize(" ".join(parts)[:max_chars])
            except Exception:
                return finalize("")
        if ext == ".ods":
            try:
                from odf.opendocument import load
                from odf import text as odf_text, teletype

                doc = load(path)
                parts = [
                    teletype.extractText(el) for el in doc.getElementsByType(odf_text.P)
                ]
                return finalize(" ".join(parts)[:max_chars])
            except Exception:
                return finalize("")
        if ext == ".odp":
            try:
                from odf.opendocument import load
                from odf import text as odf_text, teletype

                doc = load(path)
                parts = [
                    teletype.extractText(el) for el in doc.getElementsByType(odf_text.P)
                ]
                return finalize(" ".join(parts)[:max_chars])
            except Exception:
                return finalize("")
        if ext in (".xlsx", ".xls", ".xlsm"):
            import pandas as pd

            df = pd.read_excel(path, nrows=20, header=None)
            return finalize(" ".join(df.astype(str).stack().tolist())[:max_chars])
        if ext == ".xlsb":
            try:
                import pandas as pd

                df = pd.read_excel(path, engine="pyxlsb", nrows=20, header=None)
                return finalize(" ".join(df.astype(str).stack().tolist())[:max_chars])
            except Exception:
                return finalize("")
        if ext == ".pptx":
            try:
                with zipfile.ZipFile(path, "r") as z:
                    password = pw.get(ext) or pw.get("default")
                    if password:
                        z.setpassword(
                            password.encode("utf-8")
                            if isinstance(password, str)
                            else password
                        )
                    parts = []
                    for name in z.namelist():
                        if name.startswith("ppt/slides/slide") and name.endswith(
                            ".xml"
                        ):
                            data = z.read(name).decode("utf-8", errors="replace")
                            import re

                            parts.append(re.sub(r"<[^>]+>", " ", data))
                    return finalize(" ".join(parts)[:max_chars])
            except Exception:
                return finalize("")
        if ext == ".msg":
            try:
                import extract_msg

                msg = extract_msg.Message(path)
                body = (msg.body or "") + " " + (msg.subject or "")
                for att in (msg.attachments or [])[:3]:
                    body += " " + (getattr(att, "longFilename", "") or "")
                msg.close()
                return finalize(body[:max_chars])
            except Exception:
                return finalize("")
        if ext in (".eml", ".mht", ".mhtml"):
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                return finalize(f.read(max_chars))
        if ext == ".epub":
            from connectors.data_soup_formats import sample_epub_text

            return finalize(sample_epub_text(path, max_chars))
        if ext == ".parquet":
            from connectors.data_soup_formats import sample_parquet_text

            return finalize(sample_parquet_text(path, max_chars))
        if ext == ".feather":
            from connectors.data_soup_formats import sample_feather_text

            return finalize(sample_feather_text(path, max_chars))
        if ext == ".orc":
            from connectors.data_soup_formats import sample_orc_text

            return finalize(sample_orc_text(path, max_chars))
        if ext == ".avro":
            from connectors.data_soup_formats import sample_avro_text

            return finalize(sample_avro_text(path, max_chars))
        if ext == ".dbf":
            from connectors.data_soup_formats import sample_dbf_text

            return finalize(sample_dbf_text(path, max_chars))
        # .sqlite, .db, .accdb, .mdb: path/name only for text; SQLite files scanned as DB in run() when scan_sqlite_as_db
        return finalize("")
    except Exception:
        return finalize("")


def _scan_sqlite_file_as_db(
    file_path: Path,
    scanner: Any,
    sample_limit: int = 5,
) -> list[dict[str, Any]]:
    """
    Open a .sqlite/.sqlite3/.db file with SQLAlchemy, discover tables/columns, sample and detect.
    Returns list of findings (dicts for save_finding source_type=filesystem); file_name encodes table.column.
    No raw content stored.
    """
    from sqlalchemy import create_engine, inspect

    from connectors.sql_sampling import SamplingManager, resolve_sql_sample_limit

    findings = []
    try:
        engine = create_engine(f"sqlite:///{file_path.resolve()}", pool_pre_ping=True)
    except Exception:
        return []
    try:
        inspector = inspect(engine)
        eff_limit = resolve_sql_sample_limit(sample_limit)
        sqlite_logged: set[str] = set()
        with engine.connect() as conn:
            for table in inspector.get_table_names():
                try:
                    columns = inspector.get_columns(table)
                except Exception:
                    columns = []
                for col in columns:
                    cname = col["name"]
                    ctype = str(col["type"])
                    sample_parts = []
                    try:
                        safe_table = table.replace('"', '""')
                        safe_col = cname.replace('"', '""')
                        plan = SamplingManager.build_column_sample(
                            "sqlite",
                            safe_col=safe_col,
                            safe_table=safe_table,
                            safe_schema="",
                            schema=None,
                            limit=eff_limit,
                            table_metadata=None,
                        )
                        log_key = f"{file_path.name}:{table}"
                        if log_key not in sqlite_logged:
                            sqlite_logged.add(log_key)
                            try:
                                from utils.logger import get_logger

                                get_logger().info(
                                    "sql_sampling table=%s strategy=%s dialect=sqlite",
                                    log_key,
                                    plan.strategy_label,
                                )
                            except Exception:
                                pass
                        row = conn.execute(plan.query)
                        for r in row:
                            if r[0] is not None:
                                sample_parts.append(str(r[0])[:200])
                    except Exception:
                        pass
                    sample = " ".join(sample_parts)
                    res = scanner.scan_column(cname, sample, connector_data_type=ctype)
                    if res["sensitivity_level"] == "LOW":
                        continue
                    findings.append(
                        {
                            "path": str(file_path.parent),
                            "file_name": f"{file_path.name} | {table}.{cname}",
                            "data_type": ctype,
                            "sensitivity_level": res["sensitivity_level"],
                            "pattern_detected": res["pattern_detected"],
                            "norm_tag": res.get("norm_tag", ""),
                            "ml_confidence": res.get("ml_confidence", 0),
                        }
                    )
    except Exception:
        pass
    finally:
        engine.dispose()
    return findings


class FilesystemConnector:
    """
    Scan a directory recursively (or not), filter by extensions, check os.access(R_OK) before read,
    run sensitivity detection, save filesystem findings. Implements run() for engine.
    """

    SQLITE_EXTENSIONS = {".sqlite", ".sqlite3", ".db"}

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
        self.file_passwords = file_passwords or {}
        # Optional: scan inside compressed files (archives) – wiring only; extraction handled later.
        fs_opts = target_config.get("file_scan") or {}
        self.scan_compressed = bool(
            fs_opts.get("scan_compressed")
        )  # default False when not present
        # max_inner_size may be None -> meaning "use engine/connector default" in later phases
        self.max_inner_size = fs_opts.get("max_inner_size")
        self.compressed_extensions = normalize_compressed_extensions(
            fs_opts.get("compressed_extensions") or default_compressed_extensions()
        )
        # Planned: optional content-based type detection helper (magic bytes) to help
        # with renamed/cloaked files. Currently an inert toggle; future phases will
        # consult this flag before choosing how to extract/scan content.
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
        # "*" or "all" in list => use full SUPPORTED_EXTENSIONS; else use provided list or default
        use_all = False
        if extensions:
            exts = (
                list(extensions)
                if isinstance(extensions, (list, set))
                else [extensions]
            )
            use_all = any(str(x).strip().lower() in ("*", "all", ".*") for x in exts)
        self.extensions = (
            SUPPORTED_EXTENSIONS if use_all else set(extensions or SUPPORTED_EXTENSIONS)
        )
        # Normalize to lowercase with dot
        self.extensions = {
            e if e.startswith(".") else f".{e.lstrip('*')}" for e in self.extensions
        }
        from core.rich_media_magic import IMAGE_EXTENSIONS, RICH_MEDIA_SCAN_EXTENSIONS

        if self.scan_rich_media_metadata:
            self.extensions = set(self.extensions) | set(RICH_MEDIA_SCAN_EXTENSIONS)
        elif self.scan_image_ocr:
            self.extensions = set(self.extensions) | set(IMAGE_EXTENSIONS)

    def _scan_archive_contents(
        self,
        file_path: Path,
        target_name: str,
        scan_root: Path,
        audit_log_name: str,
    ) -> None:
        """Open archive and scan inner members with supported extensions; save findings with path like archive.zip|inner/path.txt."""
        scan_archive_at_path(
            archive_path=file_path,
            archive_display_name=file_path.name,
            target_name=target_name,
            path_display=str(file_path.parent),
            scanner=self.scanner,
            db_manager=self.db_manager,
            extensions=self.extensions,
            max_inner_size=self.max_inner_size,
            file_passwords=self.file_passwords,
            file_sample_max_chars=self.file_sample_max_chars,
            rich_media_metadata=self.scan_rich_media_metadata,
            scan_image_ocr=self.scan_image_ocr,
            ocr_max_dimension=self.ocr_max_dimension,
            ocr_lang=self.ocr_lang,
            scan_for_stego=self.scan_for_stego,
            use_content_type=self.use_content_type,
            scan_root=scan_root,
            audit_log_name=audit_log_name,
        )

    def run(self) -> None:
        """Walk target path, check permission, read sample, detect, save_finding or save_failure."""
        from utils.audit_log_display import (
            audit_log_target_label,
            format_filesystem_finding_location_for_audit_log,
            format_filesystem_scan_root_for_audit_log,
        )

        target_name = self.config.get("name", "filesystem")
        audit_name = audit_log_target_label(self.config, default="filesystem")
        root = self.config.get("path", "")
        recursive = self.config.get("recursive", True)
        path = Path(root)
        if not path.exists():
            self.db_manager.save_failure(
                target_name, "unreachable", f"Path does not exist: {root}"
            )
            return
        if not path.is_dir():
            self.db_manager.save_failure(
                target_name, "error", "Path is not a directory"
            )
            return
        try:
            from utils.logger import log_connection

            log_connection(
                audit_name,
                "filesystem",
                format_filesystem_scan_root_for_audit_log(path),
            )
        except Exception:
            pass
        pattern = "**/*" if recursive else "*"
        for file_path in path.glob(pattern):
            if not file_path.is_file():
                continue
            ext = file_path.suffix.lower()
            if ext not in self.extensions and not (
                self.scan_compressed and ext in self.compressed_extensions
            ):
                continue
            if not os.access(file_path, os.R_OK):
                self.db_manager.save_failure(
                    target_name, "permission_denied", str(file_path)
                )
                continue
            # When scan_compressed is enabled, open archive and scan inner members.
            if self.scan_compressed and is_supported_archive(
                file_path, exts=self.compressed_extensions
            ):
                self._scan_archive_contents(file_path, target_name, path, audit_name)
                continue
            # 2.6: treat .sqlite/.sqlite3/.db as DBs when scan_sqlite_as_db is True
            if self.scan_sqlite_as_db and ext in self.SQLITE_EXTENSIONS:
                for finding in _scan_sqlite_file_as_db(
                    file_path, self.scanner, self.sample_limit
                ):
                    self.db_manager.save_finding(
                        source_type="filesystem",
                        target_name=target_name,
                        path=finding["path"],
                        file_name=finding["file_name"],
                        data_type=finding["data_type"],
                        sensitivity_level=finding["sensitivity_level"],
                        pattern_detected=finding["pattern_detected"],
                        norm_tag=finding["norm_tag"],
                        ml_confidence=finding["ml_confidence"],
                    )
                    try:
                        from utils.logger import log_finding

                        log_finding(
                            "filesystem",
                            audit_name,
                            format_filesystem_finding_location_for_audit_log(
                                path,
                                file_path,
                                audit_name,
                                finding["file_name"],
                            ),
                            finding["sensitivity_level"],
                            finding["pattern_detected"],
                        )
                    except Exception:
                        pass
                continue
            # Optional: when use_content_type is enabled, use shared helper for the narrow PDF-only
            # slice so renamed PDFs are treated as .pdf for extraction.
            effective_ext = choose_effective_pdf_extension(
                ext, self.use_content_type, file_path
            )
            effective_ext = choose_effective_rich_media_extension(
                effective_ext, self.use_content_type, file_path
            )
            # Collect file-identity stats before read (Phase 1 — ADR-0051).
            # Stat is best-effort; failure never aborts the scan.
            _mtime_ns: int | None = None
            _size: int | None = None
            try:
                _stat = file_path.stat()
                _mtime_ns = _stat.st_mtime_ns
                _size = _stat.st_size
            except OSError:  # noqa: BLE001
                pass  # stat() best-effort for file-identity metadata
            content = _read_text_sample(
                file_path,
                effective_ext,
                self.file_sample_max_chars,
                self.file_passwords,
                rich_media_metadata=self.scan_rich_media_metadata,
                scan_image_ocr=self.scan_image_ocr,
                ocr_max_dimension=self.ocr_max_dimension,
                ocr_lang=self.ocr_lang,
                scan_for_stego=self.scan_for_stego,
            )
            res = self.scanner.scan_file_content(content, file_path)
            if res is None:
                continue
            # Compute content fingerprint from the raw byte prefix of the sample.
            # Uses the text content encoded back to UTF-8 as a best-effort proxy for
            # raw bytes (avoids re-reading the file; fast and consistent per session).
            _fingerprint: str | None = None
            try:
                if content:
                    _fingerprint = _file_content_fingerprint(
                        content.encode("utf-8", errors="replace")
                    )
            except Exception:  # noqa: BLE001
                pass  # fingerprint is optional audit metadata
            self.db_manager.save_finding(
                source_type="filesystem",
                target_name=target_name,
                path=str(file_path.parent),
                file_name=file_path.name,
                data_type=file_path.suffix.replace(".", "").upper(),
                sensitivity_level=res["sensitivity_level"],
                pattern_detected=res["pattern_detected"],
                norm_tag=res.get("norm_tag", ""),
                ml_confidence=res.get("ml_confidence", 0),
                source_mtime_ns=_mtime_ns,
                source_size=_size,
                content_fingerprint=_fingerprint,
            )
            # Phase 2 (ADR-0051): upsert cross-session file identity index.
            _sid = getattr(self.db_manager, "_current_session_id", None)
            if _sid:
                try:
                    self.db_manager.upsert_object_state(
                        target_name=target_name,
                        abs_path=str(file_path),
                        session_id=_sid,
                        mtime_ns=_mtime_ns,
                        size=_size,
                        content_fingerprint=_fingerprint,
                        sensitivity_level=res["sensitivity_level"],
                    )
                except Exception:
                    pass  # non-fatal: Phase 2 state index should not break the scan
            try:
                from utils.logger import log_finding

                log_finding(
                    "filesystem",
                    audit_name,
                    format_filesystem_finding_location_for_audit_log(
                        path,
                        file_path,
                        audit_name,
                        file_path.name,
                    ),
                    res["sensitivity_level"],
                    res["pattern_detected"],
                )
            except Exception:
                pass


def scan_archive_at_path(
    archive_path: Path,
    archive_display_name: str,
    target_name: str,
    path_display: str,
    *,
    scanner: Any,
    db_manager: Any,
    extensions: set[str],
    max_inner_size: int | None,
    file_passwords: dict[str, str],
    file_sample_max_chars: int,
    rich_media_metadata: bool = False,
    scan_image_ocr: bool = False,
    ocr_max_dimension: int = 2000,
    ocr_lang: str = "eng",
    scan_for_stego: bool = False,
    use_content_type: bool = False,
    scan_root: Path | None = None,
    audit_log_name: str | None = None,
) -> None:
    """
    Open archive at path and scan inner members; save findings with file_name like archive.zip|inner/path.txt.
    Used by FilesystemConnector and by share connectors (SMB, WebDAV, SharePoint) when scan_compressed is True.
    Inner plain-text reads use *file_sample_max_chars* (not SQL row limits).

    When *scan_root* and *audit_log_name* are set (local filesystem), audit log lines use
    ``format_filesystem_finding_location_for_audit_log`` for the third column. Share connectors
    pass only *audit_log_name* so logs stay ``archive|inner`` without a temp path.
    """
    archive_type = detect_archive_type(archive_path)
    if not archive_type:
        return
    try:
        raw_max = max_inner_size
        max_size = int(raw_max) if raw_max is not None else DEFAULT_MAX_INNER_SIZE
        max_size = max(MIN_MAX_INNER_SIZE, min(MAX_MAX_INNER_SIZE, max_size))
    except (TypeError, ValueError):
        max_size = DEFAULT_MAX_INNER_SIZE
    try:
        for member_name, data in iter_archive_members(
            archive_path,
            archive_type,
            max_size,
            extensions,
            file_passwords,
        ):
            ext = Path(member_name).suffix.lower()
            tmp_path: Path | None = None
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                    tmp.write(data)
                    tmp_path = Path(tmp.name)
                ext_use = choose_effective_pdf_extension(
                    ext, use_content_type, tmp_path
                )
                ext_use = choose_effective_rich_media_extension(
                    ext_use, use_content_type, tmp_path
                )
                content = _read_text_sample(
                    tmp_path,
                    ext_use,
                    file_sample_max_chars,
                    file_passwords,
                    rich_media_metadata=rich_media_metadata,
                    scan_image_ocr=scan_image_ocr,
                    ocr_max_dimension=ocr_max_dimension,
                    ocr_lang=ocr_lang,
                    scan_for_stego=scan_for_stego,
                )
                res = scanner.scan_file_content(content, member_name)
                if res is None:
                    continue
                db_manager.save_finding(
                    source_type="filesystem",
                    target_name=target_name,
                    path=path_display,
                    file_name=f"{archive_display_name}|{member_name}",
                    data_type=ext.replace(".", "").upper() if ext else "BIN",
                    sensitivity_level=res["sensitivity_level"],
                    pattern_detected=res["pattern_detected"],
                    norm_tag=res.get("norm_tag", ""),
                    ml_confidence=res.get("ml_confidence", 0),
                )
                try:
                    from utils.audit_log_display import (
                        format_filesystem_finding_location_for_audit_log,
                    )
                    from utils.logger import log_finding

                    log_label = audit_log_name or target_name
                    if scan_root is not None and audit_log_name is not None:
                        log_loc = format_filesystem_finding_location_for_audit_log(
                            scan_root,
                            archive_path,
                            audit_log_name,
                            f"{archive_display_name}|{member_name}",
                        )
                    else:
                        log_loc = f"{archive_display_name}|{member_name}"
                    log_finding(
                        "filesystem",
                        log_label,
                        log_loc,
                        res["sensitivity_level"],
                        res["pattern_detected"],
                    )
                except Exception:
                    pass
            finally:
                if tmp_path and tmp_path.exists():
                    tmp_path.unlink(missing_ok=True)
    except ArchiveUnsupportedError as e:
        db_manager.save_failure(
            target_name,
            "archive_unsupported",
            f"{archive_display_name}: {e}",
        )


register("filesystem", FilesystemConnector, ["name", "type", "path"])
