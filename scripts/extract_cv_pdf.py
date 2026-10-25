"""
extract_cv_pdf.py - Extrator estruturado de PDFs de perfil LinkedIn / CV.

Uso:
    uv run python scripts/extract_cv_pdf.py <pdf_path> [--json] [--out <file>]

Saida padrao: texto estruturado com secoes identificadas.
Com --json: JSON com campos extraidos (nome, linkedin_url, email, headline, etc.)
Com --out: salva saida em arquivo em vez de stdout.

Dependencias (pyproject.toml / uv):
    pypdf >= 4.0
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    from pypdf import PdfReader
except ImportError:
    print("ERRO: pypdf nao encontrado. Execute: uv add pypdf", file=sys.stderr)
    sys.exit(1)

LINKEDIN_PATTERN = re.compile(
    r"(?:linkedin\.com/in/|www\.linkedin\.com/in/)([a-zA-Z0-9\-_%]+)",
    re.IGNORECASE,
)
EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
PHONE_PATTERN = re.compile(
    r"(?:\+55\s?)?(?:\(?\d{2}\)?[\s\-]?)(?:9\s?)?\d{4}[\s\-]?\d{4}"
)

CERT_KEYWORDS = [
    "PMP",
    "PSM",
    "CSM",
    "CSPO",
    "ITIL",
    "COBIT",
    "CISM",
    "CISSP",
    "CISA",
    "CEH",
    "OSCP",
    "ITIL V3",
    "ITIL V4",
    "ISO 27001",
    "ISO 27002",
    "ISO 20000",
    "CDPO",
    "DPO",
    "Oracle Cloud",
    "Oracle APEX",
    "AWS",
    "Azure",
    "GCP",
    "CKA",
    "Security+",
    "AI Fundamentals",
]


def extract_text_from_pdf(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text)
    return "\n".join(pages)


def extract_fields(raw_text: str, pdf_path: Path) -> dict:
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    text_block = "\n".join(lines)

    linkedin_match = LINKEDIN_PATTERN.search(text_block)
    email_matches = EMAIL_PATTERN.findall(text_block)
    phone_matches = PHONE_PATTERN.findall(text_block)

    return {
        "source_file": pdf_path.name,
        "name_detected": _extract_name(lines),
        "email": email_matches[0] if email_matches else None,
        "phone": phone_matches[0].strip() if phone_matches else None,
        "linkedin_slug": linkedin_match.group(1) if linkedin_match else None,
        "linkedin_url": (
            f"https://www.example.com/profile/{linkedin_match.group(1)}"
            if linkedin_match
            else None
        ),
        "headline": _extract_headline(lines),
        "location": _extract_location(lines),
        "certifications_detected": _extract_certifications(text_block),
        "languages_detected": _extract_languages(text_block),
        "raw_text_length": len(raw_text),
    }


def _extract_headline(lines: list[str]) -> str | None:
    cargo_words = re.compile(
        r"\b(Head|Gerente|Diretor|CIO|CTO|COO|CEO|VP|Manager|Engineer|"
        r"Analyst|Advisor|Consultor|Arquiteto|Especialista|DPO|Product|Owner|"
        r"Developer|Desenvolvedor|Analista|Coordenador|Lider|Leader)\b",
        re.IGNORECASE,
    )
    candidates = []
    for i, line in enumerate(lines[:25]):
        if len(line) > 40 and ("|" in line or cargo_words.search(line)):
            candidates.append((len(line), i, line))
    if candidates:
        candidates.sort(reverse=True)
        return candidates[0][2]
    return None


def _extract_name(lines: list[str]) -> str | None:
    for line in lines[:10]:
        words = line.split()
        if (
            2 <= len(words) <= 5
            and all(w[0].isupper() for w in words if w[0].isalpha())
            and not any(c in line for c in ["@", ".", "http", "|", "/"])
        ):
            return line
    return None


def _extract_location(lines: list[str]) -> str | None:
    loc_pattern = re.compile(
        r"[A-Z][a-zA-Z\u00C0-\u024F\s]+,\s*[A-Z][a-zA-Z\u00C0-\u024F\s]+"
    )
    for line in lines[:15]:
        if (
            "," in line
            and 10 <= len(line) <= 60
            and not any(c in line for c in ["@", "|", "/"])
        ):
            if loc_pattern.search(line):
                return line
    return None


def _extract_certifications(text: str) -> list[str]:
    found = []
    for cert in CERT_KEYWORDS:
        pattern = re.compile(r"(?<!\w)" + re.escape(cert) + r"(?!\w)", re.IGNORECASE)
        if pattern.search(text):
            found.append(cert)
    return found


def _extract_languages(text: str) -> list[str]:
    lang_patterns = [
        (r"Portuguese|Portugu", "Portuguese"),
        (r"English|Ingl", "English"),
        (r"Spanish|Espanhol", "Spanish"),
        (r"French|Franc", "French"),
        (r"German|Alem", "German"),
        (r"Italian|Italiano", "Italian"),
        (r"Dutch|Holand|Nederlands", "Dutch"),
    ]
    found = []
    for pattern, name in lang_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            found.append(name)
    return found


def format_as_text(fields: dict, raw_text: str) -> str:
    return "\n".join(
        [
            "=" * 60,
            f"EXTRACAO: {fields['source_file']}",
            "=" * 60,
            f"Nome detectado  : {fields['name_detected'] or '(nao detectado)'}",
            f"LinkedIn URL    : {fields['linkedin_url'] or '(nao encontrado)'}",
            f"Email           : {fields['email'] or '(nao encontrado)'}",
            f"Telefone        : {fields['phone'] or '(nao encontrado)'}",
            f"Localizacao     : {fields['location'] or '(nao detectado)'}",
            "",
            "HEADLINE:",
            f"  {fields['headline'] or '(nao detectado)'}",
            "",
            "CERTIFICACOES DETECTADAS:",
            f"  {', '.join(fields['certifications_detected']) or '(nenhuma)'}",
            "",
            "IDIOMAS DETECTADOS:",
            f"  {', '.join(fields['languages_detected']) or '(nenhum)'}",
            "",
            f"Tamanho texto: {fields['raw_text_length']} chars",
            "=" * 60,
            "TEXTO BRUTO (8000 chars):",
            "=" * 60,
            raw_text[:8000],
            ("..." if len(raw_text) > 8000 else ""),
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extrai dados estruturados de PDFs de perfil LinkedIn / CV.",
        epilog="Exemplo: uv run python scripts/extract_cv_pdf.py docs/private/team_info/Sample_Candidate.pdf --json",
    )
    parser.add_argument("pdf", help="Caminho para o arquivo PDF")
    parser.add_argument("--json", action="store_true", help="Saida em formato JSON")
    parser.add_argument(
        "--out", metavar="FILE", help="Arquivo de saida (padrao: stdout)"
    )
    parser.add_argument(
        "--raw-only", action="store_true", help="Exibe apenas texto bruto"
    )
    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        print(f"ERRO: Arquivo nao encontrado: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    raw_text = extract_text_from_pdf(pdf_path)

    if args.raw_only:
        output = raw_text
    elif args.json:
        fields = extract_fields(raw_text, pdf_path)
        output = json.dumps(fields, ensure_ascii=False, indent=2)
    else:
        fields = extract_fields(raw_text, pdf_path)
        output = format_as_text(fields, raw_text)

    if args.out:
        Path(args.out).write_text(output, encoding="utf-8")
        print(f"Salvo em: {args.out}")
    else:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        print(output)


if __name__ == "__main__":
    main()
