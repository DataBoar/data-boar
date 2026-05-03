"""
Tests for shell and PowerShell scripts: syntax validity and safe dry-run behaviour.

SonarQube-style checks: scripts use quoted variables, explicit exit codes, and no
obvious injection; these tests ensure they parse and (where possible) run a no-op path.
"""

import py_compile
import re
import subprocess
import sys
from pathlib import Path


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


# --- Bash: prep_audit.sh syntax (bash -n) ---


def test_prep_audit_sh_syntax():
    """prep_audit.sh has valid bash syntax (bash -n). Skipped on Windows (path handling)."""
    if sys.platform == "win32":
        return  # bash -n with Windows path is unreliable (e.g. Git Bash path quirks)
    root = _project_root()
    script = root / "prep_audit.sh"
    if not script.exists():
        return  # skip if removed
    try:
        proc = subprocess.run(
            ["bash", "-n", str(script)],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=5,
        )
    except FileNotFoundError:
        return
    assert proc.returncode == 0, f"bash -n failed: {proc.stderr or proc.stdout}"


def test_prep_audit_sh_has_shebang_and_exit_code():
    """prep_audit.sh has shebang and uses explicit exit 1 when not root (Sonar best practice)."""
    root = _project_root()
    script = root / "prep_audit.sh"
    if not script.exists():
        return
    text = script.read_text(encoding="utf-8", errors="replace")
    assert text.startswith("#!/bin/bash"), "Script should have bash shebang"
    assert "exit 1" in text, (
        "Script should use explicit exit code (e.g. exit 1 when not root)"
    )


# --- PowerShell: commit-or-pr.ps1 syntax (Parser::ParseFile) ---


def test_commit_or_pr_ps1_syntax():
    """scripts/commit-or-pr.ps1 has valid PowerShell syntax (parse-only, no execution)."""
    root = _project_root()
    script = root / "scripts" / "commit-or-pr.ps1"
    if not script.exists():
        return
    # Parse-only: avoids running git or any side effects; works on all platforms
    parse_script = (
        "$path = [System.IO.Path]::GetFullPath((Join-Path (Get-Location) 'scripts/commit-or-pr.ps1')); "
        "$errors = $null; "
        "$null = [System.Management.Automation.Language.Parser]::ParseFile($path, [ref]$null, [ref]$errors); "
        "exit ([int]($errors -and $errors.Count -gt 0))"
    )
    # CI runners occasionally cold-start pwsh slowly; try both shells and allow
    # a bit more time than a typical local parse.
    timeout_s = 30
    errors: list[str] = []
    for pw in ("pwsh", "powershell"):
        try:
            proc = subprocess.run(
                [pw, "-NoProfile", "-NonInteractive", "-Command", parse_script],
                cwd=str(root),
                capture_output=True,
                text=True,
                timeout=timeout_s,
            )
        except FileNotFoundError:
            continue
        except subprocess.TimeoutExpired:
            errors.append(f"{pw}: timed out after {timeout_s}s")
            continue
        assert proc.returncode == 0, (
            f"commit-or-pr.ps1 parse failed with {pw}: {proc.stderr or proc.stdout}"
        )
        return
    if errors:
        raise AssertionError(
            "commit-or-pr.ps1 parse check: " + "; ".join(errors),
        )


def test_commit_or_pr_ps1_has_param_block():
    """scripts/commit-or-pr.ps1 has param block and ValidateSet for Action (structured)."""
    root = _project_root()
    script = root / "scripts" / "commit-or-pr.ps1"
    if not script.exists():
        return
    text = script.read_text(encoding="utf-8", errors="replace")
    assert "param(" in text
    assert "ValidateSet" in text
    assert "Preview" in text and "Commit" in text and "PR" in text


def _parse_powershell_script(script_path: Path, root: Path) -> bool:
    """Return True if script has valid PowerShell syntax (Parser::ParseFile)."""
    rel = script_path.relative_to(root)
    path_expr = (
        "[System.IO.Path]::GetFullPath((Join-Path (Get-Location) '"
        + str(rel.as_posix())
        + "'))"
    )
    parse_script = (
        f"$path = {path_expr}; "
        "$errors = $null; "
        "$null = [System.Management.Automation.Language.Parser]::ParseFile($path, [ref]$null, [ref]$errors); "
        "exit ([int]($errors -and $errors.Count -gt 0))"
    )
    for pw in ("pwsh", "powershell"):
        try:
            proc = subprocess.run(
                [pw, "-NoProfile", "-NonInteractive", "-Command", parse_script],
                cwd=str(root),
                capture_output=True,
                text=True,
                timeout=10,
            )
        except FileNotFoundError:
            continue
        return proc.returncode == 0
    return False


def test_preview_commit_ps1_syntax():
    """scripts/preview-commit.ps1 has valid PowerShell syntax (parse-only)."""
    root = _project_root()
    script = root / "scripts" / "preview-commit.ps1"
    if not script.exists():
        return
    assert _parse_powershell_script(script, root), "preview-commit.ps1 parse failed"


def test_evidence_hash_manifest_ps1_syntax():
    """scripts/evidence-hash-manifest.ps1 has valid PowerShell syntax (parse-only)."""
    root = _project_root()
    script = root / "scripts" / "evidence-hash-manifest.ps1"
    if not script.exists():
        return
    assert _parse_powershell_script(script, root), (
        "evidence-hash-manifest.ps1 parse failed"
    )


def test_mount_secure_vault_ps1_syntax():
    """scripts/mount-secure-vault.ps1 has valid PowerShell syntax (parse-only)."""
    root = _project_root()
    script = root / "scripts" / "mount-secure-vault.ps1"
    if not script.exists():
        return
    assert _parse_powershell_script(script, root), "mount-secure-vault.ps1 parse failed"


def test_pr_hygiene_remind_ps1_syntax():
    """scripts/pr-hygiene-remind.ps1 has valid PowerShell syntax (parse-only)."""
    root = _project_root()
    script = root / "scripts" / "pr-hygiene-remind.ps1"
    if not script.exists():
        return
    assert _parse_powershell_script(script, root), "pr-hygiene-remind.ps1 parse failed"


def test_maintenance_check_ps1_syntax():
    """scripts/maintenance-check.ps1 has valid PowerShell syntax (parse-only)."""
    root = _project_root()
    script = root / "scripts" / "maintenance-check.ps1"
    if not script.exists():
        return
    assert _parse_powershell_script(script, root), "maintenance-check.ps1 parse failed"


def test_docker_hub_pull_ps1_syntax():
    """scripts/docker-hub-pull.ps1 has valid PowerShell syntax (parse-only)."""
    root = _project_root()
    script = root / "scripts" / "docker-hub-pull.ps1"
    if not script.exists():
        return
    assert _parse_powershell_script(script, root), "docker-hub-pull.ps1 parse failed"


def test_docker_lab_build_ps1_syntax():
    """scripts/docker-lab-build.ps1 has valid PowerShell syntax (parse-only)."""
    root = _project_root()
    script = root / "scripts" / "docker-lab-build.ps1"
    if not script.exists():
        return
    assert _parse_powershell_script(script, root), "docker-lab-build.ps1 parse failed"


def test_docker_prune_local_ps1_syntax():
    """scripts/docker-prune-local.ps1 has valid PowerShell syntax (parse-only)."""
    root = _project_root()
    script = root / "scripts" / "docker-prune-local.ps1"
    if not script.exists():
        return
    assert _parse_powershell_script(script, root), "docker-prune-local.ps1 parse failed"


def test_pr_merge_when_green_ps1_syntax():
    """scripts/pr-merge-when-green.ps1 has valid PowerShell syntax (parse-only)."""
    root = _project_root()
    script = root / "scripts" / "pr-merge-when-green.ps1"
    if not script.exists():
        return
    assert _parse_powershell_script(script, root), (
        "pr-merge-when-green.ps1 parse failed"
    )


def test_snmp_LAB_ROUTER_01_lab_probe_ps1_syntax():
    """scripts/snmp-LAB-ROUTER-01-lab-probe.ps1 has valid PowerShell syntax (parse-only)."""
    root = _project_root()
    script = root / "scripts" / "snmp-LAB-ROUTER-01-lab-probe.ps1"
    if not script.exists():
        return
    assert _parse_powershell_script(script, root), (
        "snmp-LAB-ROUTER-01-lab-probe.ps1 parse failed"
    )


def test_lab_op_sync_and_collect_ps1_syntax():
    """scripts/lab-op-sync-and-collect.ps1 has valid PowerShell syntax (parse-only)."""
    root = _project_root()
    script = root / "scripts" / "lab-op-sync-and-collect.ps1"
    if not script.exists():
        return
    assert _parse_powershell_script(script, root), (
        "lab-op-sync-and-collect.ps1 parse failed"
    )


def test_lab_completao_orchestrate_ps1_syntax():
    """scripts/lab-completao-orchestrate.ps1 has valid PowerShell syntax (parse-only)."""
    root = _project_root()
    script = root / "scripts" / "lab-completao-orchestrate.ps1"
    if not script.exists():
        return
    assert _parse_powershell_script(script, root), (
        "lab-completao-orchestrate.ps1 parse failed"
    )


def test_lab_completao_orchestrate_hybrid_v173_ps1_syntax():
    """scripts/lab-completao-orchestrate-hybrid-v173.ps1 has valid PowerShell syntax (parse-only)."""
    root = _project_root()
    script = root / "scripts" / "lab-completao-orchestrate-hybrid-v173.ps1"
    if not script.exists():
        return
    assert _parse_powershell_script(script, root), (
        "lab-completao-orchestrate-hybrid-v173.ps1 parse failed"
    )


def test_lab_op_repo_status_ps1_syntax():
    """scripts/lab-op-repo-status.ps1 has valid PowerShell syntax (parse-only)."""
    root = _project_root()
    script = root / "scripts" / "lab-op-repo-status.ps1"
    if not script.exists():
        return
    assert _parse_powershell_script(script, root), "lab-op-repo-status.ps1 parse failed"


def test_lab_op_git_ensure_ref_ps1_syntax():
    """scripts/lab-op-git-ensure-ref.ps1 has valid PowerShell syntax (parse-only)."""
    root = _project_root()
    script = root / "scripts" / "lab-op-git-ensure-ref.ps1"
    if not script.exists():
        return
    assert _parse_powershell_script(script, root), (
        "lab-op-git-ensure-ref.ps1 parse failed"
    )


def test_collect_homelab_report_remote_ps1_syntax():
    """scripts/collect-homelab-report-remote.ps1 has valid PowerShell syntax (parse-only)."""
    root = _project_root()
    script = root / "scripts" / "collect-homelab-report-remote.ps1"
    if not script.exists():
        return
    assert _parse_powershell_script(script, root), (
        "collect-homelab-report-remote.ps1 parse failed"
    )


def test_homelab_host_report_sh_syntax():
    """scripts/homelab-host-report.sh has valid bash syntax (bash -n). Skipped on Windows."""
    if sys.platform == "win32":
        return
    root = _project_root()
    script = root / "scripts" / "homelab-host-report.sh"
    if not script.exists():
        return
    try:
        proc = subprocess.run(
            ["bash", "-n", str(script)],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=10,
        )
    except FileNotFoundError:
        return
    assert proc.returncode == 0, f"bash -n failed: {proc.stderr or proc.stdout}"


def test_labop_share_client_install_sh_syntax():
    """scripts/labop-share-client-install.sh has valid bash syntax (bash -n). Skipped on Windows."""
    if sys.platform == "win32":
        return
    root = _project_root()
    script = root / "scripts" / "labop-share-client-install.sh"
    if not script.exists():
        return
    try:
        proc = subprocess.run(
            ["bash", "-n", str(script)],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=10,
        )
    except FileNotFoundError:
        return
    assert proc.returncode == 0, f"bash -n failed: {proc.stderr or proc.stdout}"


def test_lab_completao_host_smoke_sh_syntax():
    """scripts/lab-completao-host-smoke.sh has valid bash syntax (bash -n). Skipped on Windows."""
    if sys.platform == "win32":
        return
    root = _project_root()
    script = root / "scripts" / "lab-completao-host-smoke.sh"
    if not script.exists():
        return
    try:
        proc = subprocess.run(
            ["bash", "-n", str(script)],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=10,
        )
    except FileNotFoundError:
        return
    assert proc.returncode == 0, f"bash -n failed: {proc.stderr or proc.stdout}"


def test_lab_node_01_ansible_preflight_sh_syntax():
    """scripts/lab-node-01-ansible-preflight.sh has valid bash syntax (bash -n). Skipped on Windows."""
    if sys.platform == "win32":
        return
    root = _project_root()
    script = root / "scripts" / "lab-node-01-ansible-preflight.sh"
    if not script.exists():
        return
    try:
        proc = subprocess.run(
            ["bash", "-n", str(script)],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=10,
        )
    except FileNotFoundError:
        return
    assert proc.returncode == 0, f"bash -n failed: {proc.stderr or proc.stdout}"


def test_lab_node_01_ansible_labop_podman_apply_sh_syntax():
    """scripts/lab-node-01-ansible-labop-podman-apply.sh has valid bash syntax (bash -n). Skipped on Windows."""
    if sys.platform == "win32":
        return
    root = _project_root()
    script = root / "scripts" / "lab-node-01-ansible-labop-podman-apply.sh"
    if not script.exists():
        return
    try:
        proc = subprocess.run(
            ["bash", "-n", str(script)],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=10,
        )
    except FileNotFoundError:
        return
    assert proc.returncode == 0, f"bash -n failed: {proc.stderr or proc.stdout}"


def test_lab_node_01_session_warm_sh_syntax():
    """scripts/lab-node-01-session-warm.sh has valid bash syntax (bash -n). Skipped on Windows."""
    if sys.platform == "win32":
        return
    root = _project_root()
    script = root / "scripts" / "lab-node-01-session-warm.sh"
    if not script.exists():
        return
    try:
        proc = subprocess.run(
            ["bash", "-n", str(script)],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=10,
        )
    except FileNotFoundError:
        return
    assert proc.returncode == 0, f"bash -n failed: {proc.stderr or proc.stdout}"


def test_lab_node_01_fix_docker_list_sh_syntax():
    """scripts/lab-node-01-fix-docker-list.sh has valid bash syntax (bash -n). Skipped on Windows."""
    if sys.platform == "win32":
        return
    root = _project_root()
    script = root / "scripts" / "lab-node-01-fix-docker-list.sh"
    if not script.exists():
        return
    try:
        proc = subprocess.run(
            ["bash", "-n", str(script)],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=10,
        )
    except FileNotFoundError:
        return
    assert proc.returncode == 0, f"bash -n failed: {proc.stderr or proc.stdout}"


def test_lab_node_01_docker_remove_live_restore_and_restart_sh_syntax():
    """scripts/lab-node-01-docker-remove-live-restore-and-restart.sh has valid bash syntax. Skipped on Windows."""
    if sys.platform == "win32":
        return
    root = _project_root()
    script = root / "scripts" / "lab-node-01-docker-remove-live-restore-and-restart.sh"
    if not script.exists():
        return
    try:
        proc = subprocess.run(
            ["bash", "-n", str(script)],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=10,
        )
    except FileNotFoundError:
        return
    assert proc.returncode == 0, f"bash -n failed: {proc.stderr or proc.stdout}"


def test_lab_node_01_bitwarden_cli_bootstrap_sh_syntax():
    """scripts/lab-node-01-bitwarden-cli-bootstrap.sh has valid bash syntax (bash -n). Skipped on Windows."""
    if sys.platform == "win32":
        return
    root = _project_root()
    script = root / "scripts" / "lab-node-01-bitwarden-cli-bootstrap.sh"
    if not script.exists():
        return
    try:
        proc = subprocess.run(
            ["bash", "-n", str(script)],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=10,
        )
    except FileNotFoundError:
        return
    assert proc.returncode == 0, f"bash -n failed: {proc.stderr or proc.stdout}"


def test_lab_node_01_install_veracrypt_console_debian13_sh_syntax():
    """scripts/lab-node-01-install-veracrypt-console-debian13.sh has valid bash syntax. Skipped on Windows."""
    if sys.platform == "win32":
        return
    root = _project_root()
    script = root / "scripts" / "lab-node-01-install-veracrypt-console-debian13.sh"
    if not script.exists():
        return
    try:
        proc = subprocess.run(
            ["bash", "-n", str(script)],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=10,
        )
    except FileNotFoundError:
        return
    assert proc.returncode == 0, f"bash -n failed: {proc.stderr or proc.stdout}"


def test_lab_node_01_veracrypt_mount_private_repo_sh_syntax():
    """scripts/lab-node-01-veracrypt-mount-private-repo.sh has valid bash syntax. Skipped on Windows."""
    if sys.platform == "win32":
        return
    root = _project_root()
    script = root / "scripts" / "lab-node-01-veracrypt-mount-private-repo.sh"
    if not script.exists():
        return
    try:
        proc = subprocess.run(
            ["bash", "-n", str(script)],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=10,
        )
    except FileNotFoundError:
        return
    assert proc.returncode == 0, f"bash -n failed: {proc.stderr or proc.stdout}"


def test_docker_common_ps1_syntax():
    """scripts/docker/DataBoarDockerCommon.ps1 has valid PowerShell syntax (parse-only)."""
    root = _project_root()
    script = root / "scripts" / "docker" / "DataBoarDockerCommon.ps1"
    if not script.exists():
        return
    assert _parse_powershell_script(script, root), (
        "DataBoarDockerCommon.ps1 parse failed"
    )


def test_create_pr_ps1_syntax():
    """scripts/create-pr.ps1 has valid PowerShell syntax (parse-only)."""
    root = _project_root()
    script = root / "scripts" / "create-pr.ps1"
    if not script.exists():
        return
    assert _parse_powershell_script(script, root), "create-pr.ps1 parse failed"


def test_create_pr_ps1_has_param_block():
    """scripts/create-pr.ps1 has param block with Title and BodyFilePath (structured)."""
    root = _project_root()
    script = root / "scripts" / "create-pr.ps1"
    if not script.exists():
        return
    text = script.read_text(encoding="utf-8", errors="replace")
    assert "param(" in text
    assert "Title" in text and "BodyFilePath" in text


def test_gh_ensure_default_ps1_syntax():
    """scripts/gh-ensure-default.ps1 has valid PowerShell syntax (parse-only)."""
    root = _project_root()
    script = root / "scripts" / "gh-ensure-default.ps1"
    if not script.exists():
        return
    assert _parse_powershell_script(script, root), "gh-ensure-default.ps1 parse failed"


def test_version_readiness_smoke_ps1_syntax():
    """scripts/version-readiness-smoke.ps1 has valid PowerShell syntax (parse-only)."""
    root = _project_root()
    script = root / "scripts" / "version-readiness-smoke.ps1"
    if not script.exists():
        return
    assert _parse_powershell_script(script, root), (
        "version-readiness-smoke.ps1 parse failed"
    )


def test_candidate_dossier_scaffold_ps1_syntax():
    """scripts/candidate-dossier-scaffold.ps1 has valid PowerShell syntax (parse-only)."""
    root = _project_root()
    script = root / "scripts" / "candidate-dossier-scaffold.ps1"
    if not script.exists():
        return
    assert _parse_powershell_script(script, root), (
        "candidate-dossier-scaffold.ps1 parse failed"
    )


def test_candidate_dossier_scaffold_ps1_has_core_params():
    """candidate dossier scaffold exposes key parameters for private workflow."""
    root = _project_root()
    script = root / "scripts" / "candidate-dossier-scaffold.ps1"
    if not script.exists():
        return
    text = script.read_text(encoding="utf-8", errors="replace")
    assert "CandidatePdfPath" in text
    assert "OutputDir" in text
    assert "LowPriorityCaution" in text
    assert "AdvisorRemote" in text
    assert "OperatorRelationship" in text
    assert "Overwrite" in text


def test_talent_dossier_ps1_syntax():
    """scripts/talent-dossier.ps1 has valid PowerShell syntax (parse-only)."""
    root = _project_root()
    script = root / "scripts" / "talent-dossier.ps1"
    if not script.exists():
        return
    assert _parse_powershell_script(script, root), "talent-dossier.ps1 parse failed"


def test_talent_dossier_ps1_resolves_repo_root():
    """talent-dossier supports portable repo root (env, --repo-root, PSScriptRoot)."""
    root = _project_root()
    script = root / "scripts" / "talent-dossier.ps1"
    if not script.exists():
        return
    text = script.read_text(encoding="utf-8", errors="replace")
    assert "DATA_BOAR_REPO_ROOT" in text
    assert "--repo-root" in text
    assert "Get-TalentDossierRepoRoot" in text


def test_commit_or_pr_mentions_gh_default_repo_guard():
    """commit-or-pr includes gh default repository guard for PR flow."""
    root = _project_root()
    script = root / "scripts" / "commit-or-pr.ps1"
    if not script.exists():
        return
    text = script.read_text(encoding="utf-8", errors="replace")
    assert "Set-GhDefaultRepo" in text
    assert "RunVersionSmoke" in text


def test_check_all_supports_optional_version_smoke():
    """check-all script exposes optional version readiness smoke switch."""
    root = _project_root()
    script = root / "scripts" / "check-all.ps1"
    if not script.exists():
        return
    text = script.read_text(encoding="utf-8", errors="replace")
    assert "IncludeVersionSmoke" in text
    assert "version-readiness-smoke.ps1" in text


def test_pr_hygiene_mentions_gh_preflight():
    """pr-hygiene-remind includes gh preflight reminder and quick checks switch."""
    root = _project_root()
    script = root / "scripts" / "pr-hygiene-remind.ps1"
    if not script.exists():
        return
    text = script.read_text(encoding="utf-8", errors="replace")
    assert "gh-ensure-default.ps1" in text
    assert "RunQuickChecks" in text
    assert "SLACK_WEBHOOK_URL" in text
    assert "OPERATOR_NOTIFICATION_CHANNELS" in text


def test_docs_private_scripts_syntax_optional(include_private_lint: bool):
    """
    When opted in (``pytest --include-private`` or ``INCLUDE_PRIVATE_LINT=1``),
    parse any ``*.ps1`` under ``docs/private/`` and run ``bash -n`` on ``*.sh`` there (non-Windows only).
    Skips if ``docs/private/`` is missing or contains no matching scripts.
    """
    if not include_private_lint:
        return
    root = _project_root()
    private_dir = root / "docs" / "private"
    if not private_dir.is_dir():
        return
    ps1_files = sorted(private_dir.rglob("*.ps1"))
    for script in ps1_files:
        assert _parse_powershell_script(script, root), (
            f"{script.relative_to(root)}: PowerShell parse failed"
        )
    if sys.platform == "win32":
        return
    sh_files = sorted(private_dir.rglob("*.sh"))
    for script in sh_files:
        try:
            proc = subprocess.run(
                ["bash", "-n", str(script)],
                cwd=str(root),
                capture_output=True,
                text=True,
                timeout=10,
            )
        except FileNotFoundError:
            return
        assert proc.returncode == 0, (
            f"bash -n failed for {script.relative_to(root)}: "
            f"{proc.stderr or proc.stdout}"
        )


def test_audit_concatenated_markdown_py_compiles():
    """scripts/audit_concatenated_markdown.py compiles (optional Gemini bundle sanity helper)."""
    root = _project_root()
    script = root / "scripts" / "audit_concatenated_markdown.py"
    if not script.exists():
        return
    py_compile.compile(str(script), doraise=True)


def test_export_public_gemini_bundle_py_compiles():
    """scripts/export_public_gemini_bundle.py compiles (safe tracked-files bundle for external LLM)."""
    root = _project_root()
    script = root / "scripts" / "export_public_gemini_bundle.py"
    if not script.exists():
        return
    py_compile.compile(str(script), doraise=True)


def test_audit_concat_sliding_window_py_compiles():
    """scripts/audit_concat_sliding_window.py compiles (sliding-window bundle vs corpus heuristic)."""
    root = _project_root()
    script = root / "scripts" / "audit_concat_sliding_window.py"
    if not script.exists():
        return
    py_compile.compile(str(script), doraise=True)


def test_build_final_round_bucket_concat_py_compiles():
    """scripts/build_final_round_bucket_concat.py compiles (final-round bucket concat + map-names)."""
    root = _project_root()
    script = root / "scripts" / "build_final_round_bucket_concat.py"
    if not script.exists():
        return
    py_compile.compile(str(script), doraise=True)


def test_pii_history_guard_py_compiles():
    """scripts/pii_history_guard.py compiles (history anti-regression guard)."""
    root = _project_root()
    script = root / "scripts" / "pii_history_guard.py"
    if not script.exists():
        return
    py_compile.compile(str(script), doraise=True)


def test_issue_dev_license_jwt_py_compiles():
    """scripts/issue_dev_license_jwt.py compiles (lab JWT issuer; keys stay private)."""
    root = _project_root()
    script = root / "scripts" / "issue_dev_license_jwt.py"
    if not script.exists():
        return
    py_compile.compile(str(script), doraise=True)


def test_recovery_doc_bundle_sanity_ps1_syntax():
    """scripts/recovery-doc-bundle-sanity.ps1 has valid PowerShell syntax (parse-only)."""
    root = _project_root()
    script = root / "scripts" / "recovery-doc-bundle-sanity.ps1"
    if not script.exists():
        return
    assert _parse_powershell_script(script, root), (
        "recovery-doc-bundle-sanity.ps1 parse failed"
    )


def test_operator_day_ritual_ps1_syntax():
    """scripts/operator-day-ritual.ps1 has valid PowerShell syntax (parse-only)."""
    root = _project_root()
    script = root / "scripts" / "operator-day-ritual.ps1"
    if not script.exists():
        return
    assert _parse_powershell_script(script, root), (
        "operator-day-ritual.ps1 parse failed"
    )


def test_lab_node_01_ansible_baseline_ps1_syntax():
    """scripts/lab-node-01-ansible-baseline.ps1 has valid PowerShell syntax (parse-only)."""
    root = _project_root()
    script = root / "scripts" / "lab-node-01-ansible-baseline.ps1"
    if not script.exists():
        return
    assert _parse_powershell_script(script, root), (
        "lab-node-01-ansible-baseline.ps1 parse failed"
    )


def test_run_homelab_host_report_all_ps1_syntax():
    """scripts/run-homelab-host-report-all.ps1 has valid PowerShell syntax (parse-only)."""
    root = _project_root()
    script = root / "scripts" / "run-homelab-host-report-all.ps1"
    if not script.exists():
        return
    assert _parse_powershell_script(script, root), (
        "run-homelab-host-report-all.ps1 parse failed"
    )


def test_lab_op_ps1_syntax():
    """scripts/lab-op.ps1 has valid PowerShell syntax (parse-only)."""
    root = _project_root()
    script = root / "scripts" / "lab-op.ps1"
    if not script.exists():
        return
    assert _parse_powershell_script(script, root), "lab-op.ps1 parse failed"


def test_lab_allow_data_boar_inbound_ps1_syntax():
    """scripts/lab-allow-data-boar-inbound.ps1 has valid PowerShell syntax (parse-only)."""
    root = _project_root()
    script = root / "scripts" / "lab-allow-data-boar-inbound.ps1"
    if not script.exists():
        return
    assert _parse_powershell_script(script, root), (
        "lab-allow-data-boar-inbound.ps1 parse failed"
    )


def test_lab_allow_data_boar_inbound_sh_syntax():
    """scripts/lab-allow-data-boar-inbound.sh has valid bash syntax (bash -n)."""
    if sys.platform == "win32":
        return
    root = _project_root()
    script = root / "scripts" / "lab-allow-data-boar-inbound.sh"
    if not script.exists():
        return
    try:
        proc = subprocess.run(
            ["bash", "-n", str(script)],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=5,
        )
    except FileNotFoundError:
        return
    assert proc.returncode == 0, f"bash -n failed: {proc.stderr or proc.stdout}"


def test_paired_dev_gate_shell_scripts_bash_syntax():
    """Paired Linux/macOS gate scripts (check-all, lint-only, quick-test, pre-commit-and-tests)."""
    if sys.platform == "win32":
        return
    root = _project_root()
    rels = (
        "scripts/check-all.sh",
        "scripts/lint-only.sh",
        "scripts/quick-test.sh",
        "scripts/pre-commit-and-tests.sh",
    )
    for rel in rels:
        script = root / rel
        assert script.is_file(), f"expected tracked script: {rel}"
        try:
            proc = subprocess.run(
                ["bash", "-n", str(script)],
                cwd=str(root),
                capture_output=True,
                text=True,
                timeout=5,
            )
        except FileNotFoundError:
            return
        assert proc.returncode == 0, (
            f"bash -n failed for {rel}: {proc.stderr or proc.stdout}"
        )


def test_es_find_ps1_syntax():
    """scripts/es-find.ps1 has valid PowerShell syntax (parse-only)."""
    root = _project_root()
    script = root / "scripts" / "es-find.ps1"
    if not script.exists():
        return
    assert _parse_powershell_script(script, root), "es-find.ps1 parse failed"


def test_social_x_pace_remind_ps1_syntax():
    """scripts/social-x-pace-remind.ps1 has valid PowerShell syntax (parse-only)."""
    root = _project_root()
    script = root / "scripts" / "social-x-pace-remind.ps1"
    if not script.exists():
        return
    assert _parse_powershell_script(script, root), (
        "social-x-pace-remind.ps1 parse failed"
    )


def test_run_pii_local_seeds_pickaxe_ps1_syntax():
    """scripts/run-pii-local-seeds-pickaxe.ps1 has valid PowerShell syntax (parse-only)."""
    root = _project_root()
    script = root / "scripts" / "run-pii-local-seeds-pickaxe.ps1"
    if not script.exists():
        return
    assert _parse_powershell_script(script, root), (
        "run-pii-local-seeds-pickaxe.ps1 parse failed"
    )


def test_pii_fresh_clone_audit_ps1_syntax():
    """scripts/pii-fresh-clone-audit.ps1 has valid PowerShell syntax (parse-only)."""
    root = _project_root()
    script = root / "scripts" / "pii-fresh-clone-audit.ps1"
    if not script.exists():
        return
    assert _parse_powershell_script(script, root), (
        "pii-fresh-clone-audit.ps1 parse failed"
    )


def test_check_cursor_markdown_preview_settings_ps1_syntax():
    """scripts/check-cursor-markdown-preview-settings.ps1 parses on Windows (parse-only)."""
    root = _project_root()
    script = root / "scripts" / "check-cursor-markdown-preview-settings.ps1"
    if not script.exists():
        return
    assert _parse_powershell_script(script, root), (
        "check-cursor-markdown-preview-settings.ps1 parse failed"
    )


def test_smoke_maturity_assessment_poc_ps1_parses():
    """scripts/smoke-maturity-assessment-poc.ps1 has valid PowerShell syntax (parse-only)."""
    root = _project_root()
    script = root / "scripts" / "smoke-maturity-assessment-poc.ps1"
    if not script.exists():
        return
    assert _parse_powershell_script(script, root), (
        "smoke-maturity-assessment-poc.ps1 parse failed"
    )


def test_smoke_webauthn_json_ps1_parses():
    """scripts/smoke-webauthn-json.ps1 has valid PowerShell syntax (parse-only)."""
    root = _project_root()
    script = root / "scripts" / "smoke-webauthn-json.ps1"
    if not script.exists():
        return
    assert _parse_powershell_script(script, root), (
        "smoke-webauthn-json.ps1 parse failed"
    )


# ---------------------------------------------------------------------------
# PowerShell ASCII-safety guard
# Non-ASCII characters (em-dash U+2014, curly quotes, etc.) cause
# Windows PowerShell 5.1 to emit ParserError even when the file is otherwise
# syntactically correct.  This test catches those regressions early.
# ---------------------------------------------------------------------------

_PS1_ASCII_UNSAFE_RE: re.Pattern[str] = re.compile(r"[^\x00-\x7F]")

_PS1_ASCII_EXEMPT: frozenset[str] = frozenset(
    {
        # candidate-dossier-scaffold.ps1: intentionally contains Portuguese text in
        # output strings for candidate dossier generation; targets pwsh 7+ only.
        "candidate-dossier-scaffold.ps1",
    }
)


def test_powershell_scripts_ascii_safe():
    """All .ps1 scripts under scripts/ are ASCII-only (no em-dash, curly quotes, etc.).

    Windows PowerShell 5.1 emits ParserError on non-ASCII characters in string literals
    or comments even when the file is otherwise valid.  We enforce ASCII-only to prevent
    silent breakage on the operator's Windows dev machine.

    Exemptions: add a script name (not path) to _PS1_ASCII_EXEMPT only if it explicitly
    targets pwsh 7+ and the non-ASCII is intentional.
    """
    root = _project_root()
    violations: list[str] = []
    for script in sorted((root / "scripts").glob("*.ps1")):
        if script.name in _PS1_ASCII_EXEMPT:
            continue
        text = script.read_text(encoding="utf-8", errors="replace")
        for lineno, line in enumerate(text.splitlines(), start=1):
            m = _PS1_ASCII_UNSAFE_RE.search(line)
            if m:
                char = m.group(0)
                violations.append(
                    f"  scripts/{script.name}:{lineno} non-ASCII char {char!r}"
                    f" (U+{ord(char):04X}) - use ASCII equivalent"
                )
    assert not violations, (
        "PowerShell scripts contain non-ASCII characters that break PS 5.1:\n"
        + "\n".join(violations)
    )
