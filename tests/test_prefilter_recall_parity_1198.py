"""Recall-first parity guard for issue #1198 (prefilter must not drop profile hits)."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import pytest
import yaml

from core.scanner import DataScanner
from pro.prefilter import ProPreFilter

REPO_ROOT = Path(__file__).resolve().parent.parent
COMPLIANCE_SAMPLES_DIR = REPO_ROOT / "docs" / "compliance-samples"


def _compliance_sample_yaml_files() -> list[Path]:
    if not COMPLIANCE_SAMPLES_DIR.is_dir():
        return []
    return sorted(COMPLIANCE_SAMPLES_DIR.glob("compliance-sample-*.yaml"))


def _sensitive_terms(sample_data: dict) -> list[str]:
    terms = sample_data.get("terms") or []
    out: list[str] = []
    for item in terms:
        if not isinstance(item, dict):
            continue
        text = str(item.get("text") or "").strip()
        if not text:
            continue
        label = item.get("label")
        label_s = str(label).strip().lower()
        if label in (1, True) or label_s in {"1", "true", "yes", "sensitive"}:
            out.append(text)
    return out


def _regex_patterns(sample_data: dict) -> list[str]:
    regex_items = sample_data.get("regex") or []
    out: list[str] = []
    for item in regex_items:
        if not isinstance(item, dict):
            continue
        pattern = str(item.get("pattern") or "").strip()
        if pattern:
            out.append(pattern)
    return out


def _findings_fingerprint(
    scanner: DataScanner, probes: list[str]
) -> Counter[tuple[str, str, str]]:
    found: Counter[tuple[str, str, str]] = Counter()
    for probe in probes:
        result = scanner.scan_column("profile_probe", probe)
        if result.get("sensitivity_level") != "LOW":
            found[
                (
                    str(result.get("sensitivity_level") or ""),
                    str(result.get("norm_tag") or ""),
                    str(result.get("pattern_detected") or ""),
                )
            ] += 1
    return found


@pytest.mark.parametrize(
    "sample_path", _compliance_sample_yaml_files(), ids=lambda p: p.name
)
def test_prefilter_recall_parity_for_compliance_samples(sample_path: Path) -> None:
    """
    Golden rule: findings_with_prefilter == findings_without_prefilter.

    For each compliance sample YAML, use synthetic probes from declared sensitive terms.
    """
    sample_data = yaml.safe_load(sample_path.read_text(encoding="utf-8")) or {}
    terms = _sensitive_terms(sample_data)
    regexes = _regex_patterns(sample_data)
    assert terms, f"{sample_path.name}: expected at least one sensitive term for probes"
    probes = [f"probe {term} probe" for term in terms[:12]]

    scanner = DataScanner(
        regex_overrides_path=str(sample_path),
        ml_patterns_path=str(sample_path),
    )
    baseline = _findings_fingerprint(scanner, probes)

    prefilter = ProPreFilter(profile_terms=terms, profile_regexes=regexes)
    filtered_probes = prefilter.filter_candidates(probes)
    accelerated = _findings_fingerprint(scanner, filtered_probes)

    assert accelerated == baseline
