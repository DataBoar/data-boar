"""Tests for ``pro.orchestrator`` and worker entrypoint."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, text

from pro.engine import process_chunk_worker
from pro.orchestrator import ProOrchestrator


def _fixture_db(path: Path) -> None:
    eng = create_engine(f"sqlite:///{path}")
    with eng.begin() as conn:
        conn.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY, notes TEXT)"))
        conn.execute(
            text(
                "INSERT INTO users (notes) VALUES "
                "('cpf 390.533.447-05'),"
                "('clean row'),"
                "('mail sec@example.test'),"
                "('card 4111 1111 1111 1111'),"
                "('invalid card 4111 1111 1111 1112')"
            )
        )
    eng.dispose()


def test_process_chunk_worker_filters_candidates() -> None:
    out = process_chunk_worker(
        [
            "clean row",
            "cpf 390.533.447-05",
            "mail sec@example.test",
            "card 4111 1111 1111 1111",
            "invalid card 4111 1111 1111 1112",
        ]
    )
    assert "cpf 390.533.447-05" in out
    assert "mail sec@example.test" in out
    assert "card 4111 1111 1111 1111" in out
    assert "invalid card 4111 1111 1111 1112" not in out


def test_pro_orchestrator_run_discovery_returns_findings(tmp_path: Path) -> None:
    db = tmp_path / "pro_orchestrator.db"
    state_file = tmp_path / ".boar_state.json"
    _fixture_db(db)

    orchestrator = ProOrchestrator(
        f"sqlite:///{db}",
        max_workers=2,
        batch_limit=100,
        checkpoint_file=str(state_file),
    )
    try:
        findings = orchestrator.run_discovery("users")
    finally:
        orchestrator.db.engine.dispose()

    joined = " | ".join(findings)
    assert "390.533.447-05" in joined
    assert "sec@example.test" in joined
    assert "4111 1111 1111 1111" in joined


def test_pro_orchestrator_resumes_from_checkpoint(tmp_path: Path) -> None:
    db = tmp_path / "pro_orchestrator.db"
    state_file = tmp_path / ".boar_state.json"
    _fixture_db(db)

    first = ProOrchestrator(
        f"sqlite:///{db}",
        max_workers=2,
        batch_limit=2,
        checkpoint_file=str(state_file),
    )
    try:
        first_findings = first.run_discovery("users")
    finally:
        first.db.engine.dispose()

    second = ProOrchestrator(
        f"sqlite:///{db}",
        max_workers=2,
        batch_limit=2,
        checkpoint_file=str(state_file),
    )
    try:
        second_findings = second.run_discovery("users")
    finally:
        second.db.engine.dispose()

    assert first_findings
    assert second_findings == []
