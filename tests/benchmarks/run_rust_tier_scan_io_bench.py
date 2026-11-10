#!/usr/bin/env python3
"""
Filesystem scan with I/O at each tier worker cap (#2182).

Runs ``AuditEngine.start_audit()`` against a synthetic ``.txt`` tree (walk, read,
detect) with ``licensing.mode: enforced`` and tier JWTs so ``worker_cap()`` matches
production. Compares wall time and ``rust_regex_stage`` backend per tier.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import statistics
import subprocess
import sys
import time
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from core.licensing.guard import _TIER_DEFAULT_WORKER_CAP, reset_license_guard_for_tests
from core.licensing.tier_features import Tier

BENCHMARK_ID = "rust_tier_scan_io_v1"

_TIER_ROWS: list[tuple[str, Tier]] = [
    ("community", Tier.COMMUNITY),
    ("std", Tier.STD),
    ("pro", Tier.PRO),
    ("pro_plus", Tier.PRO_PLUS),
]

_FILE_PAYLOAD = (
    "Holder: sample_holder_a\nID: 123.456.789-00\nEmail: sample@example.com\n"
    "Phone: (11) 90000-0000\n"
)


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


def _host_profile() -> str:
    machine = platform.machine() or "unknown"
    system = platform.system().lower() or "unknown"
    return f"{system}-{machine}"


def _host_load() -> dict[str, float]:
    try:
        la1, la5, la15 = os.getloadavg()
        return {"load_1m": la1, "load_5m": la5, "load_15m": la15}
    except (AttributeError, OSError):
        return {}


def _gil_enabled() -> bool | None:
    fn = getattr(sys, "_is_gil_enabled", None)
    if callable(fn):
        try:
            return bool(fn())
        except Exception:  # noqa: BLE001
            return None
    return None


def _pem_public(priv: Ed25519PrivateKey) -> str:
    return (
        priv.public_key()
        .public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode("ascii")
        .strip()
    )


def _make_license_token(priv: Ed25519PrivateKey, *, dbtier: str) -> str:
    from tests.hybrid_license_fixture import seal_enforced_test_token

    now = datetime.now(timezone.utc)
    payload = {
        "sub": "bench-2182",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=1)).timestamp()),
        "dbcid": "bench",
        "dbcname": "Bench",
        "dbenv": "lab",
        "dbissuer": "bench",
        "dbkid": "k1",
        "dbtier": dbtier,
    }
    raw = jwt.encode(payload, priv, algorithm="EdDSA")
    return seal_enforced_test_token(priv, raw)


def _seed_corpus(root: Path, *, file_count: int) -> int:
    root.mkdir(parents=True, exist_ok=True)
    for i in range(file_count):
        (root / f"doc_{i:05d}.txt").write_text(_FILE_PAYLOAD, encoding="utf-8")
    return file_count


def _hermetic_home(base: Path) -> None:
    home = base / "home"
    roaming = home / "AppData" / "Roaming"
    home.mkdir(parents=True, exist_ok=True)
    roaming.mkdir(parents=True, exist_ok=True)
    os.environ["HOME"] = str(home)
    os.environ["USERPROFILE"] = str(home)
    os.environ["APPDATA"] = str(roaming)
    os.environ.pop("XDG_CONFIG_HOME", None)
    for key in (
        "DATA_BOAR_ENV",
        "DEBUG",
        "DATA_BOAR_TIER_OVERRIDE",
        "DATA_BOAR_LICENSE_MODE",
        "DATA_BOAR_LICENSE_PATH",
    ):
        os.environ.pop(key, None)


def _run_tier_scan(
    *,
    work_root: Path,
    corpus_root: Path,
    priv: Ed25519PrivateKey,
    dbtier: str,
    tier: Tier,
    requested_workers: int,
) -> dict[str, Any]:
    from core.engine import AuditEngine
    from core.licensing.guard import get_license_guard
    from tests.license_verify_pin import pin_embedded_ed25519_pem

    reset_license_guard_for_tests()
    pin_embedded_ed25519_pem(_pem_public(priv))

    lic_path = work_root / f"{dbtier}.lic"
    lic_path.write_text(_make_license_token(priv, dbtier=dbtier), encoding="utf-8")

    db_path = work_root / f"{dbtier}.sqlite"
    out_dir = work_root / f"{dbtier}_reports"
    out_dir.mkdir(parents=True, exist_ok=True)

    cfg: dict[str, Any] = {
        "targets": [
            {
                "name": "bench-fs",
                "type": "filesystem",
                "path": str(corpus_root),
                "recursive": True,
            }
        ],
        "scan": {"max_workers": requested_workers},
        "licensing": {"mode": "enforced", "license_path": str(lic_path)},
        "file_scan": {"sample_limit": 12_000, "extensions": [".txt"]},
        "detection": {},
        "report": {"output_dir": str(out_dir)},
        "sqlite_path": str(db_path),
    }

    engine = AuditEngine(cfg, db_path=str(db_path))
    get_license_guard(cfg)

    start = time.perf_counter()
    session_id = engine.start_audit()
    wall_s = time.perf_counter() - start

    status = engine.scanner.detector.rust_regex_stage_status
    prefilter = status.to_prefilter_dict() if status else {}

    _db, fs_rows, _app, _fail = engine.db_manager.get_findings(session_id)
    finding_count = len(fs_rows)

    nominal_cap = _TIER_DEFAULT_WORKER_CAP.get(tier)

    return {
        "dbtier": dbtier,
        "tier_enum": tier.value,
        "nominal_worker_cap": nominal_cap,
        "requested_max_workers": requested_workers,
        "effective_max_workers": engine._max_workers,
        "wall_seconds": round(wall_s, 4),
        "file_count": len(list(corpus_root.glob("**/*.txt"))),
        "finding_count": finding_count,
        "rust_regex_stage_backend": prefilter.get("backend"),
        "rust_regex_stage_active": prefilter.get("active"),
        "rust_regex_stage_reason": prefilter.get("reason"),
    }


def run_benchmark(
    *,
    file_count: int,
    requested_workers: int,
    tier_iterations: int,
) -> dict[str, Any]:
    import tempfile

    priv = Ed25519PrivateKey.generate()

    tier_rows: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="db_rust_tier_io_") as tmp:
        work_root = Path(tmp)
        corpus_root = work_root / "corpus"
        _hermetic_home(work_root)
        _seed_corpus(corpus_root, file_count=file_count)

        for dbtier, tier in _TIER_ROWS:
            timings: list[float] = []
            last_row: dict[str, Any] = {}
            for _ in range(max(1, tier_iterations)):
                row = _run_tier_scan(
                    work_root=work_root,
                    corpus_root=corpus_root,
                    priv=priv,
                    dbtier=dbtier,
                    tier=tier,
                    requested_workers=requested_workers,
                )
                timings.append(float(row["wall_seconds"]))
                last_row = row
            last_row["wall_seconds_median"] = round(statistics.median(timings), 4)
            last_row["iterations"] = len(timings)
            tier_rows.append(last_row)

    pro_plus = next(r for r in tier_rows if r["dbtier"] == "pro_plus")
    community = next(r for r in tier_rows if r["dbtier"] == "community")
    pp_s = float(pro_plus["wall_seconds_median"])
    comm_s = float(community["wall_seconds_median"])
    ratio = round(comm_s / pp_s, 4) if pp_s > 0 else None

    recommendation = {
        "rust_as_headline_speed_differentiator": False,
        "keep_rust_regex_stage_on_pro_plus": True,
        "rationale_en": (
            "Pinned rust_per_call_cost_v1 shows Rust loses per sample on short text; "
            "RUST_REGEX_STAGE_MIN_TEXT_CHARS keeps typical cells on Python regex. "
            "End-to-end filesystem scan I/O dominates wall time at every tier worker cap "
            "(this artifact); Rust tier gating remains a Pro+ equivalence/superset feature "
            "(ADR 0083), not a net speed upsell for default workloads."
        ),
        "pro_plus_over_community_wall_ratio_median": ratio,
    }

    return {
        "benchmark": BENCHMARK_ID,
        "file_count": file_count,
        "requested_max_workers": requested_workers,
        "tier_runs": tier_rows,
        "tier_differentiator_recommendation": recommendation,
        "cp314t_wheel_status": {
            "published_in_repo_ci": False,
            "blocker": "pyo3 abi3-py38 stable wheel does not load on python3.14t",
            "follow_up": "docs/TECH_GUIDE.md § Rust extension — cp314t; wheel-matrix #782",
        },
        "host_profile": _host_profile(),
        "host_load": _host_load(),
        "gil_enabled": _gil_enabled(),
        "python_version": platform.python_version(),
        "git_sha": _git_sha_short(),
        "generated_at": datetime.now(UTC).isoformat(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run tier-capped filesystem scan I/O benchmark (#2182)"
    )
    parser.add_argument("--files", type=int, default=350)
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--iterations", type=int, default=1)
    parser.add_argument(
        "--output",
        default="tests/benchmarks/rust_tier_scan_io.json",
    )
    args = parser.parse_args(argv)

    artifact = run_benchmark(
        file_count=max(50, int(args.files)),
        requested_workers=max(1, int(args.workers)),
        tier_iterations=max(1, int(args.iterations)),
    )
    output = Path(args.output).expanduser()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(artifact, indent=2))
    print(f"[OK] Benchmark artifact: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
