"""Guard: public AGENTS.md must not teach the sudo $HOME reproduction (#384)."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
AGENTS_MD = REPO_ROOT / "AGENTS.md"
NFS_ENSURE = REPO_ROOT / "scripts" / "labop-nfs-server-ensure.sh"
SMB_ENSURE = REPO_ROOT / "scripts" / "labop-smb-server-ensure.sh"


def test_agents_md_omits_home_root_reproduction() -> None:
    text = AGENTS_MD.read_text(encoding="utf-8")
    assert "Open: `$HOME=root` bug" not in text
    assert "SHARE_PATH=${HOME}" not in text
    assert "Documents/<scan-corpus>" not in text
    assert "getent" in text
    assert "SUDO_USER" in text


def test_agents_md_does_not_hardcode_current_last_adr() -> None:
    """#383: next ADR id comes from disk, not a stale number in AGENTS.md."""
    text = AGENTS_MD.read_text(encoding="utf-8")
    assert "Current last:" not in text
    assert "ls docs/adr/ADR-*.md" in text
    ritual = (REPO_ROOT / ".cursor" / "rules" / "doc-hubs-sync-ritual.mdc").read_text(
        encoding="utf-8"
    )
    assert "updated **“Current last ADR”** line in **`AGENTS.md`**" not in ritual


def test_labop_ensure_scripts_resolve_operator_home_via_getent() -> None:
    nfs = NFS_ENSURE.read_text(encoding="utf-8")
    smb = SMB_ENSURE.read_text(encoding="utf-8")
    assert "getent passwd" in nfs
    assert "getent passwd" in smb
    assert "_OP_HOME" in nfs
    assert "_OP_HOME" in smb
    for text in (nfs, smb):
        assert 'FW_STATE_FILE="${HOME}' not in text
        assert "FW_STATE_FILE='${HOME}" not in text
