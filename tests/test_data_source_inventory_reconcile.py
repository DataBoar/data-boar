"""Test for inventory reconciliation with findings (#2273).

The Data source inventory sheet only lists persisted inventory snapshots.
Targets with findings but no inventory row should get a 'not_probed' row.
"""

from pathlib import Path

from openpyxl import load_workbook

from core.database import LocalDBManager
from report.generator import generate_report


def _find_inventory_row(wb, target_name: str) -> dict | None:
    """Find a row in the Data source inventory sheet by target name."""
    if "Data source inventory" not in wb.sheetnames:
        return None
    ws = wb["Data source inventory"]
    for row_idx in range(2, ws.max_row + 1):
        if ws.cell(row_idx, 1).value == target_name:
            return {
                "Target": ws.cell(row_idx, 1).value,
                "Source type": ws.cell(row_idx, 2).value or "",
                "Product": ws.cell(row_idx, 3).value or "",
                "Product version": ws.cell(row_idx, 4).value or "",
                "Protocol/API version": ws.cell(row_idx, 5).value or "",
                "Transport security": ws.cell(row_idx, 6).value or "",
                "Inventory details (executive)": ws.cell(row_idx, 7).value or "",
            }
    return None


def test_filesystem_target_with_findings_no_inventory_gets_not_probed_row(
    tmp_path: Path,
) -> None:
    """CASE (a): A filesystem target with findings but no inventory yields a not_probed row."""
    db_path = str(tmp_path / "report_inventory_fs.db")
    mgr = LocalDBManager(db_path)
    try:
        sid = "session-fs-findings"
        mgr.set_current_session_id(sid)
        mgr.create_session_record(sid)

        # Add a filesystem finding (no inventory row exists)
        mgr.save_finding(
            source_type="filesystem",
            target_name="local-data-dir",
            path="/data",
            file_name="customers.csv",
            data_type="csv",
            sensitivity_level="HIGH",
            pattern_detected="CPF",
            norm_tag="LGPD Art. 5",
            ml_confidence=95,
        )

        mgr.finish_session(sid)
        out = generate_report(mgr, sid, output_dir=str(tmp_path), config={})
        assert out is not None

        wb = load_workbook(out)
        row = _find_inventory_row(wb, "local-data-dir")
        assert row is not None, (
            "Expected inventory row for filesystem target with findings"
        )
        assert row["Source type"] == "filesystem"
        assert row["Product"] == ""
        assert row["Transport security"] == "not_probed"
        assert "not_probed" in row["Inventory details (executive)"]
    finally:
        mgr.dispose()


def test_database_target_with_inventory_row_not_duplicated(
    tmp_path: Path,
) -> None:
    """CASE (b): A database target with an inventory row is not duplicated."""
    db_path = str(tmp_path / "report_inventory_db.db")
    mgr = LocalDBManager(db_path)
    try:
        sid = "session-db-inventory"
        mgr.set_current_session_id(sid)
        mgr.create_session_record(sid)

        # Add a database finding
        mgr.save_finding(
            source_type="database",
            target_name="db-primary",
            server_ip="192.168.1.10",
            schema_name="public",
            table_name="users",
            column_name="cpf",
            data_type="TEXT",
            sensitivity_level="HIGH",
            pattern_detected="CPF",
            norm_tag="LGPD Art. 5",
            ml_confidence=95,
        )

        # Add the corresponding inventory row
        mgr.save_data_source_inventory(
            target_name="db-primary",
            source_type="database",
            product="PostgreSQL",
            product_version="15.4",
            protocol_or_api_version="postgresql",
            transport_security="tls=enabled",
            raw_details='{"driver":"psycopg","sslmode":"verify-full"}',
        )

        mgr.finish_session(sid)
        out = generate_report(mgr, sid, output_dir=str(tmp_path), config={})
        assert out is not None

        wb = load_workbook(out)
        row = _find_inventory_row(wb, "db-primary")
        assert row is not None, "Expected inventory row for database target"
        # Should have the persisted inventory values, not not_probed
        assert row["Source type"] == "database"
        assert row["Product"] == "PostgreSQL"
        assert row["Product version"] == "15.4"
        assert row["Transport security"] == "tls=enabled"
        assert (
            row["Inventory details (executive)"]
            == "driver=psycopg; sslmode=verify-full"
        )
    finally:
        mgr.dispose()


def test_mixed_scan_database_and_filesystem_targets(
    tmp_path: Path,
) -> None:
    """CASE (c): A mixed scan (database with row + filesystem/smb without) yields rows for all targets."""
    db_path = str(tmp_path / "report_inventory_mixed.db")
    mgr = LocalDBManager(db_path)
    try:
        sid = "session-mixed"
        mgr.set_current_session_id(sid)
        mgr.create_session_record(sid)

        # Database target WITH inventory row
        mgr.save_finding(
            source_type="database",
            target_name="db-primary",
            server_ip="192.168.1.10",
            schema_name="public",
            table_name="customers",
            column_name="email",
            data_type="VARCHAR",
            sensitivity_level="MEDIUM",
            pattern_detected="EMAIL",
            norm_tag="GDPR Art. 4(1)",
            ml_confidence=85,
        )
        mgr.save_data_source_inventory(
            target_name="db-primary",
            source_type="database",
            product="MySQL",
            product_version="8.0",
            protocol_or_api_version="mysql",
            transport_security="tls=enabled",
            raw_details='{"driver":"mysql-connector"}',
        )

        # Filesystem target WITHOUT inventory row
        mgr.save_finding(
            source_type="filesystem",
            target_name="file-share-data",
            path="/mnt/share",
            file_name="employees.xlsx",
            data_type="xlsx",
            sensitivity_level="HIGH",
            pattern_detected="CPF",
            norm_tag="LGPD Art. 5",
            ml_confidence=98,
        )

        # SMB target without inventory row
        mgr.save_finding(
            source_type="filesystem",
            target_name="smb-backup",
            path="\\\\backup-server\\data",
            file_name="backup.sql",
            data_type="sql",
            sensitivity_level="HIGH",
            pattern_detected="CPF",
            norm_tag="LGPD Art. 5",
            ml_confidence=90,
        )

        mgr.finish_session(sid)
        out = generate_report(mgr, sid, output_dir=str(tmp_path), config={})
        assert out is not None

        wb = load_workbook(out)

        # Check db-primary row (should have persisted values)
        db_row = _find_inventory_row(wb, "db-primary")
        assert db_row is not None
        assert db_row["Product"] == "MySQL"
        assert db_row["Transport security"] == "tls=enabled"

        # Check file-share-data row (should be not_probed)
        fs_row = _find_inventory_row(wb, "file-share-data")
        assert fs_row is not None, (
            "Expected inventory row for filesystem target with findings"
        )
        assert fs_row["Source type"] == "filesystem"
        assert fs_row["Transport security"] == "not_probed"

        # Check smb-backup row (should be not_probed)
        smb_row = _find_inventory_row(wb, "smb-backup")
        assert smb_row is not None, (
            "Expected inventory row for SMB target with findings"
        )
        assert smb_row["Source type"] == "filesystem"
        assert smb_row["Transport security"] == "not_probed"
    finally:
        mgr.dispose()


def test_target_with_no_findings_no_inventory_not_in_sheet(
    tmp_path: Path,
) -> None:
    """CASE (d): A target with no findings and no inventory row does not appear in the sheet."""
    db_path = str(tmp_path / "report_inventory_none.db")
    mgr = LocalDBManager(db_path)
    try:
        sid = "session-no-findings"
        mgr.set_current_session_id(sid)
        mgr.create_session_record(sid)

        # No findings at all - just an inventory row for a target that wasn't scanned
        mgr.save_data_source_inventory(
            target_name="never-scanned-target",
            source_type="database",
            product="Oracle",
            product_version="19c",
            protocol_or_api_version="oracle",
            transport_security="tls=enabled",
            raw_details='{"driver":"jdbc-oracle"}',
        )

        mgr.finish_session(sid)
        out = generate_report(mgr, sid, output_dir=str(tmp_path), config={})
        # With no findings, generate_report returns None (early check in line 1611)
        assert out is None, "Report should not be generated when there are no findings"
    finally:
        mgr.dispose()
