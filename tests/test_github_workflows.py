"""Ensure operator Slack workflow files exist and parse as valid YAML.

Integration (real Slack POST) is not run in pytest; see docs/ops/OPERATOR_NOTIFICATION_CHANNELS.md §4.1.

Supply Colleague-Nn: ci.yml must not use floating `version: \"latest\"` for astral-sh/setup-uv; Actions use commit SHAs.
sbom.yml pins third-party Actions to full commit SHAs (ADR 0005).
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = REPO_ROOT / ".github" / "workflows"


def _load_workflow(name: str) -> dict:
    path = WORKFLOWS / name
    assert path.is_file(), f"missing workflow file: {path}"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict), f"{name} must parse to a mapping"
    return data


def test_slack_operator_ping_workflow_present_and_valid() -> None:
    data = _load_workflow("slack-operator-ping.yml")
    assert data.get("name")
    assert "workflow_dispatch" in (data.get("on") or {})
    assert "ping" in (data.get("jobs") or {})


def test_slack_ci_failure_notify_workflow_present_and_valid() -> None:
    data = _load_workflow("slack-ci-failure-notify.yml")
    assert data.get("name")
    on = data.get("on") or {}
    assert "workflow_run" in on
    wr = on["workflow_run"]
    assert isinstance(wr, dict)
    assert wr.get("workflows") == [
        "CI",
        "Semgrep",
        "SBOM",
        "Dependabot requirements.txt sync",
    ]
    assert "notify" in (data.get("jobs") or {})


def test_slack_ci_failure_notify_has_operator_kill_switch() -> None:
    """The CI failure notifier exposes a reversible kill-switch via repo variable.

    Regression guard: the operator must be able to mute Slack CI-failure pings
    by flipping ``vars.MUTE_CI_FAILURE_NOTIFY`` (true/1/yes/on) in the GitHub
    UI without editing YAML or revoking ``secrets.SLACK_WEBHOOK_URL`` (which
    other Slack workflows share). The detect step must read the variable in
    its ``env:`` and short-circuit ``present=false`` when truthy, so the
    existing ``if: steps.<id>.outputs.present == 'true'`` gate skips the POST.
    """
    data = _load_workflow("slack-ci-failure-notify.yml")
    notify = (data.get("jobs") or {}).get("notify") or {}
    steps = notify.get("steps") or []
    detect_step = None
    for step in steps:
        if not isinstance(step, dict):
            continue
        env = step.get("env") or {}
        if "MUTE_CI_FAILURE_NOTIFY" in env and "SLACK_WEBHOOK_URL" in env:
            detect_step = step
            break
    assert detect_step is not None, (
        "slack-ci-failure-notify.yml: expected a step that reads both "
        "SLACK_WEBHOOK_URL and MUTE_CI_FAILURE_NOTIFY via env (kill-switch)."
    )
    env_block = detect_step.get("env") or {}
    assert "vars.MUTE_CI_FAILURE_NOTIFY" in str(
        env_block.get("MUTE_CI_FAILURE_NOTIFY", "")
    ), (
        "MUTE_CI_FAILURE_NOTIFY must be wired to vars.MUTE_CI_FAILURE_NOTIFY "
        "(repo Variable, not Secret) so the operator can flip it from the UI."
    )
    run_text = str(detect_step.get("run") or "")
    assert "present=false" in run_text and "exit 0" in run_text, (
        "kill-switch branch must write present=false and exit 0 cleanly so "
        "the run does not show a phantom failure when notifications are muted."
    )
    for token in ("true", "1", "yes", "on"):
        assert token in run_text, (
            f"kill-switch should accept truthy token {token!r} (case-insensitive)."
        )


def test_slack_release_published_notify_workflow_present_and_valid() -> None:
    data = _load_workflow("slack-release-published-notify.yml")
    assert data.get("name")
    on = data.get("on") or {}
    assert "release" in on
    rel = on["release"]
    assert isinstance(rel, dict)
    assert rel.get("types") == ["published"]
    assert "notify" in (data.get("jobs") or {})


def test_slack_pr_merged_notify_workflow_present_and_valid() -> None:
    data = _load_workflow("slack-pr-merged-notify.yml")
    assert data.get("name")
    on = data.get("on") or {}
    assert "pull_request" in on
    pr = on["pull_request"]
    assert isinstance(pr, dict)
    assert pr.get("types") == ["closed"]
    assert pr.get("branches") == ["main", "master"]
    assert "notify" in (data.get("jobs") or {})


def test_slack_ops_digest_workflow_present_and_valid() -> None:
    data = _load_workflow("slack-ops-digest.yml")
    assert data.get("name")
    on = data.get("on") or {}
    assert "workflow_dispatch" in on
    assert "schedule" in on
    assert "notify" in (data.get("jobs") or {})


def test_slack_post_workflows_guard_webhook_secret() -> None:
    """Slack workflows that POST must skip cleanly when SLACK_WEBHOOK_URL is empty.

    Regression guard for the "phantom failed run" class of bug: putting
    ``${{ secrets.SLACK_WEBHOOK_URL != '' }}`` in a *job-level* ``if:``
    expression makes GitHub Actions record a failed workflow run with zero
    jobs ("This run likely failed because of a workflow file issue"). The
    correct pattern is to read the secret in a step's ``env:`` block, write a
    detection output (``present=true|false``), and gate downstream steps with
    ``if: steps.<id>.outputs.present == 'true'``. Same posture as the
    ``sonar`` job in ``ci.yml``.
    """
    names = (
        "slack-operator-ping.yml",
        "slack-ci-failure-notify.yml",
        "slack-release-published-notify.yml",
        "slack-pr-merged-notify.yml",
        "slack-ops-digest.yml",
    )
    for name in names:
        data = _load_workflow(name)
        jobs = data.get("jobs") or {}
        for job_id, job in jobs.items():
            if not isinstance(job, dict):
                continue
            if job.get("runs-on") != "ubuntu-latest":
                continue
            if "steps" not in job:
                continue

            job_if = str(job.get("if") or "")
            assert "secrets." not in job_if, (
                f"{name} job {job_id}: do not reference secrets.* in a "
                f"job-level `if:` (causes phantom failed runs); detect the "
                f"webhook in a step and gate downstream steps on its output."
            )
            assert "SLACK_WEBHOOK_URL" not in job_if, (
                f"{name} job {job_id}: SLACK_WEBHOOK_URL must not appear in "
                f"the job-level `if:` — guard at step level instead."
            )

            steps = job.get("steps") or []
            assert isinstance(steps, list) and steps, (
                f"{name} job {job_id}: expected at least one step"
            )

            detect_step = None
            for step in steps:
                if not isinstance(step, dict):
                    continue
                env = step.get("env") or {}
                if "SLACK_WEBHOOK_URL" in env:
                    run_text = str(step.get("run") or "")
                    if (
                        "present=true" in run_text
                        and "present=false" in run_text
                        and "GITHUB_OUTPUT" in run_text
                    ):
                        detect_step = step
                        break
            assert detect_step is not None, (
                f"{name} job {job_id}: expected a step that reads "
                f"SLACK_WEBHOOK_URL via env and writes present=true/false "
                f"to $GITHUB_OUTPUT (step-level webhook detection)."
            )
            detect_id = detect_step.get("id")
            assert detect_id, (
                f"{name} job {job_id}: webhook detection step must have an `id:` "
                f"so downstream steps can gate on its output."
            )

            gated = [
                step
                for step in steps
                if isinstance(step, dict)
                and isinstance(step.get("if"), str)
                and f"steps.{detect_id}.outputs.present" in step["if"]
            ]
            assert gated, (
                f"{name} job {job_id}: at least one downstream step must be "
                f"gated by `if: steps.{detect_id}.outputs.present == 'true'`."
            )


def test_semgrep_workflow_present_and_valid() -> None:
    data = _load_workflow("semgrep.yml")
    assert data.get("name") == "Semgrep"
    on = data.get("on") or {}
    assert "push" in on
    assert "pull_request" in on
    jobs = data.get("jobs") or {}
    assert "semgrep" in jobs
    job = jobs["semgrep"]
    assert job.get("runs-on") == "ubuntu-latest"
    container = job.get("container") or {}
    assert "semgrep" in str(container.get("image", "")).lower()


def _ci_step_run_texts(job: dict) -> list[str]:
    """Collect shell `run:` strings from a workflow job (scalar or folded YAML)."""
    out: list[str] = []
    for step in job.get("steps") or []:
        if not isinstance(step, dict):
            continue
        run = step.get("run")
        if isinstance(run, str):
            out.append(run)
    return out


def test_sbom_workflow_present_and_valid() -> None:
    data = _load_workflow("sbom.yml")
    assert data.get("name") == "SBOM"
    on = data.get("on") or {}
    assert "push" in on
    assert "workflow_dispatch" in on
    jobs = data.get("jobs") or {}
    assert "generate" in jobs


def test_sbom_yml_pins_actions_to_shas() -> None:
    """Third-party Actions in sbom.yml use full commit SHAs (same bar as ci.yml)."""
    text = (WORKFLOWS / "sbom.yml").read_text(encoding="utf-8")
    sha_40 = re.compile(r"@[0-9a-f]{40}")
    for line in text.splitlines():
        code = line.split("#", 1)[0]
        if "uses:" not in code or "docker://" in code:
            continue
        if not any(p in code for p in ("actions/", "github/", "astral-sh/")):
            continue
        assert sha_40.search(code), (
            f"expected full commit SHA in uses line: {line.strip()!r}"
        )


def test_ci_yml_pins_actions_and_uv_cli() -> None:
    """Regression: avoid astral-sh/setup-uv `version: latest`; Actions should use 40-char SHAs."""
    text = (WORKFLOWS / "ci.yml").read_text(encoding="utf-8")
    assert 'version: "latest"' not in text
    assert "astral-sh/setup-uv@" in text
    assert 'version: "' in text
    sha_40 = re.compile(r"@[0-9a-f]{40}")
    for line in text.splitlines():
        code = line.split("#", 1)[0]
        if "uses:" not in code or "docker://" in code:
            continue
        if not any(
            p in code for p in ("actions/", "github/", "astral-sh/", "SonarSource/")
        ):
            continue
        assert sha_40.search(code), (
            f"expected full commit SHA in uses line: {line.strip()!r}"
        )


def test_dependabot_sync_workflow_present_and_valid() -> None:
    """Dependabot PRs that touch the lockfile get requirements.txt regenerated on-branch."""
    data = _load_workflow("dependabot-sync.yml")
    assert data.get("name")
    on = data.get("on") or {}
    assert "pull_request" in on
    pr = on["pull_request"]
    assert isinstance(pr, dict)
    assert pr.get("branches") == ["main", "master"]
    paths = pr.get("paths") or []
    assert "uv.lock" in paths
    assert "pyproject.toml" in paths
    jobs = data.get("jobs") or {}
    sync = jobs.get("sync-requirements")
    assert isinstance(sync, dict)
    assert "dependabot[bot]" in str(sync.get("if") or "")
    perms = sync.get("permissions") or {}
    assert perms.get("contents") == "write"
    text = (WORKFLOWS / "dependabot-sync.yml").read_text(encoding="utf-8")
    sha_40 = re.compile(r"@[0-9a-f]{40}")
    for line in text.splitlines():
        code = line.split("#", 1)[0]
        if "uses:" not in code or "docker://" in code:
            continue
        if not any(p in code for p in ("actions/", "github/", "astral-sh/")):
            continue
        assert sha_40.search(code), (
            f"expected full commit SHA in uses line: {line.strip()!r}"
        )


def test_ci_lint_job_runs_pre_commit_all_files() -> None:
    """Regression guard: lint job must run pre-commit so CI matches local hook bundle (incl. Ruff, plans-stats)."""
    data = _load_workflow("ci.yml")
    assert data.get("name") == "CI"
    jobs = data.get("jobs") or {}
    lint = jobs.get("lint")
    assert isinstance(lint, dict), "ci.yml must define a lint job"
    assert "pre-commit" in str(lint.get("name", "")).lower(), (
        "lint job name should mention pre-commit"
    )
    runs = "\n".join(_ci_step_run_texts(lint))
    assert "pre-commit run --all-files" in runs


def test_zizmor_workflow_present_and_valid() -> None:
    data = _load_workflow("zizmor.yml")
    assert data.get("name") == "Zizmor"
    on = data.get("on") or {}
    assert "pull_request" in on
    assert "push" in on
    assert "workflow_dispatch" in on
    jobs = data.get("jobs") or {}
    assert "zizmor" in jobs
    job = jobs["zizmor"]
    assert job.get("runs-on") == "ubuntu-latest"
    steps = job.get("steps") or []
    uses_lines = [
        str(step.get("uses"))
        for step in steps
        if isinstance(step, dict) and step.get("uses")
    ]
    assert any("zizmorcore/zizmor-action@" in line for line in uses_lines)


def test_workflow_security_lint_wrappers_present() -> None:
    for rel in (
        "scripts/workflow-security-lint.ps1",
        "scripts/workflow-security-lint.sh",
    ):
        path = REPO_ROOT / rel
        assert path.is_file(), f"missing local zizmor wrapper: {rel}"
