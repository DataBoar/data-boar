"""#1820 — ML confidence without joblib.Parallel inside RandomForest.predict_proba.

``joblib.Parallel`` (used by ``RandomForestClassifier.predict_proba`` even with
``n_jobs=1``) collapses when entered from several threads on free-threaded
CPython. The detector must compute the same probabilities without it:
bit-identical to ``predict_proba``, single-class safe, no-model safe, fallback
for non-forest models, consistent under 8 threads. Synthetic text only.
"""

from __future__ import annotations

import threading

import numpy as np
import pytest
import sklearn.ensemble._forest as forest_mod
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression

from core.detector import _forest_predict_proba
from core.scanner import DataScanner

_TEXTS = [
    f"doc_{i} nome;email;cpf pessoa{i}@example.com 529.982.247-25 lorem {i % 7}"
    for i in range(40)
] + [f"registro {i} sem dado pessoal lorem ipsum" for i in range(20)]


@pytest.fixture(scope="module")
def detector():
    return DataScanner().detector


def _no_joblib(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(*a, **k):
        raise AssertionError("joblib.Parallel must not run in the ML step (#1820)")

    monkeypatch.setattr(forest_mod, "Parallel", _boom)


def test_d1820_ml_forest_probabilities_are_bit_identical(detector) -> None:
    model, vec = detector._model, detector._vectorizer
    assert isinstance(model, RandomForestClassifier)
    for text in _TEXTS:
        X = vec.transform([text.lower()])
        assert np.array_equal(_forest_predict_proba(model, X), model.predict_proba(X))


def test_d1820_ml_confidence_same_without_joblib(
    detector, monkeypatch: pytest.MonkeyPatch
) -> None:
    expected = [detector._predict_ml_confidence(t) for t in _TEXTS]
    assert any(v > 0 for v in expected)
    _no_joblib(monkeypatch)
    assert [detector._predict_ml_confidence(t) for t in _TEXTS] == expected


def test_d1820_ml_single_class_model(detector, monkeypatch: pytest.MonkeyPatch) -> None:
    vec = detector._vectorizer
    X = vec.transform([t.lower() for t in _TEXTS])
    single = RandomForestClassifier(n_estimators=7, random_state=1, n_jobs=1)
    single.fit(X, [1] * X.shape[0])
    assert list(single.classes_) == [1]
    monkeypatch.setattr(detector, "_model", single)
    expected = [detector._predict_ml_confidence(t) for t in _TEXTS[:10]]
    assert expected == [100] * 10
    _no_joblib(monkeypatch)
    assert [detector._predict_ml_confidence(t) for t in _TEXTS[:10]] == expected


def test_d1820_ml_no_model_returns_zero(
    detector, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(detector, "_ml_available", False)
    assert detector._predict_ml_confidence(_TEXTS[0]) == 0


def test_d1820_ml_non_forest_model_falls_back(detector) -> None:
    vec = detector._vectorizer
    X = vec.transform([t.lower() for t in _TEXTS])
    y = [1] * 40 + [0] * 20
    lr = LogisticRegression(max_iter=200).fit(X, y)
    for text in _TEXTS[:10]:
        Xi = vec.transform([text.lower()])
        assert np.array_equal(_forest_predict_proba(lr, Xi), lr.predict_proba(Xi))


def test_d1820_ml_confidence_consistent_under_8_threads(
    detector, monkeypatch: pytest.MonkeyPatch
) -> None:
    expected = [detector._predict_ml_confidence(t) for t in _TEXTS]
    _no_joblib(monkeypatch)
    n = 8
    start = threading.Barrier(n)
    results: list[list[int]] = [[] for _ in range(n)]

    def _work(slot: int) -> None:
        start.wait()
        results[slot] = [detector._predict_ml_confidence(t) for t in _TEXTS]

    threads = [threading.Thread(target=_work, args=(s,)) for s in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert all(r == expected for r in results)
