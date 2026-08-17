"""Smoke tests for F1 validation fixtures + harness (#835).

Baseline numbers are published in docs/VALIDATION.md (measured, not asserted).
These tests only guard structure, anti-leakage, and clear-PII recall.
"""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "tests" / "data" / "f1_validation"


def test_ground_truth_manifest_exists_and_has_four_classes():
    path = FIXTURE_ROOT / "ground_truth.yaml"
    assert path.is_file(), "run scripts/generate_f1_validation_fixtures.py"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    classes = {e["class"] for e in data["files"]}
    assert classes == {"pii", "clean", "tricky_fp", "tricky_fn"}
    assert {"measure", "calibrate"} <= {e["split"] for e in data["files"]}


def test_anti_leakage_measure_vs_calibrate():
    from scripts.validate_detection_f1 import check_anti_leakage, load_manifest

    manifest = load_manifest(FIXTURE_ROOT / "ground_truth.yaml")
    ok, notes = check_anti_leakage(manifest)
    assert ok, notes


def test_measure_clear_pii_all_true_positives():
    from scripts.validate_detection_f1 import evaluate

    report = evaluate(FIXTURE_ROOT, split="measure")
    pii = [f for f in report.files if f.klass == "pii"]
    assert pii, "expected measure/pii fixtures"
    assert all(f.outcome == "TP" for f in pii)
    assert report.run_metrics.recall is not None


def test_tricky_fn_expected_miss_recorded_when_fn():
    from scripts.validate_detection_f1 import evaluate

    report = evaluate(FIXTURE_ROOT, split="measure")
    fn_expected = [
        f for f in report.files if f.klass == "tricky_fn" and f.expected_miss
    ]
    assert fn_expected
    # Honest gap: at least one known limitation entry when those are FN
    if any(f.outcome == "FN" for f in fn_expected):
        assert report.known_limitations
