"""``prefilter_status`` must not imply ``DATA_BOAR_PREFILTER`` disables regex stage (#2246)."""

from __future__ import annotations

from core.detector import SensitivityDetector


def test_prefilter_status_documents_pro_scan_env_scope_only() -> None:
    status = SensitivityDetector().rust_regex_stage_status.to_prefilter_dict()
    assert status.get("pro_prefilter_env_var") == "DATA_BOAR_PREFILTER"
    assert status.get("pro_prefilter_env_controls") == "pro_scan_path_only"
