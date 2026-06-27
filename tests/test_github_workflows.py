"""Offline guards on tracked ``.github/workflows/*.yml`` (and two wrapper scripts).

**Slack:** Parses all shipped ``slack-*.yml`` including ``slack-ci-failure-notify.yml``
(``workflow_call`` reusable workflow; upstream workflows invoke it on failure). A private snapshot may live at
``docs/private/raw_pastes/cursor-incident/slack-ci-failure-notify.yml.old`` for
pause drills — see **``docs/ops/OPERATOR_NOTIFICATION_CHANNELS.md`` §4.1.1**
(pt-BR: ``OPERATOR_NOTIFICATION_CHANNELS.pt_BR.md``).
No real Slack POST in pytest — see §4.1 overall.

**Supply chain / CI shape:** ``ci.yml`` / ``sbom.yml`` / ``gitleaks.yml`` / ``dependabot-sync.yml``
pin third-party Actions to full commit SHAs where applicable; ``ci.yml`` must not use
floating ``version: \"latest\"`` for ``astral-sh/setup-uv`` (ADR 0005). ``semgrep.yml``,
``zizmor.yml``, and ``workflow-security-lint`` wrapper paths get structural checks.
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
    assert "workflow_call" in on
    wc = on["workflow_call"]
    assert isinstance(wc, dict)
    inputs = wc.get("inputs") or {}
    for key in ("run_name", "head_branch", "event", "html_url"):
        assert key in inputs
        assert inputs[key].get("required") is True
    assert "notify" in (data.get("jobs") or {})


def test_upstream_workflows_invoke_slack_ci_failure_notify_on_failure() -> None:
    """Failure Slack ping is workflow_call from upstream CI workflows (not workflow_run)."""
    callers = (
        (
            "ci.yml",
            "CI",
            ("test", "lint", "bandit", "audit", "dependency-review", "sonar"),
        ),
        ("semgrep.yml", "Semgrep", ("semgrep",)),
        ("gitleaks.yml", "Gitleaks", ("scan",)),
        ("sbom.yml", "SBOM", ("generate",)),
        (
            "dependabot-sync.yml",
            "Dependabot requirements.txt sync",
            ("sync-requirements",),
        ),
    )
    for filename, run_name, needs_jobs in callers:
        data = _load_workflow(filename)
        jobs = data.get("jobs") or {}
        slack_jobs = [
            (jid, job)
            for jid, job in jobs.items()
            if isinstance(job, dict)
            and str(job.get("uses", "")).endswith("slack-ci-failure-notify.yml")
        ]
        assert len(slack_jobs) == 1, (
            f"{filename}: expected one slack notify reusable job, found {len(slack_jobs)}"
        )
        _jid, job = slack_jobs[0]
        job_if = str(job.get("if") or "").lower()
        assert "failure" in job_if
        assert set(job.get("needs") or []) == set(needs_jobs)
        with_block = job.get("with") or {}
        assert with_block.get("run_name") == run_name


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


def test_gitleaks_workflow_present_and_valid() -> None:
    data = _load_workflow("gitleaks.yml")
    assert data.get("name") == "Gitleaks"
    on = data.get("on") or {}
    assert "push" in on
    assert "pull_request" in on
    assert "schedule" in on
    assert "workflow_dispatch" in on
    jobs = data.get("jobs") or {}
    assert "scan" in jobs
    job = jobs["scan"]
    assert job.get("runs-on") == "ubuntu-latest"
    steps = job.get("steps") or []
    uses_lines = [
        str(step.get("uses"))
        for step in steps
        if isinstance(step, dict) and step.get("uses")
    ]
    assert any("actions/checkout@" in line for line in uses_lines)
    assert any("gitleaks/gitleaks-action@" in line for line in uses_lines)


def test_gitleaks_yml_pins_actions_to_shas() -> None:
    """Third-party Actions in gitleaks.yml use full commit SHAs (ADR 0005 bar)."""
    text = (WORKFLOWS / "gitleaks.yml").read_text(encoding="utf-8")
    sha_40 = re.compile(r"@[0-9a-f]{40}")
    for line in text.splitlines():
        code = line.split("#", 1)[0]
        if "uses:" not in code or "docker://" in code:
            continue
        if "./.github/workflows/" in code:
            continue
        if not any(p in code for p in ("actions/", "github/", "gitleaks/")):
            continue
        assert sha_40.search(code), (
            f"expected full commit SHA in uses line: {line.strip()!r}"
        )


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


def test_sbom_workflow_generates_build_digest_before_docker_build() -> None:
    """Release integrity: digest must exist before docker build (issue #711)."""
    text = (WORKFLOWS / "sbom.yml").read_text(encoding="utf-8")
    digest_idx = text.index("generate_build_digest.py")
    docker_idx = text.index("docker build -t data_boar:sbom")
    assert digest_idx < docker_idx
    assert "build-digest.txt" in text


def test_sbom_workflow_generates_release_manifest_after_docker_build() -> None:
    """Release integrity: manifest generated inside image after docker build (#713)."""
    text = (WORKFLOWS / "sbom.yml").read_text(encoding="utf-8")
    docker_idx = text.index("docker build -t data_boar:sbom")
    manifest_idx = text.index("Generate release manifest inside image")
    assert docker_idx < manifest_idx
    assert "release-manifest.json" in text


def test_sbom_yml_pins_actions_to_shas() -> None:
    """Third-party Actions in sbom.yml use full commit SHAs (same bar as ci.yml)."""
    text = (WORKFLOWS / "sbom.yml").read_text(encoding="utf-8")
    sha_40 = re.compile(r"@[0-9a-f]{40}")
    for line in text.splitlines():
        code = line.split("#", 1)[0]
        if "uses:" not in code or "docker://" in code:
            continue
        if "./.github/workflows/" in code:
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
        if "./.github/workflows/" in code:
            continue
        if not any(
            p in code for p in ("actions/", "github/", "astral-sh/", "SonarSource/")
        ):
            continue
        assert sha_40.search(code), (
            f"expected full commit SHA in uses line: {line.strip()!r}"
        )


def test_ci_yml_has_dependency_review_job_on_pull_request() -> None:
    """ADR-0074 Layer 1 / #988: PR-time dependency diff before merge."""
    data = _load_workflow("ci.yml")
    jobs = data.get("jobs") or {}
    dep = jobs.get("dependency-review")
    assert isinstance(dep, dict), "ci.yml must define dependency-review job"
    assert "pull_request" in str(dep.get("if") or "")
    perms = dep.get("permissions") or {}
    assert perms.get("pull-requests") == "read"
    steps = dep.get("steps") or []
    uses = [str(s.get("uses")) for s in steps if isinstance(s, dict) and s.get("uses")]
    assert any("actions/dependency-review-action@" in u for u in uses)


def test_rust_ci_runs_cargo_audit_and_deny() -> None:
    """ADR-0074 Layer 1 / #988: Rust SCA in rust-ci.yml."""
    text = (WORKFLOWS / "rust-ci.yml").read_text(encoding="utf-8")
    assert "cargo audit" in text
    assert "cargo deny check" in text


def test_dockerfile_pins_python_base_image_by_digest() -> None:
    """ADR-0074 Layer 1 / #988: base image digest pin, not tag-only FROM."""
    dockerfile = REPO_ROOT / "Dockerfile"
    text = dockerfile.read_text(encoding="utf-8")
    from_lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip().upper().startswith("FROM ")
    ]
    assert len(from_lines) >= 3
    for line in from_lines:
        assert "@sha256:" in line, f"expected digest pin in FROM line: {line!r}"


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
        if "./.github/workflows/" in code:
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
    env = job.get("env") or {}
    enforce_expr = str(env.get("ENFORCE_ZIZMOR", ""))
    assert "ZIZMOR_ENFORCE == 'false'" in enforce_expr
    assert "'true'" in enforce_expr


def test_workflow_security_lint_wrappers_present() -> None:
    for rel in (
        "scripts/workflow-security-lint.ps1",
        "scripts/workflow-security-lint.sh",
    ):
        path = REPO_ROOT / rel
        assert path.is_file(), f"missing local zizmor wrapper: {rel}"


def test_operator_gated_reopen_workflow_present_and_valid() -> None:
    """ADR-0072 / #990: structural guard for operator-gated issue auto-reopen."""
    data = _load_workflow("operator-gated-reopen.yml")
    assert data.get("name")
    text = (WORKFLOWS / "operator-gated-reopen.yml").read_text(encoding="utf-8")
    # PyYAML may coerce bare `on:` — assert trigger from source text.
    assert re.search(r"types:\s*\[closed\]", text)
    perms = data.get("permissions") or {}
    assert perms.get("issues") == "write"
    jobs = data.get("jobs") or {}
    assert "guard-reopen" in jobs
    assert "operator-gated" in text
    assert "gate-close-approved" in text
    assert "Gate-Close-Approved-By" in text
    assert "sorted[0]" in text or "latest" in text.lower()
    assert "issue.body" not in text.replace("latestBody", "")
    assert "actions/github-script@" in text
    sha_40 = re.compile(r"@[0-9a-f]{40}")
    for line in text.splitlines():
        code = line.split("#", 1)[0]
        if "uses:" not in code or "docker://" in code:
            continue
        if "actions/github-script@" in code:
            assert sha_40.search(code), (
                f"expected full commit SHA for github-script: {line.strip()!r}"
            )
