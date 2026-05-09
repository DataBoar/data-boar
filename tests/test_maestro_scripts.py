"""
CI guardrails for scripts/maestro (Maestro + handlers).

Parse-only PowerShell validation (same contract as tests/test_scripts.py) plus
static anti-regressions for known handler bugs (GitHub issues #329/#330 family).
"""

from __future__ import annotations

import re
from pathlib import Path

from tests.test_scripts import _parse_powershell_script, _project_root


def _maestro_ps1_paths(root: Path) -> list[Path]:
    base = root / "scripts" / "maestro"
    if not base.is_dir():
        return []
    return sorted(base.rglob("*.ps1"))


def test_all_maestro_powershell_scripts_parse() -> None:
    """Every tracked .ps1 under scripts/maestro/ parses under pwsh/PowerShell Parser."""
    root = _project_root()
    failures: list[str] = []
    for script in _maestro_ps1_paths(root):
        if not _parse_powershell_script(script, root):
            failures.append(str(script.relative_to(root)))
    assert not failures, (
        "Maestro PowerShell parse failed (install pwsh on CI if empty list is wrong): "
        + ", ".join(failures)
    )


def test_maestro_embeds_private_inventory_path() -> None:
    """Maestro.ps1 keeps the private inventory contract (no PII in path text)."""
    root = _project_root()
    text = (root / "scripts" / "maestro" / "Maestro.ps1").read_text(
        encoding="utf-8", errors="replace"
    )
    assert "docs/private/homelab/data/inventory.json" in text
    assert "Handle-$persona.ps1" in text or "Handle-$persona" in text


def test_benchmark_rc_config_exists_for_deep_mode() -> None:
    """Deep-mode handlers reference a tracked benchmark YAML."""
    root = _project_root()
    cfg = root / "tests" / "config" / "benchmark-rc.yaml"
    assert cfg.is_file(), "tests/config/benchmark-rc.yaml required for Maestro -Deep"


def test_handle_web_health_contract() -> None:
    """Anti-regression: web persona targets API port 8088 and GET /health (not legacy 8080 /api/status)."""
    root = _project_root()
    text = (root / "scripts" / "maestro" / "handlers" / "Handle-web.ps1").read_text(
        encoding="utf-8", errors="replace"
    )
    assert "$webPort = 8088" in text
    assert "/health" in text
    assert "/api/status" not in text


def test_container_handlers_define_modo_texto_for_payload() -> None:
    """Anti-regression #329: docker/podman/swarm must define $modoTexto before $payload uses it."""
    root = _project_root()
    for name in ("Handle-docker.ps1", "Handle-podman.ps1", "Handle-dockerswarm.ps1"):
        path = root / "scripts" / "maestro" / "handlers" / name
        body = path.read_text(encoding="utf-8", errors="replace")
        assert "$modoTexto" in body, (
            f"{name} must define $modoTexto for Deep smoke labelling"
        )
        assert "($modoTexto)" in body, (
            f"{name} should interpolate $modoTexto inside the smoke payload string"
        )
        cfg_idx = body.find("$configArg")
        modo_idx = body.find("$modoTexto")
        pay_idx = body.find("$payload")
        assert 0 <= cfg_idx < modo_idx < pay_idx, (
            f"{name}: expected order $configArg -> $modoTexto -> $payload"
        )


def test_handle_microk8s_fallback_tmux_sends_expanded_payload() -> None:
    """Anti-regression: fallback branch must not escape $payload into a literal for tmux."""
    root = _project_root()
    text = (
        root / "scripts" / "maestro" / "handlers" / "Handle-microk8s.ps1"
    ).read_text(encoding="utf-8", errors="replace")
    assert "`$payload" not in text, (
        "Do not escape $payload in tmux send-keys; remote shell must see the real command"
    )


def test_maestro_deep_rc_monitor_collect_wrapper_parse() -> None:
    """Token-aware lab wrapper (Deep + monitor + Collect) parses under pwsh."""
    root = _project_root()
    script = root / "scripts" / "maestro-deep-rc-monitor-collect.ps1"
    assert script.is_file()
    assert _parse_powershell_script(script, root), (
        "maestro-deep-rc-monitor-collect.ps1 parse failed (install pwsh on CI if unexpected)"
    )


def test_maestro_no_retired_workstation_codename_token() -> None:
    """Keep scripts/maestro aligned with tests/test_public_tree_no_l14_codename.py word rule."""
    root = _project_root()
    word = "".join((chr(76), chr(49), chr(52)))
    pattern = re.compile(rf"\b{re.escape(word)}\b")
    hits: list[str] = []
    for script in _maestro_ps1_paths(root):
        t = script.read_text(encoding="utf-8", errors="replace")
        if pattern.search(t):
            hits.append(str(script.relative_to(root)))
    assert not hits, (
        f"Remove retired workstation codename token from: {', '.join(hits)}"
    )
