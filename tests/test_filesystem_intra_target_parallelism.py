"""#1820 — intra-target worker pool for the filesystem connector.

Contract under test (PLAN_FILESYSTEM_INTRA_TARGET_PARALLELISM.md):

(a) Exact parity of persisted findings and scan_failures between serial and
    parallel runs (same rows, same fields, same order) on a synthetic corpus
    with sub-folders, symlinks, hard links, large and small files.
(b) ``_intra_target_workers`` = 1 keeps the serial path (no pool thread).
(c) The pool never exceeds the tier worker cap (#551 ``worker_cap`` /
    ``dbmax_workers`` claim, #856 open-mode clamp); the engine derives the
    per-target budget from the already-clamped ``scan.max_workers``.
(d) Inode de-duplication is atomic under concurrency: the same file or
    directory reached through several paths is visited exactly once.
(e) A read failure on one file neither stops the pool nor loses the other
    findings; an unexpected per-file exception keeps today's semantics
    (target aborts at the same ordered position as the serial run).
(f) Interrupting the scan mid-way leaves no pool thread alive.

Synthetic data only.
"""

from __future__ import annotations

import os
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

import connectors.filesystem_connector as fsc
from connectors.filesystem_connector import (
    INTRA_TARGET_THREAD_PREFIX,
    FilesystemConnector,
    InodeDedup,
    iter_scan_files,
)
from core.licensing.guard import reset_license_guard_for_tests
from tests.license_verify_pin import pin_embedded_ed25519_pem

# Synthetic, checksum-invalid identifiers: the stub scanner only looks for the marker.
_MARK = "CPF 000.000.000-00"


# --------------------------------------------------------------------------- helpers


class _RecDB:
    """Records every db_manager write in call order, with the writer thread."""

    def __init__(self, *, interrupt_on_finding: int | None = None) -> None:
        self._current_session_id = "sess-1820"
        self.ops: list[tuple[Any, ...]] = []
        self.writer_threads: set[int] = set()
        self._interrupt_on_finding = interrupt_on_finding
        self._findings = 0

    def _note(self) -> None:
        self.writer_threads.add(threading.get_ident())

    def save_finding(self, source_type: str, **kw: Any) -> None:
        self._note()
        self._findings += 1
        if (
            self._interrupt_on_finding is not None
            and self._findings >= self._interrupt_on_finding
        ):
            raise KeyboardInterrupt
        self.ops.append(("finding", source_type, tuple(sorted(kw.items()))))

    def save_failure(
        self, target_name: str, reason: str, details: str | None = None
    ) -> None:
        self._note()
        self.ops.append(("failure", target_name, reason, details))

    def upsert_object_state(self, **kw: Any) -> None:
        self._note()
        self.ops.append(("state", tuple(sorted(kw.items()))))


class _StubScanner:
    """Marker-based detector; optional barrier forces observable overlap (no sleeps)."""

    def __init__(
        self, *, barrier_parties: int | None = None, boom_name: str | None = None
    ) -> None:
        self._lock = threading.Lock()
        self.active = 0
        self.max_active = 0
        self.calls: list[str] = []
        self._barrier = (
            threading.Barrier(barrier_parties, timeout=20)
            if barrier_parties and barrier_parties > 1
            else None
        )
        self._boom_name = boom_name

    def scan_file_content(self, content: str, file_path: Any) -> dict | None:
        with self._lock:
            self.active += 1
            self.max_active = max(self.max_active, self.active)
            self.calls.append(str(file_path))
        try:
            if self._barrier is not None:
                self._barrier.wait()
            if self._boom_name and Path(str(file_path)).name == self._boom_name:
                raise ValueError("synthetic detector failure (#1820)")
        finally:
            with self._lock:
                self.active -= 1
        if _MARK in (content or ""):
            return {
                "sensitivity_level": "HIGH",
                "pattern_detected": "LGPD_CPF",
                "norm_tag": "LGPD",
                "ml_confidence": 90,
            }
        return None


def _pool_threads() -> list[threading.Thread]:
    return [
        t
        for t in threading.enumerate()
        if t.name.startswith(INTRA_TARGET_THREAD_PREFIX) and t.is_alive()
    ]


def _connector(
    root: Path,
    scanner: Any,
    db: Any,
    *,
    workers: int,
    extensions: list[str] | None = None,
) -> FilesystemConnector:
    target = {
        "name": "FS1820",
        "type": "filesystem",
        "path": str(root),
        "recursive": True,
        "file_scan": {},
        "_intra_target_workers": workers,
    }
    return FilesystemConnector(
        target,
        scanner,
        db,
        extensions=extensions or [".txt", ".md", ".csv", ".json", ".pdf"],
        scan_sqlite_as_db=False,
        sample_limit=5,
        file_sample_max_chars=4_000,
    )


def _build_corpus(root: Path) -> None:
    """Sub-folders, file/dir symlinks, hard links, big and small files, read barriers."""
    root.mkdir(parents=True)
    (root / "a.txt").write_text(f"{_MARK} Fulano de Tal\n", encoding="utf-8")
    (root / "b.md").write_text("nothing sensitive here\n", encoding="utf-8")
    sub1 = root / "sub1"
    (sub1 / "deep").mkdir(parents=True)
    (sub1 / "c.csv").write_text(f"id;doc\n1;{_MARK}\n", encoding="utf-8")
    (sub1 / "deep" / "d.json").write_text('{"k": "clean"}\n', encoding="utf-8")
    sub2 = root / "sub2"
    sub2.mkdir()
    # Large files: marker at the head (inside the sample) and at the tail (outside).
    (sub2 / "big_head.txt").write_text(
        _MARK + "\n" + ("x" * 1023 + "\n") * 2048, encoding="utf-8"
    )
    (sub2 / "big_tail.txt").write_text(
        ("y" * 1023 + "\n") * 2048 + _MARK + "\n", encoding="utf-8"
    )
    os.link(root / "a.txt", sub2 / "hard_a.txt")  # same inode as a.txt
    os.symlink(root / "a.txt", sub2 / "link_a.txt")  # alias of a.txt
    os.symlink(sub1 / "c.csv", root / "alias_c.csv")  # alias of sub1/c.csv
    os.symlink(sub1, root / "dirlink")  # directory symlink: not followed
    many = root / "many"
    many.mkdir()
    for i in range(48):
        body = f"row {i} {_MARK}\n" if i % 3 == 0 else f"row {i} clean\n"
        (many / f"f{i:03d}.txt").write_text(body, encoding="utf-8")
    # Read barriers: corrupt PDF (parser error swallowed) and encrypted PDF.
    (root / "broken.pdf").write_bytes(b"%PDF-1.4 not really a pdf")
    from pypdf import PdfWriter

    w = PdfWriter()
    w.add_blank_page(width=72, height=72)
    w.encrypt("synthetic-pw")
    with (root / "locked.pdf").open("wb") as fh:
        w.write(fh)
    (root / "denied.txt").write_text(f"{_MARK}\n", encoding="utf-8")


def _deny_one(monkeypatch: pytest.MonkeyPatch) -> None:
    real_access = os.access

    def _access(path: Any, mode: int, *a: Any, **k: Any) -> bool:
        if str(path).endswith("denied.txt"):
            return False
        return real_access(path, mode, *a, **k)

    monkeypatch.setattr(fsc.os, "access", _access)


def _run(
    root: Path, workers: int, scanner: Any | None = None, **kw: Any
) -> tuple[_RecDB, Any]:
    db = _RecDB()
    sc = scanner or _StubScanner()
    _connector(root, sc, db, workers=workers, **kw).run()
    return db, sc


# --------------------------------------------------------------------------- (a) parity


@pytest.mark.parametrize("workers", [2, 4, 8])
def test_d1820_a_parallel_matches_serial_exactly(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, workers: int
) -> None:
    root = tmp_path / "corpus"
    _build_corpus(root)
    _deny_one(monkeypatch)

    serial_db, _ = _run(root, 1)
    par_db, _ = _run(root, workers)

    assert serial_db.ops, "corpus must produce findings and failures"
    kinds = {op[0] for op in serial_db.ops}
    assert {"finding", "failure"} <= kinds
    reasons = {op[2] for op in serial_db.ops if op[0] == "failure"}
    assert "permission_denied" in reasons
    assert "encrypted_no_password" in reasons
    # Same rows, same fields, same order (stronger than sorted comparison).
    assert par_db.ops == serial_db.ops
    assert sorted(map(repr, par_db.ops)) == sorted(map(repr, serial_db.ops))


def test_d1820_a_parity_with_real_detector(tmp_path: Path) -> None:
    from core.scanner import DataScanner

    root = tmp_path / "corpus"
    root.mkdir()
    for i in range(24):
        sub = root / f"d{i % 4}"
        sub.mkdir(exist_ok=True)
        (sub / f"cliente_{i:02d}.csv").write_text(
            "nome;email;cpf\n"
            f"Pessoa {i};pessoa{i}@example.com;529.982.247-25\n"
            "contato;telefone\n"
            f"Contato {i};+55 21 99999-{i:04d}\n",
            encoding="utf-8",
        )
    scanner = DataScanner()
    serial_db, _ = _run(root, 1, scanner=scanner, extensions=[".csv"])
    par_db, _ = _run(root, 4, scanner=scanner, extensions=[".csv"])
    assert any(op[0] == "finding" for op in serial_db.ops)
    assert par_db.ops == serial_db.ops


def test_d1820_a_db_writes_happen_only_on_the_target_thread(tmp_path: Path) -> None:
    root = tmp_path / "corpus"
    _build_corpus(root)
    db, _ = _run(root, 8)
    assert db.writer_threads == {threading.get_ident()}


# --------------------------------------------------------------------------- (b) N=1


def test_d1820_b_one_worker_is_the_serial_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "corpus"
    _build_corpus(root)
    par_db, _ = _run(root, 3)

    class _NoPool:
        def __init__(self, *a: Any, **k: Any) -> None:
            raise AssertionError("workers=1 must not build a thread pool")

    monkeypatch.setattr(fsc, "ThreadPoolExecutor", _NoPool, raising=False)
    serial_db, _ = _run(root, 1)
    assert serial_db.ops == par_db.ops
    assert _pool_threads() == []


def test_d1820_b_default_without_budget_key_is_serial(tmp_path: Path) -> None:
    root = tmp_path / "corpus"
    _build_corpus(root)
    db = _RecDB()
    sc = _StubScanner()
    target = {"name": "FS1820", "type": "filesystem", "path": str(root)}
    FilesystemConnector(target, sc, db, extensions=[".txt"]).run()
    assert sc.max_active == 1


# --------------------------------------------------------------------------- (c) cap


@pytest.mark.parametrize("workers", [2, 3, 5])
def test_d1820_c_connector_runs_exactly_budget_workers(
    tmp_path: Path, workers: int
) -> None:
    root = tmp_path / "corpus"
    root.mkdir()
    for i in range(workers * 6):
        (root / f"f{i:03d}.txt").write_text(f"{_MARK} {i}\n", encoding="utf-8")
    sc = _StubScanner(barrier_parties=workers)
    db, _ = _run(root, workers, scanner=sc)
    assert sc.max_active == workers
    assert sum(1 for op in db.ops if op[0] == "finding") == workers * 6


@pytest.mark.parametrize(
    ("max_workers", "concurrent_targets", "expected"),
    [
        (1, 1, 1),
        (0, 1, 1),
        (2, 1, 2),
        (4, 1, 4),
        (4, 2, 2),
        (4, 3, 1),
        (8, 3, 2),
        (8, 20, 1),
        (16, 0, 16),
    ],
)
def test_d1820_c_budget_never_exceeds_clamped_max_workers(
    max_workers: int, concurrent_targets: int, expected: int
) -> None:
    from core.engine import _intra_target_worker_budget

    got = _intra_target_worker_budget(max_workers, concurrent_targets)
    assert got == expected
    outer = max(1, min(max(1, max_workers), max(1, concurrent_targets)))
    assert got * outer <= max(1, max_workers)


@pytest.fixture
def _clean_license_env():
    reset_license_guard_for_tests()
    keys = (
        "DATA_BOAR_ENV",
        "DEBUG",
        "DATA_BOAR_TIER_OVERRIDE",
        "DATA_BOAR_LICENSE_MODE",
        "DATA_BOAR_LICENSE_PATH",
        "DATA_BOAR_LICENSE_PUBLIC_KEY_PEM",
        "DATA_BOAR_LICENSE_PUBLIC_KEY_PATH",
        "DATA_BOAR_LICENSE_REVOCATION_PATH",
    )
    saved = {k: os.environ.get(k) for k in keys}
    for k in keys:
        os.environ.pop(k, None)
    yield
    reset_license_guard_for_tests()
    for k, v in saved.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


def _license(tmp_path: Path, extra: dict) -> dict:
    priv = Ed25519PrivateKey.generate()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": "lic-1820",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=7)).timestamp()),
        "dbcid": "cust-1820",
        "dbcname": "Synthetic Customer",
        "dbenv": "qa",
        "dbissuer": "test-issuer",
        "dbkid": "k1",
        **extra,
    }
    from tests.hybrid_license_fixture import seal_enforced_test_token

    token = seal_enforced_test_token(priv, jwt.encode(payload, priv, algorithm="EdDSA"))
    lic = tmp_path / "t.lic"
    lic.write_text(token, encoding="utf-8")
    pem = (
        priv.public_key()
        .public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode("ascii")
        .strip()
    )
    pin_embedded_ed25519_pem(pem)
    return {"mode": "enforced", "license_path": str(lic)}


def _engine_run(
    tmp_path: Path,
    *,
    max_workers: int,
    licensing: dict | None,
    expected: int,
    n_targets: int = 1,
) -> tuple[Any, _StubScanner]:
    from core.engine import AuditEngine
    from core.licensing.guard import get_license_guard

    targets = []
    for t in range(n_targets):
        root = tmp_path / f"corpus{t}"
        root.mkdir()
        for i in range(max(1, expected) * 4):
            (root / f"f{i:03d}.txt").write_text(f"{_MARK} {i}\n", encoding="utf-8")
        targets.append({"name": f"fs{t}", "type": "filesystem", "path": str(root)})
    cfg: dict = {
        "targets": targets,
        "scan": {"max_workers": max_workers},
        "file_scan": {"extensions": [".txt"]},
        "sqlite_path": str(tmp_path / "audit.db"),
    }
    if licensing:
        cfg["licensing"] = licensing
    engine = AuditEngine(cfg, db_path=str(tmp_path / "audit.db"))
    get_license_guard(engine.config)
    sc = _StubScanner(barrier_parties=expected if n_targets == 1 else None)
    engine.scanner = sc
    engine.start_audit()
    return engine, sc


def _error_failures(tmp_path: Path) -> list[tuple]:
    import sqlite3

    con = sqlite3.connect(tmp_path / "audit.db")
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
def test_d1820_c_engine_intra_target_pool_respects_tier_cap(
    tmp_path: Path,
    _clean_license_env: None,
    claims: dict,
    max_workers: int,
    expected: int,
) -> None:
    licensing = _license(tmp_path, claims)
    engine, sc = _engine_run(
        tmp_path, max_workers=max_workers, licensing=licensing, expected=expected
    )
    assert engine._max_workers == expected
    assert sc.max_active == expected
    assert _error_failures(tmp_path) == []
    assert _pool_threads() == []


def test_d1820_c_engine_open_mode_clamp_applies_to_intra_target(
    tmp_path: Path, _clean_license_env: None
) -> None:
    from core.integrity_anchor import OPEN_MODE_WORKER_CAP

    _, sc = _engine_run(
        tmp_path, max_workers=16, licensing=None, expected=OPEN_MODE_WORKER_CAP
    )
    assert sc.max_active == OPEN_MODE_WORKER_CAP
    assert _error_failures(tmp_path) == []


def test_d1820_c_engine_multi_target_total_stays_within_cap(
    tmp_path: Path, _clean_license_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: list[int] = []
    real_init = FilesystemConnector.__init__

    def _spy(self: Any, target_config: dict, *a: Any, **k: Any) -> None:
        seen.append(int(target_config.get("_intra_target_workers", 0)))
        real_init(self, target_config, *a, **k)

    monkeypatch.setattr(FilesystemConnector, "__init__", _spy)
    licensing = _license(tmp_path, {"dbtier": "pro"})
    _, sc = _engine_run(
        tmp_path, max_workers=16, licensing=licensing, expected=4, n_targets=2
    )
    assert seen == [2, 2]
    assert sc.max_active <= 4
    assert _error_failures(tmp_path) == []


# --------------------------------------------------------------------------- (d) dedup


def test_d1820_d_inode_claim_is_atomic_under_threads() -> None:
    dedup = InodeDedup()
    keys = [(1, i) for i in range(200)]
    n = 16
    start = threading.Barrier(n)
    wins: list[list[tuple[int, int]]] = [[] for _ in range(n)]

    def _worker(slot: int) -> None:
        start.wait()
        for k in keys:
            if dedup.claim(k):
                wins[slot].append(k)

    threads = [threading.Thread(target=_worker, args=(s,)) for s in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    flat = [k for w in wins for k in w]
    assert sorted(flat) == sorted(keys)  # every key claimed exactly once


def test_d1820_d_shared_dedup_visits_each_inode_once_across_threads(
    tmp_path: Path,
) -> None:
    root = tmp_path / "root"
    sub_a = root / "a"
    sub_b = root / "b"
    sub_a.mkdir(parents=True)
    sub_b.mkdir()
    for i in range(30):
        f = sub_a / f"f{i:02d}.txt"
        f.write_text(f"{i}\n", encoding="utf-8")
        os.link(f, sub_b / f"hard{i:02d}.txt")
        os.symlink(f, sub_b / f"sym{i:02d}.txt")
    os.symlink(sub_a, sub_b / "dirlink")
    shared = InodeDedup()
    n = 8
    start = threading.Barrier(n)
    out: list[list[Path]] = [[] for _ in range(n)]
    roots = [sub_a, sub_b] * (n // 2)

    def _walk(slot: int) -> None:
        start.wait()
        out[slot].extend(iter_scan_files(roots[slot], recursive=True, dedup=shared))

    threads = [threading.Thread(target=_walk, args=(s,)) for s in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    inodes = [os.stat(p).st_ino for w in out for p in w]
    assert len(inodes) == 30
    assert len(set(inodes)) == 30


def test_d1820_d_parallel_scan_detects_each_inode_once(tmp_path: Path) -> None:
    root = tmp_path / "corpus"
    _build_corpus(root)
    sc = _StubScanner()
    _run(root, 8, scanner=sc)
    inodes = [os.stat(p).st_ino for p in sc.calls]
    assert len(inodes) == len(set(inodes))
    assert os.stat(root / "a.txt").st_ino in inodes


# --------------------------------------------------------------------------- (e) failures


def test_d1820_e_read_failure_keeps_pool_and_other_findings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "corpus"
    _build_corpus(root)
    _deny_one(monkeypatch)
    real_read = fsc._read_text_sample

    def _flaky(path: Path, *a: Any, **k: Any) -> str:
        if path.name == "f003.txt":
            # Same contract as an I/O error inside the reader: empty sample.
            raise_inside = real_read(root / "does-not-exist.txt", *a, **k)
            return raise_inside
        return real_read(path, *a, **k)

    monkeypatch.setattr(fsc, "_read_text_sample", _flaky)
    serial_db, _ = _run(root, 1)
    par_db, _ = _run(root, 6)
    assert par_db.ops == serial_db.ops
    finding_files = {
        dict(op[2])["file_name"] for op in par_db.ops if op[0] == "finding"
    }
    assert "f003.txt" not in finding_files
    assert {
        "f000.txt",
        "f006.txt",
        "f045.txt",
        "c.csv",
        "big_head.txt",
    } <= finding_files
    assert _pool_threads() == []


def test_d1820_e_unexpected_error_aborts_at_same_ordered_position(
    tmp_path: Path,
) -> None:
    root = tmp_path / "corpus"
    _build_corpus(root)

    serial_db = _RecDB()
    with pytest.raises(ValueError, match="synthetic detector failure"):
        _connector(root, _StubScanner(boom_name="f020.txt"), serial_db, workers=1).run()
    par_db = _RecDB()
    with pytest.raises(ValueError, match="synthetic detector failure"):
        _connector(root, _StubScanner(boom_name="f020.txt"), par_db, workers=6).run()
    assert par_db.ops == serial_db.ops
    assert _pool_threads() == []


# --------------------------------------------------------------------------- (f) stop


def test_d1820_f_interrupt_mid_scan_leaves_no_pool_threads(tmp_path: Path) -> None:
    root = tmp_path / "corpus"
    _build_corpus(root)
    db = _RecDB(interrupt_on_finding=3)
    with pytest.raises(KeyboardInterrupt):
        _connector(root, _StubScanner(), db, workers=6).run()
    assert sum(1 for op in db.ops if op[0] == "finding") == 2
    assert _pool_threads() == []


def test_d1820_f_interrupt_inside_worker_leaves_no_pool_threads(
    tmp_path: Path,
) -> None:
    root = tmp_path / "corpus"
    _build_corpus(root)

    class _InterruptingScanner(_StubScanner):
        def scan_file_content(self, content: str, file_path: Any) -> dict | None:
            if Path(str(file_path)).name == "f010.txt":
                raise KeyboardInterrupt
            return super().scan_file_content(content, file_path)

    with pytest.raises(KeyboardInterrupt):
        _connector(root, _InterruptingScanner(), _RecDB(), workers=6).run()
    assert _pool_threads() == []
