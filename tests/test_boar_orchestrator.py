"""Tests for Pro worker logic and ``BoarOrchestrator``."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, text

from core.discovery_orchestrator import BoarOrchestrator
from pro.worker_logic import basic_python_scan


def _fixture_db(path: Path) -> None:
    eng = create_engine(f"sqlite:///{path}")
    with eng.begin() as conn:
        conn.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY, notes TEXT)"))
        conn.execute(
            text(
                "INSERT INTO users (notes) VALUES "
                "('cpf válido 390.533.447-05'),"
                "('clean sem pii'),"
                "('mail dev@example.test'),"
                "('card 4111 1111 1111 1111'),"
                "('invalid card 4111 1111 1111 1112')"
            )
        )
    eng.dispose()


def test_basic_python_scan_filters_luhn_valid_card_only() -> None:
    payloads = [
        "safe text",
        "email ops@example.test",
        "cpf 390.533.447-05",
        "card 4111 1111 1111 1111",
        "invalid card 4111 1111 1111 1112",
    ]
    out = basic_python_scan(payloads)
    assert payloads[1] in out
    assert payloads[2] in out
    assert payloads[3] in out
    assert payloads[4] not in out


def test_boar_orchestrator_collects_pro_chunk_results(tmp_path: Path) -> None:
    db = tmp_path / "orchestrator.db"
    _fixture_db(db)

    orchestrator = BoarOrchestrator(
        f"sqlite:///{db}",
        max_workers=2,
        batch_limit=100,
    )
    try:
        out = orchestrator.run_discovery("users")
    finally:
        orchestrator.db.engine.dispose()

    joined = " | ".join(out)
    assert "390.533.447-05" in joined
    assert "dev@example.test" in joined
    assert "4111 1111 1111 1111" in joined
    assert "4111 1111 1111 1112" not in joined
