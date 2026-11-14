"""Per-file resume for filesystem/mount targets (``--resume``, extends #1330; #1820 epic 2).

Contract:

- Every processed candidate file of a filesystem/NFS target is checkpointed in
  the current session with ``(abs_path, mtime_ns, size)``, after its findings
  and failures are persisted (batched writes).
- ``start_audit(resume_session_id=...)`` skips files whose checkpoint matches
  and re-scans the others; before re-scanning a file it removes that file's
  partial rows from the same session, so a resumed scan never duplicates and
  never loses findings — even when the last checkpoint batch was lost (kill -9).
- The resumed session ends with the **same multiset** of findings and failures
  as an uninterrupted run, serial and with the intra-target pool.

Synthetic data only.
"""

from __future__ import annotations

import sqlite3
import threading
from collections import Counter
from pathlib import Path
from typing import Any

import pytest

import connectors.filesystem_connector as fsc

_MARK = "CPF 000.000.000-00"


class _Scanner:
    """Marker detector; raises KeyboardInterrupt on the N-th call when armed."""

    def __init__(self, interrupt_at: int | None = None) -> None:
        self._lock = threading.Lock()
        self.calls = 0
        self.interrupt_at = interrupt_at

    def scan_file_content(self, content: str, file_path: Any) -> dict | None:
        with self._lock:
            self.calls += 1
            n = self.calls
        if self.interrupt_at is not None and n == self.interrupt_at:
            raise KeyboardInterrupt
        if _MARK in (content or ""):
            return {
                "sensitivity_level": "HIGH",
                "pattern_detected": "LGPD_CPF",
                "norm_tag": "LGPD",
                "ml_confidence": 90,
            }
        return None


def _corpus(root: Path) -> None:
    for i in range(90):
        sub = root / f"d{i % 6}"
        sub.mkdir(parents=True, exist_ok=True)
        body = f"row {i} {_MARK}\n" if i % 3 == 0 else f"row {i} clean\n"
        (sub / f"f{i:03d}.txt").write_text(body, encoding="utf-8")
    (root / "broken.pdf").write_bytes(b"%PDF-1.4 not a pdf")


def _engine(db: Path, root: Path, workers: int, scanner: Any) -> Any:
    from core.engine import AuditEngine

    cfg = {
        "targets": [{"name": "fs_resume", "type": "filesystem", "path": str(root)}],
        "scan": {"max_workers": workers},
        "file_scan": {"extensions": [".txt", ".pdf"]},
        "sqlite_path": str(db),
    }
    eng = AuditEngine(cfg, db_path=str(db))
    eng.scanner = scanner
    return eng


def _rows(db: Path, session_id: str) -> tuple[Counter, Counter]:
    con = sqlite3.connect(db)
    try:
        findings = Counter(
            con.execute(
                "SELECT target_name, path, file_name, pattern_detected, "
                "sensitivity_level FROM filesystem_findings WHERE session_id = ?",
                (session_id,),
            ).fetchall()
        )
        failures = Counter(
            con.execute(
                "SELECT target_name, reason, details FROM scan_failures "
                "WHERE session_id = ?",
                (session_id,),
            ).fetchall()
        )
    finally:
        con.close()
    return findings, failures


def _reference(tmp_path: Path, root: Path) -> tuple[Counter, Counter]:
    db = tmp_path / "ref.db"
    sid = _engine(db, root, 1, _Scanner()).start_audit()
    return _rows(db, sid)


def _interrupted_then_resumed(
    tmp_path: Path, root: Path, workers: int, interrupt_at: int
) -> tuple[Counter, Counter, str, Path]:
    db = tmp_path / f"run_{workers}_{interrupt_at}.db"
    eng = _engine(db, root, workers, _Scanner(interrupt_at=interrupt_at))
    with pytest.raises(KeyboardInterrupt):
        eng.start_audit()
    sid = eng.db_manager.current_session_id
    partial, _ = _rows(db, sid)
    assert 0 < sum(partial.values())
    eng2 = _engine(db, root, workers, _Scanner())
    assert eng2.start_audit(resume_session_id=sid) == sid
    findings, failures = _rows(db, sid)
    return findings, failures, sid, db


@pytest.mark.parametrize("workers", [1, 4])
def test_resume_after_interrupt_matches_uninterrupted_run(
    tmp_path: Path, workers: int
) -> None:
    root = tmp_path / "corpus"
    _corpus(root)
    ref_f, ref_x = _reference(tmp_path, root)
    assert sum(ref_f.values()) == 30
    findings, failures, _, _ = _interrupted_then_resumed(
        tmp_path, root, workers, interrupt_at=40
    )
    assert findings == ref_f  # same multiset: no duplicates, nothing lost
    assert failures == ref_x


def test_resume_skips_checkpointed_files(tmp_path: Path) -> None:
    root = tmp_path / "corpus"
    _corpus(root)
    db = tmp_path / "skip.db"
    eng = _engine(db, root, 1, _Scanner(interrupt_at=50))
    with pytest.raises(KeyboardInterrupt):
        eng.start_audit()
    sid = eng.db_manager.current_session_id
    scanner = _Scanner()
    _engine(db, root, 1, scanner).start_audit(resume_session_id=sid)
    # 91 candidates; 49 fully processed before the interrupt are skipped.
    assert scanner.calls == 91 - 49


@pytest.mark.parametrize("workers", [1, 4])
def test_resume_without_last_checkpoint_batch_does_not_duplicate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, workers: int
) -> None:
    """kill -9 loses the unflushed batch: those files are re-scanned, not duplicated."""
    root = tmp_path / "corpus"
    _corpus(root)
    ref_f, ref_x = _reference(tmp_path, root)
    monkeypatch.setattr(fsc, "FILE_CHECKPOINT_BATCH", 16)
    real_flush = fsc._FileCheckpointer.flush

    def _lossy_flush(self: Any, *, final: bool = False) -> None:
        if final:
            return  # the process "dies" before the last batch reaches SQLite
        real_flush(self, final=final)

    monkeypatch.setattr(fsc._FileCheckpointer, "flush", _lossy_flush)
    db = tmp_path / f"kill_{workers}.db"
    eng = _engine(db, root, workers, _Scanner(interrupt_at=60))
    with pytest.raises(KeyboardInterrupt):
        eng.start_audit()
    sid = eng.db_manager.current_session_id
    monkeypatch.setattr(fsc._FileCheckpointer, "flush", real_flush)
    _engine(db, root, workers, _Scanner()).start_audit(resume_session_id=sid)
    findings, failures = _rows(db, sid)
    assert findings == ref_f
    assert failures == ref_x


def test_resume_rescans_file_changed_since_checkpoint(tmp_path: Path) -> None:
    root = tmp_path / "corpus"
    _corpus(root)
    db = tmp_path / "changed.db"
    eng = _engine(db, root, 1, _Scanner(interrupt_at=80))
    with pytest.raises(KeyboardInterrupt):
        eng.start_audit()
    sid = eng.db_manager.current_session_id
    done = eng.db_manager.list_file_checkpoints("fs_resume")
    changed = next(
        Path(p)
        for p in sorted(done)
        if Path(p).suffix == ".txt" and "clean" in Path(p).read_text(encoding="utf-8")
    )
    changed.write_text(f"now sensitive {_MARK} and longer\n", encoding="utf-8")
    _engine(db, root, 1, _Scanner()).start_audit(resume_session_id=sid)
    findings, _ = _rows(db, sid)
    names = Counter(f[2] for f in findings.elements())
    assert names[changed.name] == 1
    assert sum(findings.values()) == 31


def test_fresh_session_checkpoints_every_candidate(tmp_path: Path) -> None:
    root = tmp_path / "corpus"
    _corpus(root)
    db = tmp_path / "fresh.db"
    eng = _engine(db, root, 4, _Scanner())
    sid = eng.start_audit()
    done = eng.db_manager.list_file_checkpoints("fs_resume")
    assert len(done) == 91
    some = next(iter(done))
    assert Path(some).is_absolute()
    con = sqlite3.connect(db)
    try:
        n = con.execute(
            "SELECT COUNT(*) FROM scan_file_checkpoints WHERE session_id = ?", (sid,)
        ).fetchone()[0]
    finally:
        con.close()
    assert n == 91


def test_legacy_db_gains_file_checkpoint_table(tmp_path: Path) -> None:
    from core.database import LocalDBManager

    db = tmp_path / "legacy.db"
    LocalDBManager(str(db)).engine.dispose()
    con = sqlite3.connect(db)
    con.execute("DROP TABLE scan_file_checkpoints")
    con.commit()
    con.close()
    mgr = LocalDBManager(str(db))
    con = sqlite3.connect(db)
    try:
        names = {
            r[0]
            for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
    finally:
        con.close()
    mgr.engine.dispose()
    assert "scan_file_checkpoints" in names
