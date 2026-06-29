"""Gate trailer decorative SSH attestation (ADR-0056 file namespace)."""

from __future__ import annotations

import subprocess

import scripts.gate_trailer_attest as gta

GOLDEN_COMMIT = "888f175e61a668256d345f278c71791c0e6bd66a"


def _commit_available(sha: str) -> bool:
    proc = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", sha],
        capture_output=True,
        check=False,
    )
    return proc.returncode == 0


def test_extract_trailer_and_signature_from_golden_commit():
    if not _commit_available(GOLDEN_COMMIT):
        return
    proc = subprocess.run(
        ["git", "show", "-s", "--format=%B", GOLDEN_COMMIT],
        capture_output=True,
        text=True,
        check=True,
    )
    body = proc.stdout
    line = gta.extract_trailer_line(body)
    assert line is not None
    assert line.startswith("Gate-Change-Approved-By:")
    sig = gta.extract_signature_pem(body)
    assert sig is not None
    assert "BEGIN SSH SIGNATURE" in sig


def test_verify_golden_commit_decorative_signature():
    if not _commit_available(GOLDEN_COMMIT):
        return
    code = gta.main(["verify", "--commit", GOLDEN_COMMIT])
    assert code == 0


def test_trailer_payload_has_no_trailing_newline():
    line = "Gate-Change-Approved-By: @FabioLeitao"
    payload = gta.trailer_payload_bytes(line)
    assert not payload.endswith(b"\n")
    assert payload == line.encode("utf-8")
