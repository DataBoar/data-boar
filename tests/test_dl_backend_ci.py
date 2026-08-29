"""Minimal real encode through ``core/dl_backend.py`` (optional extra ``dl``, #1822).

Default CI / local ``uv sync --extra shares`` does not install sentence-transformers.
This module skips unless the package is present — except when ``DATA_BOAR_CI_DL=1``
(job ``test-dl``), where a skip would hide a missing extra.
"""

from __future__ import annotations

import os

import pytest

from core.dl_backend import DLClassifier, is_available

_CI_DL = os.environ.get("DATA_BOAR_CI_DL") == "1"

# Two classes so LogisticRegression can fit; phrases are synthetic, not real PII.
_TRAIN_TERMS: list[dict[str, str]] = [
    {"text": "national identity number on a government form", "label": "sensitive"},
    {"text": "passport number field in an application", "label": "sensitive"},
    {"text": "bank account routing details", "label": "sensitive"},
    {"text": "sunny weather and weekend picnic plans", "label": "non_sensitive"},
    {"text": "recipe for tomato pasta dinner", "label": "non_sensitive"},
    {"text": "soccer match score last night", "label": "non_sensitive"},
]


@pytest.mark.filterwarnings("ignore::FutureWarning")
@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_dl_classifier_encode_via_backend() -> None:
    """``DLClassifier`` must call embedder.encode (init + predict_proba), not import-only."""
    if not is_available():
        if _CI_DL:
            pytest.fail(
                "DATA_BOAR_CI_DL=1 requires extra dl (sentence-transformers + sklearn)"
            )
        pytest.skip("optional extra dl (sentence-transformers) is not installed")

    clf = DLClassifier(_TRAIN_TERMS)
    assert clf.is_ready is True
    proba = clf.predict_proba("please send your national identity number")
    assert proba is not None
    assert 0.0 <= float(proba) <= 1.0
