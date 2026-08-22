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
            (
                "test",
                "test-extras",
                "test-windows",
                "lint",
                "bandit",
                "audit",
                "dependency-review",
                "sonar",
                "ansible-syntax",
            ),
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
    run_blob = "\n".join(
        str(step.get("run", ""))
        for step in steps
        if isinstance(step, dict) and step.get("run")
    )
    assert "gitleaks_${VER}_linux_x64.tar.gz" in run_blob
    assert "sha256sum -c" in run_blob
    assert "./gitleaks git ." in run_blob
    assert "--config .gitleaks.toml" in run_blob


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
        if not any(p in code for p in ("actions/", "github/")):
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
    assert "--patch-native-into" in text
    assert "native_packages" in text
    assert "refusing to clobber native_packages[]" in text
    assert "gh release view" in text


def test_sbom_yml_pins_actions_to_shas() -> None:
    """Third-party Actions in sbom.yml use full commit SHAs (same bar as ci.yml)."""
    text = (WORKFLOWS / "sbom.yml").read_text(encoding="utf-8")
    sha_40 = re.compile(r"@[0-9a-f]{40}")
    for line in text.splitlines():
        code = line.split("#", 1)[0]
        if "uses:" not in code or "docker://" in code:
            continue
        # Local reusable workflows / composite actions are not third-party pins.
        if "./.github/workflows/" in code or "./.github/actions/" in code:
            continue
        if not any(p in code for p in ("actions/", "github/", "astral-sh/")):
            continue
        assert sha_40.search(code), (
            f"expected full commit SHA in uses line: {line.strip()!r}"
        )


def test_sbom_yml_libmariadb_uses_timed_composite_action() -> None:
    """SBOM must share the #1646 azure→archive pin; do not inline bare apt-get."""
    text = (WORKFLOWS / "sbom.yml").read_text(encoding="utf-8")
    assert "sudo apt-get update && sudo apt-get install -y libmariadb-dev" not in text
    assert "./.github/actions/install-libmariadb-dev" in text
    assert "timeout 240 sudo apt-get install -y build-essential" in text
    # Pin + apt-get update live only in the composite action (#1648).
    data = _load_workflow("sbom.yml")
    runs = _ci_step_run_texts(data["jobs"]["generate"])
    assert not any("apt-get update" in r for r in runs)


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
        # Local reusable workflows / composite actions are not third-party pins.
        if "./.github/workflows/" in code or "./.github/actions/" in code:
            continue
        if not any(
            p in code for p in ("actions/", "github/", "astral-sh/", "SonarSource/")
        ):
            continue
        assert sha_40.search(code), (
            f"expected full commit SHA in uses line: {line.strip()!r}"
        )


def test_ci_yml_libmariadb_install_uses_timed_composite_action() -> None:
    """#1627: bare apt-get libmariadb must not hang jobs; use composite with timeouts."""
    text = (WORKFLOWS / "ci.yml").read_text(encoding="utf-8")
    assert "sudo apt-get update && sudo apt-get install -y libmariadb-dev" not in text
    # test-extras (Python 3.13) omits libmariadb — upstream mariadb 1.1.14
    # SyntaxError; remaining jobs still use the timed composite (#1627).
    assert text.count("./.github/actions/install-libmariadb-dev") >= 4

    action = REPO_ROOT / ".github" / "actions" / "install-libmariadb-dev" / "action.yml"
    assert action.is_file(), f"missing composite action: {action}"
    action_text = action.read_text(encoding="utf-8")
    # Composite steps cannot declare timeout-minutes (GHA schema); use coreutils timeout.
    assert "timeout-minutes:" not in action_text
    assert "timeout " in action_text
    assert "libmariadb-dev" in action_text
    # #1646: repoint stalled regional mirror before apt-get update.
    # Regex on file body (not URL substring `in`) — CodeQL py/incomplete-url-substring-sanitization.
    assert re.search(
        r"repoint_azure /etc/apt/apt-mirrors\.txt",
        action_text,
    ), "missing apt-mirrors repoint hook (#1646)"
    assert re.search(
        r"s\|azure\\\.archive\\\.ubuntu\\\.com\|archive\.ubuntu\.com\|g",
        action_text,
    ), "missing azure→archive sed repoint (#1646)"
    assert "timeout 240 sudo apt-get update" in action_text


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
    """Dependabot PRs that touch the lockfile get requirements.txt closure (#1419)."""
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
    job_if = str(sync.get("if") or "")
    assert "dependabot[bot]" in job_if
    assert "dependabot/" in job_if
    perms = sync.get("permissions") or {}
    assert perms.get("contents") == "write"
    assert perms.get("pull-requests") == "write"
    text = (WORKFLOWS / "dependabot-sync.yml").read_text(encoding="utf-8")
    assert "path: trusted" in text
    assert "path: dependabot-input" in text
    assert "pull_request.base.ref" in text
    assert "pull_request.head.sha" in text
    assert "sparse-checkout: scripts/ci_dependabot_requirements_sync.sh" in text
    assert (
        'bash "${{ github.workspace }}/trusted/scripts/ci_dependabot_requirements_sync.sh"'
        in text
    )
    assert "ref: ${{ github.event.pull_request.head.ref }}" not in text
    assert 'git push "https://x-access-token' not in text
    assert "HEAD:${GITHUB_EVENT_PULL_REQUEST_HEAD_REF}" not in text
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


def test_dependabot_sync_script_never_unsigned_push_to_dependabot_head() -> None:
    """#1419: closure script must not unsigned-push onto the Dependabot PR branch."""
    script = REPO_ROOT / "scripts" / "ci_dependabot_requirements_sync.sh"
    assert script.is_file()
    text = script.read_text(encoding="utf-8")
    assert not re.search(r"^git push .*HEAD_REF", text, flags=re.MULTILINE)
    assert re.search(
        r'^git push "https://x-access-token:\$\{GH_TOKEN\}@github\.com/\$\{GITHUB_REPOSITORY\}" "HEAD:\$\{SYNC_BRANCH\}"$',
        text,
        flags=re.MULTILINE,
    )
    assert "DEPENDABOT_SYNC_WORKSPACE" in text
    assert "DEPENDABOT_SYNC_SSH_SIGNING_KEY" in text
    assert "gh pr comment" in text
    assert "git commit -S" in text


def test_ci_yml_has_optional_extras_job() -> None:
    """#1638: dedicated job installs SQL extras (minus mariadb on 3.13) and caps skips."""
    data = _load_workflow("ci.yml")
    jobs = data.get("jobs") or {}
    extras = jobs.get("test-extras")
    assert isinstance(extras, dict), "ci.yml must define test-extras job"
    assert extras.get("runs-on") == "ubuntu-latest"
    assert extras.get("timeout-minutes") == 50
    assert extras.get("continue-on-error") in (None, False)
    env = extras.get("env") or {}
    assert env.get("DATA_BOAR_CI_EXTRAS") == "1"
    assert "MAESTRO_ROOT" not in env
    yaml_text = (WORKFLOWS / "ci.yml").read_text(encoding="utf-8")
    extras_chunk = yaml_text.split("test-extras:")[1].split("\n  lint:")[0]
    assert "repository: DataBoar/maestro" not in extras_chunk
    assert "MAESTRO_CHECKOUT_TOKEN" not in extras_chunk
    assert "opt-in" in extras_chunk
    runs = "\n".join(_ci_step_run_texts(extras))
    for extra in (
        "postgres",
        "mysql",
        "mssql",
        "mssql-pyodbc",
        "oracle",
        "nosql",
        "compressed",
        "dataformats",
    ):
        assert f"--extra {extra}" in runs, extra
    assert "--extra shares --group dev" in runs
    assert "--extra sql-all" not in runs
    assert "--extra mariadb" not in runs
    assert "pytest" in runs
    assert "--junitxml=extras-junit.xml" in runs
    assert "scripts/ci_pytest_skip_ceiling.py" in runs
    assert "--max-skipped 60" in runs
    assert "--ignore=tests/test_maestro_scripts.py" in runs
    assert (
        "--deselect=tests/test_issue_dev_license_qa.py::test_maestro_handler_issues_60d_machine_bound"
        in runs
    )
    assert (
        "--deselect=tests/test_security.py::test_sync_working_tree_excludes_dotenv_from_rsync"
        in runs
    )
    assert (
        "--deselect=tests/test_security.py::test_maestro_aggregates_real_failures_in_exit"
        in runs
    )
    assert "./.github/actions/install-libmariadb-dev" not in str(extras)
    assert "unixodbc-dev" in runs


def test_ci_yml_has_windows_test_job() -> None:
    """#1427: Windows is CI-tested (not only declared) via windows-latest."""
    data = _load_workflow("ci.yml")
    jobs = data.get("jobs") or {}
    win = jobs.get("test-windows")
    assert isinstance(win, dict), "ci.yml must define test-windows job"
    assert win.get("runs-on") == "windows-latest"
    # Cap hung runners (GH/outage class); do not soft-fail — Windows must stay green.
    assert win.get("timeout-minutes") == 40
    assert win.get("continue-on-error") in (None, False)
    env = win.get("env") or {}
    assert "UV_PYTHON" in env, "Windows job must pin UV_PYTHON to matrix Python"
    assert env.get("JOBLIB_MULTIPROCESSING") == "0"
    runs = "\n".join(_ci_step_run_texts(win))
    assert "uv sync" in runs
    assert "--python" in runs
    assert "pytest" in runs
    assert "pip install" in runs
    assert "demo_headless" in runs
    # Prefer bash for the pytest step (sklearn/OpenMP + pwsh signal quirks).
    steps = win.get("steps") or []
    pytest_steps = [
        s for s in steps if isinstance(s, dict) and "pytest" in str(s.get("run") or "")
    ]
    assert pytest_steps, "Windows job must have a pytest step"
    assert pytest_steps[0].get("shell") == "bash"


def test_zizmor_workflow_present_and_valid() -> None:
    data = _load_workflow("zizmor.yml")
    assert data.get("name") == "Zizmor"
    on = data.get("on") or {}
    assert "pull_request" in on
    assert "push" in on
    assert "schedule" in on
    assert "workflow_dispatch" in on
    pr = on.get("pull_request") or {}
    push = on.get("push") or {}
    assert pr.get("branches") == ["main", "master"]
    assert push.get("branches") == ["main", "master"]
    assert "paths" not in pr, (
        "path filter on pull_request omits zizmor SARIF for non-workflow PRs "
        "(code_scanning ruleset deadlock)"
    )
    assert "paths" not in push, (
        "path filter on push omits zizmor SARIF when main lands without "
        "workflow changes (code_scanning ruleset deadlock)"
    )
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
    assert any("github/codeql-action/upload-sarif@" in line for line in uses_lines)
    text = (WORKFLOWS / "zizmor.yml").read_text(encoding="utf-8")
    assert "github.event.pull_request.head.sha" in text
    assert "refs/pull/{0}/head" in text or "refs/pull/${" in text
    assert "advanced-security: false" in text
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
    assert "SSHSIG" in text or "SSH SIGNATURE" in text
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


def test_publish_pypi_workflow_present_and_valid() -> None:
    """#1042 / #74: OIDC PyPI publish — build in CI, prod gated on dispatch target=pypi."""
    data = _load_workflow("publish-pypi.yml")
    assert data.get("name") == "Publish to PyPI"
    on = data.get("on") or {}
    assert "release" in on
    rel = on["release"]
    assert isinstance(rel, dict)
    assert rel.get("types") == ["published"]
    assert "workflow_dispatch" in on
    wd = on["workflow_dispatch"]
    assert isinstance(wd, dict)
    target = (wd.get("inputs") or {}).get("target") or {}
    assert target.get("type") == "choice"
    assert target.get("default") == "testpypi"
    assert set(target.get("options") or []) == {"testpypi", "pypi"}

    jobs = data.get("jobs") or {}
    for job_id in ("build", "publish-testpypi", "publish-pypi"):
        assert job_id in jobs, f"missing job {job_id}"

    build = jobs["build"]
    runs = "\n".join(_ci_step_run_texts(build))
    assert "uv build" in runs
    assert "twine check" in runs

    testpypi = jobs["publish-testpypi"]
    assert testpypi.get("environment") == "testpypi"
    test_if = str(testpypi.get("if") or "")
    assert "release" in test_if
    assert "testpypi" in test_if
    test_perms = testpypi.get("permissions") or {}
    assert test_perms.get("id-token") == "write"

    prod = jobs["publish-pypi"]
    assert prod.get("environment") == "pypi"
    prod_if = str(prod.get("if") or "")
    assert "pypi" in prod_if
    assert "workflow_dispatch" in prod_if
    prod_perms = prod.get("permissions") or {}
    assert prod_perms.get("id-token") == "write"

    bump = jobs["bump-homebrew"]
    assert bump.get("needs") == "publish-pypi" or bump.get("needs") == ["publish-pypi"]
    assert bump.get("uses") == "./.github/workflows/homebrew-tap.yml"
    assert str((bump.get("with") or {}).get("bump")).lower() in {"true", "yes", "1"}
    bump_if = str(bump.get("if") or "")
    assert "pypi" in bump_if
    bump_secrets = bump.get("secrets") or {}
    assert bump_secrets != "inherit"
    assert "HOMEBREW_TAP_TOKEN" in bump_secrets


def test_publish_pypi_yml_pins_actions_to_shas() -> None:
    """ADR-0074: publish-pypi.yml pins all third-party Actions (incl. pypa/gh-action-pypi-publish)."""
    text = (WORKFLOWS / "publish-pypi.yml").read_text(encoding="utf-8")
    sha_40 = re.compile(r"@[0-9a-f]{40}")
    for line in text.splitlines():
        code = line.split("#", 1)[0]
        if "uses:" not in code or "docker://" in code:
            continue
        if "./.github/workflows/" in code:
            continue
        if not any(
            p in code
            for p in (
                "actions/",
                "github/",
                "astral-sh/",
                "pypa/gh-action-pypi-publish@",
            )
        ):
            continue
        assert sha_40.search(code), (
            f"expected full commit SHA in uses line: {line.strip()!r}"
        )


def test_native_packages_workflow_present_and_valid() -> None:
    """#1437 / #1408: nfpm CI build + release attach (wheelhouse payload)."""
    data = _load_workflow("native-packages.yml")
    assert data.get("name") == "Native packages"
    on = data.get("on") or {}
    assert "workflow_dispatch" in on
    assert "pull_request" in on
    assert "release" in on
    env = data.get("env") or {}
    assert env.get("WHEELHOUSE_TAG") == "wheelhouse-x86-64-v1-2026-07-29"
    assert env.get("UV_PYTHON") == "3.14.6+freethreaded"
    assert env.get("NFPM_VERSION") == "2.47.0"
    assert env.get("DISABLE_SQLALCHEMY_CEXT") == "1"
    assert re.fullmatch(r"[0-9a-f]{64}", str(env.get("NFPM_SHA256") or ""))
    assert re.fullmatch(r"[0-9a-f]{64}", str(env.get("UV_SHA256") or ""))

    jobs = data.get("jobs") or {}
    assert "build-deb-rpm" in jobs
    assert "smoke-deb" in jobs
    assert "smoke-rpm" in jobs
    assert "attach-release" in jobs
    build = jobs["build-deb-rpm"]
    runs = "\n".join(_ci_step_run_texts(build))
    assert "native-nfpm-populate-staging.sh" in runs
    assert "nfpm package" in runs
    assert "--packager" in runs
    assert "for packager in deb rpm apk archlinux" in runs
    assert "refusing to package placeholder" in runs
    assert "native_package_release.py" in runs
    assert "normalize-apk" in runs
    assert "EXTERNALLY-MANAGED" in runs

    smoke_deb = jobs["smoke-deb"]
    assert "debian:bookworm" in str(smoke_deb.get("container") or "")
    smoke_deb_runs = "\n".join(_ci_step_run_texts(smoke_deb))
    assert "-m data_boar --version" in smoke_deb_runs
    assert "EXTERNALLY-MANAGED" in smoke_deb_runs
    assert "sqlalchemy" in smoke_deb_runs
    # bookworm-slim /bin/sh is dash — install step must use bash for pipefail.
    deb_steps = smoke_deb.get("steps") or []
    launcher_steps = [
        s
        for s in deb_steps
        if isinstance(s, dict) and "apt install .deb" in str(s.get("name") or "")
    ]
    assert launcher_steps, "expected apt install .deb step"
    assert launcher_steps[0].get("shell") == "bash"

    smoke_rpm = jobs["smoke-rpm"]
    assert "rockylinux:9" in str(smoke_rpm.get("container") or "")
    smoke_rpm_runs = "\n".join(_ci_step_run_texts(smoke_rpm))
    assert "-m data_boar --version" in smoke_rpm_runs
    assert "EXTERNALLY-MANAGED" in smoke_rpm_runs
    assert "sqlalchemy" in smoke_rpm_runs
    attach = jobs["attach-release"]
    assert attach.get("if") == "github.event_name == 'release'"
    attach_runs = "\n".join(_ci_step_run_texts(attach))
    assert "gh release upload" in attach_runs
    assert "SHA256SUMS" in attach_runs
    assert "merge-manifest" in attach_runs
    assert "native_package_release.py" in attach_runs
    assert "Refusing to clobber with an empty stub" in attach_runs
    assert attach_runs.index("gh release download") < attach_runs.rindex(
        "gh release upload"
    )
    attach_env_keys = []
    for step in attach.get("steps") or []:
        if isinstance(step, dict):
            attach_env_keys.extend((step.get("env") or {}).keys())
    assert "NATIVE_PACKAGE_GPG_PRIVATE_KEY" not in attach_env_keys
    attach_checkout = [
        s
        for s in (attach.get("steps") or [])
        if isinstance(s, dict) and "actions/checkout@" in str(s.get("uses") or "")
    ]
    assert attach_checkout, "attach-release must checkout a trusted helper"
    assert attach_checkout[0].get("with", {}).get("ref") == (
        "${{ github.event.repository.default_branch }}"
    )

    sign = jobs["sign-release-sums"]
    assert sign.get("if") == "github.event_name == 'release'"
    assert sign.get("needs") == ["attach-release"]
    sign_dump = yaml.dump(sign)
    assert "NATIVE_PACKAGE_GPG_PRIVATE_KEY" in sign_dump
    sign_checkout = [
        s
        for s in (sign.get("steps") or [])
        if isinstance(s, dict) and "actions/checkout@" in str(s.get("uses") or "")
    ]
    assert sign_checkout, "sign-release-sums must checkout the default branch"
    assert sign_checkout[0].get("with", {}).get("ref") == (
        "${{ github.event.repository.default_branch }}"
    )
    sign_runs = "\n".join(_ci_step_run_texts(sign))
    assert "SHA256SUMS.asc" in sign_runs
    rpm_steps = smoke_rpm.get("steps") or []
    rpm_launcher = [
        s
        for s in rpm_steps
        if isinstance(s, dict) and "dnf install .rpm" in str(s.get("name") or "")
    ]
    assert rpm_launcher, "expected dnf install .rpm step"
    assert rpm_launcher[0].get("shell") == "bash"


def test_void_xbps_workflow_present_and_valid() -> None:
    """#1404: generated overlay check + xbps-src show in Void containers."""
    data = _load_workflow("void-xbps.yml")
    assert data.get("name") == "Void xbps"
    on = data.get("on") or {}
    assert "workflow_dispatch" in on
    assert "pull_request" in on
    jobs = data.get("jobs") or {}
    assert "generated-check" in jobs
    assert "xbps-src-show" in jobs
    check_runs = "\n".join(_ci_step_run_texts(jobs["generated-check"]))
    assert "generate_void_xbps_packages.py --check" in check_runs
    assert "test_void_xbps_foundation.py" in check_runs
    show = jobs["xbps-src-show"]
    show_runs = "\n".join(_ci_step_run_texts(show))
    assert "./xbps-src show data-boar" in show_runs
    assert "/bin/sh -c" in show_runs
    inner = show_runs.split("/bin/sh -c", 1)[1]
    assert "set -eu" in inner
    assert "set -euo pipefail" not in inner
    assert "-o pipefail" not in inner
    assert "xbps-install -y git bash util-linux shadow" in inner
    assert "command -v bash" in inner
    assert "command -v getopt" in inner
    assert "command -v useradd" in inner
    assert "command -v runuser" in inner
    assert "useradd -m -U builder" in inner
    assert "runuser -u builder -- ./xbps-src show data-boar" in inner
    assert "void-glibc" in str(show.get("strategy") or "")
    assert "void-musl" in str(show.get("strategy") or "")
    text = (WORKFLOWS / "void-xbps.yml").read_text(encoding="utf-8")
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


def test_homebrew_tap_workflow_present_and_valid() -> None:
    """#1425: macos-14 brew audit --strict --new plus install/test; PyPI bump job."""
    data = _load_workflow("homebrew-tap.yml")
    assert data.get("name") == "Homebrew tap"
    on = data.get("on") or {}
    assert "pull_request" in on
    assert "workflow_dispatch" in on
    assert "workflow_call" in on
    jobs = data.get("jobs") or {}
    assert "formula-check" in jobs
    assert "brew-macos" in jobs
    assert "bump-formula" in jobs
    macos = jobs["brew-macos"]
    assert macos.get("runs-on") == "macos-14"
    macos_runs = "\n".join(_ci_step_run_texts(macos))
    assert "brew audit --strict --new" in macos_runs
    assert "brew install" in macos_runs
    assert "brew test" in macos_runs
    bump = jobs["bump-formula"]
    bump_runs = "\n".join(_ci_step_run_texts(bump))
    assert "homebrew_formula_bump.py --write" in bump_runs
    assert "HOMEBREW_TAP_TOKEN" in bump_runs
    text = (WORKFLOWS / "homebrew-tap.yml").read_text(encoding="utf-8")
    assert "enable-cache: true" not in text
    assert "enable-cache: false" in text
    on_call = on.get("workflow_call") or {}
    call_secrets = on_call.get("secrets") or {}
    assert "HOMEBREW_TAP_TOKEN" in call_secrets
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


def test_native_packages_yml_pins_actions_to_shas() -> None:
    """#1437 / ADR-0005: native-packages.yml pins third-party Actions to full SHAs."""
    text = (WORKFLOWS / "native-packages.yml").read_text(encoding="utf-8")
    sha_40 = re.compile(r"@[0-9a-f]{40}")
    for line in text.splitlines():
        code = line.split("#", 1)[0]
        if "uses:" not in code or "docker://" in code:
            continue
        # Local reusable workflows / composite actions are not third-party pins.
        if "./.github/workflows/" in code or "./.github/actions/" in code:
            continue
        if not any(p in code for p in ("actions/", "github/", "astral-sh/")):
            continue
        assert sha_40.search(code), (
            f"expected full commit SHA in uses line: {line.strip()!r}"
        )


def test_native_packages_build_job_pins_ubuntu_apt_mirror() -> None:
    """build-deb-rpm is ubuntu-latest: same azure.archive flake as #1648 / #1702."""
    data = _load_workflow("native-packages.yml")
    build = data["jobs"]["build-deb-rpm"]
    uses = [
        str(s.get("uses") or "")
        for s in (build.get("steps") or [])
        if isinstance(s, dict)
    ]
    assert any("./.github/actions/install-libmariadb-dev" in u for u in uses)
    runs = _ci_step_run_texts(build)
    assert not any("apt-get update" in r for r in runs)
    assert any(
        "timeout 240 sudo apt-get install" in r and "build-essential" in r for r in runs
    )


def test_native_packages_smoke_deb_uses_debian_cdn_not_ubuntu_azure_pin() -> None:
    """smoke-deb runs in debian:bookworm-slim — Ubuntu apt-mirrors pin does not apply."""
    text = (WORKFLOWS / "native-packages.yml").read_text(encoding="utf-8")
    # Assert the documented Debian-CDN policy comment, not a hostname substring
    # (CodeQL py/incomplete-url-sanitization flags `in text` on URL-like hosts).
    assert "Do NOT copy the #1648 ubuntu azure.archive pin" in text
    assert "debian.sources" in text
    data = _load_workflow("native-packages.yml")
    smoke = data["jobs"]["smoke-deb"]
    assert "debian:bookworm-slim" in str(smoke.get("container") or "")
    dump = yaml.dump(smoke)
    assert "apt-mirrors.txt" not in dump
    runs = _ci_step_run_texts(smoke)
    assert any("apt-get update" in r for r in runs)
