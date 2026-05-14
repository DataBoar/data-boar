"""
GLPI asset export → canonical scope-import CSV adapter (Phase E, PLAN_SCOPE_IMPORT_FROM_EXPORTS).

GLPI (Gestion Libre du Parc Informatique) exports via *Assets → Computers → Export CSV* typically
include the columns below.  This adapter normalises the most common variants into the
:mod:`config.scope_import_csv` canonical schema so the result can be passed directly to
``scripts/scope_import_csv.py``.

Typical GLPI Computer export columns (case-insensitive; spaces/dashes normalised):
  - ``Name`` / ``Computer Name`` → ``name`` (and ``hostname``)
  - ``IP Address`` / ``IP`` → ``ip``
  - ``Domain`` → included in ``hostname`` hint when present
  - ``Type`` / ``Computer Type`` → mapped to target type (servers → ``filesystem``; DB class → ``database``; …)
  - ``Operating System`` → included in ``tags``
  - ``Location`` → included in ``tags``
  - ``Serial Number`` / ``Serial`` → forwarded as ``asset_id``
  - ``Inventory Number`` / ``Inventory`` → forwarded as ``asset_id`` when serial absent
  - ``Status`` / ``State`` → rows with status *Retired* / *Disposed* are skipped by default

Canonical columns emitted (subset):
  ``type, name, host, ip, asset_id, hostname, tags, path_hints, source_system, source_export_type``

Usage::

    from config.scope_import_glpi import glpi_csv_to_canonical_csv
    canonical_text = glpi_csv_to_canonical_csv(raw_glpi_csv_text)
    # then pass canonical_text to config.scope_import_csv.parse_csv_to_yaml_fragment

See ``scripts/scope_import_glpi.py`` for the CLI wrapper.
"""

from __future__ import annotations

import csv
import io
import re

# Columns emitted in the canonical CSV output.
_CANONICAL_HEADER = [
    "type",
    "name",
    "host",
    "path",  # filesystem: must be filled by operator post-import
    "driver",  # database: must be filled by operator post-import
    "ip",
    "port",
    "asset_id",
    "hostname",
    "tags",
    "path_hints",
    "source_system",
    "source_export_type",
]

# GLPI column aliases → canonical name (after norm_header: lower, spaces→_).
_GLPI_COLUMN_MAP: dict[str, str] = {
    "name": "glpi_name",
    "computer_name": "glpi_name",
    "computer": "glpi_name",
    "nom": "glpi_name",  # French locale
    "ip_address": "ip",
    "ip_addresses": "ip",
    "ip": "ip",
    "adresse_ip": "ip",  # French
    "serial_number": "serial",
    "serial": "serial",
    "numero_de_serie": "serial",
    "inventory_number": "inventory_no",
    "inventorynumber": "inventory_no",
    "numero_d_inventaire": "inventory_no",
    "type": "computer_type",
    "computer_type": "computer_type",
    "type_de_materiel": "computer_type",
    "operating_system": "os",
    "operatingsystem": "os",
    "os": "os",
    "systeme_d_exploitation": "os",
    "location": "location",
    "localisation": "location",
    "domain": "domain",
    "domaine": "domain",
    "status": "status",
    "state": "status",
    "etat": "status",
    "statut": "status",
}

# Computer types that suggest a database role.
_DB_TYPE_HINTS = frozenset(
    {
        "database",
        "db",
        "dbserver",
        "db server",
        "database server",
        "serveur base de données",
    }
)

# Statuses that mean the asset is decommissioned — skip by default.
_RETIRED_STATUSES = frozenset(
    {
        "retired",
        "disposed",
        "decommissioned",
        "decomm",
        "hors_service",
        "réformé",
        "recycled",
    }
)


def _norm_header(h: str) -> str:
    """Lowercase + replace spaces/dashes/dots with underscores."""
    return re.sub(r"[\s\-\.]+", "_", (h or "").strip().lower())


def _norm_status(raw: str | None) -> str:
    return re.sub(r"[\s\-]", "_", (raw or "").strip().lower())


def _detect_type(computer_type: str) -> str:
    """Map GLPI computer type to a canonical scope-import type."""
    t = (computer_type or "").strip().lower()
    if t in _DB_TYPE_HINTS:
        return "database"
    # Default: filesystem-accessible host (server, laptop, VM, etc.)
    return "filesystem"


def _build_tags(os_val: str, location: str, computer_type: str) -> str:
    """Combine OS, location, and computer_type into a pipe-separated tag string."""
    parts: list[str] = []
    for v in (os_val, location, computer_type):
        s = (v or "").strip()
        if s:
            parts.append(s)
    return "|".join(parts) if parts else ""


def glpi_csv_to_canonical_csv(
    raw_text: str,
    *,
    skip_retired: bool = True,
    default_type: str = "filesystem",
    source_system: str = "GLPI",
) -> str:
    """Convert a GLPI Computer export CSV to the canonical scope-import CSV format.

    Parameters
    ----------
    raw_text:
        Raw UTF-8 (or latin-1 decoded) text from a GLPI CSV export.
    skip_retired:
        If *True* (default), rows whose ``status`` maps to *retired / decommissioned*
        are silently dropped.  Set to *False* to include all rows.
    default_type:
        Canonical target type used when the GLPI ``Type`` column is absent or
        unrecognised.  Defaults to ``"filesystem"``.
    source_system:
        Value written to the ``source_system`` column (default ``"GLPI"``).

    Returns
    -------
    str
        UTF-8 canonical CSV text with header row ``_CANONICAL_HEADER``.
    """
    # Detect and normalise BOM + encoding quirks.
    text = raw_text.lstrip("\ufeff")

    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        return _empty_canonical_csv()

    # Build normalised field → original field mapping.
    norm_to_orig: dict[str, str] = {_norm_header(f): f for f in reader.fieldnames}

    # Build semantic_key → original column name, via _GLPI_COLUMN_MAP.
    # _GLPI_COLUMN_MAP: {normalised_glpi_col → semantic_key}
    # Invert: semantic_key → original_col (first match wins)
    semantic_to_orig: dict[str, str] = {}
    for norm_glpi_col, sem_key in _GLPI_COLUMN_MAP.items():
        if norm_glpi_col in norm_to_orig and sem_key not in semantic_to_orig:
            semantic_to_orig[sem_key] = norm_to_orig[norm_glpi_col]

    def _get(row: dict, semantic_key: str) -> str:
        """Return row value by semantic key; empty string if column absent."""
        orig = semantic_to_orig.get(semantic_key)
        if orig is None:
            return ""
        return (row.get(orig) or "").strip()

    out = io.StringIO()
    writer = csv.DictWriter(
        out,
        fieldnames=_CANONICAL_HEADER,
        extrasaction="ignore",
        lineterminator="\r\n",
    )
    writer.writeheader()

    for row in reader:
        status = _get(row, "status")
        if skip_retired and _norm_status(status) in _RETIRED_STATUSES:
            continue

        glpi_name = _get(row, "glpi_name")
        ip = _get(row, "ip").split(";")[0].strip()  # take first IP if multi-value
        serial = _get(row, "serial")
        inventory_no = _get(row, "inventory_no")
        computer_type_raw = _get(row, "computer_type")
        os_val = _get(row, "os")
        location = _get(row, "location")
        domain = _get(row, "domain")

        # Compose hostname: name + domain when both present.
        hostname = glpi_name
        if domain and glpi_name and "." not in glpi_name:
            hostname = f"{glpi_name}.{domain}"

        asset_id = serial or inventory_no

        canonical_type = (
            _detect_type(computer_type_raw) if computer_type_raw else default_type
        )
        tags = _build_tags(os_val, location, computer_type_raw)

        writer.writerow(
            {
                "type": canonical_type,
                "name": glpi_name,
                "host": ip or hostname,
                "path": "",  # operator fills post-import for filesystem targets
                "driver": "",  # operator fills post-import for database targets
                "port": "",
                "ip": ip,
                "asset_id": asset_id,
                "hostname": hostname,
                "tags": tags,
                "path_hints": "",
                "source_system": source_system,
                "source_export_type": "glpi_computer_export",
            }
        )

    return out.getvalue()


def _empty_canonical_csv() -> str:
    """Return a header-only canonical CSV (no data rows)."""
    buf = io.StringIO()
    writer = csv.DictWriter(
        buf,
        fieldnames=_CANONICAL_HEADER,
        extrasaction="ignore",
        lineterminator="\r\n",
    )
    writer.writeheader()
    return buf.getvalue()
