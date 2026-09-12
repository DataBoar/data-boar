"""
Optional deep-learning backend for sensitivity detection.
Uses sentence embeddings (e.g. sentence-transformers) + a classifier trained on
configurable (text, label) terms. When available, the detector uses this in a
hybrid step together with regex and ML (TF-IDF + RandomForest).

Training terms format: list of { text: str, label: "sensitive"|"non_sensitive" or 1|0 }.
Same structure as ML terms; can share the same config file or use a separate dl_patterns_file.
"""

from __future__ import annotations

import math
from typing import Any

from core.cpu_preflight import warn_if_numpy_unsafe

# Optional: sentence-transformers (pulls torch + numpy). Fail gracefully if not
# installed. CPU pre-flight must run first — SIGILL is not ImportError (#929).
_DL_AVAILABLE = False
_SentenceTransformer = None
_LogisticRegression = None

if warn_if_numpy_unsafe():
    try:
        from sentence_transformers import SentenceTransformer

        _SentenceTransformer = SentenceTransformer
        _DL_AVAILABLE = True
    except ImportError:
        _SentenceTransformer = None
        _DL_AVAILABLE = False

    try:
        from sklearn.linear_model import LogisticRegression

        _LogisticRegression = LogisticRegression
    except ImportError:
        _LogisticRegression = None


# Default small model: 384-dim, ~80MB; good balance of speed and semantic quality
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def is_available() -> bool:
    """Return True if the DL backend can be used (sentence_transformers + sklearn)."""
    return bool(_DL_AVAILABLE and _SentenceTransformer and _LogisticRegression)


def _normalize_terms(
    terms: list[tuple[str, int]] | list[dict[str, Any]],
) -> list[tuple[str, int]]:
    """Convert config-style terms to list of (text_lower, 1|0)."""
    out: list[tuple[str, int]] = []
    for t in terms or []:
        if isinstance(t, dict):
            text = (t.get("text") or "").strip()
            label = t.get("label", "sensitive")
            if not text:
                continue
            lab = 1 if label in ("sensitive", 1, "1") else 0
            out.append((text.lower(), lab))
        elif isinstance(t, (list, tuple)) and len(t) >= 2:
            text = str(t[0]).strip().lower()
            lab = 1 if t[1] in (1, "1", "sensitive") else 0
            if text:
                out.append((text, lab))
    return out


class DLClassifier:
    """
    Train a classifier on sentence embeddings of (text, label) terms.
    predict_proba(text) returns probability of sensitive (0..1). No model stored after init.
    """

    def __init__(
        self,
        terms: list[tuple[str, int]] | list[dict[str, Any]],
        embedding_model: str | None = None,
    ):
        """
        terms: list of (text, 1|0) or list of { text, label } (1 = sensitive, 0 = non_sensitive).
        embedding_model: name for SentenceTransformer; default all-MiniLM-L6-v2.
        """
        self._model = None
        self._embedder = None
        self._ready = False
        self._sensitive_prototype: list[float] | None = None
        norm = _normalize_terms(terms)
        if not norm or not is_available():
            return
        embedding_model = embedding_model or DEFAULT_EMBEDDING_MODEL
        try:
            self._embedder = _SentenceTransformer(embedding_model)
            texts = [t[0] for t in norm]
            labels = [t[1] for t in norm]
            X = self._embedder.encode(texts, convert_to_numpy=True)
            self._model = _LogisticRegression(max_iter=500, random_state=42)
            self._model.fit(X, labels)
            self._sensitive_prototype = self._build_sensitive_prototype(X, labels)
            self._ready = True
        except Exception as model_err:
            # Keep DL backend optional: model init failures disable readiness.
            _ = str(model_err)

    @staticmethod
    def _build_sensitive_prototype(
        embeddings: Any, labels: list[int]
    ) -> list[float] | None:
        """Centroid of sensitive-term embeddings, used for optional semantic hints."""
        sens_rows = [embeddings[i] for i, lab in enumerate(labels) if int(lab) == 1]
        if not sens_rows:
            return None
        dim = len(sens_rows[0])
        centroid = [0.0] * dim
        for row in sens_rows:
            for i in range(dim):
                centroid[i] += float(row[i])
        denom = float(len(sens_rows))
        return [v / denom for v in centroid]

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        """Cosine similarity in [0,1] for non-zero vectors."""
        if len(a) != len(b) or not a:
            return 0.0
        dot = 0.0
        na = 0.0
        nb = 0.0
        for i in range(len(a)):
            av = float(a[i])
            bv = float(b[i])
            dot += av * bv
            na += av * av
            nb += bv * bv
        if na <= 0.0 or nb <= 0.0:
            return 0.0
        return max(0.0, min(1.0, dot / (math.sqrt(na) * math.sqrt(nb))))

    def predict_proba(self, text: str) -> float | None:
        """
        Return P(sensitive) in [0, 1], or None if backend not ready.
        """
        if not self._ready or not self._embedder or not self._model:
            return None
        if not (text or "").strip():
            return None
        try:
            vec = self._embedder.encode([text], convert_to_numpy=True)
            prob = self._model.predict_proba(vec)[0][1]
            return float(prob)
        except Exception:
            return None

    def sensitive_prototype_similarity(self, text: str) -> int | None:
        """
        Return similarity (0..100) between text embedding and sensitive-term prototype.
        Used by optional Plan §5 semantic hint.
        """
        if (
            not self._ready
            or not self._embedder
            or not self._sensitive_prototype
            or not (text or "").strip()
        ):
            return None
        try:
            vec = self._embedder.encode([text], convert_to_numpy=True)[0]
            v = [float(x) for x in vec]
            sim = self._cosine_similarity(v, self._sensitive_prototype)
            return int(round(sim * 100))
        except Exception:
            return None

    @property
    def is_ready(self) -> bool:
        return self._ready
