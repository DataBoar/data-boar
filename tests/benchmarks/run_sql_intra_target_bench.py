#!/usr/bin/env python3
"""
SQL per-table worker pool: serial vs parallel on one target (#1322).

Runs ``AuditEngine.start_audit()`` (connect, discover, sample, detect, persist;
no report) on one synthetic SQLite source with several tables and columns.
``licensing.mode: enforced`` with an Enterprise test JWT so the tier cap does
not clamp the requested ``scan.max_workers``; one target, so the per-target
pool equals ``max_workers`` (``core.engine._intra_target_worker_budget``).
The engine's real ``DataScanner`` does the detection.

Profiles:

* ``local_sqlite`` — the source is a local SQLite file: no network wait, so
  with the GIL only a free-threaded build can overlap detection.
* ``simulated_query_latency`` — same source, each column sample preceded by a
  fixed ``time.sleep`` (``--latency-ms``) standing in for a network round trip
  to a remote database (the #1322 engagement measured ~140 ms). The sleep
  releases the GIL. **Simulated**: it is not a measurement of a real remote
  database, of its connection limits or of its server-side cost.

Each row records every wall time, the median, and whether the persisted
findings are identical to the serial run (ordered and sorted). The header
records interpreter, GIL state before and after the run, host load, CPU count
and commit.

Reproduce (repo root):

    python3.14t -X gil=0 tests/benchmarks/run_sql_intra_target_bench.py \\
        --output tests/benchmarks/sql_intra_target_nogil.json
    python3.14 tests/benchmarks/run_sql_intra_target_bench.py \\
        --output tests/benchmarks/sql_intra_target_gil.json

Both interpreters need the project dependencies and the repo root on
``PYTHONPATH``.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import sqlite3
import statistics
import subprocess
import sys
import sysconfig
import tempfile
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

BENCHMARK_ID = "sql_intra_target_v1"


def _git_sha_short() -> str | None:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return out.strip() or None
    except (OSError, subprocess.CalledProcessError):
        return None


def _gil_enabled() -> bool | None:
    fn = getattr(sys, "_is_gil_enabled", None)
    if callable(fn):
        try:
            return bool(fn())
        except Exception:  # noqa: BLE001
            return None
    return True


def _host_load() -> dict[str, float]:
    try:
        la1, la5, la15 = os.getloadavg()
        return {"load_1m": la1, "load_5m": la5, "load_15m": la15}
    except (AttributeError, OSError):
        return {}


def _seed_source(path: Path, *, tables: int, rows: int) -> dict[str, int]:
    """Synthetic only: checksum-valid sample CPF, example.com e-mails."""
    cols = ("nome", "email", "cpf", "telefone", "observacao", "vazio")
    con = sqlite3.connect(str(path))
    try:
        for t in range(tables):
            con.execute(
                f"CREATE TABLE clientes_{t:03d} ({', '.join(f'{c} TEXT' for c in cols)})"
            )
            con.executemany(
                f"INSERT INTO clientes_{t:03d} VALUES (?, ?, ?, ?, ?, ?)",
                [
                    (
                        f"Pessoa {t} {r}",
                        f"pessoa{t}x{r}@example.com",
                        "529.982.247-25",
                        f"+55 21 99999-{r % 10_000:04d}",
                        f"registro {r} sem dado pessoal",
                        None,
                    )
                    for r in range(rows)
                ],
            )
        con.commit()
    finally:
        con.close()
    return {"tables": tables, "columns_per_table": len(cols), "rows_per_table": rows}


def _license(work: Path) -> dict[str, Any]:
    import jwt
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    from tests.hybrid_license_fixture import seal_enforced_test_token
    from tests.license_verify_pin import pin_embedded_ed25519_pem

    priv = Ed25519PrivateKey.generate()
    now = datetime.now(UTC)
    payload = {
        "sub": "bench-1322",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=1)).timestamp()),
        "dbcid": "bench",
        "dbcname": "Bench",
        "dbenv": "lab",
        "dbissuer": "bench",
        "dbkid": "k1",
        "dbtier": "enterprise",
    }
    token = seal_enforced_test_token(priv, jwt.encode(payload, priv, algorithm="EdDSA"))
    lic = work / "bench.lic"
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


def _hermetic_home(base: Path) -> None:
    home = base / "home"
    home.mkdir(parents=True, exist_ok=True)
    os.environ["HOME"] = str(home)
    os.environ.pop("XDG_CONFIG_HOME", None)
    for key in (
        "DATA_BOAR_ENV",
        "DEBUG",
        "DATA_BOAR_TIER_OVERRIDE",
        "DATA_BOAR_LICENSE_MODE",
        "DATA_BOAR_LICENSE_PATH",
    ):
        os.environ.pop(key, None)


def _scan_once(
    *, work: Path, source: Path, licensing: dict[str, Any], workers: int, tag: str
) -> tuple[float, list[tuple], int]:
    from core.engine import AuditEngine
    from core.licensing.guard import get_license_guard, reset_license_guard_for_tests

    reset_license_guard_for_tests()
    db_path = work / f"{tag}.sqlite"
    if db_path.exists():
        db_path.unlink()
    cfg: dict[str, Any] = {
        "targets": [
            {
                "name": "bench-sql",
                "type": "database",
                "driver": "sqlite",
                "database": str(source),
            },
        ],
        "scan": {"max_workers": workers},
        "licensing": licensing,
        "file_scan": {"sample_limit": 5},
        "report": {"output_dir": str(work / "reports")},
        "sqlite_path": str(db_path),
    }
    engine = AuditEngine(cfg, db_path=str(db_path))
    get_license_guard(cfg)
    start = time.perf_counter()
    session_id = engine.start_audit()
    wall = time.perf_counter() - start
    effective = int(engine._max_workers)
    db_rows, _fs, _app, failures = engine.db_manager.get_findings(session_id)
    keys = [
        (
            str(r.get("schema_name")),
            str(r.get("table_name")),
            str(r.get("column_name")),
            str(r.get("pattern_detected")),
            str(r.get("sensitivity_level")),
            str(r.get("norm_tag")),
            str(r.get("ml_confidence")),
        )
        for r in db_rows
    ]
    if failures:
        raise RuntimeError(f"benchmark scan recorded failures: {failures[:3]}")
    engine.db_manager.engine.dispose()
    return wall, keys, effective


def _run_profile(
    *,
    name: str,
    work: Path,
    source: Path,
    licensing: dict[str, Any],
    workers_list: list[int],
    iterations: int,
    latency_ms: float,
) -> dict[str, Any]:
    from connectors.sql_connector import SQLConnector

    real_sample = SQLConnector.sample

    def _slow_sample(self: Any, *a: Any, **k: Any) -> str:
        time.sleep(latency_ms / 1000.0)
        return real_sample(self, *a, **k)

    if latency_ms > 0:
        SQLConnector.sample = _slow_sample  # type: ignore[method-assign]
    rows: list[dict[str, Any]] = []
    serial_keys: list[tuple] | None = None
    try:
        # Warm-up (imports, detector compile, page cache) — not recorded.
        _scan_once(work=work, source=source, licensing=licensing, workers=1, tag="warm")
        for workers in workers_list:
            walls: list[float] = []
            keys: list[tuple] = []
            effective = 0
            for it in range(iterations):
                wall, keys, effective = _scan_once(
                    work=work,
                    source=source,
                    licensing=licensing,
                    workers=workers,
                    tag=f"{name}_{workers}_{it}",
                )
                walls.append(round(wall, 4))
            if workers == 1:
                serial_keys = keys
            assert serial_keys is not None, "workers list must start with 1"
            rows.append(
                {
                    "workers": workers,
                    "effective_max_workers": effective,
                    "iterations": iterations,
                    "wall_seconds": walls,
                    "wall_seconds_median": round(statistics.median(walls), 4),
                    "finding_count": len(keys),
                    "parity_exact_ordered": keys == serial_keys,
                    "parity_exact_sorted": sorted(keys) == sorted(serial_keys),
                }
            )
    finally:
        SQLConnector.sample = real_sample  # type: ignore[method-assign]
    serial_median = rows[0]["wall_seconds_median"]
    for row in rows:
        row["speedup_vs_serial"] = round(serial_median / row["wall_seconds_median"], 3)
    return {
        "name": name,
        "simulated": latency_ms > 0,
        "simulated_query_latency_ms": latency_ms,
        "rows": rows,
    }


def run_benchmark(
    *,
    tables: int,
    rows_per_table: int,
    workers_list: list[int],
    iterations: int,
    latency_ms: float,
) -> dict[str, Any]:
    gil_before = _gil_enabled()
    load_before = _host_load()
    with tempfile.TemporaryDirectory(prefix="db_sql_intra_1322_") as tmp:
        work = Path(tmp)
        _hermetic_home(work)
        source = work / "source.db"
        source_info = _seed_source(source, tables=tables, rows=rows_per_table)
        licensing = _license(work)
        profiles = [
            _run_profile(
                name="local_sqlite",
                work=work,
                source=source,
                licensing=licensing,
                workers_list=workers_list,
                iterations=iterations,
                latency_ms=0.0,
            ),
            _run_profile(
                name="simulated_query_latency",
                work=work,
                source=source,
                licensing=licensing,
                workers_list=workers_list,
                iterations=iterations,
                latency_ms=latency_ms,
            ),
        ]
    gil_after = _gil_enabled()
    return {
        "benchmark": BENCHMARK_ID,
        "issue": "#1322",
        "source": source_info,
        "profiles": profiles,
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "free_threaded_build": bool(sysconfig.get_config_var("Py_GIL_DISABLED")),
        "gil_enabled_before": gil_before,
        "gil_enabled_after": gil_after,
        "cpu_count": os.cpu_count() or 1,
        "host_profile": f"{platform.system().lower()}-{platform.machine()}",
        "host_load_before": load_before,
        "host_load": _host_load(),
        "git_sha": _git_sha_short(),
        "generated_at": datetime.now(UTC).isoformat(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SQL per-table pool benchmark (#1322)")
    parser.add_argument("--tables", type=int, default=60)
    parser.add_argument("--rows", type=int, default=50)
    parser.add_argument("--workers", default="1,2,4,8")
    parser.add_argument("--iterations", type=int, default=5)
    parser.add_argument("--latency-ms", type=float, default=20.0)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    workers_list = sorted({max(1, int(w)) for w in str(args.workers).split(",")})
    if workers_list[0] != 1:
        workers_list.insert(0, 1)
    artifact = run_benchmark(
        tables=max(8, int(args.tables)),
        rows_per_table=max(5, int(args.rows)),
        workers_list=workers_list,
        iterations=max(5, int(args.iterations)),
        latency_ms=max(0.1, float(args.latency_ms)),
    )
    if artifact["gil_enabled_before"] != artifact["gil_enabled_after"]:
        print("[FAIL] GIL state changed during the run; artifact invalid.")
        return 2
    output = Path(args.output).expanduser()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(artifact, indent=2))
    print(f"[OK] Benchmark artifact: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
