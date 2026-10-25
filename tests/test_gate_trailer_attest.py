"""Gate trailer decorative SSH attestation (ADR-0056 file namespace)."""

from __future__ import annotations

import subprocess
from pathlib import Path

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


def test_sign_uses_openssh_y_sign_syntax_without_verify_identity(monkeypatch, tmp_path):
    key = tmp_path / "attest-key"
    key.write_text("placeholder", encoding="utf-8")
    captured: list[list[str]] = []

    class Completed:
        returncode = 0
        stdout = ""
        stderr = ""

    def fake_run(command, **kwargs):
        captured.append(command)
        signature_path = Path(f"{command[-1]}.sig")
        signature_path.write_text("-----BEGIN SSH SIGNATURE-----\n", encoding="utf-8")
        return Completed()

    monkeypatch.setattr(gta.subprocess, "run", fake_run)
    ok, _ = gta.sign_trailer(
        "Gate-Change-Approved-By: @FabioLeitao",
        key,
    )

    assert ok
    assert captured
    assert "-Y" in captured[0]
    assert "sign" in captured[0]
    assert "-I" not in captured[0]
    assert "-s" not in captured[0]
