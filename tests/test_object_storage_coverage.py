"""Partial coverage: the inventory block and the report (epic #2306, task 2306.2).

Source: ``docs/desenho/2306.md`` (revision 2 and later), section 10 (coverage block of the
inventory, DEC-12) and section 14 (sheet "Target coverage", line "Coverage" of "Report info",
hints of ``failure_hint``). Cases ``D2306-70`` .. ``D2306-75``.

D-70 runs the connector against the simulated S3. D-71 to D-73 write inventory rows straight
into a ``LocalDBManager`` and build the workbook with ``generate_report``: the report reads the
generic block of any inventory row, without looking at the type.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from openpyxl import load_workbook

from core.database import failure_hint
from tests.object_storage_dev_harness import (
    COVERAGE_KEYS,
    MIB,
    TARGET_NAME,
    Harness,
    executive,
    s3_target,
)
from tests.s3_fake import FakeDB

SESSION = "session-coverage-d2306"


@pytest.fixture
def h(monkeypatch: pytest.MonkeyPatch) -> Harness:
    return Harness(monkeypatch)


# ----------------------------------------------------------------------------
# D-70: the coverage block of the inventory
# ----------------------------------------------------------------------------


def test_D2306_70_bloco_de_cobertura_completo(h: Harness) -> None:
    """D2306-70: everything under the prefix scanned -> coverage complete."""
    fake = h.s3()
    out = h.run(fake.transport, s3_target())

    ex = executive(out.db)
    assert ex["coverage"] == "complete"
    assert ex["objects_not_scanned"] == 0
    assert ex["bytes_not_scanned"] == 0
    assert ex["objects_unknown_size"] == 0
    assert ex["listing_complete"] is True
    assert ex["not_scanned_by_reason"] == {}
    assert ex["limits_disabled"] == []
    # Revision 6, R6-6: the generic keys and objects_scanned.
    assert COVERAGE_KEYS <= set(ex)
    assert ex["objects_listed"] == 3
    assert ex["objects_scanned"] == 3


def test_D2306_70_bloco_de_cobertura_parcial(h: Harness) -> None:
    """D2306-70: one too_large of 5 MiB and one entry without Size -> partial,
    objects_not_scanned 2, bytes_not_scanned 5242880 and objects_unknown_size 1."""
    fake = h.s3(
        {
            "corpus/grande.txt": b"x",
            "corpus/sem-size.txt": b"x",
            "corpus/ok.txt": b"x",
        }
    )
    fake.lie_size("corpus/grande.txt", 5 * MIB, 1)
    fake.lie_size("corpus/sem-size.txt", None, 1)
    out = h.run(fake.transport, s3_target(max_object_bytes=MIB))

    ex = executive(out.db)
    assert ex["coverage"] == "partial"
    assert ex["objects_not_scanned"] == 2
    assert ex["bytes_not_scanned"] == 5 * MIB
    assert ex["objects_unknown_size"] == 1
    assert ex["listing_complete"] is True
    assert ex["not_scanned_by_reason"] == {"too_large": 1, "invalid_key": 1}
    assert ex["objects_scanned"] == 1


def test_D2306_70_listagem_parada_em_max_objects(h: Harness) -> None:
    """D2306-70: the listing stopped at max_objects -> listing_complete false, partial."""
    fake = h.s3({f"corpus/k{i:02d}.txt": b"x" for i in range(12)})
    out = h.run(fake.transport, s3_target(max_objects=5))

    ex = executive(out.db)
    assert ex["listing_complete"] is False
    assert ex["coverage"] == "partial"
    assert ex["objects_listed"] == 5


def test_D2306_70_download_failed_no_meio_deixa_parcial(h: Harness) -> None:
    """D2306-70: one download_failed in the middle -> partial."""
    fake = h.s3()
    fake.error_on("GetObject", key="corpus/b.txt", status=404, code="NoSuchKey")
    out = h.run(fake.transport, s3_target())

    ex = executive(out.db)
    assert ex["coverage"] == "partial"
    assert ex["objects_not_scanned"] == 1
    assert ex["not_scanned_by_reason"] == {"download_failed": 1}
    assert ex["objects_scanned"] == 2


def test_D2306_70_invariante_de_contagem(h: Harness) -> None:
    """D2306-70 and R6-6: objects_listed = objects_scanned + objects_not_scanned +
    folder_marker + extension; the last two are out of scope and out of the coverage."""
    fake = h.s3(
        {
            "corpus/a.txt": b"x",
            "corpus/b.txt": b"x",
            "corpus/dir/": b"",
            "corpus/tool.exe": b"MZ",
            "corpus/grande.txt": b"x" * 20,
        }
    )
    out = h.run(fake.transport, s3_target(max_object_bytes=10))

    ex = executive(out.db)
    assert ex["objects_listed"] == 5
    assert ex["objects_scanned"] == 2
    assert ex["objects_not_scanned"] == 1
    assert ex["not_scanned_by_reason"] == {"too_large": 1}
    assert ex["objects_listed"] == ex["objects_scanned"] + ex["objects_not_scanned"] + 2


# ----------------------------------------------------------------------------
# D-71 to D-73: the report
# ----------------------------------------------------------------------------


def _block(coverage: str, **extra: Any) -> dict[str, Any]:
    partial = coverage == "partial"
    block: dict[str, Any] = {
        "engine": "s3",
        "status": "completed",
        "objects_listed": 3,
        "objects_downloaded": 2 if partial else 3,
        "objects_scanned": 2 if partial else 3,
        "bytes_downloaded": 100,
        "coverage": coverage,
        "objects_not_scanned": 1 if partial else 0,
        "bytes_not_scanned": 2 * MIB if partial else 0,
        "objects_unknown_size": 0,
        "listing_complete": True,
        "not_scanned_by_reason": {"too_large": 1} if partial else {},
        "limits_disabled": [],
    }
    block.update(extra)
    return block


def _report(
    tmp_path: Path,
    rows: list[tuple[str, str, dict[str, Any] | None]],
    failures: list[tuple[str, str, str]],
    findings: list[dict[str, Any]] | None = None,
) -> Any:
    """Write inventory rows, failures and findings into a real LocalDBManager and load the
    workbook built by generate_report."""
    from core.database import LocalDBManager
    from report.generator import generate_report

    tmp_path.mkdir(parents=True, exist_ok=True)
    mgr = LocalDBManager(str(tmp_path / "audit_cov.db"))
    try:
        mgr.set_current_session_id(SESSION)
        mgr.create_session_record(SESSION)
        db = FakeDB(real=mgr)
        for target, source_type, executive_block in rows:
            raw = (
                None
                if executive_block is None
                else json.dumps({"executive": executive_block, "technical": {}})
            )
            db.save_data_source_inventory(
                target, source_type, "Product", None, "proto", "tls=https", raw
            )
        for target, reason, detail in failures:
            db.save_failure(target, reason, detail)
        for finding in findings or []:
            db.save_finding("filesystem", **finding)
        mgr.finish_session(SESSION)
        path = generate_report(mgr, SESSION, output_dir=str(tmp_path), config={})
        assert path is not None
        return load_workbook(path)
    finally:
        mgr.dispose()


def _rows(wb: Any, name: str) -> list[dict[str, Any]]:
    assert name in wb.sheetnames, (name, wb.sheetnames)
    ws = wb[name]
    headers = [c.value for c in ws[1]]
    return [
        dict(zip(headers, [c.value for c in row], strict=False))
        for row in ws.iter_rows(min_row=2)
    ]


def _info(wb: Any, field: str) -> list[str]:
    return [
        str(r["Value"]) for r in _rows(wb, "Report info") if r.get("Field") == field
    ]


COLUMNS = [
    "Target",
    "Source type",
    "Coverage",
    "Objects listed",
    "Objects scanned",
    "Objects not scanned",
    "Bytes not scanned",
    "Bytes not scanned (readable)",
    "Objects with unknown size",
    "Listing complete",
    "Not scanned by reason",
    "Limits disabled",
    "Note",
]


def test_D2306_71_parcial_sem_achados_nunca_e_resultado_limpo(tmp_path: Path) -> None:
    """D2306-71: one partial inventory row and zero findings for the target -> the
    "Target coverage" sheet right after "Report info" with PARTIAL (highlighted) and the
    Note "No findings in the scanned part only..."; "Report info" has the Coverage line
    "PARTIAL: 1 target(s) ..."."""
    wb = _report(
        tmp_path,
        [(TARGET_NAME, "object_storage", _block("partial"))],
        [(TARGET_NAME, "skipped", "1 objects skipped: too_large=1")],
    )

    assert "Target coverage" in wb.sheetnames
    assert wb.sheetnames.index("Target coverage") == (
        wb.sheetnames.index("Report info") + 1
    )
    ws = wb["Target coverage"]
    header = [c.value for c in ws[1]]
    # Section 14 with revision 6 (R6-6): the readable column right after the integer one.
    assert header[: len(COLUMNS)] == COLUMNS
    rows = _rows(wb, "Target coverage")
    assert len(rows) == 1
    row = rows[0]
    assert row["Target"] == TARGET_NAME
    assert row["Source type"] == "object_storage"
    assert row["Coverage"] == "PARTIAL"
    assert int(row["Objects not scanned"]) == 1
    assert int(row["Bytes not scanned"]) == 2 * MIB
    assert row["Bytes not scanned (readable)"] == "2.0 MiB"
    assert int(row["Objects scanned"]) == 2
    assert row["Not scanned by reason"] == "too_large=1"
    assert row["Note"] == (
        "No findings in the scanned part only. 1 objects (2.0 MiB) were not scanned; "
        "this is not a clean result."
    )
    coverage_cell = ws.cell(row=2, column=header.index("Coverage") + 1)
    assert coverage_cell.fill is not None and coverage_cell.fill.fill_type is not None
    info = _info(wb, "Coverage")
    assert len(info) == 1
    assert info[0].startswith("PARTIAL: 1 target(s)")


def test_D2306_71_parcial_com_achados_e_listagem_incompleta(tmp_path: Path) -> None:
    """D2306-71 (section 14, item 2): PARTIAL with findings, and the extra sentence when the
    listing stopped before the end."""
    finding = {
        "target_name": TARGET_NAME,
        "path": "s3://databoar-sintetico/corpus/a.txt",
        "file_name": "a.txt",
        "data_type": "TXT",
        "sensitivity_level": "HIGH",
        "pattern_detected": "LGPD_CPF",
        "norm_tag": "LGPD Art. 5",
        "ml_confidence": 100,
    }
    wb = _report(
        tmp_path,
        [(TARGET_NAME, "object_storage", _block("partial", listing_complete=False))],
        [(TARGET_NAME, "limit_reached", "max_objects reached (3)")],
        [finding],
    )

    (row,) = _rows(wb, "Target coverage")
    note = str(row["Note"])
    assert note.startswith(
        "1 objects (2.0 MiB) were not scanned; findings cover the scanned part only."
    )
    assert note.endswith(
        "Listing stopped before the end; the number of unlisted objects is unknown."
    )


def test_D2306_71_unidades_legiveis_e_motivos_em_ordem(tmp_path: Path) -> None:
    """R6-6: "Bytes not scanned (readable)" in binary units with one decimal (below 1024,
    an integer with B), and "Not scanned by reason" as key=value in alphabetical order."""
    cases = {
        "alvo-b": (512, "512 B"),
        "alvo-kib": (2048, "2.0 KiB"),
        "alvo-mib": (2 * MIB, "2.0 MiB"),
        "alvo-gib": (1536 * MIB, "1.5 GiB"),
        "alvo-tib": (1024 * 1024 * MIB, "1.0 TiB"),
    }
    rows = [
        (
            name,
            "object_storage",
            _block(
                "partial",
                bytes_not_scanned=size,
                objects_not_scanned=3,
                objects_scanned=0,
                not_scanned_by_reason={"unsafe_key": 2, "too_large": 1},
            ),
        )
        for name, (size, _readable) in cases.items()
    ]
    wb = _report(tmp_path, rows, [(name, "skipped", "x") for name in cases])

    got = {r["Target"]: r for r in _rows(wb, "Target coverage")}
    assert set(got) == set(cases)
    for name, (size, readable) in cases.items():
        assert int(got[name]["Bytes not scanned"]) == size, name
        assert got[name]["Bytes not scanned (readable)"] == readable, name
        assert got[name]["Not scanned by reason"] == "too_large=1, unsafe_key=2", name
        assert f"3 objects ({readable})" in str(got[name]["Note"]), name


def test_D2306_72_so_completo_ou_sem_bloco(tmp_path: Path) -> None:
    """D2306-72: only complete coverage -> the sheet lists it, the Note is empty, and
    "Report info" has no Coverage line; with no row carrying the block, no sheet at all and
    no Coverage line either."""
    wb = _report(
        tmp_path / "a",
        [(TARGET_NAME, "object_storage", _block("complete"))],
        [(TARGET_NAME, "skipped", "x")],
    )
    (row,) = _rows(wb, "Target coverage")
    assert row["Coverage"] == "COMPLETE"
    assert row["Note"] in (None, "")
    assert _info(wb, "Coverage") == []

    wb = _report(
        tmp_path / "b",
        [("db-alvo", "database", None)],
        [("db-alvo", "error", "x")],
    )
    assert "Target coverage" not in wb.sheetnames
    assert _info(wb, "Coverage") == []


def test_D2306_73_linha_sem_bloco_fica_fora_da_cobertura(tmp_path: Path) -> None:
    """D2306-73: an inventory row of another connector without the block does not show in
    "Target coverage", and "Data source inventory" still lists both rows."""
    wb = _report(
        tmp_path,
        [
            ("db-alvo", "database", {"engine": "postgresql", "status": "completed"}),
            (TARGET_NAME, "object_storage", _block("partial")),
        ],
        [(TARGET_NAME, "skipped", "1 objects skipped: too_large=1")],
    )

    rows = _rows(wb, "Target coverage")
    assert [r["Target"] for r in rows] == [TARGET_NAME]
    inventory = _rows(wb, "Data source inventory")
    names = {str(v) for r in inventory for v in r.values() if v is not None}
    assert "db-alvo" in names
    assert TARGET_NAME in names


# ----------------------------------------------------------------------------
# D-75: hints
# ----------------------------------------------------------------------------

# Revision 6, R6-1: the 11 reasons with a hint of their own ("error" stays generic).
NEW_REASONS = [
    "config_error",
    "not_found",
    "throttled",
    "skipped",
    "limit_reached",
    "too_large",
    "unsafe_key",
    "size_mismatch",
    "download_failed",
    "protocol_error",
    "scope_violation",
]


@pytest.mark.parametrize("reason", NEW_REASONS)
def test_D2306_75_failure_hint_tem_dica_propria(reason: str) -> None:
    """D2306-75: failure_hint returns a non-empty text, different from the generic one, for
    each new reason of sections 11 and 14 (item 5) and of the table of "Onde cada peça
    mora" (scope_violation)."""
    generic = failure_hint("a-reason-nobody-uses")
    hint = failure_hint(reason)
    assert hint
    assert hint != generic


def test_D2306_75_dica_de_limit_reached_diz_como_subir_o_limite() -> None:
    """D2306-75 (section 14, item 5): the limit_reached hint names the per-target limits."""
    hint = failure_hint("limit_reached")
    for key in ("max_objects", "max_download_bytes", "max_object_bytes"):
        assert key in hint
