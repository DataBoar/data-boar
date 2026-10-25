import sqlite3
import subprocess
import sys
from pathlib import Path


def _mk(path: Path, schema: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    try:
        conn.executescript(schema)
    finally:
        conn.close()


def test_benchmark_sqlite_diff_cli(tmp_path: Path) -> None:
    a = tmp_path / "a.db"
    b = tmp_path / "b.db"
    _mk(a, "CREATE TABLE t1 (x INT);")
    _mk(
        b,
        "CREATE TABLE t1 (x INT); CREATE TABLE scan_metadata ("
        "safety_protocol TEXT, sampling_method TEXT);",
    )
    script = (
        Path(__file__).resolve().parents[1] / "scripts" / "benchmark_sqlite_diff.py"
    )
    out = subprocess.run(
        [sys.executable, str(script), str(a), str(b)],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "scan_metadata" in out.stdout
    assert "safety_protocol" in out.stdout
