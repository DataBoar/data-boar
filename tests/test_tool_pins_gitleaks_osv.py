"""Regression: pinned gitleaks/osv-scanner tool bootstrap (#1933)."""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOL_PINS = REPO_ROOT / "scripts" / "tool-pins.sh"


def test_tool_pins_gitleaks_and_osv_constants() -> None:
    text = TOOL_PINS.read_text(encoding="utf-8")
    assert 'DB_GITLEAKS_VERSION="${DB_GITLEAKS_VERSION:-8.30.1}"' in text
    assert "88f91962aa2f93ac6ab281d553b9e125f5197bbbce38f9f2437f7299c32e5509" in text
    assert 'DB_OSV_SCANNER_VERSION="${DB_OSV_SCANNER_VERSION:-2.6.0}"' in text
    assert "ca69b3d3cd08f889a49dc0a383122f71cc528b83803671df5fd874d97485b108" in text
    assert re.search(r"security/gitleaks\.toml", text)


def test_strict_gitleaks_scripts_present() -> None:
    assert (REPO_ROOT / "scripts/run-gitleaks-strict.sh").is_file()
    assert (REPO_ROOT / "scripts/run-osv-scanner.sh").is_file()
    assert (REPO_ROOT / "scripts/db-tool-bootstrap.sh").is_file()
    strict = (REPO_ROOT / "scripts/run-gitleaks-strict.sh").read_text(encoding="utf-8")
    assert "--ignore-gitleaks-allow" in strict
    assert "rm -f .gitleaks.toml" in strict
