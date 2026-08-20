"""#1385: local check-all must run the same tripwire as CI (ADR-0080).

Lives outside tests/test_gate_change_tripwire.py so this slice does not
touch GATE_FILES (no Gate-Change-Approved-By trailer).
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_check_all_wrappers_invoke_tripwire_and_fail_closed() -> None:
    sh = (ROOT / "scripts" / "check-all.sh").read_text(encoding="utf-8")
    ps1 = (ROOT / "scripts" / "check-all.ps1").read_text(encoding="utf-8")
    for text in (sh, ps1):
        assert "gate_change_tripwire.py" in text
        assert "--base origin/main" in text
        assert "ABORTED by gate_change_tripwire" in text
    assert "gate_change_tripwire.py --base origin/main || true" not in sh
    assert "gate_change_tripwire.py --base origin/main) || true" not in sh
    # `if ! cmd; then exit "$?"; fi` exits 0 (successful negation). The
    # tripwire must use `cmd || { rc=$?; ...; exit "$rc"; }`.
    assert (
        'if ! uv run python "$REPO_ROOT/scripts/gate_change_tripwire.py" --base origin/main; then'
        not in sh
    )
    assert (
        'uv run python "$REPO_ROOT/scripts/gate_change_tripwire.py" --base origin/main || {'
        in sh
    )
    assert 'exit "$rc"' in sh
