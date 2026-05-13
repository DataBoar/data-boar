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


def test_target_cifs_handler_exists() -> None:
    """Inventory persona target_cifs must have a dedicated handler."""
    root = _project_root()
    handler = root / "scripts" / "maestro" / "handlers" / "Handle-target_cifs.ps1"
    assert handler.is_file(), "Missing handler for persona target_cifs"


def test_db_target_handlers_exist() -> None:
    """Inventory DB personas must have dedicated handlers."""
    root = _project_root()
    for name in (
        "Handle-target_mariadb.ps1",
        "Handle-target_postgres.ps1",
        "Handle-target_mongodb.ps1",
    ):
        handler = root / "scripts" / "maestro" / "handlers" / name
        assert handler.is_file(), f"Missing handler for persona {name}"


def test_db_target_handlers_use_compose_contract() -> None:
    """DB target handlers should use compose services from deploy/lab-smoke-stack."""
    root = _project_root()
    mariadb = (
        root / "scripts" / "maestro" / "handlers" / "Handle-target_mariadb.ps1"
    ).read_text(encoding="utf-8", errors="replace")
    postgres = (
        root / "scripts" / "maestro" / "handlers" / "Handle-target_postgres.ps1"
    ).read_text(encoding="utf-8", errors="replace")
    mongo = (
        root / "scripts" / "maestro" / "handlers" / "Handle-target_mongodb.ps1"
    ).read_text(encoding="utf-8", errors="replace")
    assert "lab-mariadb" in mariadb
    assert "lab-postgres" in postgres
    assert "docker-compose.mongo.yml" in mongo
    assert "TARGET_MARIADB_READY" in mariadb
    assert "TARGET_POSTGRES_READY" in postgres
    assert "TARGET_MONGODB_READY" in mongo
    assert "podman info" in mariadb
    assert "docker info" in mariadb
    assert "podman run -d --name lab-mariadb" in mariadb
    assert "docker.io/library/mariadb:11" in mariadb
    assert "pick_port()" in mariadb
    assert "LAB_MY_PORT_CANDIDATES" in mariadb
    assert "TARGET_MARIADB_READY port=" in mariadb
    assert "LAB_TARGET_DB_AUTOCLEAN" in mariadb
    assert "podman info" in postgres
    assert "docker info" in postgres
    assert "podman run -d --name lab-postgres" in postgres
    assert "docker.io/library/postgres:16-alpine" in postgres
    assert "pick_port()" in postgres
    assert "LAB_PG_PORT_CANDIDATES" in postgres
    assert "TARGET_POSTGRES_READY port=" in postgres
    assert "LAB_TARGET_DB_AUTOCLEAN" in postgres
    assert "podman info" in mongo
    assert "docker info" in mongo
    assert "podman run -d --name lab-mongodb" in mongo
    assert "docker.io/library/mongo:7" in mongo
    assert "pick_port()" in mongo
    assert "LAB_MONGO_PORT_CANDIDATES" in mongo
    assert "TARGET_MONGODB_READY port=" in mongo
    assert "LAB_TARGET_DB_AUTOCLEAN" in mongo


def test_handle_web_health_contract() -> None:
    """Anti-regression: web persona targets API port 8088 and GET /health (not legacy 8080 /api/status)."""
    root = _project_root()
    text = (root / "scripts" / "maestro" / "handlers" / "Handle-web.ps1").read_text(
        encoding="utf-8", errors="replace"
    )
    assert '-Name "web_port" -DefaultValue 8088' in text
    assert "/health" in text
    assert "/api/status" not in text
    assert "web_allow_insecure_tls" in text
    assert "web_check_retries" in text
    assert "Get-NodePropOrDefault" in text
    assert "PSObject.Properties" in text
    assert "--allow-insecure-http" in text
    assert "--host 0.0.0.0" in text
    assert "CFG_ARG" in text
    assert "--config deploy/config.example.yaml" in text
    assert "~/.labop-web-port" in text
    assert "curl -fsS --max-time 5" in text
    assert "__NODE_PATH__" in text
    assert '.Replace("__NODE_PATH__"' in text


def test_maestro_dispatch_orders_container_before_web() -> None:
    """Container personas must execute before web checks for readiness coherence."""
    root = _project_root()
    text = (root / "scripts" / "maestro" / "Maestro.ps1").read_text(
        encoding="utf-8", errors="replace"
    )
    assert "$orderedPersonas" in text
    assert '"docker" { 0; break }' in text
    assert '"web" { 2; break }' in text
    assert "Handler ausente para persona" in text


def test_sync_working_tree_uses_explicit_sync_result() -> None:
    """Sync flow should rely on syncOk, avoiding false success from unrelated ssh exit codes."""
    root = _project_root()
    text = (root / "scripts" / "maestro" / "Sync-WorkingTree.ps1").read_text(
        encoding="utf-8", errors="replace"
    )
    assert "$syncOk = $false" in text
    assert "if ($syncOk)" in text
    assert "if ($LASTEXITCODE -eq 0) {" in text
    assert "Hash check OK" in text
    assert "return [bool]$syncOk" in text
    assert "--exclude='data-boar-*.tar'" in text
    assert "ConnectTimeout=15" in text
    assert "if ($syncOk) {" in text
    assert "tmux new-session -d -s completao" in text
    assert "> $null 2>&1" in text


def test_gitignore_ignores_maestro_ephemeral_tar_bundles() -> None:
    """Pre-release/beta Maestro tarballs at repo root stay local-only."""
    root = _project_root()
    gi = (root / ".gitignore").read_text(encoding="utf-8", errors="replace")
    assert "/data-boar-*-beta.tar" in gi
    assert "/data-boar-*-rc.tar" in gi


def test_maestro_skips_handlers_when_sync_fails() -> None:
    """Maestro must not run handlers after a failed mandatory sync."""
    root = _project_root()
    text = (root / "scripts" / "maestro" / "Maestro.ps1").read_text(
        encoding="utf-8", errors="replace"
    )
    assert '$syncOk = [bool](& "$PSScriptRoot/Sync-WorkingTree.ps1"' in text
    assert "Sync obrigatorio falhou" in text
    assert "continue" in text


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


def test_maestro_collect_exit_semantics_warn_without_hard_fail() -> None:
    """Collect mode tracks warnings but keeps hard-fail exit reserved for critical cases."""
    root = _project_root()
    text = (root / "scripts" / "maestro" / "Maestro.ps1").read_text(
        encoding="utf-8", errors="replace"
    )
    assert "$warningCount = 0" in text
    assert "Coleta ignorada" in text
    assert "Nenhum host com SSH UP no inventario para coletar artefatos." in text
    assert "warnings de coleta" in text
    assert "exit 6" in text
    assert "exit 0" in text


def test_maestro_benchmark_context_is_opt_in_and_forwarded() -> None:
    """Maestro exposes benchmark context flags and forwards them to handlers."""
    root = _project_root()
    text = (root / "scripts" / "maestro" / "Maestro.ps1").read_text(
        encoding="utf-8", errors="replace"
    )
    assert "[string]$BenchTrack" in text
    assert "[string]$BenchRunId" in text
    assert "[switch]$BenchCompare" in text
    assert "[int]$BenchWebPort" in text
    assert "[string]$BenchHealthUrl" in text
    assert "BenchTrack = $BenchTrack" in text
    assert "BenchRunId = $BenchRunId" in text
    assert "BenchCompare = $BenchCompare" in text
    assert "BenchWebPort = $BenchWebPort" in text
    assert "BenchHealthUrl = $BenchHealthUrl" in text


def test_container_handlers_forward_benchmark_flags_to_host_smoke() -> None:
    """Container-oriented handlers pass bench track/run id and compare flags to smoke script."""
    root = _project_root()
    for name in (
        "Handle-baremetal.ps1",
        "Handle-docker.ps1",
        "Handle-podman.ps1",
        "Handle-dockerswarm.ps1",
        "Handle-lxd.ps1",
        "Handle-microk8s.ps1",
    ):
        body = (root / "scripts" / "maestro" / "handlers" / name).read_text(
            encoding="utf-8", errors="replace"
        )
        assert "[string]$BenchTrack" in body, f"{name}: missing BenchTrack param"
        assert "[string]$BenchRunId" in body, f"{name}: missing BenchRunId param"
        assert "LAB_COMPLETAO_BENCH_COMPARE=1" in body, (
            f"{name}: should export compare flag env when requested"
        )
        assert "--bench-track $BenchTrack" in body
        assert "--bench-run-id $BenchRunId" in body


def test_wrapper_has_optional_web_readiness_gate() -> None:
    """Wrapper supports skip/warn/fail web readiness before long monitor loops."""
    root = _project_root()
    text = (root / "scripts" / "maestro-deep-rc-monitor-collect.ps1").read_text(
        encoding="utf-8", errors="replace"
    )
    assert "$HealthUrl" in text
    assert "WebReadinessMode" in text
    assert 'ValidateSet("skip", "warn", "fail")' in text
    assert "Test-WebReadiness" in text
    assert "Web readiness failed" in text


def test_build_container_artefact_has_docker_fallback_policy() -> None:
    """Build script should rebuild when Docker is up and fallback to tar when Docker is down."""
    root = _project_root()
    text = (root / "scripts" / "maestro" / "Build-ContainerArtefact.ps1").read_text(
        encoding="utf-8", errors="replace"
    )
    assert "Test-DockerEngineReady" in text
    assert "Docker indisponivel e sem artefato local" in text
    assert "rebuild" in text.lower() or "Rebuild" in text
    assert "lessons learned" in text


def test_wrapper_docker_precheck_accepts_tar_fallback() -> None:
    """Wrapper precheck should continue when Docker is down if tar fallback exists."""
    root = _project_root()
    text = (root / "scripts" / "maestro-deep-rc-monitor-collect.ps1").read_text(
        encoding="utf-8", errors="replace"
    )
    assert "Get-VersionTagFromPyproject" in text
    assert "fallback via" in text
    assert "fallback ausente" in text


def test_container_handlers_enable_lab_stack_up_in_deep_mode() -> None:
    """Deep container personas pass --lab-stack-up into host smoke payload."""
    root = _project_root()
    for name in ("Handle-docker.ps1", "Handle-podman.ps1", "Handle-dockerswarm.ps1"):
        body = (root / "scripts" / "maestro" / "handlers" / name).read_text(
            encoding="utf-8", errors="replace"
        )
        assert "$stackArg" in body, f"{name} should define $stackArg"
        assert "--lab-stack-up" in body, (
            f"{name} should inject --lab-stack-up in Deep mode payload"
        )
        assert "$smokeArgs" in body
        assert "$smokeArgText" in body
        assert "lab-completao-host-smoke.sh $smokeArgText" in body


def test_maestro_benchmark_ab_has_sleep_before_collect() -> None:
    """Bug 3 regression: maestro-benchmark-ab.ps1 must wait for async smoke before Collect."""
    root = _project_root()
    text = (root / "scripts" / "maestro-benchmark-ab.ps1").read_text(
        encoding="utf-8", errors="replace"
    )
    assert "SleepBeforeCollect" in text, (
        "maestro-benchmark-ab.ps1 must have -SleepBeforeCollect to prevent race between "
        "async tmux smoke and -Collect SCP phase"
    )
    assert "Start-Sleep -Seconds $SleepBeforeCollect" in text, (
        "Sleep must be applied before Collect phase"
    )


def test_maestro_no_retired_workstation_codename_token() -> None:
    """Maestro *.ps1 must not embed the retired workstation codename token (guard: test_public_tree_no_*codename*)."""
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
