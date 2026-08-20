"""Give-back nfpm example for upstream podman-tui (#1424)."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = REPO_ROOT / "docs/ops/giveback/podman-tui/nfpm.yaml.example"


def test_podman_tui_nfpm_example_has_license_file_and_named_maintainer() -> None:
    text = EXAMPLE.read_text(encoding="utf-8")
    assert "unofficial build" not in text.lower()
    assert "Full Name <you@example.com>" in text
    assert "usr/share/doc/podman-tui/copyright" in text
    assert "Apache-2.0" in text
    apk_block = text.split("apk:", 1)[1]
    assert "podman" in apk_block.split("archlinux:", 1)[0]
