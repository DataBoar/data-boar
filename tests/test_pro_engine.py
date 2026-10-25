"""Tests for ``pro.engine`` wrapper behavior with fallback mode."""

from __future__ import annotations

from pro.engine import ProScanner, RUST_AVAILABLE


def test_pro_scanner_fallback_filters_candidates_without_rust() -> None:
    if RUST_AVAILABLE:
        # Contract is still valid with Rust; fallback-specific assertion is not.
        return
    scanner = ProScanner()
    out = scanner.scan(["clean row", "cpf 390.533.447-05", "mail x@example.test"])
    assert out == ["cpf 390.533.447-05", "mail x@example.test"]


def test_pro_scanner_uses_callable_path() -> None:
    called: dict[str, object] = {}

    def _deep(rows: list[str]) -> dict[str, object]:
        called["rows"] = rows
        return {"ok": True, "rows": rows}

    def _legacy(rows: list[str]) -> dict[str, object]:
        called["rows"] = rows
        return {"ok": True, "rows": rows}

    scanner = ProScanner(deep_scan_fn=_deep, legacy_scan_fn=_legacy)
    out = scanner.scan(["clean row", "cpf 390.533.447-05"])
    assert isinstance(out, dict)
    assert out["ok"] is True
    assert "rows" in called
