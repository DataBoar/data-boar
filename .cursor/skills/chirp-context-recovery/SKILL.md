---
name: chirp-context-recovery
description: Recover and reconcile canonical project context across Codex, Claude Code, Cursor, tmux, GitHub, local repositories, and the Obsidian vault. Use when the operator says “CHIRP/chirp”, resumes after context loss, asks for cross-tool status, or agents disagree about work, ownership, or completion.
---

# CHIRP Context Recovery

CHIRP means **Cross-tool Hub-Indexed Recall Pattern**. It is a read-first
handoff protocol: locate the canonical source, verify current state in the
relevant tool or host, reconcile discrepancies, and return a compact,
evidence-backed status without treating model memory as authoritative.

## Workflow

### 1. Resolve context

- Identify the repository, branch, host, session, issue/PR, and tool in scope.
- Read the relevant canonical hub before deep-diving. For Data Boar, start with
  `AGENTS.md`, `docs/hubs/INDEX.md`, the applicable `docs/ops/` hub, and private
  vault material when the task is commercial, homelab, or cross-agent.
- Treat GitHub, local checkout, tmux, vault, and agent output as separate
  evidence surfaces; do not merge them mentally without checking.

### 2. Gather evidence read-first

- Use the narrowest reliable source: `git status/log`, GitHub issue/PR/check
  data, vault issue/plan, or `tmux capture-pane`.
- For tmux, capture read-only panes; never send keys merely to inspect state.
  For SSH, read the host access runbook first and keep host-specific details
  out of tracked output.
- Record concrete anchors: commit SHA, PR/issue number, URL, host/session,
  command result, and observation time when relevant.

### 3. Reconcile, do not average

- Separate **observed**, **reported**, **planned**, **stale**, and **blocked**.
- Prefer direct current evidence over an agent summary when they conflict.
- Call contradictions out explicitly; do not silently choose a convenient
  narrative.
- Distinguish “command was issued”, “command succeeded”, “artifact exists”,
  “remote state matches”, and “merged/published”.

### 4. Produce the handoff

Return a compact report in this order:

1. **CHIRP status:** one-line state and confidence.
2. **Observed:** verified facts with anchors.
3. **Discrepancies:** conflicts, stale panes, missing logs, or assumptions.
4. **Ownership:** which agent/tool/host currently acts.
5. **Next safe action:** one or two concrete steps, including blockers.

Do not claim completion from a prompt, spinner, or “success” text alone when a
commit, push, CI result, or remote SHA can be checked.

## Boundaries

- CHIRP is not a license to expose secrets, private paths, credentials, raw PII,
  or full chat/session logs.
- Do not create duplicate issues or plans. Update the canonical item or report
  that it is missing.
- Do not write, commit, push, merge, or send tmux input unless the operator
  separately authorizes that action.
- When a source is unavailable, report the technical failure and lower
  confidence; never replace it with generic memory.
