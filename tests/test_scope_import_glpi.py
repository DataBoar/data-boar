"""
Tests for the GLPI scope-import adapter (config/scope_import_glpi.py).

Phase E of PLAN_SCOPE_IMPORT_FROM_EXPORTS.md.
"""

import csv
import io


def _parse_csv(text: str) -> list[dict]:
    reader = csv.DictReader(io.StringIO(text))
    return list(reader)


GLPI_MINIMAL = """Name,IP Address,Serial Number,Type,Operating System,Location,Status,Domain
SRV-APP01,10.0.1.10,SN123,Server,Windows Server 2022,DC1,In use,corp.example.com
SRV-DB01,10.0.1.20,SN456,Database Server,Ubuntu 22.04,DC1,In use,corp.example.com
WS-LAPTOP01,10.0.1.30,,Laptop,Windows 11,Office,Retired,corp.example.com
"""

GLPI_FRENCH = """Nom,Adresse IP,Numero de serie,Type de materiel,Systeme d exploitation,Localisation,Statut,Domaine
SRV-FR01,10.0.2.1,FR001,Serveur,Debian 11,Paris,En production,fr.example.com
"""


def test_glpi_basic_conversion():
    """Basic GLPI export produces canonical CSV with expected rows."""
    from config.scope_import_glpi import glpi_csv_to_canonical_csv

    result = glpi_csv_to_canonical_csv(GLPI_MINIMAL)
    rows = _parse_csv(result)
    # Retired row should be skipped by default
    assert len(rows) == 2
    names = {r["name"] for r in rows}
    assert "SRV-APP01" in names
    assert "SRV-DB01" in names
    assert "WS-LAPTOP01" not in names


def test_glpi_type_mapping():
    """Database Server type maps to canonical 'database'; Server maps to 'filesystem'."""
    from config.scope_import_glpi import glpi_csv_to_canonical_csv

    result = glpi_csv_to_canonical_csv(GLPI_MINIMAL)
    rows = _parse_csv(result)
    by_name = {r["name"]: r for r in rows}
    assert by_name["SRV-APP01"]["type"] == "filesystem"
    assert by_name["SRV-DB01"]["type"] == "database"


def test_glpi_hostname_with_domain():
    """Hostname is composed as name.domain when domain is present."""
    from config.scope_import_glpi import glpi_csv_to_canonical_csv

    result = glpi_csv_to_canonical_csv(GLPI_MINIMAL)
    rows = _parse_csv(result)
    by_name = {r["name"]: r for r in rows}
    assert by_name["SRV-APP01"]["hostname"] == "SRV-APP01.corp.example.com"


def test_glpi_asset_id_from_serial():
    """Serial number is used as asset_id."""
    from config.scope_import_glpi import glpi_csv_to_canonical_csv

    result = glpi_csv_to_canonical_csv(GLPI_MINIMAL)
    rows = _parse_csv(result)
    by_name = {r["name"]: r for r in rows}
    assert by_name["SRV-APP01"]["asset_id"] == "SN123"


def test_glpi_include_retired():
    """With skip_retired=False, retired rows are included."""
    from config.scope_import_glpi import glpi_csv_to_canonical_csv

    result = glpi_csv_to_canonical_csv(GLPI_MINIMAL, skip_retired=False)
    rows = _parse_csv(result)
    assert len(rows) == 3
    names = {r["name"] for r in rows}
    assert "WS-LAPTOP01" in names


def test_glpi_source_metadata():
    """source_system and source_export_type are set correctly."""
    from config.scope_import_glpi import glpi_csv_to_canonical_csv

    result = glpi_csv_to_canonical_csv(GLPI_MINIMAL, source_system="GLPI-PROD")
    rows = _parse_csv(result)
    for row in rows:
        assert row["source_system"] == "GLPI-PROD"
        assert row["source_export_type"] == "glpi_computer_export"


def test_glpi_tags_include_os_and_location():
    """Tags pipe-join OS, location, and computer type."""
    from config.scope_import_glpi import glpi_csv_to_canonical_csv

    result = glpi_csv_to_canonical_csv(GLPI_MINIMAL)
    rows = _parse_csv(result)
    by_name = {r["name"]: r for r in rows}
    tags = by_name["SRV-APP01"]["tags"]
    assert "Windows Server 2022" in tags
    assert "DC1" in tags
    assert "Server" in tags


def test_glpi_ip_used_as_host():
    """'host' column uses IP when available."""
    from config.scope_import_glpi import glpi_csv_to_canonical_csv

    result = glpi_csv_to_canonical_csv(GLPI_MINIMAL)
    rows = _parse_csv(result)
    by_name = {r["name"]: r for r in rows}
    assert by_name["SRV-APP01"]["host"] == "10.0.1.10"
    assert by_name["SRV-APP01"]["ip"] == "10.0.1.10"


def test_glpi_empty_input():
    """Empty text returns header-only canonical CSV."""
    from config.scope_import_glpi import glpi_csv_to_canonical_csv

    result = glpi_csv_to_canonical_csv("")
    rows = _parse_csv(result)
    assert rows == []


def test_glpi_bom_stripped():
    """BOM at start of file is silently ignored."""
    from config.scope_import_glpi import glpi_csv_to_canonical_csv

    bom_text = "\ufeff" + GLPI_MINIMAL
    result = glpi_csv_to_canonical_csv(bom_text)
    rows = _parse_csv(result)
    assert len(rows) == 2


def test_glpi_french_columns():
    """French GLPI column names are mapped to canonical schema."""
    from config.scope_import_glpi import glpi_csv_to_canonical_csv

    result = glpi_csv_to_canonical_csv(GLPI_FRENCH)
    rows = _parse_csv(result)
    assert len(rows) == 1
    row = rows[0]
    assert row["name"] == "SRV-FR01"
    assert row["ip"] == "10.0.2.1"
    assert row["asset_id"] == "FR001"


def test_glpi_to_yaml_roundtrip():
    """Canonical CSV with operator-supplied path round-trips to YAML for filesystem targets.

    GLPI exports provide host+IP but not filesystem paths.  The operator adds those columns
    after reviewing the canonical CSV.  Database-type rows also require driver+database name
    (not available in GLPI exports); the operator supplies those separately.
    """
    import csv as _csv
    import io as _io

    from config.scope_import_glpi import glpi_csv_to_canonical_csv, _CANONICAL_HEADER
    from config.scope_import_csv import csv_to_fragment_yaml

    # Use only filesystem-type GLPI row for roundtrip (Server → filesystem)
    glpi_fs_only = (
        "Name,IP Address,Serial Number,Type,Operating System,Status,Domain\r\n"
        "SRV-APP01,10.0.1.10,SN123,Server,Windows Server 2022,In use,corp.example.com\r\n"
    )
    canonical = glpi_csv_to_canonical_csv(glpi_fs_only)
    rows = list(_csv.DictReader(_io.StringIO(canonical)))
    assert len(rows) == 1
    assert rows[0]["type"] == "filesystem"

    # Operator adds path after scope review.
    rows[0]["path"] = "/srv/data"

    buf = _io.StringIO()
    writer = _csv.DictWriter(
        buf, fieldnames=_CANONICAL_HEADER, extrasaction="ignore", lineterminator="\r\n"
    )
    writer.writeheader()
    writer.writerows(rows)
    patched_csv = buf.getvalue()

    yaml_text = csv_to_fragment_yaml(patched_csv)
    assert "SRV-APP01" in yaml_text
    assert "/srv/data" in yaml_text
