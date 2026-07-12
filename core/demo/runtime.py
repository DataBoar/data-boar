"""Demo workspace preparation for ``data-boar --demo`` (#1113, #834)."""

from __future__ import annotations

import atexit
import os
import tempfile
from pathlib import Path
from typing import Any

from core.demo.synthetic_corpus import ALL_SCENARIOS, generate_corpus

_DEFAULT_SCENARIOS = "happy,unhappy,false_positive"
_DEMO_DIRNAME = "data_boar_demo"
_registered_cleanup: Path | None = None


def _default_demo_root() -> Path:
    return Path(tempfile.gettempdir()) / _DEMO_DIRNAME


def _write_demo_config(demo_dir: Path, port: int) -> Path:
    corpus = demo_dir / "corpus"
    reports = demo_dir / "reports"
    audit_logs = demo_dir / "audit_logs"
    reports.mkdir(parents=True, exist_ok=True)
    audit_logs.mkdir(parents=True, exist_ok=True)
    config_path = demo_dir / "demo.config.yaml"
    config_path.write_text(
        (
            "targets:\n"
            "  - name: demo-corpus\n"
            "    type: filesystem\n"
            f"    path: {corpus}\n"
            "    recursive: true\n"
            "\n"
            "report:\n"
            f"  output_dir: {reports}\n"
            "\n"
            f"sqlite_path: {demo_dir / 'audit_results.db'}\n"
            "\n"
            "api:\n"
            f"  port: {port}\n"
            "  host: 127.0.0.1\n"
            "  allow_insecure_http: true\n"
            "  audit_logs:\n"
            "    enabled: true\n"
            f"    directory: {audit_logs}\n"
        ),
        encoding="utf-8",
    )
    return config_path


def _cleanup_demo_dir(demo_dir: Path) -> None:
    import shutil

    if demo_dir.exists():
        shutil.rmtree(demo_dir, ignore_errors=True)


def register_demo_cleanup(demo_dir: Path) -> None:
    """Register atexit cleanup for a single-process ``--demo`` run."""
    global _registered_cleanup
    if _registered_cleanup is not None:
        return
    _registered_cleanup = demo_dir

    def _on_exit() -> None:
        _cleanup_demo_dir(demo_dir)

    atexit.register(_on_exit)


def print_demo_banner(port: int, demo_dir: Path) -> None:
    print("")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  Data Boar — Demo (synthetic corpus, zero real data)     ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print(f"[demo] Workspace: {demo_dir}")
    print(f"[demo] Dashboard: http://127.0.0.1:{port}/pt-br/")
    print("[demo] Press Ctrl+C to stop (temp files removed on exit).")
    print("")


def prepare_demo_workspace(
    *,
    port: int = 8088,
    scenarios: str = _DEFAULT_SCENARIOS,
    demo_root: Path | None = None,
    register_cleanup: bool = True,
) -> tuple[Path, Path, dict[str, Any]]:
    """
    Generate synthetic corpus + minimal config under a temp directory.

    Returns ``(demo_dir, config_path, config_dict)`` where ``config_dict`` is
    ready to pass to ``load_config``-equivalent flows (after YAML load).
    """
    from config.loader import load_config

    demo_dir = (demo_root or _default_demo_root()).resolve()
    demo_dir.mkdir(parents=True, exist_ok=True)
    corpus_dir = demo_dir / "corpus"
    corpus_dir.mkdir(parents=True, exist_ok=True)

    selected = [s.strip() for s in scenarios.split(",") if s.strip()]
    generate_corpus(corpus_dir, selected or ALL_SCENARIOS[:3])

    config_path = _write_demo_config(demo_dir, port)
    os.environ["CONFIG_PATH"] = str(config_path)
    config = load_config(str(config_path))

    if register_cleanup:
        register_demo_cleanup(demo_dir)

    return demo_dir, config_path, config
