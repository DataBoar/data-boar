"""Adversarial guard for ``core.regex_translate`` (#1414 / PLAN §2.7)."""

from __future__ import annotations

import re

import pytest

from core.regex_translate import translate

_TURKISH_I = "\u0130"  # LATIN CAPITAL LETTER I WITH DOT ABOVE


@pytest.mark.parametrize(
    ("pattern", "expect_none", "reason_substr"),
    [
        ("(?i:cpf)i", True, "scoped_case_insensitive"),
        (r"\b(?=[A-Z0-9./-]*[A-Z])[A-Z0-9]{2}\b", True, "lookahead"),
        ("a++", True, "possessive"),
    ],
)
def test_translate_forces_python_fallback(
    pattern: str, expect_none: bool, reason_substr: str
) -> None:
    rust_pattern, reason = translate(pattern)
    if expect_none:
        assert rust_pattern is None
        assert reason_substr in reason
    else:
        assert rust_pattern is not None


@pytest.fixture(scope="module")
def rust_engine():
    mod = pytest.importorskip(
        "boar_fast_filter",
        reason="Run maturin develop for boar_fast_filter",
    )
    return mod.RegexStageEngine


def _rust_is_match(rust_engine, pattern: str, text: str) -> bool:
    engine = rust_engine.compile_patterns(["probe"], [pattern], None)
    return "probe" in engine.match_names(text)


@pytest.mark.parametrize(
    "pattern",
    [
        "(?i)i",
        "(?i)[h-j]",
        "(?i)(?P<x>i)",
        "(?i)^[a-z]+$",
    ],
)
def test_translate_case_insensitive_patterns_compile_in_rust(
    pattern: str, rust_engine
) -> None:
    rust_pattern, reason = translate(pattern)
    assert rust_pattern is not None, reason
    assert reason in {"direct", "translated"}
    assert _rust_is_match(rust_engine, rust_pattern, _TURKISH_I)


def test_translate_dollar_before_final_newline(rust_engine) -> None:
    rust_pattern, reason = translate("xyz$")
    assert rust_pattern is not None
    assert reason == "translated"
    assert _rust_is_match(rust_engine, rust_pattern, "xyz\n")
    assert re.search("xyz$", "xyz\n") is not None


def test_lgpd_cnpj_alnum_stays_python_fallback() -> None:
    pattern = (
        r"\b(?=[A-Z0-9./-]*[A-Z])[A-Z0-9]{2}\.?[A-Z0-9]{3}\.?[A-Z0-9]{3}/?"
        r"[A-Z0-9]{4}-\d{2}\b"
    )
    rust_pattern, reason = translate(pattern)
    assert rust_pattern is None
    assert reason == "lookahead"
