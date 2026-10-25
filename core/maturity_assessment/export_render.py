"""CSV / Markdown export for maturity assessment batches (local operator download)."""

from __future__ import annotations

import csv
from io import StringIO

from core.maturity_assessment.pack import MaturityPack
from core.maturity_assessment.scoring import RubricScoreResult, compute_rubric_score

# Shown in exports; keep aligned with dashboard disclaimer tone (USAGE / assessment page).
EXPORT_DISCLAIMER_EN = (
    "Self-reported maturity signal only — not legal advice, audit, or certification. "
    "Questionnaire wording may be confidential; this export reflects answers stored locally."
)


def maturity_assessment_rows_to_answers(
    rows: list[dict[str, object]],
) -> dict[str, str]:
    """Map DB integrity rows to question_id -> answer_text."""
    out: dict[str, str] = {}
    for row in rows:
        qid = str(row.get("question_id") or "").strip()
        if not qid:
            continue
        out[qid] = str(row.get("answer_text") or "")
    return out


def render_maturity_export_csv(
    *,
    pack: MaturityPack,
    batch_id: str,
    score: RubricScoreResult,
) -> str:
    buf = StringIO()
    w = csv.writer(buf)
    w.writerow(["disclaimer", EXPORT_DISCLAIMER_EN])
    w.writerow(["batch_id", batch_id])
    w.writerow(["pack_version", pack.version])
    if score.has_rubric and score.percentage is not None:
        w.writerow(["rubric_total", f"{score.total:g}"])
        w.writerow(["rubric_maximum", f"{score.maximum:g}"])
        w.writerow(["rubric_percent", f"{score.percentage:g}"])
    w.writerow([])
    w.writerow(
        [
            "section_id",
            "section_title",
            "question_id",
            "prompt",
            "answer",
            "points_earned",
            "points_max",
        ]
    )
    for line in score.lines:
        w.writerow(
            [
                line.section_id,
                line.section_title,
                line.question_id,
                line.prompt,
                line.answer_normalized,
                f"{line.points_earned:g}",
                f"{line.points_max:g}",
            ]
        )
    return buf.getvalue()


def render_maturity_export_markdown(
    *,
    pack: MaturityPack,
    batch_id: str,
    score: RubricScoreResult,
) -> str:
    """Human-readable Markdown; prompts may be long — keep structure simple."""
    lines: list[str] = [
        "# Maturity self-assessment export",
        "",
        f"- **Batch:** `{batch_id}`",
        f"- **Pack version:** {pack.version}",
        f"- **Disclaimer:** {EXPORT_DISCLAIMER_EN}",
        "",
    ]
    if score.has_rubric and score.percentage is not None:
        lines.extend(
            [
                "## Score",
                "",
                f"- **Total:** {score.total:g} / {score.maximum:g} ({score.percentage:g}%)",
                "",
            ]
        )
    lines.append("## Questions")
    lines.append("")
    current_sec = ""
    for line in score.lines:
        if line.section_id != current_sec:
            current_sec = line.section_id
            lines.append(f"### {line.section_title}")
            lines.append("")
        lines.append(f"**{line.question_id}** — {line.prompt}")
        lines.append("")
        lines.append(f"- Answer (normalized): `{line.answer_normalized}`")
        lines.append(f"- Points: {line.points_earned:g} / {line.points_max:g}")
        lines.append("")
    return "\n".join(lines)


def score_for_export(
    pack: MaturityPack, rows: list[dict[str, object]]
) -> RubricScoreResult:
    answers = maturity_assessment_rows_to_answers(rows)
    return compute_rubric_score(pack, answers)
