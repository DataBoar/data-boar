"""Demo workspace preparation for ``data-boar --demo`` (#1113, #834, #1190)."""

from __future__ import annotations

import atexit
import os
import secrets
import tempfile
from pathlib import Path
from typing import Any

from core.demo.synthetic_corpus import ALL_SCENARIOS, generate_corpus

_DEFAULT_SCENARIOS = "happy,unhappy,false_positive"
_DEMO_DIRNAME = "data_boar_demo"
_DEMO_API_KEY_BYTES = 32
_registered_cleanup: Path | None = None


def _default_demo_root() -> Path:
    return Path(tempfile.gettempdir()) / _DEMO_DIRNAME


def generate_demo_api_key() -> str:
    """Return a fresh per-run API key (32 random bytes as hex)."""
    return secrets.token_hex(_DEMO_API_KEY_BYTES)


def _write_demo_config(demo_dir: Path, port: int, *, api_key: str) -> Path:
    """
    Write demo.config.yaml.

    Provisions a loopback-only API key with ``audit_logs.read`` only (#1190).
    Does **not** grant ``admin`` and does **not** disable RBAC default-deny.
    """
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
            f"  api_key: {api_key}\n"
            "  rbac:\n"
            "    api_key_roles:\n"
            "      - audit_logs.read\n"
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


def print_demo_banner(port: int, demo_dir: Path, *, api_key: str) -> None:
    """Print demo startup banner including the per-run audit-log API key (#1190)."""
    print("")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  Data Boar — Demo (synthetic corpus, zero real data)     ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print(f"[demo] Workspace: {demo_dir}")
    print(f"[demo] Dashboard: http://127.0.0.1:{port}/pt-br/")
    print(f"[demo] Audit log API key (this run only): {api_key}")
    print(
        "[demo] Role: audit_logs.read only (not admin). "
        "Requests without this key still get HTTP 401 (RBAC default-deny)."
    )
    print(
        f'[demo] Example: curl -sS -H "X-API-Key: {api_key}" '
        f'"http://127.0.0.1:{port}/logs/<session_id>"'
    )
    print("[demo] Press Ctrl+C to stop (temp files removed on exit).")
    print("")


def prepare_demo_workspace(
    *,
    port: int = 8088,
    scenarios: str = _DEFAULT_SCENARIOS,
    demo_root: Path | None = None,
    register_cleanup: bool = True,
    api_key: str | None = None,
) -> tuple[Path, Path, dict[str, Any]]:
    """
    Generate synthetic corpus + minimal config under a temp directory.

    Returns ``(demo_dir, config_path, config_dict)`` where ``config_dict`` is
    ready to pass to ``load_config``-equivalent flows (after YAML load).

    Each run provisions ``api.api_key`` (32 random bytes as hex) and
    ``api.rbac.api_key_roles: [audit_logs.read]`` so ``GET /logs/{session_id}``
    is reachable with the key while unauthenticated calls stay 401 (#1190).
    """
    from config.loader import load_config

    demo_dir = (demo_root or _default_demo_root()).resolve()
    demo_dir.mkdir(parents=True, exist_ok=True)
    corpus_dir = demo_dir / "corpus"
    corpus_dir.mkdir(parents=True, exist_ok=True)

    selected = [s.strip() for s in scenarios.split(",") if s.strip()]
    generate_corpus(corpus_dir, selected or ALL_SCENARIOS[:3])

    key = api_key if api_key is not None else generate_demo_api_key()
    config_path = _write_demo_config(demo_dir, port, api_key=key)
    os.environ["CONFIG_PATH"] = str(config_path)
    config = load_config(str(config_path))

    if register_cleanup:
        register_demo_cleanup(demo_dir)

    return demo_dir, config_path, config
