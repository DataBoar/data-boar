"""Operator-gated PR attestation (#1709) — GATE_FILES reuse + latest-comment SSHSIG."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

import scripts.gate_change_tripwire as gct
import scripts.gate_trailer_attest as gta
import scripts.operator_gated_pr_guard as ogp

from tests.test_gate_trailer_attest import GOLDEN_COMMIT, _commit_available

_FAKE_HEAD = "0" * 40


def test_needs_attestation_gate_file_not_docs() -> None:
    assert ogp.needs_attestation(["SECURITY.md"], []) is False
    assert ogp.needs_attestation([".github/workflows/ci.yml"], []) is True
    assert ogp.needs_attestation(["README.md"], ["operator-gated"]) is True
    assert ogp.needs_attestation(["README.md"], ["unrelated"]) is False


def test_collect_pulls_api_paths_includes_previous_filename_on_rename() -> None:
    paths = ogp.collect_pulls_api_paths(
        [
            {
                "filename": "docs/unlisted.md",
                "previous_filename": "scripts/gatekeeper_audit.py",
                "status": "renamed",
            }
        ]
    )
    assert paths == ["docs/unlisted.md", "scripts/gatekeeper_audit.py"]
    assert ogp.needs_attestation(paths, []) is True


def test_collect_pulls_api_paths_includes_previous_filename_on_copy() -> None:
    paths = ogp.collect_pulls_api_paths(
        [
            {
                "filename": "tmp/copy.yml",
                "previous_filename": ".github/workflows/ci.yml",
                "status": "copied",
            }
        ]
    )
    assert ".github/workflows/ci.yml" in paths
    assert ogp.needs_attestation(paths, []) is True


def test_collect_pulls_api_paths_modified_uses_filename_only() -> None:
    paths = ogp.collect_pulls_api_paths(
        [{"filename": "scripts/gatekeeper_audit.py", "status": "modified"}]
    )
    assert paths == ["scripts/gatekeeper_audit.py"]
    assert ogp.needs_attestation(paths, []) is True


def test_gate_files_list_is_not_duplicated() -> None:
    assert ogp.GATE_FILES is gct.GATE_FILES
    assert ".github/workflows/ci.yml" in ogp.GATE_FILES
    assert ".github/workflows/operator-gated-pr-guard.yml" in ogp.GATE_FILES
    assert "scripts/operator_gated_pr_guard.py" in ogp.GATE_FILES
    assert "scripts/gate_trailer_attest.py" in ogp.GATE_FILES
    assert "docs/adr/allowed_signers" in ogp.GATE_FILES
    assert "scripts/__init__.py" in ogp.GATE_FILES


def test_bound_pr_payload_includes_pr_and_head() -> None:
    line = "Gate-Change-Approved-By: @FabioLeitao"
    payload = gta.bound_pr_payload_bytes(line, 1832, "Ab" + "c" * 38)
    text = payload.decode("utf-8")
    assert text.startswith(line)
    assert "PR: 1832" in text
    assert f"Head: {'ab' + 'c' * 38}" in text
    assert not payload.endswith(b"\n")
    assert payload != gta.trailer_payload_bytes(line)


def test_bound_pr_payload_rejects_short_sha() -> None:
    with pytest.raises(ValueError, match="40"):
        gta.bound_pr_payload_bytes("Gate-Change-Approved-By: @FabioLeitao", 1, "abc")


def test_trailer_without_sshsig_is_not_approval() -> None:
    ok, msg = ogp.latest_comment_approves(
        "Gate-Change-Approved-By: @FabioLeitao\n\nlooks official\n",
        pr_number=1832,
        head_sha=_FAKE_HEAD,
    )
    assert ok is False
    assert "SSHSIG" in msg or "trailer" in msg.lower()


def test_empty_or_unrelated_latest_comment_fails() -> None:
    ok, _ = ogp.latest_comment_approves("", pr_number=1, head_sha=_FAKE_HEAD)
    assert ok is False
    ok2, _ = ogp.latest_comment_approves("LGTM", pr_number=1, head_sha=_FAKE_HEAD)
    assert ok2 is False


def test_golden_commit_body_is_not_replayable_as_pr_approval() -> None:
    """SSHSIG over trailer-only must not attest an unbound PR comment (#1832)."""
    if not _commit_available(GOLDEN_COMMIT):
        return
    proc = subprocess.run(
        ["git", "show", "-s", "--format=%B", GOLDEN_COMMIT],
        capture_output=True,
        text=True,
        check=True,
    )
    ok, _msg = ogp.latest_comment_approves(
        proc.stdout, pr_number=1832, head_sha=_FAKE_HEAD
    )
    assert ok is False


def test_cli_changed_from_file_and_labels_file(tmp_path: Path) -> None:
    paths = tmp_path / "changed.txt"
    labels = tmp_path / "labels.txt"
    paths.write_text("docs/USAGE.md\n", encoding="utf-8")
    labels.write_text("unrelated\n", encoding="utf-8")
    assert (
        ogp.main(
            [
                "--changed-from-file",
                str(paths),
                "--labels-file",
                str(labels),
            ]
        )
        == 0
    )


def test_cli_out_of_scope_exits_zero() -> None:
    assert ogp.main(["--changed", "docs/USAGE.md", "--labels", ""]) == 0


def test_cli_in_scope_without_pr_head_exits_two() -> None:
    assert ogp.main(["--changed", ".github/workflows/ci.yml", "--labels", ""]) == 2


def test_cli_in_scope_without_message_exits_one() -> None:
    assert (
        ogp.main(
            [
                "--changed",
                ".github/workflows/ci.yml",
                "--labels",
                "",
                "--pr",
                "1832",
                "--head",
                _FAKE_HEAD,
            ]
        )
        == 1
    )
