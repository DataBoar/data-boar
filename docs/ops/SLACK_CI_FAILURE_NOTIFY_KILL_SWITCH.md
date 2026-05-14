# Slack CI failure notify — operator kill-switch

The workflow [`.github/workflows/slack-ci-failure-notify.yml`](../../.github/workflows/slack-ci-failure-notify.yml)
posts a short message to Slack when one of the watched workflows
(`CI`, `Semgrep`, `SBOM`, `Dependabot requirements.txt sync`) finishes with
`conclusion == 'failure'`.

While iterating on a known-broken state on `main` (or any watched branch),
the constant pings become noise. Removing the secret
`SLACK_WEBHOOK_URL` would silence the failure pings, but it would *also*
disable every other Slack workflow that shares it (operator-ping,
PR-merged, release-published, ops-digest). That is too blunt.

## Kill-switch (no code change to mute)

The detect step reads a repository **Variable** (not Secret):

| Variable name             | Truthy values (case-insensitive) | Effect                                |
| ------------------------- | -------------------------------- | ------------------------------------- |
| `MUTE_CI_FAILURE_NOTIFY`  | `true`, `1`, `yes`, `on`         | Detect step writes `present=false`, downstream POST step skips, the run finishes green. |
| `MUTE_CI_FAILURE_NOTIFY`  | unset / empty / anything else    | Default behavior — POST when the secret is configured. |

Because the gate is at *step* level (not job-level `if: secrets.*`), GitHub
does not record a phantom failed run with zero jobs (same posture used by
the `sonar` job in `ci.yml` and documented in
[`docs/ops/OPERATOR_NOTIFICATION_CHANNELS.md`](OPERATOR_NOTIFICATION_CHANNELS.md)).

## How to flip it (GitHub UI)

1. Open the repository on GitHub → **Settings** → **Secrets and variables** → **Actions** → **Variables** tab.
2. **Mute:** click *New repository variable*, set `Name = MUTE_CI_FAILURE_NOTIFY`, `Value = true`, save.
3. **Un-mute:** delete the variable, or set its value to `false` / empty.

The change takes effect on the *next* triggered run; in-flight runs that
already started detection complete with their original setting.

## Why a Variable, not a Secret

GitHub Actions exposes Variables in step logs, which is useful here: the
detect step prints `MUTE_CI_FAILURE_NOTIFY=<value> -> skipping Slack POST
(operator kill-switch).` so the audit trail is obvious in the run log.
Secrets get redacted to `***` and would hide the reason for skipping.

## Regression guard

`tests/test_github_workflows.py::test_slack_ci_failure_notify_has_operator_kill_switch`
asserts the detect step still wires `vars.MUTE_CI_FAILURE_NOTIFY` and
short-circuits cleanly. If you refactor the workflow, keep that contract.

## Related

- [`OPERATOR_NOTIFICATION_CHANNELS.md`](OPERATOR_NOTIFICATION_CHANNELS.md) — channels A/B/C and Slack message format.
- [`.cursor/rules/operator-notification-channels.mdc`](../../.cursor/rules/operator-notification-channels.mdc) — agent rule.
