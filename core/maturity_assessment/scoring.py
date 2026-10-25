"""Rubric scoring for maturity questionnaire packs (YAML-defined per-answer weights)."""

from __future__ import annotations

from dataclasses import dataclass

from core.maturity_assessment.pack import MaturityPack, MaturityQuestion


@dataclass(frozen=True)
class RubricLine:
    """One row in the rubric breakdown (aligned with pack question order)."""

    section_id: str
    section_title: str
    question_id: str
    prompt: str
    answer_normalized: str
    points_earned: float
    points_max: float


@dataclass(frozen=True)
class RubricScoreResult:
    """Aggregate score for a submission against the current pack."""

    total: float
    maximum: float
    percentage: float | None
    has_rubric: bool
    lines: tuple[RubricLine, ...]


def _per_question_max(q: MaturityQuestion) -> float:
    return max(q.score_yes, q.score_no, q.score_na, q.score_unset)


def _normalize_answer(raw: str) -> str:
    s = (raw or "").strip().lower()
    if s in ("yes", "no", "na"):
        return s
    return "unset"


def _points_for_normalized(q: MaturityQuestion, normalized: str) -> tuple[float, float]:
    """Return (earned, max) for one question; max is the best achievable score for that question."""
    max_pts = _per_question_max(q)
    if normalized == "yes":
        return (q.score_yes, max_pts)
    if normalized == "no":
        return (q.score_no, max_pts)
    if normalized == "na":
        return (q.score_na, max_pts)
    return (q.score_unset, max_pts)


def compute_rubric_score(
    pack: MaturityPack, answers_by_question_id: dict[str, str]
) -> RubricScoreResult:
    """
    Sum rubric weights from the pack using stored answers.

    Unknown question ids in ``answers_by_question_id`` are ignored. Missing answers count as unset.
    """
    lines: list[RubricLine] = []
    total = 0.0
    maximum = 0.0
    for sec in pack.sections:
        for q in sec.questions:
            raw = answers_by_question_id.get(q.id, "")
            normalized = _normalize_answer(str(raw))
            earned, max_pts = _points_for_normalized(q, normalized)
            lines.append(
                RubricLine(
                    section_id=sec.id,
                    section_title=sec.title,
                    question_id=q.id,
                    prompt=q.prompt,
                    answer_normalized=normalized,
                    points_earned=earned,
                    points_max=max_pts,
                )
            )
            total += earned
            maximum += max_pts
    has_rubric = maximum > 0.0
    pct: float | None
    if maximum > 0:
        pct = round(100.0 * (total / maximum), 1)
    else:
        pct = None
    return RubricScoreResult(
        total=total,
        maximum=maximum,
        percentage=pct,
        has_rubric=has_rubric,
        lines=tuple(lines),
    )


def rubric_result_to_summary_dict(r: RubricScoreResult) -> dict[str, object]:
    """Template-friendly strings for i18n one-liners (total / max / percent)."""

    def fmt_num(x: float) -> str:
        if abs(x - round(x)) < 1e-9:
            return str(int(round(x)))
        s = f"{x:.2f}".rstrip("0").rstrip(".")
        return s

    pct_disp = ""
    if r.percentage is not None:
        pct_disp = f"{r.percentage:.1f}"
    return {
        "has_rubric": r.has_rubric,
        "total_display": fmt_num(r.total),
        "maximum_display": fmt_num(r.maximum),
        "percentage_display": pct_disp,
    }
