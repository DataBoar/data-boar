"""Benchmark gate — speed axis + safe (recall) axis (#1338).

The gate is **blocking**: a recall regression fails even when wall-clock improves.
No compensation between axes (ponytail-style ``safe`` column).
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# NASA Safe-Hold floor documented in pro/engine.py and pro/worker_logic.py.
SAFE_HOLD_MIN_SPEEDUP = 0.574

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OFFICIAL_MANIFEST = (
    REPO_ROOT
    / "tests"
    / "benchmarks"
    / "reference_manifests"
    / "official_pro_v1_200k.json"
)


@dataclass(frozen=True)
class BenchmarkGateResult:
    """Outcome of evaluating one benchmark artifact against gate rules."""

    speed_axis_pass: bool
    safe_axis_pass: bool
    speedup_vs_opencore: float
    opencore_hits: int
    pro_hits: int
    opencore_seconds: float
    pro_seconds: float
    expected_hits: int | None
    tolerance: str
    failure_reasons: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return self.speed_axis_pass and self.safe_axis_pass

    def to_gate_dict(self) -> dict[str, Any]:
        return {
            "speed_axis": "pass" if self.speed_axis_pass else "fail",
            "safe_axis": "pass" if self.safe_axis_pass else "fail",
            "safe_hold_min_speedup": SAFE_HOLD_MIN_SPEEDUP,
            "speedup_vs_opencore": round(self.speedup_vs_opencore, 4),
            "opencore_hits": self.opencore_hits,
            "pro_hits": self.pro_hits,
            "opencore_seconds": round(self.opencore_seconds, 6),
            "pro_seconds": round(self.pro_seconds, 6),
            "expected_hits": self.expected_hits,
            "tolerance": self.tolerance,
            "failure_reasons": list(self.failure_reasons),
        }


def _load_manifest(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    if not path.is_file():
        raise FileNotFoundError(f"benchmark reference manifest missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def evaluate_official_pro_v1(
    artifact: dict[str, Any],
    *,
    manifest: dict[str, Any] | None = None,
    manifest_path: Path | None = DEFAULT_OFFICIAL_MANIFEST,
) -> BenchmarkGateResult:
    """Evaluate ``official_pro_v1`` JSON against speed + safe axes.

    **Safe axis (blocking):** ``opencore_hits == pro_hits`` with **exact** tolerance
    (no band). Optional manifest pins the expected count for the synthetic corpus.

    **Speed axis (blocking):** ``speedup_vs_opencore`` must stay at or above
    ``SAFE_HOLD_MIN_SPEEDUP`` (0.574). A faster Pro path still passes; a slower one
    triggers NASA Safe-Hold.
    """
    if manifest is None and manifest_path is not None:
        manifest = _load_manifest(manifest_path)

    opencore_hits = int(artifact["opencore_hits"])
    pro_hits = int(artifact["pro_hits"])
    speedup = float(artifact["speedup_vs_opencore"])
    opencore_seconds = float(artifact["opencore_seconds"])
    pro_seconds = float(artifact["pro_seconds"])

    tolerance = "exact"
    expected_hits: int | None = None
    if manifest:
        tolerance = str(manifest.get("tolerance") or "exact")
        raw_expected = manifest.get("expected_opencore_hits")
        if raw_expected is not None:
            expected_hits = int(raw_expected)

    failures: list[str] = []

    safe_pass = opencore_hits == pro_hits
    if not safe_pass:
        failures.append(
            f"safe_axis: opencore_hits={opencore_hits} != pro_hits={pro_hits}"
        )
    if expected_hits is not None and tolerance == "exact":
        if opencore_hits != expected_hits:
            failures.append(
                f"safe_axis: opencore_hits={opencore_hits} != expected={expected_hits}"
            )
        if pro_hits != expected_hits:
            failures.append(
                f"safe_axis: pro_hits={pro_hits} != expected={expected_hits}"
            )
        safe_pass = (
            safe_pass and opencore_hits == expected_hits and pro_hits == expected_hits
        )

    speed_pass = speedup >= SAFE_HOLD_MIN_SPEEDUP
    if not speed_pass:
        failures.append(
            f"speed_axis: speedup_vs_opencore={speedup:.4f} < "
            f"safe_hold_min={SAFE_HOLD_MIN_SPEEDUP}"
        )

    return BenchmarkGateResult(
        speed_axis_pass=speed_pass,
        safe_axis_pass=safe_pass,
        speedup_vs_opencore=speedup,
        opencore_hits=opencore_hits,
        pro_hits=pro_hits,
        opencore_seconds=opencore_seconds,
        pro_seconds=pro_seconds,
        expected_hits=expected_hits,
        tolerance=tolerance,
        failure_reasons=tuple(failures),
    )


def evaluate_ab_recall_parity(
    legacy_findings: int,
    candidate_findings: int,
    *,
    expected_findings: int | None = None,
) -> tuple[bool, tuple[str, ...]]:
    """Lab A/B safe check: legacy and candidate must match exactly (26=26 precedent)."""
    failures: list[str] = []
    if legacy_findings != candidate_findings:
        failures.append(
            f"safe_axis: legacy_findings={legacy_findings} != "
            f"candidate_findings={candidate_findings}"
        )
    if expected_findings is not None:
        if legacy_findings != expected_findings:
            failures.append(
                f"safe_axis: legacy_findings={legacy_findings} != "
                f"expected={expected_findings}"
            )
        if candidate_findings != expected_findings:
            failures.append(
                f"safe_axis: candidate_findings={candidate_findings} != "
                f"expected={expected_findings}"
            )
    return (not failures, tuple(failures))


def format_gate_report(result: BenchmarkGateResult) -> str:
    """Human-readable lines: time and recall together (ponytail-style)."""
    lines = [
        "BENCHMARK GATE (speed + safe)",
        "-" * 40,
        (
            f"time: opencore={result.opencore_seconds:.4f}s | "
            f"pro={result.pro_seconds:.4f}s | "
            f"speedup_vs_opencore={result.speedup_vs_opencore:.4f}"
        ),
        (
            f"recall: opencore_hits={result.opencore_hits} | "
            f"pro_hits={result.pro_hits}"
            + (
                f" | expected={result.expected_hits}"
                if result.expected_hits is not None
                else ""
            )
        ),
        f"speed_axis: {'PASS' if result.speed_axis_pass else 'FAIL'}",
        f"safe_axis: {'PASS' if result.safe_axis_pass else 'FAIL'}",
        f"gate: {'PASS' if result.passed else 'FAIL'}",
    ]
    if result.failure_reasons:
        lines.append("reasons:")
        lines.extend(f"  - {reason}" for reason in result.failure_reasons)
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate official_pro_v1 benchmark JSON (speed + safe gate)"
    )
    parser.add_argument(
        "artifact",
        nargs="?",
        help="Path to benchmark JSON (default: stdin)",
    )
    parser.add_argument(
        "--manifest",
        default=str(DEFAULT_OFFICIAL_MANIFEST),
        help="Reference manifest JSON (use 'none' to skip pinning)",
    )
    args = parser.parse_args(argv)

    if args.artifact:
        payload = json.loads(Path(args.artifact).read_text(encoding="utf-8"))
    else:
        payload = json.load(sys.stdin)

    manifest_path: Path | None
    if str(args.manifest).lower() == "none":
        manifest_path = None
    else:
        manifest_path = Path(args.manifest).expanduser()

    result = evaluate_official_pro_v1(payload, manifest_path=manifest_path)
    print(format_gate_report(result))
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
