"""HMAC tamper-evidence for maturity self-assessment POC rows (SQLite)."""

from __future__ import annotations

from pathlib import Path

from core.database import LocalDBManager
from core.maturity_assessment.integrity import (
    HMAC_VERSION,
    compute_answer_hmac,
    load_integrity_secret_from_config,
    verify_maturity_assessment_rows,
)


def test_compute_answer_hmac_golden_vector_regression():
    """
    Frozen HMAC output: changing canonical payload, algorithm, or HMAC_VERSION must update this test.
    """
    assert HMAC_VERSION == "maturity-answer-hmac-v1"
    got = compute_answer_hmac(
        b"golden-hmac-test-key",
        batch_id="abcd1234",
        locale_slug="en",
        pack_version=2,
        question_id="q_sample",
        answer_text="yes",
    )
    assert got == ("29470dee9272f9a3495dae99329afac9e1056de3cb5e6182e5521f9c629e28dd")
    alt = compute_answer_hmac(
        b"golden-hmac-test-key",
        batch_id="abcd1234",
        locale_slug="en",
        pack_version=2,
        question_id="q_sample",
        answer_text="no",
    )
    assert alt != got


def test_verify_rows_empty():
    assert verify_maturity_assessment_rows(secret=b"k", rows=[]) == {
        "secret_configured": True,
        "rows_checked": 0,
        "rows_ok": 0,
        "rows_mismatch": 0,
        "rows_unsealed": 0,
        "rows_unknown_sealed": 0,
    }


def test_verify_rows_ok_and_mismatch():
    secret = b"unit-test-secret"
    rows = [
        {
            "batch_id": "b1",
            "locale_slug": "en",
            "pack_version": 1,
            "question_id": "q1",
            "answer_text": "yes",
            "row_hmac": compute_answer_hmac(
                secret,
                batch_id="b1",
                locale_slug="en",
                pack_version=1,
                question_id="q1",
                answer_text="yes",
            ),
        },
        {
            "batch_id": "b1",
            "locale_slug": "en",
            "pack_version": 1,
            "question_id": "q1",
            "answer_text": "tampered",
            "row_hmac": compute_answer_hmac(
                secret,
                batch_id="b1",
                locale_slug="en",
                pack_version=1,
                question_id="q1",
                answer_text="yes",
            ),
        },
    ]
    out = verify_maturity_assessment_rows(secret=secret, rows=rows)
    assert out["rows_ok"] == 1
    assert out["rows_mismatch"] == 1
    assert out["rows_unsealed"] == 0


def test_verify_rows_unsealed_and_unknown_sealed():
    rows = [
        {
            "batch_id": "b",
            "locale_slug": "en",
            "pack_version": 1,
            "question_id": "q",
            "answer_text": "a",
            "row_hmac": "",
        },
        {
            "batch_id": "b",
            "locale_slug": "en",
            "pack_version": 1,
            "question_id": "q",
            "answer_text": "a",
            "row_hmac": "ab" * 32,
        },
    ]
    out_none = verify_maturity_assessment_rows(secret=None, rows=rows)
    assert out_none["secret_configured"] is False
    assert out_none["rows_unsealed"] == 1
    assert out_none["rows_unknown_sealed"] == 1


def test_load_integrity_secret_from_config_default_env(monkeypatch):
    monkeypatch.delenv("DATA_BOAR_MATURITY_INTEGRITY_SECRET", raising=False)
    monkeypatch.delenv("MY_CUSTOM_MATURITY_SECRET", raising=False)
    assert load_integrity_secret_from_config({"api": {}}) is None
    monkeypatch.setenv("DATA_BOAR_MATURITY_INTEGRITY_SECRET", "  abc  ")
    assert load_integrity_secret_from_config({"api": {}}) == b"abc"


def test_load_integrity_secret_from_config_named_env(monkeypatch):
    monkeypatch.delenv("DATA_BOAR_MATURITY_INTEGRITY_SECRET", raising=False)
    monkeypatch.setenv("MY_CUSTOM_MATURITY_SECRET", "named")
    cfg = {"api": {"maturity_integrity_secret_from_env": "MY_CUSTOM_MATURITY_SECRET"}}
    assert load_integrity_secret_from_config(cfg) == b"named"


def test_db_save_verify_tamper(tmp_path: Path):
    db_path = str(tmp_path / "t.db")
    mgr = LocalDBManager(db_path)
    try:
        secret = b"db-test-secret"
        mgr.save_maturity_assessment_answers(
            batch_id="batch1",
            locale_slug="en",
            pack_version=2,
            answers={"q1": "original"},
            integrity_secret=secret,
        )
        v = mgr.verify_maturity_assessment_integrity(secret)
        assert v["secret_configured"] is True
        assert v["rows_checked"] == 1
        assert v["rows_ok"] == 1
        assert v["rows_mismatch"] == 0

        # Direct tamper: change answer_text in SQLite without updating MAC
        from sqlalchemy import text

        with mgr.engine.connect() as conn:
            conn.execute(
                text(
                    "UPDATE maturity_assessment_answers SET answer_text = :t WHERE question_id = :q"
                ),
                {"t": "hacked", "q": "q1"},
            )
            conn.commit()
        v2 = mgr.verify_maturity_assessment_integrity(secret)
        assert v2["rows_mismatch"] == 1
        assert v2["rows_ok"] == 0
    finally:
        mgr.dispose()


def test_maturity_rows_for_batch_matches_full_table(tmp_path: Path):
    db_path = str(tmp_path / "batch.db")
    mgr = LocalDBManager(db_path)
    try:
        mgr.save_maturity_assessment_answers(
            batch_id="batch-a",
            locale_slug="en",
            pack_version=1,
            answers={"q1": "x"},
            integrity_secret=None,
        )
        mgr.save_maturity_assessment_answers(
            batch_id="batch-b",
            locale_slug="en",
            pack_version=1,
            answers={"q2": "y"},
            integrity_secret=None,
        )
        a = mgr.maturity_assessment_rows_for_integrity_batch("batch-a")
        b = mgr.maturity_assessment_rows_for_integrity_batch("batch-b")
        assert len(a) == 1 and len(b) == 1
        assert a[0]["question_id"] == "q1"
        assert b[0]["question_id"] == "q2"
    finally:
        mgr.dispose()


def test_db_unsealed_when_no_secret(tmp_path: Path):
    db_path = str(tmp_path / "u.db")
    mgr = LocalDBManager(db_path)
    try:
        mgr.save_maturity_assessment_answers(
            batch_id="b",
            locale_slug="en",
            pack_version=1,
            answers={"q1": "x"},
            integrity_secret=None,
        )
        v = mgr.verify_maturity_assessment_integrity(None)
        assert v["rows_unsealed"] == 1
        assert v["rows_ok"] == 0
    finally:
        mgr.dispose()
