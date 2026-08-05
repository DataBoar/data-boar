"""Fail-graceful host wiring for the Enterprise remediation hook (#606 / #1443).

Never raises into the scan worker: plugin absence, load failure, non-conformance,
or remediate() errors are logged and skipped (Safe-Hold of the scan target).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


def maybe_run_remediation_hook(
    config: dict[str, Any],
    session_id: str,
    db_manager: Any | None = None,
) -> None:
    """
    Opt-in post-scan remediation when ``remediation.enabled`` and Enterprise
    (or OPEN lab) tier grants ``remediation_plugin``.

    When ``db_manager`` is provided, writes
    ``{report.output_dir}/findings_{session_id}.jsonl`` from SQLite using the
    #649 remediation-target taxonomy, then calls the plugin. Fail-graceful:
    all plugin errors go to stderr; scan outcome is unchanged.
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

    if db_manager is None:
        if not findings_path.is_file():
            print(
                "[remediation] skipped — findings JSONL not written (no db_manager) "
                f"and missing: {findings_path}",
                file=sys.stderr,
            )
            return
    else:
        from core.remediation_manifest import write_findings_jsonl

        written = write_findings_jsonl(
            db_manager,
            session_id=session_id,
            path=findings_path,
            config=config if isinstance(config, dict) else None,
        )
        if written is None:
            print(
                "[remediation] skipped — could not write findings JSONL "
                "(unknown or empty session_id)",
                file=sys.stderr,
            )
            return

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
