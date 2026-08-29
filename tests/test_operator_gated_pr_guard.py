"""Operator-gated PR attestation (#1709) — GATE_FILES reuse + latest-comment SSHSIG."""

from __future__ import annotations

import subprocess

import scripts.gate_change_tripwire as gct
import scripts.operator_gated_pr_guard as ogp

from tests.test_gate_trailer_attest import GOLDEN_COMMIT, _commit_available


def test_needs_attestation_gate_file_not_docs() -> None:
    assert ogp.needs_attestation(["SECURITY.md"], []) is False
    assert ogp.needs_attestation([".github/workflows/ci.yml"], []) is True
    assert ogp.needs_attestation(["README.md"], ["operator-gated"]) is True
    assert ogp.needs_attestation(["README.md"], ["unrelated"]) is False


def test_gate_files_list_is_not_duplicated() -> None:
    assert ogp.GATE_FILES is gct.GATE_FILES
    assert ".github/workflows/ci.yml" in ogp.GATE_FILES


def test_trailer_without_sshsig_is_not_approval() -> None:
    ok, msg = ogp.latest_comment_approves(
        "Gate-Change-Approved-By: @FabioLeitao\n\nlooks official\n"
    )
    assert ok is False
    assert "SSHSIG" in msg or "trailer" in msg.lower()


def test_empty_or_unrelated_latest_comment_fails() -> None:
    ok, _ = ogp.latest_comment_approves("")
    assert ok is False
    ok2, _ = ogp.latest_comment_approves("LGTM")
    assert ok2 is False


def test_valid_sshsig_from_golden_commit_body() -> None:
    if not _commit_available(GOLDEN_COMMIT):
        return
    proc = subprocess.run(
        ["git", "show", "-s", "--format=%B", GOLDEN_COMMIT],
        capture_output=True,
        text=True,
        check=True,
    )
    ok, msg = ogp.latest_comment_approves(proc.stdout)
    assert ok is True, msg


def test_cli_out_of_scope_exits_zero() -> None:
    assert ogp.main(["--changed", "docs/USAGE.md", "--labels", ""]) == 0


def test_cli_in_scope_without_message_exits_one() -> None:
    assert ogp.main(["--changed", ".github/workflows/ci.yml", "--labels", ""]) == 1
