"""
Load a structured questionnaire pack from YAML (exported from private DOCX or authored by hand).

Public repo ships schema + generic samples only — no proprietary wording from operator DOCX.

Optional per-question ``scores:`` maps **yes** / **no** / **na** / **unset** weights. PyYAML treats
bare ``yes``/``no`` as booleans; the loader accepts both string keys and those booleans.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class MaturityQuestion:
    id: str
    prompt: str
    score_yes: float = 0.0
    score_no: float = 0.0
    score_na: float = 0.0
    score_unset: float = 0.0


@dataclass(frozen=True)
class MaturitySection:
    id: str
    title: str
    questions: tuple[MaturityQuestion, ...]


@dataclass(frozen=True)
class MaturityPack:
    version: int
    sections: tuple[MaturitySection, ...]

    def iter_questions(self) -> Iterator[MaturityQuestion]:
        """All questions in YAML order (section order, then question order)."""
        for sec in self.sections:
            yield from sec.questions


def _float_score(raw: object, default: float = 0.0) -> float:
    if raw is None:
        return default
    try:
        return float(raw)
    except (TypeError, ValueError):
        raise ValueError("scores must be numeric") from None


def _normalize_score_key(key: object) -> str:
    """YAML 1.1 parses bare ``yes`` / ``no`` as booleans — map back to rubric slots."""
    if key is True:
        return "yes"
    if key is False:
        return "no"
    return str(key).strip().lower()


def _parse_question_block(q: dict) -> MaturityQuestion | None:
    qid = str(q.get("id") or "").strip()
    prompt = str(q.get("prompt") or "").strip()
    if not qid or not prompt:
        return None
    sy = sn = sna = su = 0.0
    scores = q.get("scores")
    if scores is not None:
        if not isinstance(scores, dict):
            raise ValueError("question scores must be a mapping when present")
        for raw_key, raw_val in scores.items():
            slot = _normalize_score_key(raw_key)
            val = _float_score(raw_val, 0.0)
            if slot == "yes":
                sy = val
            elif slot == "no":
                sn = val
            elif slot == "na":
                sna = val
            elif slot == "unset":
                su = val
    return MaturityQuestion(
        id=qid,
        prompt=prompt,
        score_yes=sy,
        score_no=sn,
        score_na=sna,
        score_unset=su,
    )


def load_maturity_pack(path: str | Path) -> MaturityPack:
    """Parse YAML into a pack. Raises FileNotFoundError, ValueError, or yaml.YAMLError."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(str(p))
    raw = p.read_text(encoding="utf-8")
    data = yaml.safe_load(raw)
    if not isinstance(data, dict):
        raise ValueError("pack root must be a mapping")
    version = int(data.get("version", 1))
    sections_raw = data.get("sections")
    if not isinstance(sections_raw, list):
        raise ValueError("sections must be a list")
    sections: list[MaturitySection] = []
    seen_qids: set[str] = set()
    for s in sections_raw:
        if not isinstance(s, dict):
            continue
        sid = str(s.get("id") or "").strip()
        title = str(s.get("title") or "").strip()
        qs: list[MaturityQuestion] = []
        for q in s.get("questions") or []:
            if not isinstance(q, dict):
                continue
            mq = _parse_question_block(q)
            if mq is None:
                continue
            if mq.id in seen_qids:
                raise ValueError(f"duplicate question id: {mq.id}")
            seen_qids.add(mq.id)
            qs.append(mq)
        if sid and title and qs:
            sections.append(MaturitySection(id=sid, title=title, questions=tuple(qs)))
    if not sections:
        raise ValueError("pack has no valid sections with questions")
    return MaturityPack(version=version, sections=tuple(sections))
