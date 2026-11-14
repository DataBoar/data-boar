#!/usr/bin/env python3
"""
Filesystem intra-target worker pool: serial vs parallel on one target (#1820).

Runs ``AuditEngine.start_audit()`` (walk, read, detect, persist; no report) on a
synthetic tree with sub-folders, hard links, file symlinks, small and large
files. ``licensing.mode: enforced`` with an Enterprise test JWT so the tier cap
does not clamp the requested ``scan.max_workers``; one target, so the per-target
pool equals ``max_workers`` (``core.engine._intra_target_worker_budget``).

Profiles:

* ``local_disk`` — files on the local filesystem (page cache warm after the
  first iteration). Detection is CPU-bound here (see
  ``filesystem_phase_breakdown_v1``), so only a GIL-free build can gain.
* ``simulated_read_latency`` — same corpus, each sample read preceded by a
  fixed ``time.sleep`` (``--latency-ms``) standing in for NFS/SSHFS round trips.
  The sleep releases the GIL, so any build can overlap it. **Simulated**: it is
  not a measurement of a real network filesystem.

Each row records every wall time, the median, and whether the persisted
findings are identical to the serial run (ordered and sorted). The header
records interpreter, GIL state before and after the run (a C extension
without free-threading support re-enables the GIL on import), host, CPU count
and commit.

Reproduce (repo root):

    python3.14t -X gil=0 tests/benchmarks/run_filesystem_intra_target_bench.py \\
        --output tests/benchmarks/filesystem_intra_target_nogil.json
    python3.14 tests/benchmarks/run_filesystem_intra_target_bench.py \\
        --output tests/benchmarks/filesystem_intra_target_gil.json

Both interpreters need the project dependencies (``uv export`` + ``uv pip
install``) and the repo root on ``PYTHONPATH``.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import statistics
import subprocess
import sys
import sysconfig
import tempfile
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

BENCHMARK_ID = "filesystem_intra_target_v1"

_SMALL = (
    "nome;email;cpf;telefone\n"
    "Pessoa {i};pessoa{i}@example.com;529.982.247-25;+55 21 99999-{j:04d}\n"
)
_FILLER = "lorem ipsum dolor sit amet consectetur adipiscing elit " * 20 + "\n"


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


def _seed_corpus(root: Path, *, file_count: int, large_every: int) -> dict[str, int]:
    """Synthetic only: checksum-valid sample CPF, example.com e-mails."""
    root.mkdir(parents=True, exist_ok=True)
    large = 0
    for i in range(file_count):
        sub = root / f"d{i % 32:02d}" / f"s{i % 5}"
        sub.mkdir(parents=True, exist_ok=True)
        body = _SMALL.format(i=i, j=i % 10_000)
        if large_every and i % large_every == 0:
            body += _FILLER * 400  # ~0.5 MB, sample cap still applies
            large += 1
        elif i % 4 == 1:
            body = f"registro {i} sem dado pessoal\n" + _FILLER
        (sub / f"doc_{i:05d}.csv").write_text(body, encoding="utf-8")
    alias = root / "aliases"
    alias.mkdir()
    links = 0
    for i in range(0, file_count, 50):
        src = root / f"d{i % 32:02d}" / f"s{i % 5}" / f"doc_{i:05d}.csv"
        os.link(src, alias / f"hard_{i:05d}.csv")
        os.symlink(src, alias / f"sym_{i:05d}.csv")
        links += 2
    return {"files": file_count, "large_files": large, "alias_links": links}


def _license(work: Path) -> dict[str, Any]:
    import jwt
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    from tests.hybrid_license_fixture import seal_enforced_test_token
    from tests.license_verify_pin import pin_embedded_ed25519_pem

    priv = Ed25519PrivateKey.generate()
    now = datetime.now(UTC)
    payload = {
        "sub": "bench-1820",
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
    *, work: Path, corpus: Path, licensing: dict[str, Any], workers: int, tag: str
) -> tuple[float, list[tuple], int]:
    from core.engine import AuditEngine
    from core.licensing.guard import get_license_guard, reset_license_guard_for_tests

    reset_license_guard_for_tests()
    db_path = work / f"{tag}.sqlite"
    if db_path.exists():
        db_path.unlink()
    cfg: dict[str, Any] = {
        "targets": [
            {"name": "bench-fs", "type": "filesystem", "path": str(corpus)},
        ],
        "scan": {"max_workers": workers},
        "licensing": licensing,
        "file_scan": {"extensions": [".csv"]},
        "report": {"output_dir": str(work / "reports")},
        "sqlite_path": str(db_path),
    }
    engine = AuditEngine(cfg, db_path=str(db_path))
    get_license_guard(cfg)
    start = time.perf_counter()
    session_id = engine.start_audit()
    wall = time.perf_counter() - start
    effective = int(engine._max_workers)
    _db, fs_rows, _app, _fail = engine.db_manager.get_findings(session_id)
    keys = [
        (
            str(r.get("path")),
            str(r.get("file_name")),
            str(r.get("pattern_detected")),
            str(r.get("sensitivity_level")),
            str(r.get("data_type")),
        )
        for r in fs_rows
    ]
    engine.db_manager.engine.dispose()
    return wall, keys, effective


def _run_profile(
    *,
    name: str,
    work: Path,
    corpus: Path,
    licensing: dict[str, Any],
    workers_list: list[int],
    iterations: int,
    latency_ms: float,
) -> dict[str, Any]:
    import connectors.filesystem_connector as fsc

    real_read = fsc._read_text_sample

    def _slow_read(*a: Any, **k: Any) -> str:
        time.sleep(latency_ms / 1000.0)
        return real_read(*a, **k)

    if latency_ms > 0:
        fsc._read_text_sample = _slow_read
    rows: list[dict[str, Any]] = []
    serial_keys: list[tuple] | None = None
    try:
        # Warm-up (page cache, imports, detector compile) — not recorded.
        _scan_once(work=work, corpus=corpus, licensing=licensing, workers=1, tag="warm")
        for workers in workers_list:
            walls: list[float] = []
            keys: list[tuple] = []
            effective = 0
            for it in range(iterations):
                wall, keys, effective = _scan_once(
                    work=work,
                    corpus=corpus,
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
        fsc._read_text_sample = real_read
    serial_median = rows[0]["wall_seconds_median"]
    for row in rows:
        row["speedup_vs_serial"] = round(serial_median / row["wall_seconds_median"], 3)
    return {
        "name": name,
        "simulated": latency_ms > 0,
        "simulated_read_latency_ms": latency_ms,
        "rows": rows,
    }


def run_benchmark(
    *, file_count: int, workers_list: list[int], iterations: int, latency_ms: float
) -> dict[str, Any]:
    gil_before = _gil_enabled()
    with tempfile.TemporaryDirectory(prefix="db_fs_intra_1820_") as tmp:
        work = Path(tmp)
        _hermetic_home(work)
        corpus = work / "corpus"
        corpus_info = _seed_corpus(
            corpus, file_count=file_count, large_every=max(1, file_count // 40)
        )
        licensing = _license(work)
        profiles = [
            _run_profile(
                name="local_disk",
                work=work,
                corpus=corpus,
                licensing=licensing,
                workers_list=workers_list,
                iterations=iterations,
                latency_ms=0.0,
            ),
            _run_profile(
                name="simulated_read_latency",
                work=work,
                corpus=corpus,
                licensing=licensing,
                workers_list=workers_list,
                iterations=iterations,
                latency_ms=latency_ms,
            ),
        ]
    gil_after = _gil_enabled()
    return {
        "benchmark": BENCHMARK_ID,
        "issue": "#1820",
        "corpus": corpus_info,
        "profiles": profiles,
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "free_threaded_build": bool(sysconfig.get_config_var("Py_GIL_DISABLED")),
        "gil_enabled_before": gil_before,
        "gil_enabled_after": gil_after,
        "cpu_count": os.cpu_count() or 1,
        "host_profile": f"{platform.system().lower()}-{platform.machine()}",
        "host_load": _host_load(),
        "git_sha": _git_sha_short(),
        "generated_at": datetime.now(UTC).isoformat(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Filesystem intra-target pool benchmark (#1820)"
    )
    parser.add_argument("--files", type=int, default=2000)
    parser.add_argument("--workers", default="1,2,4,8")
    parser.add_argument("--iterations", type=int, default=3)
    parser.add_argument("--latency-ms", type=float, default=2.0)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    workers_list = sorted({max(1, int(w)) for w in str(args.workers).split(",")})
    if workers_list[0] != 1:
        workers_list.insert(0, 1)
    artifact = run_benchmark(
        file_count=max(100, int(args.files)),
        workers_list=workers_list,
        iterations=max(3, int(args.iterations)),
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
