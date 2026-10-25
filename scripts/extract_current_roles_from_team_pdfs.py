from __future__ import annotations

import json
import re
from pathlib import Path

from pypdf import PdfReader


def normalize_key(s: str) -> str:
    s = s.lower()
    # Keep only alphanumerics to make fuzzy matching more resilient to accents/mojibake.
    return re.sub(r"[^a-z0-9]+", "", s)


def find_pdf_by_name(team_dir: Path, wanted: str) -> Path | None:
    # Fast path: exact match
    exact = team_dir / wanted
    if exact.exists():
        return exact

    wanted_key = normalize_key(wanted)
    best = None
    best_score = -1.0
    for pdf in team_dir.glob("*.pdf"):
        k2 = normalize_key(pdf.name)
        if not wanted_key or not k2:
            continue
        # Simple containment scoring
        if wanted_key in k2 or k2 in wanted_key:
            return pdf
        common = sum(1 for ch in set(wanted_key) if ch in set(k2))
        score = common / max(1, len(set(wanted_key)))
        if score > best_score:
            best_score = score
            best = pdf
    return best


def extract_text(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    chunks: list[str] = []
    for page in reader.pages:
        chunks.append(page.extract_text() or "")
    return "\n".join(chunks)


def find_best_evidence_line(
    lines: list[str], candidate_idx: list[int]
) -> tuple[int | None, str | None]:
    if not candidate_idx:
        return None, None
    # Prefer the first candidate that includes a 4-digit year.
    for i in candidate_idx:
        if re.search(r"(?<!\d)(19\d{2}|20\d{2})(?!\d)", lines[i]):
            return i, lines[i]
    return candidate_idx[0], lines[candidate_idx[0]]


def first_evidence_line(text: str) -> tuple[str | None, str]:
    # Avoid strict word boundaries because encoding can be noisy (mojibake).
    # Priority: "Present/Presente" first, then Portuguese "Atual".
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    # Avoid false positives like "apresentações" containing "present".
    # We target the date-range style: "- Present" or "- Presente" (hyphen/en dash/em dash variants).
    present_re = re.compile(r"[-\u2013\u2014]\s*(present|presente)", re.IGNORECASE)
    # Avoid strict word boundaries because mojibake may break letter adjacency.
    # We still rely on "best evidence" selecting a line that includes a year.
    atual_re = re.compile(r"atual", re.IGNORECASE)

    present_candidates = [i for i, ln in enumerate(lines) if present_re.search(ln)]
    i_best, ln_best = find_best_evidence_line(lines, present_candidates)
    if i_best is not None and ln_best:
        context = "\n".join(lines[max(0, i_best - 2) : i_best + 1])
        return ln_best, context

    atual_candidates = [i for i, ln in enumerate(lines) if atual_re.search(ln)]
    i_best, ln_best = find_best_evidence_line(lines, atual_candidates)
    if i_best is not None and ln_best:
        context = "\n".join(lines[max(0, i_best - 2) : i_best + 1])
        return ln_best, context

    return None, ""


def extract_years_from_line(line: str) -> list[str]:
    # Mojibake/encoding quirks can break \b boundaries; use numeric lookarounds instead.
    return re.findall(r"(?<!\d)(19\d{2}|20\d{2})(?!\d)", line)


def build_rows(
    wanted: dict[str, str | None], team_dir: Path
) -> list[tuple[str, str, str, str]]:
    rows: list[tuple[str, str, str, str]] = []
    # (profile, evidence_line, context/snippet, status)

    for profile, pdf_name in wanted.items():
        if pdf_name is None:
            rows.append((profile, "(não há PDF em team_info)", "-", "MISSING"))
            continue

        pdf = find_pdf_by_name(team_dir, pdf_name)
        if pdf is None:
            rows.append((profile, f"(PDF não encontrado: {pdf_name})", "-", "MISSING"))
            continue

        text = extract_text(pdf)
        evidence_line, context = first_evidence_line(text)
        if evidence_line is None:
            rows.append(
                (
                    profile,
                    "(não encontrei Present/Presente no texto extraído)",
                    context[:1200],
                    "PARTIAL",
                )
            )
            continue

        years = extract_years_from_line(evidence_line)
        status = "OK" if years else "PARTIAL"
        rows.append((profile, evidence_line, context[:1600], status))

    return rows


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    team_dir = repo_root / "docs" / "private" / "team_info"
    out_path = (
        repo_root
        / "docs"
        / "private"
        / "commercial"
        / "TALENT_POOL_CV_CURRENT_ROLES.pt_BR.md"
    )

    mapping_path = (
        repo_root / "docs" / "private" / "commercial" / "team_pdf_mappings.json"
    )
    wanted: dict[str, str | None] = {}
    if mapping_path.exists():
        try:
            loaded = json.loads(mapping_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                wanted = loaded
        except json.JSONDecodeError:
            print(f"WARN: invalid JSON in {mapping_path}; using empty mapping.")

    rows = build_rows(wanted, team_dir)

    # Render markdown
    out_lines: list[str] = []
    out_lines.append("# Cargo atual (CV/PDF) — auditoria por Present/Presente")
    out_lines.append("")
    out_lines.append("Fonte: `docs/private/team_info/*.pdf` (pypdf extract_text).")
    out_lines.append("")
    out_lines.append(
        "| Perfil | Evidência (linha com Present/Presente) | Início (se ano explícito aparecer) | Status |"
    )
    out_lines.append("| --- | --- | --- | --- |")

    for profile, evidence, context, status in rows:
        years = extract_years_from_line(evidence) if evidence != "-" else []
        years_part = ", ".join(years) if years else ""
        out_lines.append(f"| {profile} | {evidence} | {years_part} | **{status}** |")

    out_lines.append("")
    out_lines.append("## Contexto (snippet) por perfil")
    out_lines.append("")
    for profile, evidence, context, status in rows:
        out_lines.append(f"### {profile} ({status})")
        out_lines.append(f"- Evidência: `{evidence}`")
        out_lines.append("- Snippet:")
        out_lines.append("```")
        out_lines.append(context or "-")
        out_lines.append("```")
        out_lines.append("")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(out_lines), encoding="utf-8")
    print(f"Wrote: {out_path}")


if __name__ == "__main__":
    main()
