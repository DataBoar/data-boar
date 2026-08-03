"""Fail-graceful host wiring for the Enterprise remediation hook (#606).

Never raises into the scan worker: plugin absence, load failure, non-conformance,
or remediate() errors are logged and skipped (Safe-Hold of the scan target).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


def maybe_run_remediation_hook(config: dict[str, Any], session_id: str) -> None:
    """
    Opt-in post-scan remediation when ``remediation.enabled`` and Enterprise
    (or OPEN lab) tier grants ``remediation_plugin``.

    Fail-graceful: all plugin errors go to stderr; scan outcome is unchanged.
    """
    remediation_cfg = config.get("remediation") if isinstance(config, dict) else None
    if not isinstance(remediation_cfg, dict) or not remediation_cfg.get("enabled"):
        return

    from core.licensing.runtime_feature_tier import get_runtime_tier_for_features
    from core.licensing.tier_features import is_feature_available
    from core.plugins import PluginError, load_remediation_plugin

    tier = get_runtime_tier_for_features(config)
    if not is_feature_available("remediation_plugin", tier):
        print(
            "[remediation] skipped — remediation_plugin requires Enterprise tier. "
            "Set licensing.effective_tier: enterprise in config.",
            file=sys.stderr,
        )
        return

    plugin_path = remediation_cfg.get("plugin")
    if not plugin_path or not isinstance(plugin_path, str):
        print(
            "[remediation] plugin error: remediation.enabled but plugin is null/empty",
            file=sys.stderr,
        )
        return

    report_cfg = config.get("report") if isinstance(config.get("report"), dict) else {}
    output_dir = Path(str(report_cfg.get("output_dir") or "."))
    findings_path = output_dir / f"findings_{session_id}.jsonl"

    try:
        plugin = load_remediation_plugin(plugin_path)
        report = plugin.remediate(findings_path, remediation_cfg.get("config") or {})
        print(f"Remediation complete: {report}")
        if remediation_cfg.get("verify_after"):
            print("[remediation] post-remediation verification pending (see #653)")
    except PluginError as exc:
        print(f"[remediation] plugin error: {exc}", file=sys.stderr)
    except Exception as exc:  # noqa: BLE001 — Safe-Hold: never crash the scan
        print(f"[remediation] plugin error: {exc}", file=sys.stderr)
