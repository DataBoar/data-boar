"""ADR INVENTORY.txt must list every ADR-*.md with matching SHA-256."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ADR_DIR = REPO / "docs" / "adr"
INVENTORY = ADR_DIR / "INVENTORY.txt"

ROW_RE = re.compile(
    r"^(\d{4}) \| (\w+) \| ([0-9A-F]{64}) \| (ADR-\d{4}-.+\.md) \| ",
    re.MULTILINE,
)


def _file_sha256(path: Path) -> str:
    raw = path.read_text(encoding="utf-8")
    norm = raw.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(norm.encode("utf-8")).hexdigest().upper()


def test_inventory_lists_every_adr_file():
    if not INVENTORY.is_file():
        return
    text = INVENTORY.read_text(encoding="utf-8")
    listed = {m.group(4) for m in ROW_RE.finditer(text)}
    adrs = sorted(ADR_DIR.glob("ADR-*.md"))
    assert adrs, "expected at least one ADR-*.md"
    missing = [p.name for p in adrs if p.name not in listed]
    assert not missing, f"INVENTORY.txt missing rows for: {missing}"


def test_inventory_row_hashes_match_adr_files():
    if not INVENTORY.is_file():
        return
    text = INVENTORY.read_text(encoding="utf-8")
    for m in ROW_RE.finditer(text):
        filename, recorded = m.group(4), m.group(3)
        path = ADR_DIR / filename
        assert path.is_file(), f"inventory references missing file {filename}"
        actual = _file_sha256(path)
        assert actual == recorded, (
            f"stale hash for {filename}: run scripts/inv-adr.ps1 and commit INVENTORY.txt"
        )
