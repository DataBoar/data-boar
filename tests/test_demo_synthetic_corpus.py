"""Synthetic demo corpus guarantees (#1447 demo v0, #2176).

The public demo scans ``core.demo.synthetic_corpus`` output (scenarios happy,
unhappy and false_positive). These tests pin two properties:

* every checksum-valid CPF/CNPJ in the demo corpus comes from the declared
  synthetic pools (nothing random can collide with a real number by accident);
* scenario 4 (false_positive) is deterministic and contains no checksum-valid
  CPF/CNPJ, so the checksum-gated detectors never fire on it.
"""

from __future__ import annotations

import contextlib
import io
import re
from pathlib import Path

from connectors.filesystem_connector import FilesystemConnector
from core.brazilian_cpf import (
    cnpj_checksum_valid,
    cpf_checksum_valid,
    normalize_cnpj_digits,
    normalize_cpf_digits,
)
from core.demo import synthetic_corpus as sc
from core.demo.runtime import _DEFAULT_SCENARIOS
from core.scanner import DataScanner

_CPF_TOKEN = re.compile(r"(?<!\d)\d{3}\.?\d{3}\.?\d{3}-?\d{2}(?!\d)")
_CNPJ_TOKEN = re.compile(r"(?<!\d)\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}(?!\d)")
_EMAIL_TOKEN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_TEXT_SUFFIXES = {".txt", ".csv", ".json"}


def _generate(base: Path, scenarios: list[str]) -> Path:
    with contextlib.redirect_stdout(io.StringIO()):
        sc.generate_corpus(base, scenarios)
    return base


def _text_files(root: Path) -> list[Path]:
    return sorted(
        p for p in root.rglob("*") if p.is_file() and p.suffix in _TEXT_SUFFIXES
    )


def _read(path: Path) -> str:
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def _valid_cpfs(text: str) -> set[str]:
    out = set()
    for m in _CPF_TOKEN.finditer(text):
        d = normalize_cpf_digits(m.group())
        if d and cpf_checksum_valid(d):
            out.add(d)
    return out


def _valid_cnpjs(text: str) -> set[str]:
    out = set()
    for m in _CNPJ_TOKEN.finditer(text):
        d = normalize_cnpj_digits(m.group())
        if d and cnpj_checksum_valid(d):
            out.add(d)
    return out


class _CaptureDB:
    def __init__(self) -> None:
        self.findings: list[dict] = []
        self.failures: list[tuple[str, str, str]] = []

    def save_failure(self, target_name: str, reason: str, details: str) -> None:
        self.failures.append((target_name, reason, details))

    def save_finding(self, *args, **kwargs) -> None:
        self.findings.append(kwargs)


def test_false_positive_scenario_is_deterministic(tmp_path):
    """#2176: two generations of scenario 4 must be byte-identical."""
    a = _generate(tmp_path / "a", ["false_positive"]) / "4_false_positive"
    b = _generate(tmp_path / "b", ["false_positive"]) / "4_false_positive"
    files_a = {p.name: p.read_bytes() for p in a.iterdir()}
    files_b = {p.name: p.read_bytes() for p in b.iterdir()}
    assert files_a == files_b


def test_false_positive_scenario_has_no_checksum_valid_identifier(tmp_path):
    """#2176: CPF/CNPJ-shaped tokens in scenario 4 fail Mod-11 by construction."""
    root = _generate(tmp_path, ["false_positive"]) / "4_false_positive"
    for path in _text_files(root):
        text = _read(path)
        assert not _valid_cpfs(text), f"checksum-valid CPF in {path.name}"
        assert not _valid_cnpjs(text), f"checksum-valid CNPJ in {path.name}"


def test_false_positive_scenario_never_triggers_checksum_gated_patterns(tmp_path):
    """#2176: a real filesystem scan of scenario 4 yields no LGPD_CPF/LGPD_CNPJ."""
    root = _generate(tmp_path, ["false_positive"]) / "4_false_positive"
    db = _CaptureDB()
    FilesystemConnector(
        {"name": "demo", "type": "filesystem", "path": str(root), "recursive": True},
        DataScanner(),
        db,
        scan_sqlite_as_db=False,
        sample_limit=5000,
    ).run()
    gated = [
        (f.get("file_name"), f.get("pattern_detected"))
        for f in db.findings
        if re.search(r"\bLGPD_CPF\b|\bLGPD_CNPJ\b", str(f.get("pattern_detected")))
    ]
    assert gated == []


def test_demo_corpus_valid_identifiers_come_only_from_declared_synthetic_pools(
    tmp_path,
):
    """Every checksum-valid CPF/CNPJ and every e-mail in the demo corpus is a
    declared synthetic value (``_CPFS``/``_CNPJS``/``_EMAILS``)."""
    scenarios = [s.strip() for s in _DEFAULT_SCENARIOS.split(",")]
    root = _generate(tmp_path, scenarios)
    pool_cpfs = {normalize_cpf_digits(c) for c in sc._CPFS}
    pool_cnpjs = {normalize_cnpj_digits(c) for c in sc._CNPJS}
    pool_emails = set(sc._EMAILS)
    for path in _text_files(root):
        text = _read(path)
        assert _valid_cpfs(text) <= pool_cpfs, path.name
        assert _valid_cnpjs(text) <= pool_cnpjs, path.name
        assert set(_EMAIL_TOKEN.findall(text)) <= pool_emails, path.name


def test_demo_corpus_manifest_labels_content_as_synthetic(tmp_path):
    """The generated manifest and every scenario folder say the data is synthetic."""
    import json

    scenarios = [s.strip() for s in _DEFAULT_SCENARIOS.split(",")]
    root = _generate(tmp_path, scenarios)
    manifest = json.loads((root / "CORPUS_MANIFEST.json").read_text(encoding="utf-8"))
    assert "synthetic" in manifest["note"].lower()
    for sub in ("1_happy", "2_unhappy", "4_false_positive"):
        assert (root / sub / "EXPECTED.txt").is_file()
