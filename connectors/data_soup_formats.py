"""
Tier-1 "data soup" text extraction for additional file formats (see PLAN_ADDITIONAL_DATA_SOUP_FORMATS.md).

Optional dependencies: ``pyarrow``, ``fastavro``, ``dbfread`` (install ``pip install -e ".[dataformats]"``).
"""

from __future__ import annotations

import re
import zipfile
from pathlib import Path


def sample_epub_text(path: Path, max_chars: int) -> str:
    """OCF EPUB: read XHTML/HTML members from the ZIP; strip tags; bounded."""
    parts: list[str] = []
    total = 0
    try:
        with zipfile.ZipFile(path, "r") as z:
            names = z.namelist()
            # Optional: follow container.xml for OPF path (fallback: scan all html/xhtml)
            opf_names = [n for n in names if n.lower().endswith(".opf")]
            html_names = [
                n
                for n in names
                if n.lower().endswith((".xhtml", ".html", ".htm"))
                and "META-INF" not in n.replace("\\", "/").split("/")
            ]
            to_read = html_names
            if not to_read and opf_names:
                try:
                    opf_xml = z.read(opf_names[0]).decode("utf-8", errors="replace")
                    # spine itemrefs -> hrefs (lightweight; namespaces vary)
                    for m in re.finditer(
                        r'href\s*=\s*["\']([^"\']+\.(?:xhtml|html|htm))["\']',
                        opf_xml,
                        re.I,
                    ):
                        href = m.group(1).split("/")[-1]
                        for n in names:
                            if n.endswith(href) or n.endswith("/" + href):
                                to_read.append(n)
                                break
                except Exception:
                    to_read = html_names
            for name in to_read[:200]:
                if total >= max_chars:
                    break
                low = name.lower()
                if low.endswith(".opf"):
                    continue
                try:
                    raw = z.read(name).decode("utf-8", errors="replace")
                except Exception:
                    continue
                # Strip tags; keep text nodes roughly
                text = re.sub(r"<[^>]+>", " ", raw)
                text = re.sub(r"\s+", " ", text).strip()
                if text:
                    parts.append(text)
                    total += len(text)
    except Exception:
        return ""
    out = " ".join(parts)
    return out[:max_chars]


def sample_parquet_text(path: Path, max_chars: int) -> str:
    try:
        import pyarrow.parquet as pq  # type: ignore[import-untyped]
    except ImportError:
        return ""
    try:
        pf = pq.ParquetFile(path)
        parts: list[str] = [str(pf.schema_arrow)[:800]]
        if pf.num_row_groups > 0:
            table = pf.read_row_group(0)
            parts.append(str(table.slice(0, 48).to_pydict()))
        return " ".join(parts)[:max_chars]
    except Exception:
        return ""


def sample_feather_text(path: Path, max_chars: int) -> str:
    try:
        import pyarrow.feather as feather  # type: ignore[import-untyped]
    except ImportError:
        return ""
    try:
        t = feather.read_table(path)
        return str(t.slice(0, 50).to_pydict())[:max_chars]
    except Exception:
        return ""


def sample_orc_text(path: Path, max_chars: int) -> str:
    try:
        import pyarrow.orc as orc  # type: ignore[import-untyped]
    except ImportError:
        return ""
    try:
        with orc.ORCFile(path) as f:
            t = f.read()
        return str(t.slice(0, 50).to_pydict())[:max_chars]
    except Exception:
        return ""


def sample_avro_text(path: Path, max_chars: int) -> str:
    try:
        import fastavro  # type: ignore[import-untyped]
    except ImportError:
        return ""
    try:
        with open(path, "rb") as fo:
            reader = fastavro.reader(fo)
            schema = str(reader.schema)[:800]
            rows: list[str] = []
            for i, rec in enumerate(reader):
                rows.append(str(rec)[:400])
                if i >= 24:
                    break
            return (schema + " " + " ".join(rows))[:max_chars]
    except Exception:
        return ""


def sample_dbf_text(path: Path, max_chars: int) -> str:
    try:
        from dbfread import DBF  # type: ignore[import-untyped]
    except ImportError:
        return ""
    try:
        table = DBF(
            str(path),
            encoding="utf-8",
            ignore_missing_memofile=True,
            char_decode_errors="replace",
        )
        field_names = [str(getattr(f, "name", f)) for f in table.fields[:80]]
        parts: list[str] = [" ".join(field_names)]
        for i, rec in enumerate(table):
            parts.append(" ".join(str(v) for v in rec.values())[:500])
            if i >= 40:
                break
        return " ".join(parts)[:max_chars]
    except Exception:
        return ""
