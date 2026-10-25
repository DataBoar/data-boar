"""Contract tests for Open Core and Pro+ pre-filter implementations."""

from __future__ import annotations

from core.prefilter import OpenCorePreFilter, PreFilter
from pro.prefilter import ProPreFilter, get_prefilter


def test_opencore_prefilter_contract() -> None:
    pf = OpenCorePreFilter()
    assert isinstance(pf, PreFilter)
    rows = [
        "clean text",
        "cpf 390.533.447-05",
        "email alpha@example.test",
    ]
    out = pf.filter_candidates(rows)
    assert "clean text" not in out
    assert any("390.533.447-05" in x for x in out)
    assert any("alpha@example.test" in x for x in out)


def test_pro_prefilter_fallback_without_rust() -> None:
    pf = ProPreFilter()
    rows = ["clean", "mail beta@example.test"]
    out = pf.filter_candidates(rows)
    assert out == ["mail beta@example.test"]


def test_get_prefilter_switch() -> None:
    assert get_prefilter(enable_pro=False).name == "open_core_regex_prefilter_v1"
    assert get_prefilter(enable_pro=True).name == "pro_prefilter_auto_v1"


def test_prefilter_recall_first_passthrough_when_profile_terms_active() -> None:
    rows = ["clean text", "diagnóstico oncológico", "biometric_template"]
    oc = OpenCorePreFilter(
        profile_terms=["diagnóstico oncológico"],
        recall_first_passthrough_on_profile=True,
    )
    pro = ProPreFilter(profile_terms=["diagnóstico oncológico"])
    assert oc.filter_candidates(rows) == rows
    assert pro.filter_candidates(rows) == rows
