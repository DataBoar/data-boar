"""#1322 — per-table worker pool inside one SQL target.

Contract under test (PLAN_DB_PER_TABLE_PARALLELISM.md), same pattern as the
filesystem pool of #1820:

(a) Exact parity of persisted findings, scan_failures and table checkpoints
    between serial and parallel runs (same rows, same fields, same order) on a
    synthetic SQLite source with several tables and columns; DB writes only
    on the target thread.
(b) ``_intra_target_workers`` = 1 (or absent) keeps the serial path: no pool.
(c) The pool never exceeds the tier worker cap (#551 ``worker_cap`` /
    ``dbmax_workers`` claim, #856 open-mode clamp); the engine derives the
    per-target budget from the already-clamped ``scan.max_workers``; the
    connection pool is sized so every worker gets its own connection; the
    existing brakes (``inter_query_delay_ms``, adaptive rate limit) and an
    in-memory SQLite source keep the target serial.
(d) Interrupt (Ctrl+C / SIGTERM mapped to KeyboardInterrupt) or a simulated
    hard kill in the middle of a table, then ``--resume``: completed tables
    are not re-scanned, nothing is lost or duplicated, the final result is
    identical to an uninterrupted scan (the in-progress table is re-scanned
    and its partial findings replaced, matching names literally).
(e) A sampling failure on one column neither stops the pool nor loses other
    findings; an unexpected exception aborts the target at the same ordered
    position as the serial run.
(f) Stopping leaves no pool thread alive and does not wait for whole tables.

Synthetic data only.
"""

from __future__ import annotations

import sqlite3
import threading
import time
from pathlib import Path
from typing import Any

import pytest

import connectors.sql_connector as sqlc
from connectors.sql_connector import SQLConnector
from core.database import LocalDBManager

# Same helpers as the #1820 pool tests (enforced test JWTs, clean licensing env).
import tests.test_filesystem_intra_target_parallelism as _fs_pool

_clean_license_env = _fs_pool._clean_license_env  # pytest fixture, reused
_license = _fs_pool._license

# Thread-name prefix of the SQL pool workers (connectors.sql_connector).
SQL_POOL_PREFIX = "databoar-sql-intra"

# Synthetic, checksum-invalid identifier: the stub scanner only looks for the marker.
_MARK = "CPF 000.000.000-00"
_SID = "sess-1322"
_TARGET = "DB1322"


# --------------------------------------------------------------------------- source


def _table_names() -> list[str]:
    # Wildcard-bearing names guard the literal match of the resume replace:
    # discovery is name-sorted ('q"uo%te', t00..t09, "z%b", "z_b", "zxb"), so
    # when "z_b" is interrupted, "z%b" is already completed and a LIKE "z_b"
    # would wrongly drop its findings.
    return [f"t{i:02d}" for i in range(10)] + ['q"uo%te', "z%b", "z_b", "zxb"]


def _col(table_idx: int, j: int) -> str:
    return f"k{table_idx:02d}_c{j}"


def _build_source(path: Path, *, columns: int = 3, rows: int = 4) -> list[str]:
    """SQLite source: per table c0 has the marker, c1 an e-mail, c2.. plain/NULL."""
    names = _table_names()
    con = sqlite3.connect(str(path))
    try:
        for ti, name in enumerate(names):
            cols = [_col(ti, j) for j in range(columns)]
            qname = name.replace('"', '""')
            con.execute(
                f'CREATE TABLE "{qname}" ({", ".join(f"{c} TEXT" for c in cols)})'
            )
            for r in range(rows):
                vals: list[str | None] = []
                for j in range(columns):
                    if j == 0:
                        vals.append(f"{_MARK} {ti}-{r}")
                    elif j == 1:
                        vals.append(f"pessoa{ti}x{r}@example.com")
                    elif j == 2:
                        vals.append(None)  # all-NULL column: empty sample
                    else:
                        vals.append(f"texto {ti} {r} {j}")
                marks = ", ".join("?" for _ in cols)
                con.execute(f'INSERT INTO "{qname}" VALUES ({marks})', vals)
        con.commit()
    finally:
        con.close()
    return names


def _wide_source(path: Path, *, tables: int, columns: int) -> None:
    con = sqlite3.connect(str(path))
    try:
        for ti in range(tables):
            cols = [_col(ti, j) for j in range(columns)]
            con.execute(
                f"CREATE TABLE w{ti:03d} ({', '.join(f'{c} TEXT' for c in cols)})"
            )
            marks = ", ".join("?" for _ in cols)
            con.execute(
                f"INSERT INTO w{ti:03d} VALUES ({marks})",
                [f"{_MARK} {ti}-{j}" for j in range(columns)],
            )
        con.commit()
    finally:
        con.close()


# --------------------------------------------------------------------------- doubles


class _StubScanner:
    """Marker-based detector; optional barrier, interrupt, failure and delay."""

    def __init__(
        self,
        *,
        barrier_parties: int | None = None,
        interrupt_on: str | None = None,
        boom_on: str | None = None,
        delay_s: float = 0.0,
    ) -> None:
        self._lock = threading.Lock()
        self.active = 0
        self.max_active = 0
        self.calls: list[str] = []
        self.threads: set[str] = set()
        self._barrier = (
            threading.Barrier(barrier_parties, timeout=20)
            if barrier_parties and barrier_parties > 1
            else None
        )
        self._interrupt_on = interrupt_on
        self._boom_on = boom_on
        self._delay_s = delay_s

    def scan_column(
        self,
        column_name: str,
        sample_content: str,
        *,
        connector_data_type: str | None = None,
    ) -> dict[str, Any]:
        with self._lock:
            self.active += 1
            self.max_active = max(self.max_active, self.active)
            self.calls.append(column_name)
            self.threads.add(threading.current_thread().name)
        try:
            if self._barrier is not None:
                self._barrier.wait()
            if self._delay_s:
                time.sleep(self._delay_s)
            if column_name == self._interrupt_on:
                raise KeyboardInterrupt
            if column_name == self._boom_on:
                raise ValueError("synthetic detector failure (#1322)")
        finally:
            with self._lock:
                self.active -= 1
        sample = sample_content or ""
        if _MARK in sample:
            return {
                "sensitivity_level": "HIGH",
                "pattern_detected": "LGPD_CPF",
                "norm_tag": "LGPD",
                "ml_confidence": 90,
            }
        if "@example.com" in sample:
            return {
                "sensitivity_level": "MEDIUM",
                "pattern_detected": "EMAIL",
                "norm_tag": "LGPD",
                "ml_confidence": 70,
            }
        return {
            "sensitivity_level": "LOW",
            "pattern_detected": None,
            "norm_tag": None,
            "ml_confidence": 0,
        }


class _RecDB:
    """Non-LocalDBManager double: records writes in call order with the writer thread."""

    def __init__(self) -> None:
        self._current_session_id = _SID
        self.ops: list[tuple[Any, ...]] = []
        self.writer_threads: set[int] = set()

    def save_finding(self, source_type: str, **kw: Any) -> None:
        self.writer_threads.add(threading.get_ident())
        self.ops.append(("finding", source_type, tuple(sorted(kw.items()))))

    def save_failure(
        self, target_name: str, reason: str, details: str | None = None
    ) -> None:
        self.writer_threads.add(threading.get_ident())
        self.ops.append(("failure", target_name, reason, details))


class _SpyDB(LocalDBManager):
    """Real LocalDBManager that notes writer threads and can simulate a kill."""

    def __init__(self, *a: Any, kill_on_column: str | None = None, **k: Any) -> None:
        super().__init__(*a, **k)
        self.writer_threads: set[int] = set()
        self.kill_on_column = kill_on_column

    def save_finding(self, source_type: str, **kwargs: Any) -> None:
        self.writer_threads.add(threading.get_ident())
        if self.kill_on_column and kwargs.get("column_name") == self.kill_on_column:
            raise KeyboardInterrupt  # process "dies" before this write
        super().save_finding(source_type, **kwargs)

    def save_failure(self, *a: Any, **k: Any) -> None:
        self.writer_threads.add(threading.get_ident())
        super().save_failure(*a, **k)

    def mark_sql_table_in_progress(self, *a: Any, **k: Any) -> None:
        self.writer_threads.add(threading.get_ident())
        super().mark_sql_table_in_progress(*a, **k)

    def mark_sql_table_completed(self, *a: Any, **k: Any) -> None:
        self.writer_threads.add(threading.get_ident())
        super().mark_sql_table_completed(*a, **k)


# --------------------------------------------------------------------------- helpers


def _pool_threads() -> list[threading.Thread]:
    return [
        t
        for t in threading.enumerate()
        if t.name.startswith(SQL_POOL_PREFIX) and t.is_alive()
    ]


def _target(source: Path, workers: int | None, **extra: Any) -> dict[str, Any]:
    target: dict[str, Any] = {
        "name": _TARGET,
        "type": "database",
        "driver": "sqlite",
        "database": str(source),
        **extra,
    }
    if workers is not None:
        target["_intra_target_workers"] = workers
    return target


def _connector(
    source: Path, scanner: Any, db: Any, workers: int | None, **extra: Any
) -> SQLConnector:
    return SQLConnector(_target(source, workers, **extra), scanner, db, sample_limit=5)


def _ghost_column(monkeypatch: pytest.MonkeyPatch, table: str = "t01") -> None:
    """Add a table that does not exist right after *table*: its sample fails.

    (A missing *column* would not fail on SQLite: an unknown double-quoted
    identifier is read as a string literal.)
    """
    real = SQLConnector.discover

    def _discover(self: SQLConnector) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for item in real(self):
            out.append(item)
            if item["table"] == table:
                out.append(
                    {
                        "schema": item["schema"],
                        "table": f"{table}_ghost",
                        "columns": [{"name": "ghost_col", "type": "TEXT"}],
                    }
                )
        return out

    monkeypatch.setattr(SQLConnector, "discover", _discover)


def _discovered(source: Path) -> list[str]:
    """Table names in discovery order (honours an active _ghost_column patch)."""
    c = _connector(source, _StubScanner(), _RecDB(), 1)
    c.connect()
    try:
        return [item["table"] for item in c.discover()]
    finally:
        c.close()


def _new_db(path: Path, cls: type = LocalDBManager, **kw: Any) -> Any:
    db = cls(str(path), **kw)
    db.create_session_record(_SID)
    db.set_current_session_id(_SID)
    return db


def _rows(audit: Path) -> dict[str, list[tuple]]:
    con = sqlite3.connect(str(audit))
    try:
        return {
            "findings": con.execute(
                "SELECT target_name, server_ip, engine_details, schema_name, "
                "table_name, column_name, data_type, sensitivity_level, "
                "pattern_detected, norm_tag, ml_confidence FROM database_findings "
                "ORDER BY id"
            ).fetchall(),
            "failures": con.execute(
                "SELECT target_name, reason, details FROM scan_failures ORDER BY id"
            ).fetchall(),
            "checkpoints": con.execute(
                "SELECT target_name, schema_name, table_name, status "
                "FROM scan_table_checkpoints ORDER BY id"
            ).fetchall(),
        }
    finally:
        con.close()


def _scan_to(
    audit: Path,
    source: Path,
    workers: int | None,
    scanner: Any | None = None,
    db_cls: type = LocalDBManager,
    **db_kw: Any,
) -> tuple[dict[str, list[tuple]], Any, Any]:
    db = _new_db(audit, db_cls, **db_kw)
    sc = scanner or _StubScanner()
    try:
        _connector(source, sc, db, workers).run()
    finally:
        db.dispose()
    return _rows(audit), sc, db


# --------------------------------------------------------------------------- (a) parity


@pytest.mark.parametrize("workers", [2, 4, 8])
def test_d1322_a_parallel_matches_serial_exactly(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, workers: int
) -> None:
    source = tmp_path / "source.db"
    _build_source(source)
    _ghost_column(monkeypatch)

    serial, _, _ = _scan_to(tmp_path / "serial.db", source, 1)
    par, sc, _ = _scan_to(tmp_path / "par.db", source, workers)

    assert serial["findings"], "source must produce findings"
    assert {r[7] for r in serial["findings"]} == {"HIGH", "MEDIUM"}
    assert [r[1] for r in serial["failures"]] == ["sampling_error"]
    assert all(r[3] == "completed" for r in serial["checkpoints"])
    assert len(serial["checkpoints"]) == len(_table_names()) + 1  # + ghost table
    # Same rows, same fields, same order (stronger than a sorted comparison).
    assert par == serial
    assert any(name.startswith(SQL_POOL_PREFIX) for name in sc.threads)


def test_d1322_a_recorded_ops_match_serial_with_plain_double(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Without LocalDBManager (no checkpoints) the replayed write stream is identical."""
    source = tmp_path / "source.db"
    _build_source(source)
    _ghost_column(monkeypatch)
    serial_db, par_db = _RecDB(), _RecDB()
    _connector(source, _StubScanner(), serial_db, 1).run()
    _connector(source, _StubScanner(), par_db, 4).run()
    assert {op[0] for op in serial_db.ops} == {"finding", "failure"}
    assert par_db.ops == serial_db.ops
    assert par_db.writer_threads == {threading.get_ident()}


def test_d1322_a_parity_with_real_detector(tmp_path: Path) -> None:
    from core.scanner import DataScanner

    source = tmp_path / "source.db"
    con = sqlite3.connect(str(source))
    try:
        for t in range(8):
            con.execute(
                f"CREATE TABLE clientes_{t} (nome TEXT, email TEXT, cpf TEXT, obs TEXT)"
            )
            for r in range(5):
                con.execute(
                    f"INSERT INTO clientes_{t} VALUES (?, ?, ?, ?)",
                    (
                        f"Pessoa {t} {r}",
                        f"pessoa{t}{r}@example.com",
                        "529.982.247-25",
                        f"nota {r}",
                    ),
                )
        con.commit()
    finally:
        con.close()
    scanner = DataScanner()
    serial, _, _ = _scan_to(tmp_path / "serial.db", source, 1, scanner=scanner)
    par, _, _ = _scan_to(tmp_path / "par.db", source, 4, scanner=scanner)
    assert serial["findings"]
    assert par == serial


def test_d1322_a_db_writes_happen_only_on_the_target_thread(tmp_path: Path) -> None:
    source = tmp_path / "source.db"
    _build_source(source)
    _, sc, db = _scan_to(tmp_path / "audit.db", source, 8, db_cls=_SpyDB)
    assert any(name.startswith(SQL_POOL_PREFIX) for name in sc.threads)
    assert db.writer_threads == {threading.get_ident()}


# --------------------------------------------------------------------------- (b) N=1


def test_d1322_b_one_worker_is_the_serial_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source.db"
    _build_source(source)
    par, _, _ = _scan_to(tmp_path / "par.db", source, 3)

    class _NoPool:
        def __init__(self, *a: Any, **k: Any) -> None:
            raise AssertionError("workers=1 must not build a thread pool")

    monkeypatch.setattr(sqlc, "ThreadPoolExecutor", _NoPool, raising=False)
    serial, sc, _ = _scan_to(tmp_path / "serial.db", source, 1)
    assert serial == par
    assert sc.threads == {threading.current_thread().name}
    assert _pool_threads() == []


def test_d1322_b_default_without_budget_key_is_serial(tmp_path: Path) -> None:
    source = tmp_path / "source.db"
    _build_source(source)
    _, sc, _ = _scan_to(tmp_path / "audit.db", source, None)
    assert sc.max_active == 1
    assert sc.threads == {threading.current_thread().name}


# --------------------------------------------------------------------------- (c) cap


@pytest.mark.parametrize("workers", [2, 3, 5, 16])
def test_d1322_c_connector_runs_exactly_budget_workers(
    tmp_path: Path, workers: int
) -> None:
    """16 is above SQLAlchemy's default QueuePool (5 + 10 overflow): the pool must grow."""
    source = tmp_path / "wide.db"
    _wide_source(source, tables=workers * 3, columns=2)
    sc = _StubScanner(barrier_parties=workers)
    rows, _, _ = _scan_to(tmp_path / "audit.db", source, workers, scanner=sc)
    assert sc.max_active == workers
    assert rows["failures"] == []
    assert len(rows["findings"]) == workers * 3 * 2


def test_d1322_c_in_memory_sqlite_stays_serial(tmp_path: Path) -> None:
    """A per-thread in-memory database would show each worker an empty DB."""
    target = {
        "name": _TARGET,
        "type": "database",
        "driver": "sqlite",
        "url": "sqlite://",
        "_intra_target_workers": 4,
    }
    mem = SQLConnector(target, _StubScanner(), _RecDB(), sample_limit=5)
    mem.connect()
    try:
        assert mem.intra_target_workers() == 1
    finally:
        mem.close()
    source = tmp_path / "source.db"
    _build_source(source)
    on_disk = _connector(source, _StubScanner(), _RecDB(), 4)
    on_disk.connect()
    try:
        assert on_disk.intra_target_workers() == 4
    finally:
        on_disk.close()


def test_d1322_c_inter_query_delay_keeps_target_serial(tmp_path: Path) -> None:
    source = tmp_path / "source.db"
    _build_source(source)
    db = _RecDB()
    sc = _StubScanner()
    _connector(source, sc, db, 4, inter_query_delay_ms=1).run()
    assert sc.threads == {threading.current_thread().name}


def _engine(tmp_path: Path, cfg_extra: dict, sources: list[Path]) -> Any:
    from core.engine import AuditEngine
    from core.licensing.guard import get_license_guard

    cfg: dict = {
        "targets": [
            {
                "name": f"db{i}",
                "type": "database",
                "driver": "sqlite",
                "database": str(p),
            }
            for i, p in enumerate(sources)
        ],
        "file_scan": {"sample_limit": 5},
        "sqlite_path": str(tmp_path / "audit.db"),
        **cfg_extra,
    }
    engine = AuditEngine(cfg, db_path=str(tmp_path / "audit.db"))
    get_license_guard(engine.config)
    return engine


def _failures(tmp_path: Path) -> list[tuple]:
    con = sqlite3.connect(str(tmp_path / "audit.db"))
    try:
        return con.execute(
            "SELECT target_name, reason, details FROM scan_failures"
        ).fetchall()
    finally:
        con.close()


@pytest.mark.parametrize(
    ("claims", "max_workers", "expected"),
    [
        ({"dbtier": "community"}, 16, 2),
        ({"dbtier": "pro"}, 16, 4),
        ({"dbtier": "pro_plus"}, 16, 8),
        ({"dbtier": "enterprise", "dbmax_workers": 3}, 16, 3),
        ({"dbtier": "enterprise"}, 6, 6),
        ({"dbtier": "community"}, 1, 1),
    ],
)
def test_d1322_c_engine_per_table_pool_respects_tier_cap(
    tmp_path: Path,
    _clean_license_env: None,
    claims: dict,
    max_workers: int,
    expected: int,
) -> None:
    source = tmp_path / "wide.db"
    _wide_source(source, tables=expected * 3, columns=2)
    licensing = _license(tmp_path, claims)
    engine = _engine(
        tmp_path,
        {"scan": {"max_workers": max_workers}, "licensing": licensing},
        [source],
    )
    sc = _StubScanner(barrier_parties=expected)
    engine.scanner = sc
    engine.start_audit()
    assert engine._max_workers == expected
    assert sc.max_active == expected
    assert _failures(tmp_path) == []
    assert _pool_threads() == []


def test_d1322_c_engine_open_mode_clamp_applies_to_per_table_pool(
    tmp_path: Path, _clean_license_env: None
) -> None:
    from core.integrity_anchor import OPEN_MODE_WORKER_CAP

    source = tmp_path / "wide.db"
    _wide_source(source, tables=OPEN_MODE_WORKER_CAP * 3, columns=2)
    engine = _engine(tmp_path, {"scan": {"max_workers": 16}}, [source])
    sc = _StubScanner(barrier_parties=OPEN_MODE_WORKER_CAP)
    engine.scanner = sc
    engine.start_audit()
    assert sc.max_active == OPEN_MODE_WORKER_CAP
    assert _failures(tmp_path) == []


def test_d1322_c_engine_multi_target_total_stays_within_cap(
    tmp_path: Path, _clean_license_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: list[int] = []
    real_init = SQLConnector.__init__

    def _spy(self: Any, target_config: dict, *a: Any, **k: Any) -> None:
        seen.append(int(target_config.get("_intra_target_workers", 0)))
        real_init(self, target_config, *a, **k)

    monkeypatch.setattr(SQLConnector, "__init__", _spy)
    sources = []
    for i in range(2):
        p = tmp_path / f"wide{i}.db"
        _wide_source(p, tables=6, columns=2)
        sources.append(p)
    licensing = _license(tmp_path, {"dbtier": "pro"})
    engine = _engine(
        tmp_path, {"scan": {"max_workers": 16}, "licensing": licensing}, sources
    )
    sc = _StubScanner()
    engine.scanner = sc
    engine.start_audit()
    assert seen == [2, 2]
    assert sc.max_active <= 4
    assert _failures(tmp_path) == []


def test_d1322_c_engine_adaptive_rate_limit_keeps_tables_serial(
    tmp_path: Path, _clean_license_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: list[int] = []
    real_init = SQLConnector.__init__

    def _spy(self: Any, target_config: dict, *a: Any, **k: Any) -> None:
        seen.append(int(target_config.get("_intra_target_workers", 1)))
        real_init(self, target_config, *a, **k)

    monkeypatch.setattr(SQLConnector, "__init__", _spy)
    source = tmp_path / "wide.db"
    _wide_source(source, tables=4, columns=2)
    licensing = _license(tmp_path, {"dbtier": "pro"})
    engine = _engine(
        tmp_path,
        {
            "scan": {"max_workers": 4, "adaptive_rate_limit": True},
            "licensing": licensing,
        },
        [source],
    )
    engine.scanner = _StubScanner()
    engine.start_audit()
    assert seen == [1]


# --------------------------------------------------------------------------- (d) resume


def _resume_case(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    workers: int,
    *,
    kill_in_write: bool,
) -> None:
    source = tmp_path / "source.db"
    names = _build_source(source)
    _ghost_column(monkeypatch)  # failure in t01, before the interruption
    reference, _, _ = _scan_to(tmp_path / "ref.db", source, workers)

    order = _discovered(source)
    cut_name = "z_b"  # interrupted table; "z%b" is completed before it
    cut = names.index(cut_name)
    audit = tmp_path / "audit.db"
    if kill_in_write:
        # Hard kill after the first finding of the table was written.
        first = _SpyDB(str(audit), kill_on_column=_col(cut, 1))
        sc1 = _StubScanner()
    else:
        first = _SpyDB(str(audit))
        sc1 = _StubScanner(interrupt_on=_col(cut, 1))
    first.create_session_record(_SID)
    first.set_current_session_id(_SID)
    try:
        with pytest.raises(KeyboardInterrupt):
            _connector(source, sc1, first, workers).run()
    finally:
        first.dispose()
    assert _pool_threads() == []

    mid = _rows(audit)
    done_before = [r[2] for r in mid["checkpoints"] if r[3] == "completed"]
    assert done_before == order[: order.index(cut_name)]
    # The interrupted table was started, with partial writes, and is not completed.
    assert [r[2:] for r in mid["checkpoints"] if r[3] != "completed"] == [
        (cut_name, "in_progress")
    ]
    assert any(r[4] == cut_name for r in mid["findings"])

    second = LocalDBManager(str(audit))
    second.set_current_session_id(_SID)  # what --resume does (#1330)
    sc2 = _StubScanner()
    try:
        _connector(source, sc2, second, workers).run()
    finally:
        second.dispose()

    rescanned_tables = {c.split("_c")[0] for c in sc2.calls}
    after = order[order.index(cut_name) :]
    assert rescanned_tables == {f"k{names.index(t):02d}" for t in after}
    final = _rows(audit)
    assert final == reference


@pytest.mark.parametrize("workers", [1, 2, 4])
def test_d1322_d_interrupt_then_resume_equals_uninterrupted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, workers: int
) -> None:
    _resume_case(tmp_path, monkeypatch, workers, kill_in_write=False)


@pytest.mark.parametrize("workers", [1, 2, 4])
def test_d1322_d_kill_mid_table_then_resume_has_no_duplicates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, workers: int
) -> None:
    _resume_case(tmp_path, monkeypatch, workers, kill_in_write=True)


def test_d1322_d_engine_interrupt_and_resume_end_to_end(
    tmp_path: Path, _clean_license_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    from core.engine import AuditEngine

    source = tmp_path / "source.db"
    names = _build_source(source)
    licensing = _license(tmp_path, {"dbtier": "pro"})

    ref_dir = tmp_path / "ref"
    ref_dir.mkdir()
    ref = _engine(
        ref_dir, {"scan": {"max_workers": 4}, "licensing": licensing}, [source]
    )
    ref.scanner = _StubScanner()
    ref.start_audit()
    reference = _rows(ref_dir / "audit.db")

    cut = names.index("t05")
    engine = _engine(
        tmp_path, {"scan": {"max_workers": 4}, "licensing": licensing}, [source]
    )
    engine.scanner = _StubScanner(interrupt_on=_col(cut, 0))
    with pytest.raises(KeyboardInterrupt):
        engine.start_audit()
    sid = engine.db_manager.current_session_id
    assert engine.db_manager.get_session_status(sid) == "interrupted"
    engine.db_manager.dispose()
    assert _pool_threads() == []

    resumed = AuditEngine(dict(engine.config), db_path=str(tmp_path / "audit.db"))
    sc2 = _StubScanner()
    resumed.scanner = sc2
    assert resumed.start_audit(resume_session_id=sid) == sid
    assert resumed.db_manager.get_session_status(sid) == "completed"
    resumed.db_manager.dispose()
    assert not any(c.startswith(("k00_", "k04_", "k10_")) for c in sc2.calls)
    assert any(c.startswith("k05_") for c in sc2.calls)

    assert _rows(tmp_path / "audit.db") == reference


# --------------------------------------------------------------------------- (e) errors


@pytest.mark.parametrize("workers", [1, 4])
def test_d1322_e_sampling_failure_keeps_pool_and_other_findings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, workers: int
) -> None:
    source = tmp_path / "source.db"
    names = _build_source(source)
    _ghost_column(monkeypatch, table="t03")
    rows, _, _ = _scan_to(tmp_path / "audit.db", source, workers)
    assert [r[1] for r in rows["failures"]] == ["sampling_error"]
    assert "t03_ghost" in rows["failures"][0][2]
    # Every table still completes and keeps its two findings (marker + e-mail).
    assert len(rows["checkpoints"]) == len(names) + 1
    assert len(rows["findings"]) == 2 * len(names)


def test_d1322_e_unexpected_error_aborts_at_same_ordered_position(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.db"
    names = _build_source(source)
    boom = _col(names.index("t04"), 1)
    serial, _, _ = _scan_to(
        tmp_path / "serial.db", source, 1, scanner=_StubScanner(boom_on=boom)
    )
    par, _, _ = _scan_to(
        tmp_path / "par.db", source, 4, scanner=_StubScanner(boom_on=boom)
    )
    assert [r[1] for r in serial["failures"]] == ["error"]
    order = _discovered(source)
    done = [r[2] for r in serial["checkpoints"] if r[3] == "completed"]
    assert done == order[: order.index("t04")]
    assert par == serial


# --------------------------------------------------------------------------- (f) stop


def test_d1322_f_interrupt_on_target_thread_leaves_no_pool_threads(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.db"
    names = _build_source(source)
    audit = tmp_path / "audit.db"
    db = _new_db(audit, _SpyDB, kill_on_column=_col(names.index("t02"), 0))
    try:
        with pytest.raises(KeyboardInterrupt):
            _connector(source, _StubScanner(), db, 6).run()
    finally:
        db.dispose()
    assert _pool_threads() == []
    # Discovery order: 'q"uo%te' (k10), t00, t01, then t02 dies on its first write.
    assert {r[5] for r in _rows(audit)["findings"]} == {
        _col(i, j) for i in (10, 0, 1) for j in (0, 1)
    }


def test_d1322_f_interrupt_inside_worker_stops_without_finishing_tables(
    tmp_path: Path,
) -> None:
    source = tmp_path / "wide.db"
    _wide_source(source, tables=8, columns=40)
    sc = _StubScanner(interrupt_on=_col(0, 0), delay_s=0.02)
    db = _RecDB()
    with pytest.raises(KeyboardInterrupt):
        _connector(source, sc, db, 4).run()
    assert _pool_threads() == []
    # Without a stop signal the three other workers would each finish a
    # 40-column table (120 more calls); they must stop at the next column.
    assert len(sc.calls) < 40
    assert db.ops == []
