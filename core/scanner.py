"""
Unified scanner that uses core.detector only (regex + ML + optional DL).
Interface: scan_column(label, sample, connector_data_type=...) and scan_file_content(content, path) returning
structured result for LocalDBManager.save_finding.

**Scan-path observability (#1411 / #1412):** paid-tier readiness is reported via
``core.pro_scan_path`` (CLI ``--prefilter-status``, ``detection_prefilter`` on
``/status``, ``scan_evidence``). Product direction is Rust **regex-stage parity**
(#1414 / ADR-0083), not a skip-before-ML prefilter.

**Postura de segurança / evidência:** metadados de amostragem, timeouts e rastro DBA para relatórios
ficam no ``scan_manifest`` (``report.scan_evidence``) e no ``audit_log`` da API quando aplicável —
não duplicar aqui para evitar acoplamento ao fluxo de detecção.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from core.detector import SensitivityDetector
from core.pro_scan_path import resolve_pro_scan_path


class DataScanner:
    """Uses SensitivityDetector for DB columns and file content; returns dicts for save_finding."""

    def __init__(
        self,
        regex_overrides_path: str | None = None,
        ml_patterns_path: str | None = None,
        ml_terms_inline: list | None = None,
        dl_patterns_path: str | None = None,
        dl_terms_inline: list | None = None,
        detection_config: dict | None = None,
        file_encoding: str = "utf-8",
        licensing_config: dict | None = None,
    ):
        self.detector = SensitivityDetector(
            regex_overrides_path=regex_overrides_path,
            ml_patterns_path=ml_patterns_path,
            ml_terms_inline=ml_terms_inline,
            dl_patterns_path=dl_patterns_path,
            dl_terms_inline=dl_terms_inline,
            detection_config=detection_config,
            file_encoding=file_encoding or "utf-8",
            licensing_config=licensing_config,
        )
        self._pending: dict[str, Any] | None = None
        self._pro_scanner, _pro_status = resolve_pro_scan_path(
            licensing_config,
            deep_scan_fn=self._pro_deep_scan,
            legacy_scan_fn=self._pro_deep_scan,
        )
        # #1414 — primary observability is rust regex stage (not ProScanner skip path).
        self.prefilter_status = (
            self.detector.rust_regex_stage_status.to_prefilter_dict()
        )

    def _pro_deep_scan(self, batch: list[str]) -> list[dict[str, Any]]:
        """Deep path for ProScanner: full detector on each surviving payload."""
        pending = self._pending
        if not pending:
            return []
        out: list[dict[str, Any]] = []
        for _item in batch:
            out.append(
                self._scan_column_direct(
                    pending["column_name"],
                    pending["sample_content"],
                    connector_data_type=pending.get("connector_data_type"),
                )
            )
        return out

    def _scan_column_direct(
        self,
        column_name: str,
        sample_content: str,
        *,
        connector_data_type: str | None = None,
    ) -> dict[str, Any]:
        level, pattern, norm, conf = self.detector.analyze(
            column_name,
            sample_content or "",
            connector_data_type=connector_data_type,
        )
        return {
            "sensitivity_level": level,
            "pattern_detected": pattern,
            "norm_tag": norm,
            "ml_confidence": conf,
        }

    @staticmethod
    def _low_result() -> dict[str, Any]:
        return {
            "sensitivity_level": "LOW",
            "pattern_detected": None,
            "norm_tag": None,
            "ml_confidence": 0,
        }

    def scan_column(
        self,
        column_name: str,
        sample_content: str,
        *,
        connector_data_type: str | None = None,
    ) -> dict[str, Any]:
        """
        Analyze a DB column (name + sample). Returns dict with sensitivity_level, pattern_detected, norm_tag, ml_confidence.
        Sample content is not stored. Optional ``connector_data_type`` (e.g. VARCHAR(11) from SQLAlchemy) feeds Plan §4 hints when enabled in config.
        """
        if self._pro_scanner is None:
            return self._scan_column_direct(
                column_name,
                sample_content,
                connector_data_type=connector_data_type,
            )

        payload = f"{column_name} {sample_content or ''}"
        self._pending = {
            "column_name": column_name,
            "sample_content": sample_content or "",
            "connector_data_type": connector_data_type,
        }
        try:
            out = self._pro_scanner.scan([payload])
            if not out:
                return self._low_result()
            if isinstance(out, list):
                return out[0]
            return out  # type: ignore[return-value]
        except Exception:  # noqa: BLE001 — fail-soft to core path
            return self._scan_column_direct(
                column_name,
                sample_content,
                connector_data_type=connector_data_type,
            )
        finally:
            self._pending = None

    def scan_file_content(
        self, content: str, file_path: str | Path
    ) -> dict[str, Any] | None:
        """
        Analyze file content (and path for context). Returns same shape as scan_column if sensitivity != LOW; else None.
        """
        path_str = str(file_path)
        name = Path(file_path).name if isinstance(file_path, (str, Path)) else path_str
        result = self.scan_column(name, content or "")
        if result["sensitivity_level"] == "LOW":
            return None
        return result

    # Backward compatibility: analyze_data used by old code
    def analyze_data(self, column_name: str, sample_content: str) -> tuple[str, str]:
        """Returns (sensitivity_level, pattern_detected) for callers that expect a tuple."""
        d = self.scan_column(column_name, sample_content)
        return d["sensitivity_level"], d["pattern_detected"]
