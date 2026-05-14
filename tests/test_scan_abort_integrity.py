"""
G-13-15: SQLite audit-log integrity after abrupt scan termination.

Verifies that the SQLite audit database remains readable and structurally
intact after a scan process is killed (SIGTERM / process.kill on Windows)
mid-transaction -- i.e., before the scan session is committed/closed
cleanly.

SQLite guarantees ACID recovery via its WAL or DELETE journal:
- Uncommitted transactions are rolled back on next open.
- The file is not corrupted by a mid-write kill.

This test exercises that guarantee end-to-end using LocalDBManager so
any future WAL-mode change or connection-pool change is automatically
covered.
"""

from __future__ import annotations

import os
import signal
import sqlite3
import subprocess
import sys
import textwrap
import time
from pathlib import Path


# ---------------------------------------------------------------------------
# Helper: subprocess writer script
# ---------------------------------------------------------------------------

_WRITER_SCRIPT = textwrap.dedent(
    """
    import sys, time, sqlite3
    from pathlib import Path

    db_path = sys.argv[1]
    ready_file = sys.argv[2]

    conn = sqlite3.connect(db_path, isolation_level=None)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS abort_test "
        "(id INTEGER PRIMARY KEY, phase TEXT, committed INTEGER)"
    )

    # Committed row (clean)
    conn.execute("BEGIN")
    conn.execute("INSERT INTO abort_test (phase, committed) VALUES ('pre_abort', 1)")
    conn.execute("COMMIT")

    # Start a new transaction that will NOT be committed before kill
    conn.execute("BEGIN")
    conn.execute("INSERT INTO abort_test (phase, committed) VALUES ('during_abort', 0)")

    # Signal the parent that we are inside the uncommitted transaction
    Path(ready_file).write_text("ready")

    # Wait until killed -- the transaction remains open
    time.sleep(60)
    conn.execute("COMMIT")  # never reached
    """
)


def _run_writer(db_path: str, ready_file: str) -> subprocess.Popen:  # type: ignore[type-arg]
    """Start the writer subprocess and return the Popen handle."""
    return subprocess.Popen(
        [sys.executable, "-c", _WRITER_SCRIPT, db_path, ready_file],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _wait_for_ready(ready_file: str, timeout: float = 10.0) -> bool:
    """Wait until the writer signals it is inside the open transaction."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if Path(ready_file).exists():
            return True
        time.sleep(0.1)
    return False


def _kill(proc: subprocess.Popen) -> None:  # type: ignore[type-arg]
    """Kill the subprocess unconditionally (cross-platform)."""
    try:
        if sys.platform == "win32":
            proc.kill()
        else:
            os.kill(proc.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    proc.wait(timeout=5)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_sqlite_integrity_after_abort(tmp_path: Path) -> None:
    """PRAGMA integrity_check passes after a mid-transaction kill."""
    db_file = str(tmp_path / "abort_test.db")
    ready_file = str(tmp_path / "ready.flag")

    proc = _run_writer(db_file, ready_file)
    try:
        assert _wait_for_ready(ready_file), "Writer did not signal readiness in time"
        _kill(proc)
    finally:
        if proc.poll() is None:
            _kill(proc)

    # SQLite must be openable and pass integrity check
    conn = sqlite3.connect(db_file)
    try:
        result = conn.execute("PRAGMA integrity_check").fetchone()
    finally:
        conn.close()
    assert result is not None, "PRAGMA integrity_check returned no result"
    assert result[0] == "ok", f"PRAGMA integrity_check failed: {result[0]}"


def test_sqlite_uncommitted_rows_absent_after_abort(tmp_path: Path) -> None:
    """Rows written inside the killed transaction must not appear in the DB."""
    db_file = str(tmp_path / "abort_test2.db")
    ready_file = str(tmp_path / "ready2.flag")

    proc = _run_writer(db_file, ready_file)
    try:
        assert _wait_for_ready(ready_file), "Writer did not signal readiness in time"
        _kill(proc)
    finally:
        if proc.poll() is None:
            _kill(proc)

    conn2 = sqlite3.connect(db_file)
    try:
        rows = conn2.execute(
            "SELECT phase, committed FROM abort_test ORDER BY id"
        ).fetchall()
    finally:
        conn2.close()

    # The committed row must be there, the uncommitted one must not
    phases = [r[0] for r in rows]
    assert "pre_abort" in phases, f"Committed row missing after abort; got: {phases}"
    assert "during_abort" not in phases, (
        f"Uncommitted row survived abort — SQLite ACID not holding; got: {phases}"
    )


def test_sqlite_localdbmanager_reopens_cleanly_after_abort(tmp_path: Path) -> None:
    """LocalDBManager can re-open a DB that was closed without a clean shutdown."""
    # This mirrors what happens when the operator restarts Data Boar after a kill:
    # the LocalDBManager must initialise (schema create/migrate) without error.
    # We run the re-open in a subprocess so that any SQLAlchemy/sqlite3 connection
    # finalizers are cleaned up cleanly inside that process (avoids
    # PytestUnraisableExceptionWarning from in-process GC finalisers).
    db_file = str(tmp_path / "localdb_abort.db")
    ready_file = str(tmp_path / "ready3.flag")
    result_file = str(tmp_path / "integrity_result.txt")
    repo_root = str(Path(__file__).parent.parent)

    # Phase 1: create the schema in a subprocess that will be killed
    _setup_script = textwrap.dedent(
        f"""
        import sys
        sys.path.insert(0, r"{repo_root}")
        from core.database import LocalDBManager
        from pathlib import Path
        import time

        mgr = LocalDBManager(db_path=r"{db_file}")
        mgr.create_session_record("kill_test_session", config_scope_hash="abc123")
        Path(r"{ready_file}").write_text("ready")
        time.sleep(60)
        """
    )
    proc = subprocess.Popen(
        [sys.executable, "-c", _setup_script],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        assert _wait_for_ready(ready_file), "LocalDBManager subprocess not ready"
        _kill(proc)
    finally:
        if proc.poll() is None:
            _kill(proc)

    # Phase 2: verify in a *separate* subprocess that re-opens cleanly
    _verify_script = textwrap.dedent(
        f"""
        import sys, sqlite3
        sys.path.insert(0, r"{repo_root}")
        from core.database import LocalDBManager
        from pathlib import Path

        try:
            mgr2 = LocalDBManager(db_path=r"{db_file}")
            mgr2.engine.dispose()
        except Exception as exc:
            Path(r"{result_file}").write_text(f"OPEN_FAIL: {{exc}}")
            sys.exit(1)

        with sqlite3.connect(r"{db_file}") as conn:
            row = conn.execute("PRAGMA integrity_check").fetchone()
        Path(r"{result_file}").write_text(row[0] if row else "NO_RESULT")
        sys.exit(0)
        """
    )
    verify = subprocess.run(
        [sys.executable, "-c", _verify_script],
        capture_output=True,
        timeout=30,
    )
    result_text = (
        Path(result_file).read_text().strip() if Path(result_file).exists() else ""
    )
    assert verify.returncode == 0, (
        f"LocalDBManager re-open subprocess failed (rc={verify.returncode}); "
        f"result={result_text!r}; stderr={verify.stderr.decode()[:300]}"
    )
    assert result_text == "ok", (
        f"PRAGMA integrity_check after LocalDBManager abort: {result_text!r}"
    )
