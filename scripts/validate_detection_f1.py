#!/usr/bin/env python3
"""Compute detection precision/recall/F1 against ground_truth.yaml (#835).

Measures against the real detector tuple from ``SensitivityDetector.analyze``:
  (sensitivity_level, pattern_detected, norm_tag, confidence 0-100)

Default split is **measure** only. The **calibrate** split is reserved for
confidence-threshold exploration and must not reuse measure templates
(Presidio-research anti-leakage). Do not publish F1 from calibrate.

Usage:
  uv run python scripts/validate_detection_f1.py
  uv run python scripts/validate_detection_f1.py --split measure --json
  uv run python scripts/validate_detection_f1.py --split calibrate --confidence-hist
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.detector import SensitivityDetector  # noqa: E402

POSITIVE_CLASSES = frozenset({"pii", "tricky_fn"})
NEGATIVE_CLASSES = frozenset({"clean", "tricky_fp"})
DEFAULT_FIXTURE_ROOT = ROOT / "tests" / "data" / "f1_validation"
# Neutral column name — avoid schema-hint elevations on file content.
_COLUMN = "sample_text"


@dataclass
class FileResult:
    path: str
    split: str
    klass: str
    template_id: str
    expected_miss: bool
    expected_patterns: list[str]
    sensitivity: str
    pattern_detected: str
    norm_tag: str
    confidence: int
    is_finding: bool
    outcome: str  # TP|FP|TN|FN


@dataclass
class Metrics:
    tp: int = 0
    fp: int = 0
    tn: int = 0
    fn: int = 0

    @property
    def precision(self) -> float | None:
        denom = self.tp + self.fp
        return (self.tp / denom) if denom else None

    @property
    def recall(self) -> float | None:
        denom = self.tp + self.fn
        return (self.tp / denom) if denom else None

    @property
    def f1(self) -> float | None:
        p, r = self.precision, self.recall
        if p is None or r is None or (p + r) == 0:
            return None
        return 2 * p * r / (p + r)

    def as_dict(self) -> dict[str, Any]:
        return {
            "tp": self.tp,
            "fp": self.fp,
            "tn": self.tn,
            "fn": self.fn,
            "precision": self.precision,
            "recall": self.recall,
            "f1": self.f1,
        }


@dataclass
class RunReport:
    split: str
    fixture_root: str
    file_count: int
    run_metrics: Metrics = field(default_factory=Metrics)
    per_pattern: dict[str, Metrics] = field(default_factory=dict)
    per_class: dict[str, Metrics] = field(default_factory=dict)
    files: list[FileResult] = field(default_factory=list)
    known_limitations: list[dict[str, Any]] = field(default_factory=list)
    confidence_hist: dict[str, int] = field(default_factory=dict)
    anti_leakage_ok: bool = True
    anti_leakage_notes: list[str] = field(default_factory=list)


def _is_finding(sensitivity: str, pattern_detected: str) -> bool:
    if sensitivity in ("HIGH", "MEDIUM") and (pattern_detected or "").strip():
        return True
    return False


def _pattern_names(pattern_detected: str) -> set[str]:
    names: set[str] = set()
    for chunk in (pattern_detected or "").split(","):
        raw = chunk.strip()
        if not raw:
            continue
        names.add(raw.split("(", 1)[0].strip())
    return names


def _has_expected_patterns(pattern_detected: str, expected: list[str]) -> bool:
    if not expected:
        return _is_finding("HIGH", pattern_detected)  # fallback
    names = _pattern_names(pattern_detected)
    for pat in expected:
        if pat in names or any(pat in n for n in names):
            return True
    return False


def _file_positive_hit(entry: dict[str, Any], sens: str, pattern: str) -> bool:
    """Whether this labeled-positive file counts as detected.

    For ``tricky_fn`` with ``expected_miss: true``, require at least one
    ``expected_patterns`` hit so ML-only MEDIUM noise does not hide the FN.
    """
    if not _is_finding(sens, pattern):
        return False
    if entry.get("class") == "tricky_fn" and entry.get("expected_miss"):
        return _has_expected_patterns(
            pattern, list(entry.get("expected_patterns") or [])
        )
    return True


def _outcome(klass: str, found: bool) -> str:
    if klass in POSITIVE_CLASSES:
        return "TP" if found else "FN"
    if klass in NEGATIVE_CLASSES:
        return "FP" if found else "TN"
    return "TN" if not found else "FP"


def _fmt(x: float | None) -> str:
    return f"{x:.4f}" if x is not None else "n/a"


def load_manifest(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "files" not in data:
        raise ValueError(f"Invalid ground_truth manifest: {path}")
    return data


def check_anti_leakage(manifest: dict[str, Any]) -> tuple[bool, list[str]]:
    """Ensure measure and calibrate do not share template_id or synthetic ids."""
    notes: list[str] = []
    by_split: dict[str, set[str]] = defaultdict(set)
    for entry in manifest.get("files", []):
        by_split[entry["split"]].add(entry["template_id"])
    overlap = by_split.get("measure", set()) & by_split.get("calibrate", set())
    if overlap:
        notes.append(f"shared template_id across splits: {sorted(overlap)}")
    families = manifest.get("template_families") or {}
    m_ids = set((families.get("measure") or {}).values())
    c_ids = set((families.get("calibrate") or {}).values())
    id_overlap = m_ids & c_ids
    if id_overlap:
        notes.append(
            f"shared synthetic identifiers across families: {sorted(id_overlap)}"
        )
    return (not notes), notes


def evaluate(
    fixture_root: Path,
    *,
    split: str = "measure",
    detector: SensitivityDetector | None = None,
) -> RunReport:
    manifest_path = fixture_root / "ground_truth.yaml"
    manifest = load_manifest(manifest_path)
    ok, notes = check_anti_leakage(manifest)
    det = detector or SensitivityDetector()
    report = RunReport(
        split=split,
        fixture_root=str(fixture_root),
        file_count=0,
        anti_leakage_ok=ok,
        anti_leakage_notes=notes,
    )
    conf_bucket: Counter[str] = Counter()

    for entry in manifest["files"]:
        if entry["split"] != split:
            continue
        rel = entry["path"]
        path = fixture_root / rel
        text = path.read_text(encoding="utf-8", errors="replace")
        sens, pattern, norm, conf = det.analyze(_COLUMN, text)
        if entry["class"] in POSITIVE_CLASSES:
            found = _file_positive_hit(entry, sens, pattern)
        else:
            found = _is_finding(sens, pattern)
        outcome = _outcome(entry["class"], found)
        fr = FileResult(
            path=rel,
            split=entry["split"],
            klass=entry["class"],
            template_id=entry["template_id"],
            expected_miss=bool(entry.get("expected_miss")),
            expected_patterns=list(entry.get("expected_patterns") or []),
            sensitivity=sens,
            pattern_detected=pattern,
            norm_tag=norm,
            confidence=int(conf),
            is_finding=found,
            outcome=outcome,
        )
        report.files.append(fr)
        conf_bucket[f"{(conf // 10) * 10}-{((conf // 10) * 10) + 9}"] += 1

        m = report.run_metrics
        if outcome == "TP":
            m.tp += 1
        elif outcome == "FP":
            m.fp += 1
        elif outcome == "TN":
            m.tn += 1
        elif outcome == "FN":
            m.fn += 1

        cm = report.per_class.setdefault(entry["class"], Metrics())
        if outcome == "TP":
            cm.tp += 1
        elif outcome == "FP":
            cm.fp += 1
        elif outcome == "TN":
            cm.tn += 1
        elif outcome == "FN":
            cm.fn += 1

        # Per-pattern: expected pattern present in pattern_detected → TP for that pattern
        # on positive files; on negative files, unexpected pattern hit → FP.
        detected_names = _pattern_names(pattern)

        for pat in entry.get("expected_patterns") or []:
            pm = report.per_pattern.setdefault(pat, Metrics())
            if entry["class"] in POSITIVE_CLASSES:
                if pat in detected_names or any(pat in d for d in detected_names):
                    pm.tp += 1
                else:
                    pm.fn += 1
            elif entry["class"] in NEGATIVE_CLASSES:
                if pat in detected_names or any(pat in d for d in detected_names):
                    pm.fp += 1
                else:
                    pm.tn += 1

        if entry.get("expected_miss") and outcome == "FN":
            report.known_limitations.append(
                {
                    "path": rel,
                    "template_id": entry["template_id"],
                    "notes": entry.get("notes") or "",
                    "sensitivity": sens,
                    "pattern_detected": pattern,
                    "confidence": conf,
                }
            )

    report.file_count = len(report.files)
    report.confidence_hist = dict(sorted(conf_bucket.items()))
    return report


def report_to_dict(report: RunReport) -> dict[str, Any]:
    return {
        "split": report.split,
        "fixture_root": report.fixture_root,
        "file_count": report.file_count,
        "anti_leakage_ok": report.anti_leakage_ok,
        "anti_leakage_notes": report.anti_leakage_notes,
        "run": report.run_metrics.as_dict(),
        "per_class": {k: v.as_dict() for k, v in sorted(report.per_class.items())},
        "per_pattern": {k: v.as_dict() for k, v in sorted(report.per_pattern.items())},
        "known_limitations": report.known_limitations,
        "confidence_hist": report.confidence_hist,
        "files": [asdict(f) for f in report.files],
    }


def print_human(report: RunReport, *, show_files: bool = False) -> None:
    print(f"F1 validation — split={report.split}  files={report.file_count}")
    print(f"fixture_root: {report.fixture_root}")
    if not report.anti_leakage_ok:
        print("ANTI-LEAKAGE FAILED:", "; ".join(report.anti_leakage_notes))
    else:
        print("anti-leakage: OK (measure vs calibrate template families disjoint)")
    m = report.run_metrics
    print(
        f"run: TP={m.tp} FP={m.fp} TN={m.tn} FN={m.fn}  "
        f"P={_fmt(m.precision)} R={_fmt(m.recall)} F1={_fmt(m.f1)}"
    )
    if report.per_class:
        print("per_class:")
        for name, cm in sorted(report.per_class.items()):
            print(
                f"  {name}: TP={cm.tp} FP={cm.fp} TN={cm.tn} FN={cm.fn}  "
                f"P={_fmt(cm.precision)} R={_fmt(cm.recall)} F1={_fmt(cm.f1)}"
            )
    if report.per_pattern:
        print("per_pattern:")
        for name, pm in sorted(report.per_pattern.items()):
            print(
                f"  {name}: TP={pm.tp} FP={pm.fp} TN={pm.tn} FN={pm.fn}  "
                f"P={_fmt(pm.precision)} R={_fmt(pm.recall)} F1={_fmt(pm.f1)}"
            )
    if report.known_limitations:
        print("known_limitations (expected_miss + FN):")
        for item in report.known_limitations:
            print(f"  - {item['path']}: {item.get('notes') or '(no notes)'}")
    if show_files:
        print("files:")
        for fr in report.files:
            print(
                f"  [{fr.outcome}] {fr.path} class={fr.klass} "
                f"sens={fr.sensitivity} pat={fr.pattern_detected!r} conf={fr.confidence}"
            )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fixture-root",
        type=Path,
        default=DEFAULT_FIXTURE_ROOT,
        help="Directory containing ground_truth.yaml",
    )
    parser.add_argument(
        "--split",
        choices=("measure", "calibrate", "all"),
        default="measure",
        help="Which split to score (default: measure). 'all' prints both; "
        "only measure is for published baseline.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON report")
    parser.add_argument(
        "--files",
        action="store_true",
        help="Include per-file lines in human output",
    )
    parser.add_argument(
        "--confidence-hist",
        action="store_true",
        help="Print confidence histogram (useful on calibrate split)",
    )
    args = parser.parse_args()
    root = args.fixture_root.resolve()
    if not (root / "ground_truth.yaml").is_file():
        print(
            f"Missing {root / 'ground_truth.yaml'} — run generate_f1_validation_fixtures.py",
            file=sys.stderr,
        )
        return 2

    splits = ["measure", "calibrate"] if args.split == "all" else [args.split]
    payloads: list[dict[str, Any]] = []
    for sp in splits:
        if sp == "calibrate":
            print(
                "NOTE: calibrate split is for confidence tuning only — "
                "do not publish these numbers as the product F1 baseline.\n"
            )
        report = evaluate(root, split=sp)
        if args.json:
            payloads.append(report_to_dict(report))
        else:
            print_human(report, show_files=args.files)
            if args.confidence_hist:
                print("confidence_hist:", report.confidence_hist)
            print()
        if not report.anti_leakage_ok:
            return 3
    if args.json:
        out = payloads[0] if len(payloads) == 1 else {"splits": payloads}
        print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
