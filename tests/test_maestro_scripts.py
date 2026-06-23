"""
CI guardrails for scripts/maestro (Maestro + handlers).

Parse-only PowerShell validation (same contract as tests/test_scripts.py) plus
static anti-regressions for known handler bugs (GitHub issues #329/#330 family).
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from tests.test_scripts import _parse_powershell_script, _project_root


def _find_pwsh() -> str | None:
    """Return the first available PowerShell executable, or None."""
    for pw in ("pwsh", "powershell"):
        if shutil.which(pw):
            return pw
    return None


def _maestro_ps1_paths(root: Path) -> list[Path]:
    base = root / "scripts" / "maestro"
    if not base.is_dir():
        return []
    return sorted(base.rglob("*.ps1"))


def test_all_maestro_powershell_scripts_parse(warm_pwsh) -> None:
    """Every tracked .ps1 under scripts/maestro/ parses under pwsh/PowerShell Parser.

    ``warm_pwsh`` (#860): session-scoped warm-up absorbs the pwsh cold-start
    once, so the per-file ParseFile timeout never flakes after a fresh boot.
    """
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
    for text, persona in (
        (mariadb, "target_mariadb"),
        (postgres, "target_postgres"),
        (mongo, "target_mongodb"),
    ):
        assert f"{persona}_sentinel.txt" in text, (
            f"DB handler must write {persona}_sentinel.txt (#953)"
        )
        assert "__SENTINEL__" in text or "SENTINEL=" in text


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
    assert "if ($IsWindows)" in text
    assert "bash -c" in text
    assert "PSObject.Properties['git_origin']" in text
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


def test_maestro_deep_rc_monitor_collect_wrapper_parse(warm_pwsh) -> None:
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
        assert "--bench-config $configArg" in body, (
            f"{name}: Deep smoke must pass --bench-config so lab-completao-host-smoke.sh parses argv"
        )


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


def test_build_container_artefact_has_container_engine_fallback_policy() -> None:
    """Build script should rebuild when docker/podman is up and fallback to tar when both are down."""
    root = _project_root()
    text = (root / "scripts" / "maestro" / "Build-ContainerArtefact.ps1").read_text(
        encoding="utf-8", errors="replace"
    )
    assert "Test-ContainerEngineReady" in text
    assert "Invoke-ContainerImageBuild" in text
    assert '"podman"' in text
    assert "DOCKER_BUILDKIT" in text
    assert "Container engine indisponivel" in text
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


def test_lab_completao_host_smoke_uses_main_py_not_data_boar_scan() -> None:
    """Baremetal RC must invoke python main.py --config (no fictional data-boar scan subcommand)."""
    root = _project_root()
    text = (root / "scripts" / "lab-completao-host-smoke.sh").read_text(
        encoding="utf-8", errors="replace"
    )
    # --no-sync keeps the boar_fast_filter wheel installed for the real scan (#951).
    assert "uv run --no-sync python main.py --config" in text
    assert "uv run data-boar scan" not in text
    assert "DONE_FAILED_BAREMETAL" in text
    assert "LC_BAREMETAL_SCAN_OK" in text
    assert "maturin develop --release" in text


def test_lab_completao_host_smoke_parses_bench_config_flag() -> None:
    """Maestro --bench-config must be a real flag (not positional $1) so Deep argv parses."""
    root = _project_root()
    text = (root / "scripts" / "lab-completao-host-smoke.sh").read_text(
        encoding="utf-8", errors="replace"
    )
    assert "    --bench-config)" in text
    assert 'CONFIG_RC="${LC_BENCH_CONFIG:-tests/config/benchmark-rc.yaml}"' in text


def test_labop_maestro_target_sudoers_example_lists_check_and_apply() -> None:
    """Narrow sudoers example covers Maestro --check and --apply for NFS and CIFS."""
    root = _project_root()
    path = root / "docs/private.example/homelab/labop-maestro-target-sudoers.example"
    assert path.is_file(), "missing labop-maestro-target-sudoers.example"
    text = path.read_text(encoding="utf-8", errors="replace")
    assert "LABOP_NFS_SERVER" in text
    assert "LABOP_SMB_SERVER" in text
    assert "--check" in text
    assert "--apply" in text
    assert "/usr/bin/bash" in text


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
    assert "Wait-BaremetalBenchSentinel.ps1" in text, (
        "maestro-benchmark-ab.ps1 must poll baremetal bench sentinel before Collect"
    )
    assert "Start-Sleep -Seconds $SleepBeforeCollect" in text, (
        "Sleep must remain as fallback when sentinel misses or is skipped"
    )


def test_lab_completao_host_smoke_writes_baremetal_scan_sentinel() -> None:
    """Baremetal bench runs must drop a Maestro-visible completion marker under LC_BENCH_ROOT."""
    root = _project_root()
    text = (root / "scripts" / "lab-completao-host-smoke.sh").read_text(
        encoding="utf-8", errors="replace"
    )
    assert ".baremetal_scan_complete" in text
    assert "LC_BENCH_ROOT" in text


def test_invoke_api_post_status_uses_numeric_status_not_locale_string() -> None:
    """Anti-regression #818: redirect detection must use numeric status code, not locale-dependent message text.

    PowerShell throws on 3xx when -MaximumRedirection 0; the exception message is
    locale-translated on non-English systems (e.g. pt_BR), so matching the word
    'redirect' in the message text is unreliable.  The fix reads
    $_.Exception.Response.StatusCode (an integer) instead.
    """
    root = _project_root()
    text = (root / "scripts" / "maestro" / "Handle-LicensingMatrix.ps1").read_text(
        encoding="utf-8", errors="replace"
    )
    assert "[Rr]edirect" not in text, (
        "Invoke-ApiPostStatus must not match the word 'redirect' in the exception message "
        "(locale-dependent); check numeric StatusCode instead"
    )
    assert ".StatusCode -ge 300" in text, (
        "Invoke-ApiPostStatus must check numeric 3xx lower bound (.StatusCode -ge 300)"
    )
    assert ".StatusCode -lt 400" in text, (
        "Invoke-ApiPostStatus must check numeric 3xx upper bound (.StatusCode -lt 400)"
    )


def test_stop_matrix_api_process_is_cross_platform() -> None:
    """Anti-regression #820: Stop-MatrixApiProcess must not use Windows-only taskkill
    or unconditional Get-NetTCPConnection; cross-platform kill and port poll required.
    """
    root = _project_root()
    text = (root / "scripts" / "maestro" / "Handle-LicensingMatrix.ps1").read_text(
        encoding="utf-8", errors="replace"
    )
    assert "& taskkill" not in text, (
        "Stop-MatrixApiProcess must not invoke taskkill (Windows-only); use proc.Kill or Stop-Process"
    )
    # Get-NetTCPConnection must be guarded by $IsWindows when present
    if "Get-NetTCPConnection" in text:
        assert "$IsWindows" in text, (
            "Get-NetTCPConnection is Windows-only and must be inside an 'if ($IsWindows)' block"
        )
    # Cross-platform port poll must use .NET IPGlobalProperties
    assert "GetActiveTcpListeners" in text, (
        "Port-free poll must use .NET GetActiveTcpListeners() which works cross-platform "
        "instead of Windows-only Get-NetTCPConnection"
    )
    # Cross-platform process kill must be present
    assert "proc.Kill" in text or "Stop-Process" in text, (
        "Stop-MatrixApiProcess must use proc.Kill($true) or Stop-Process for cross-platform kill"
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


def test_start_matrix_api_process_guards_window_style_linux() -> None:
    """Anti-regression #827: -WindowStyle Hidden must be guarded by $IsWindows.

    On Linux/macOS, Start-Process throws a ParameterBindingException for -WindowStyle
    Hidden — it does NOT silently ignore the parameter as an older comment claimed.
    The fix conditionally adds WindowStyle only on Windows via a splatted hashtable.
    """
    root = _project_root()
    text = (root / "scripts" / "maestro" / "Handle-LicensingMatrix.ps1").read_text(
        encoding="utf-8", errors="replace"
    )
    # -WindowStyle must either be absent or guarded by $IsWindows
    if "-WindowStyle" in text:
        assert "$IsWindows" in text, (
            "Start-MatrixApiProcess uses -WindowStyle Hidden without an $IsWindows guard; "
            "on Linux Start-Process throws ParameterBindingException, killing the first API spawn"
        )
    # The misleading 'silently ignores' comment must be corrected
    assert "silently ignores" not in text, (
        "Handle-LicensingMatrix.ps1 still carries the incorrect 'silently ignores' comment "
        "about -WindowStyle Hidden on Linux — the parameter THROWS, not ignores"
    )


def test_start_matrix_api_process_propagates_spawn_failure() -> None:
    """Anti-regression #827: Start-Process must be wrapped in try/catch to propagate exit != 0.

    Previously Start-Process exceptions were unhandled, causing the function to return null
    and the caller to silently continue (masking spawn failures as exit 0).
    """
    root = _project_root()
    text = (root / "scripts" / "maestro" / "Handle-LicensingMatrix.ps1").read_text(
        encoding="utf-8", errors="replace"
    )
    # Must have try/catch guarding Start-Process
    assert "try {" in text or "try{" in text, (
        "Start-MatrixApiProcess must wrap Start-Process in try/catch to propagate spawn failures"
    )
    assert "throw" in text, (
        "Start-MatrixApiProcess must re-throw or throw a descriptive error on spawn failure"
    )


# ---------------------------------------------------------------------------
# #830 / #831 — handler quote/escape safety + sentinel pattern
# ---------------------------------------------------------------------------

_SMOKE_HANDLER_PERSONAS = [
    "baremetal",
    "docker",
    "dockerswarm",
    "lxd",
    "microk8s",
    "podman",
    "target_cifs",
    "target_nfs",
    "target_sshfs",
]


def _handler_text(root: Path, persona: str) -> str:
    path = root / "scripts" / "maestro" / "handlers" / f"Handle-{persona}.ps1"
    return path.read_text(encoding="utf-8", errors="replace")


def test_smoke_handlers_use_base64_payload_for_tmux() -> None:
    """Anti-regression #830: handler payloads must be base64-encoded before tmux send-keys.

    Embedding raw shell commands in tmux send-keys single-quoted args fails when
    Node.path, BenchRunId, or Ref contain single quotes or shell metacharacters.
    The fix encodes the payload as base64 so the tmux arg is always safe ASCII.
    """
    root = _project_root()
    # Handlers that use tmux send-keys to inject a bash payload
    tmux_handlers = [
        "baremetal",
        "docker",
        "dockerswarm",
        "lxd",
        "microk8s",
        "podman",
        "target_cifs",
        "target_nfs",
        "target_sshfs",
    ]
    for persona in tmux_handlers:
        text = _handler_text(root, persona)
        assert "base64" in text.lower() or "Invoke-HandlerTmuxPayload" in text, (
            f"Handle-{persona}.ps1 must base64-encode the tmux payload (#830); "
            "raw single-quoted payloads break on paths or values with special chars"
        )
        assert "ToBase64String" in text or "payloadB64" in text, (
            f"Handle-{persona}.ps1 must use [Convert]::ToBase64String or equivalent (#830)"
        )


def test_smoke_handlers_have_ref_allowlist() -> None:
    """Anti-regression #830: handlers that accept -Ref must validate it against an allowlist.

    An unvalidated -Ref value could inject shell metacharacters into the payload.
    """
    root = _project_root()
    # All persona handlers accept -Ref; those that inject it into shell commands must validate
    inject_ref_handlers = [
        "baremetal",
        "docker",
        "dockerswarm",
        "lxd",
        "microk8s",
        "podman",
    ]
    for persona in inject_ref_handlers:
        text = _handler_text(root, persona)
        assert "safeRefPattern" in text or "allowlist" in text.lower(), (
            f"Handle-{persona}.ps1 must validate -Ref against an allowlist (#830); "
            "unvalidated Ref values can inject shell metacharacters into the payload"
        )


def test_smoke_handlers_write_sentinel_file() -> None:
    """Anti-regression #831: each smoke handler must write a sentinel file with the exit code.

    Without a sentinel, Maestro cannot machine-verify whether the smoke actually passed
    or failed (tmux inject exits 0 regardless of smoke outcome).
    """
    root = _project_root()
    for persona in _SMOKE_HANDLER_PERSONAS:
        text = _handler_text(root, persona)
        assert "_sentinel.txt" in text, (
            f"Handle-{persona}.ps1 must write a sentinel file (e.g. {persona}_sentinel.txt) "
            "with the smoke exit code for real pass/fail aggregation (#831)"
        )
        # Sentinel must capture the actual exit code
        assert "_rc" in text or "sentinel" in text.lower(), (
            f"Handle-{persona}.ps1 must record the smoke exit code in the sentinel (#831)"
        )


def test_wait_handler_sentinel_exists_and_parses(warm_pwsh) -> None:
    """Anti-regression #831: Wait-HandlerSentinel.ps1 must exist and parse cleanly."""
    root = _project_root()
    sentinel_script = root / "scripts" / "maestro" / "Wait-HandlerSentinel.ps1"
    assert sentinel_script.exists(), (
        "scripts/maestro/Wait-HandlerSentinel.ps1 must exist to generalize "
        "the baremetal sentinel pattern to all handler personas (#831)"
    )
    text = sentinel_script.read_text(encoding="utf-8", errors="replace")
    assert "Personas" in text, (
        "Wait-HandlerSentinel.ps1 must accept a -Personas parameter listing which "
        "handlers to wait for (#831)"
    )
    assert "_sentinel.txt" in text, (
        "Wait-HandlerSentinel.ps1 must poll for *_sentinel.txt files written by handlers (#831)"
    )


def test_build_container_artefact_degrades_without_hub() -> None:
    """#888: Build-ContainerArtefact must detect podman/docker, build+save a local
    tar (never assume Docker Hub), and emit an actionable error when no engine and
    no cached artefact are available.
    """
    root = _project_root()
    text = (root / "scripts" / "maestro" / "Build-ContainerArtefact.ps1").read_text(
        encoding="utf-8", errors="replace"
    )
    assert "podman" in text and "docker" in text, (
        "Build-ContainerArtefact must detect both podman and docker engines (#888)."
    )
    assert re.search(r"\$engineCmd\s+save|save\s+\$fullImage", text), (
        "Build-ContainerArtefact must `save` the image to a local tar (offline/-rc, "
        "no Docker Hub) (#888)."
    )
    # Never pull/push from a registry as the primary path (build is from the working tree).
    assert "docker pull" not in text and "podman pull" not in text, (
        "Build-ContainerArtefact must not assume a registry/Hub pull (#888)."
    )
    assert "exit 9" in text, (
        "Build-ContainerArtefact must exit with an actionable code when no engine and "
        "no local artefact exist (#888)."
    )


def test_sync_container_artefact_scp_fallback_is_actionable() -> None:
    """#888: Sync-ContainerArtefact must scp the local tar and `load` it remotely,
    and surface failures (missing artefact / scp failure) as actionable errors
    instead of silently swallowing them.
    """
    root = _project_root()
    text = (root / "scripts" / "maestro" / "Sync-ContainerArtefact.ps1").read_text(
        encoding="utf-8", errors="replace"
    )
    assert "scp " in text, (
        "Sync-ContainerArtefact must scp the artefact to the node (#888)."
    )
    assert re.search(r"(podman|docker)\s+load|load -i", text), (
        "Sync-ContainerArtefact must `load` the tar on the remote engine (#888)."
    )
    assert "Test-Path -LiteralPath $tarPath" in text, (
        "Sync-ContainerArtefact must guard against a missing local artefact before scp (#888)."
    )
    # The scp failure path must be an error (actionable), not a swallowed warning.
    assert re.search(r"scp exit \$LASTEXITCODE", text) and "Write-Error" in text, (
        "Sync-ContainerArtefact must report scp failure as an actionable error (#888)."
    )


def test_handle_web_reconciles_exit_code_after_recovery() -> None:
    """#889: Handle-web must reconcile the exit code with the real process health.

    Scenario "HTTP 200 but realFail": after recovery, an external 200 must NOT be
    reported as success when the recovered process never answered on the host's own
    loopback. The handler must exit non-zero (exit 7) so Maestro counts a realFail,
    and the final post-fallback failure path must also exit non-zero (no silent
    fall-through to exit 0).
    """
    root = _project_root()
    text = (root / "scripts" / "maestro" / "handlers" / "Handle-web.ps1").read_text(
        encoding="utf-8", errors="replace"
    )
    # Ground-truth signal is captured (remote loopback curl result).
    assert "$remoteCurlOk" in text, (
        "Handle-web must capture the remote loopback curl result to reconcile against "
        "the external HTTP probe (#889)."
    )
    # 200-but-realFail reconciliation: inside the success branch, a failed remote curl
    # forces exit 7 instead of returning success.
    assert re.search(r"if \(-not \$remoteCurlOk\)\s*\{[^}]*exit 7", text, re.DOTALL), (
        "Handle-web must exit 7 when HTTP 200 contradicts the remote loopback check (#889)."
    )
    # Real failures (fallback start failed; final health check failed) must exit 7,
    # not fall through to exit 0.
    assert text.count("exit 7") >= 3, (
        "Handle-web must propagate realFail via exit 7 on start failure, the 200-but-"
        "realFail reconciliation, and the final post-fallback failure (#889)."
    )
    # The final failure line must be an error + exit, not a swallowed warning.
    assert re.search(r"Health Check Web falhou[\s\S]{0,200}exit 7", text), (
        "Handle-web final failure after fallback must surface a non-zero exit (#889)."
    )


def _run_maestro_build_decision(pwsh: str, personas: list[str], tmp: Path) -> bool:
    """Run a real copy of Maestro.ps1 against a fixture inventory with stubbed child
    scripts; return True if Build-ContainerArtefact was invoked (marker written).

    Lab-free (#950): the Get-LabStatus stub returns SSH=DOWN, so the node dispatch
    loop is a no-op (no SSH, no sync, no handlers). Only the top-level container-build
    decision and the final report run. The Build stub writes a marker we can observe.
    """
    root = _project_root()
    maestro_src = root / "scripts" / "maestro" / "Maestro.ps1"
    mdir = tmp / "scripts" / "maestro"
    mdir.mkdir(parents=True)
    data_dir = tmp / "docs" / "private" / "homelab" / "data"
    data_dir.mkdir(parents=True)

    shutil.copyfile(maestro_src, mdir / "Maestro.ps1")
    marker = mdir / "build_invoked.marker"
    (mdir / "Build-ContainerArtefact.ps1").write_text(
        'Set-Content -LiteralPath "$PSScriptRoot/build_invoked.marker" -Value built\n',
        encoding="utf-8",
    )
    (mdir / "Get-LabStatus.ps1").write_text(
        "param($TargetHost, $TargetUser)\n"
        "[pscustomobject]@{ SSH = 'DOWN'; Tmux = ''; Node = $null; Host = $TargetHost }\n",
        encoding="utf-8",
    )
    inv = {"lab_members": [{"hostname": "h1", "user": "u", "personas": personas}]}
    (data_dir / "inventory.json").write_text(json.dumps(inv), encoding="utf-8")

    proc = subprocess.run(
        [pwsh, "-NoProfile", "-NonInteractive", "-File", str(mdir / "Maestro.ps1")],
        cwd=str(tmp),
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert proc.returncode == 0, (
        f"Maestro.ps1 exited {proc.returncode}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    )
    return marker.exists()


def test_maestro_skips_container_build_when_no_container_persona(warm_pwsh) -> None:
    """#950 guard: baremetal-only inventory -> Build-ContainerArtefact is NOT invoked.

    Behavioral, lab-free: runs a real copy of Maestro.ps1 with a fixture inventory
    that has no docker/podman/dockerswarm persona; the build must be skipped.
    """
    pwsh = _find_pwsh()
    if not pwsh:
        return
    with tempfile.TemporaryDirectory() as td:
        built = _run_maestro_build_decision(pwsh, ["baremetal"], Path(td))
    assert not built, (
        "Build-ContainerArtefact ran even though no node has a container persona (#950)"
    )


def test_maestro_runs_container_build_when_container_persona_present(warm_pwsh) -> None:
    """#950 guard: a node with a container persona -> Build-ContainerArtefact still runs.

    Behavioral, lab-free: same harness as the skip case but with a docker persona;
    the build must be invoked.
    """
    pwsh = _find_pwsh()
    if not pwsh:
        return
    with tempfile.TemporaryDirectory() as td:
        built = _run_maestro_build_decision(pwsh, ["baremetal", "docker"], Path(td))
    assert built, (
        "Build-ContainerArtefact did NOT run even though a node has a docker persona (#950)"
    )


# ---------------------------------------------------------------------------
# P0 bundle #955/#953/#956/#949/#954 — sentinel/collect/tmux/priv regressions
# ---------------------------------------------------------------------------

_TMUX_SMOKE_HANDLERS = [
    "Handle-baremetal.ps1",
    "Handle-docker.ps1",
    "Handle-podman.ps1",
    "Handle-dockerswarm.ps1",
    "Handle-lxd.ps1",
    "Handle-microk8s.ps1",
    "Handle-target_nfs.ps1",
    "Handle-target_cifs.ps1",
    "Handle-target_sshfs.ps1",
]


def test_handlers_no_shared_completao_cc_clobber() -> None:
    """#955: multi-persona nodes must not C-c the shared 'completao' session."""
    root = _project_root()
    hits: list[str] = []
    for name in _TMUX_SMOKE_HANDLERS:
        text = (root / "scripts" / "maestro" / "handlers" / name).read_text(
            encoding="utf-8", errors="replace"
        )
        if "send-keys -t completao C-c" in text:
            hits.append(name)
    assert not hits, f"Remove shared-session C-c clobber in: {', '.join(hits)}"


def test_handlers_use_per_persona_tmux_helper() -> None:
    """#955: handlers dot-source Lab-MaestroCommon and inject via Invoke-HandlerTmuxPayload."""
    root = _project_root()
    for name in _TMUX_SMOKE_HANDLERS:
        text = (root / "scripts" / "maestro" / "handlers" / name).read_text(
            encoding="utf-8", errors="replace"
        )
        assert "Lab-MaestroCommon.ps1" in text, (
            f"{name} must dot-source Lab-MaestroCommon.ps1"
        )
        assert "Invoke-HandlerTmuxPayload" in text, (
            f"{name} must use Invoke-HandlerTmuxPayload (#955)"
        )


def test_target_nfs_cifs_use_priv_env_bash_ensure() -> None:
    """#954: ensure runs as `$PRIV env ... bash` (doas strips caller env without env prefix)."""
    root = _project_root()
    for name in ("Handle-target_nfs.ps1", "Handle-target_cifs.ps1"):
        text = (root / "scripts" / "maestro" / "handlers" / name).read_text(
            encoding="utf-8", errors="replace"
        )
        assert "Build-EnsureRemoteCommand" in text
        assert "command -v doas" in (
            root / "scripts" / "maestro" / "Lab-MaestroCommon.ps1"
        ).read_text(encoding="utf-8", errors="replace")
        assert "`$PRIV $envPrefix bash" in (
            root / "scripts" / "maestro" / "Lab-MaestroCommon.ps1"
        ).read_text(encoding="utf-8", errors="replace")


def test_target_nfs_deep_apply_fail_is_real_fail() -> None:
    """#954/#949 bundle: Deep ensure --apply failure must exit non-zero and write sentinel 1."""
    root = _project_root()
    text = (
        root / "scripts" / "maestro" / "handlers" / "Handle-target_nfs.ps1"
    ).read_text(encoding="utf-8", errors="replace")
    assert "elseif ($Deep)" in text
    assert "[REAL FAIL] NFS ensure --apply" in text
    assert "Write-RemoteSentinel" in text
    assert "exit 1" in text


def test_collect_artifacts_uses_repo_log_path() -> None:
    """#956/#968: post-flight collect pulls from <repo>/log/; Join-Path; REAL FAIL if empty."""
    root = _project_root()
    text = (root / "scripts" / "maestro" / "Collect-Artifacts.ps1").read_text(
        encoding="utf-8", errors="replace"
    )
    assert "/log/*.log" in text
    assert "audit_trail" in text
    assert "~/log/*.log" in text  # legacy fallback only
    assert "Join-Path" in text
    assert "[REAL FAIL] Collect" in text
    assert "Get-CollectArtifactCount" in text
    assert "${localDestDir}/" in text
    assert "$localDestDir\\" not in text


def test_sync_working_tree_tar_fallback_on_rsync_failure() -> None:
    """#969: rsync failure triggers tar|ssh fallback with same exclude set."""
    root = _project_root()
    text = (root / "scripts" / "maestro" / "Sync-WorkingTree.ps1").read_text(
        encoding="utf-8", errors="replace"
    )
    assert "Invoke-SyncTarSshFallback" in text
    assert "Sync-Fallback #969" in text
    assert "tar -czf -" in text
    assert "tar -xzf -" in text
    assert "--exclude='docs/private'" in text


def test_maestro_canonical_guard_fail_closed() -> None:
    """#948: canonical/maestro nodes skip WorkingTree overwrite; ephemeral under /tmp/databoar_bench."""
    root = _project_root()
    guard = (root / "scripts" / "maestro" / "Maestro-CanonicalGuard.ps1").read_text(
        encoding="utf-8", errors="replace"
    )
    sync = (root / "scripts" / "maestro" / "Sync-WorkingTree.ps1").read_text(
        encoding="utf-8", errors="replace"
    )
    ensure = (root / "scripts" / "lab-op-git-ensure-ref.ps1").read_text(
        encoding="utf-8", errors="replace"
    )
    assert "Test-MaestroInventoryNodeProtected" in guard
    assert "Test-ManifestRepoPathProtected" in guard
    assert "Get-MaestroEphemeralRepoPath" in guard
    assert "/tmp/databoar_bench/" in guard
    assert "Maestro-CanonicalGuard.ps1" in sync
    assert "[GUARD #948]" in sync
    assert "Maestro-CanonicalGuard.ps1" in ensure
    assert "[GUARD #948] Skip git Reset" in ensure


def test_maestro_calls_wait_handler_sentinel_for_real_results() -> None:
    """#949: Maestro polls Wait-HandlerSentinel after dispatch (real pass/fail, not inject-only)."""
    root = _project_root()
    text = (root / "scripts" / "maestro" / "Maestro.ps1").read_text(
        encoding="utf-8", errors="replace"
    )
    assert "Wait-HandlerSentinel.ps1" in text
    assert "dispatchedSentinelPersonas" in text
    assert "-OnlyHosts" in text
    assert "Wait-HandlerSentinel reportou falha" in text


def test_wait_handler_sentinel_supports_only_hosts_filter() -> None:
    """#949: limit polling to hosts that ran this Maestro turn."""
    root = _project_root()
    text = (root / "scripts" / "maestro" / "Wait-HandlerSentinel.ps1").read_text(
        encoding="utf-8", errors="replace"
    )
    assert "OnlyHosts" in text
    assert "-notcontains $node.hostname" in text


def test_smoke_handlers_clear_sentinel_before_run() -> None:
    """Bundle guard: stale sentinel from prior run must be removed (rm -f) before smoke."""
    root = _project_root()
    for persona in ("baremetal", "docker", "podman", "dockerswarm", "lxd", "microk8s"):
        text = _handler_text(root, persona)
        assert "rm -f $sentinelFile" in text or "rm -f $sentinelFile ;" in text, (
            f"Handle-{persona}.ps1 must rm -f sentinel before run"
        )
