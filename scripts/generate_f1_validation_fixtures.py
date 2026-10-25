#!/usr/bin/env python3
"""Generate Phase-1 F1 validation fixtures + ground_truth.yaml (#835).

Two disjoint template families (Presidio-research anti-leakage):
  - measure/   — final P/R/F1 publication only
  - calibrate/ — reserved for confidence-threshold tuning (never reuse measure templates)

Classes: pii | clean | tricky_fp | tricky_fn
Same synthetic identifiers are repeated across text formats under each pii
template so extraction failures can be isolated from detection failures later.

Usage:
  uv run python scripts/generate_f1_validation_fixtures.py
  uv run python scripts/generate_f1_validation_fixtures.py --output tests/data/f1_validation
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import textwrap
from pathlib import Path

import yaml

# Measure family A (publication split) — never copy these strings into calibrate/
_M_CPF = "529.982.247-25"
_M_CNPJ = "11.222.333/0001-81"
_M_EMAIL = "ana.souza@example-test.com"
_M_NAME = "Ana Paula Souza"

# Calibrate family B (disjoint) — different ids + narratives
_C_CPF = "390.533.447-05"
_C_CNPJ = "12.345.678/0001-95"
_C_EMAIL = "carlos.lima@demo.invalid"
_C_NAME = "Carlos Eduardo Lima"

_INVALID_CPF = "111.111.111-11"


def _w(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _roster_block(name: str, cpf: str, cnpj: str, email: str) -> str:
    return textwrap.dedent(
        f"""\
        RELATORIO SINTETICO — APENAS PARA VALIDACAO F1 (NAO E PESSOA REAL)
        Nome: {name}
        CPF: {cpf}
        CNPJ: {cnpj}
        Email: {email}
        """
    )


def _write_formats(base: Path, stem: str, body: str, row: dict[str, str]) -> None:
    """Write the same payload across text formats (isolates detection vs extraction)."""
    mapping: dict[str, str] = {
        f"{stem}.txt": body,
        f"{stem}.json": json.dumps(row, ensure_ascii=False, indent=2) + "\n",
        f"{stem}.xml": (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            f"<record><nome>{row['nome']}</nome><cpf>{row['cpf']}</cpf>"
            f"<cnpj>{row['cnpj']}</cnpj><email>{row['email']}</email></record>\n"
        ),
        f"{stem}.html": (
            "<!DOCTYPE html><html><body>"
            f"<p>Nome: {row['nome']}</p><p>CPF: {row['cpf']}</p>"
            f"<p>CNPJ: {row['cnpj']}</p><p>Email: {row['email']}</p>"
            "</body></html>\n"
        ),
    }
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["nome", "cpf", "cnpj", "email"])
    w.writerow([row["nome"], row["cpf"], row["cnpj"], row["email"]])
    mapping[f"{stem}.csv"] = buf.getvalue()
    tbuf = io.StringIO()
    tw = csv.writer(tbuf, delimiter="\t")
    tw.writerow(["nome", "cpf", "cnpj", "email"])
    tw.writerow([row["nome"], row["cpf"], row["cnpj"], row["email"]])
    mapping[f"{stem}.tsv"] = tbuf.getvalue()

    for name, content in mapping.items():
        _w(base / name, content)


def _entry(
    path: str,
    *,
    split: str,
    klass: str,
    template_id: str,
    expected_patterns: list[str] | None = None,
    expected_miss: bool = False,
    notes: str = "",
) -> dict:
    return {
        "path": path,
        "split": split,
        "class": klass,
        "template_id": template_id,
        "expected_patterns": expected_patterns or [],
        "expected_miss": expected_miss,
        "notes": notes,
    }


def build(root: Path) -> Path:
    measure = root / "measure"
    calibrate = root / "calibrate"
    files: list[dict] = []

    # --- measure / pii (family A, multi-format) ---
    pii_dir = measure / "pii"
    row_m = {
        "nome": _M_NAME,
        "cpf": _M_CPF,
        "cnpj": _M_CNPJ,
        "email": _M_EMAIL,
    }
    body_m = _roster_block(_M_NAME, _M_CPF, _M_CNPJ, _M_EMAIL)
    _write_formats(pii_dir, "roster_a", body_m, row_m)
    for name in (
        "roster_a.txt",
        "roster_a.csv",
        "roster_a.tsv",
        "roster_a.json",
        "roster_a.xml",
        "roster_a.html",
    ):
        rel = f"measure/pii/{name}"
        files.append(
            _entry(
                rel,
                split="measure",
                klass="pii",
                template_id="measure_roster_v1",
                expected_patterns=["LGPD_CPF", "LGPD_CNPJ", "EMAIL"],
                notes="Clear PII; same identifiers across formats",
            )
        )

    # --- measure / clean ---
    clean_txt = textwrap.dedent(
        """\
        Catalogo de produtos sinteticos para laboratorio de validacao.
        Este arquivo descreve apenas itens de estoque e nao contem identificadores
        pessoais. SKU-1001 Parafuso M6 quantidade 500 localizacao A-12.
        SKU-1002 Arruela 8mm quantidade 200 localizacao B-03.
        Versao de firmware 2.4.11 build 20240315 para dispositivos de teste.
        """
    )
    _w(measure / "clean" / "catalog.txt", clean_txt)
    _w(
        measure / "clean" / "catalog.json",
        json.dumps(
            {
                "description": "Synthetic product catalog without personal data",
                "items": [
                    {"sku": "SKU-1001", "name": "Parafuso M6", "qty": 500},
                    {"sku": "SKU-1002", "name": "Arruela 8mm", "qty": 200},
                ],
            },
            indent=2,
        )
        + "\n",
    )
    files.append(
        _entry(
            "measure/clean/catalog.txt",
            split="measure",
            klass="clean",
            template_id="measure_catalog_v1",
            notes="No personal identifiers",
        )
    )
    files.append(
        _entry(
            "measure/clean/catalog.json",
            split="measure",
            klass="clean",
            template_id="measure_catalog_v1",
            notes="No personal identifiers",
        )
    )

    # --- measure / tricky_fp ---
    lyrics = textwrap.dedent(
        """\
        [Verse 1]
        Eu nasci em 15/03/1985 na cidade do amor
        telefone antigo 0800 123 4567 na letra da cancao
        [Chorus]
        sol do 21 98888-0002 bate na janela
        cifra: C Am F G  D2sus9  EM7
        """
    )
    _w(measure / "tricky_fp" / "lyrics_dates.txt", lyrics)
    files.append(
        _entry(
            "measure/tricky_fp/lyrics_dates.txt",
            split="measure",
            klass="tricky_fp",
            template_id="measure_lyrics_v1",
            notes="Dates/phone-like tokens in song lyrics (entertainment context)",
        )
    )
    invalid = textwrap.dedent(
        f"""\
        Numeros de serie / placeholders (NAO sao CPF validos)
        serial: {_INVALID_CPF}
        pedido: 123.456.789-00
        ip_like: 192.168.0.1
        """
    )
    _w(measure / "tricky_fp" / "invalid_cpf_shape.txt", invalid)
    files.append(
        _entry(
            "measure/tricky_fp/invalid_cpf_shape.txt",
            split="measure",
            klass="tricky_fp",
            template_id="measure_invalid_cpf_v1",
            notes="CPF-shaped but checksum-invalid; checksum gate should suppress LGPD_CPF",
        )
    )

    # --- measure / tricky_fn (honest expected misses) ---
    masked = textwrap.dedent(
        """\
        Cadastro parcialmente mascarado (sintetico)
        Nome: Ana **** Souza
        CPF: ***.***.***-**
        documento_oculto: 5 2 9 . 9 8 2 . 2 4 7 - 2 5
        """
    )
    _w(measure / "tricky_fn" / "masked_spaced_cpf.txt", masked)
    files.append(
        _entry(
            "measure/tricky_fn/masked_spaced_cpf.txt",
            split="measure",
            klass="tricky_fn",
            template_id="measure_mask_spaced_v1",
            expected_patterns=["LGPD_CPF"],
            expected_miss=True,
            notes="Spaced/masked CPF — known FN risk; counted in recall honestly",
        )
    )
    stego_note = textwrap.dedent(
        """\
        STEGO PLACEHOLDER (Phase 1 text-only)
        Um CPF valido foi escondido em LSB de imagem em cenarios POC;
        neste arquivo nao ha digitos de CPF colados — esperado NAO detectar.
        """
    )
    _w(measure / "tricky_fn" / "stego_placeholder.txt", stego_note)
    files.append(
        _entry(
            "measure/tricky_fn/stego_placeholder.txt",
            split="measure",
            klass="tricky_fn",
            template_id="measure_stego_note_v1",
            expected_patterns=["LGPD_CPF"],
            expected_miss=True,
            notes="Documents known stego gap without embedding binary; expected miss",
        )
    )

    # --- calibrate / family B (disjoint templates + ids) ---
    cal_pii = calibrate / "pii"
    row_c = {
        "nome": _C_NAME,
        "cpf": _C_CPF,
        "cnpj": _C_CNPJ,
        "email": _C_EMAIL,
    }
    # Different narrative: invoice, not employee roster
    invoice = textwrap.dedent(
        f"""\
        NOTA FISCAL SINTETICA — CALIBRACAO (NAO REUSAR EM MEASURE)
        Cliente: {_C_NAME}
        Documento fiscal CPF: {_C_CPF}
        Emitente CNPJ: {_C_CNPJ}
        Contato: {_C_EMAIL}
        """
    )
    _w(cal_pii / "invoice_b.txt", invoice)
    _w(
        cal_pii / "invoice_b.json",
        json.dumps(row_c, ensure_ascii=False, indent=2) + "\n",
    )
    files.append(
        _entry(
            "calibrate/pii/invoice_b.txt",
            split="calibrate",
            klass="pii",
            template_id="calibrate_invoice_v1",
            expected_patterns=["LGPD_CPF", "LGPD_CNPJ", "EMAIL"],
            notes="Calibrate-only template family B",
        )
    )
    files.append(
        _entry(
            "calibrate/pii/invoice_b.json",
            split="calibrate",
            klass="pii",
            template_id="calibrate_invoice_v1",
            expected_patterns=["LGPD_CPF", "LGPD_CNPJ", "EMAIL"],
        )
    )
    cal_clean = textwrap.dedent(
        """\
        Inventario de lab: rack U12, switch port 24, VLAN lab-pb
        build_id=calibrate-only-2026
        """
    )
    _w(calibrate / "clean" / "lab_inventory.txt", cal_clean)
    files.append(
        _entry(
            "calibrate/clean/lab_inventory.txt",
            split="calibrate",
            klass="clean",
            template_id="calibrate_inventory_v1",
        )
    )
    cal_lyrics = textwrap.dedent(
        """\
        [Bridge]
        No ano de 1990-07-22 o vento mudou
        ligue 0800 765 4321 e peca a cifra Em7 A7
        """
    )
    _w(calibrate / "tricky_fp" / "bridge_lyrics.txt", cal_lyrics)
    files.append(
        _entry(
            "calibrate/tricky_fp/bridge_lyrics.txt",
            split="calibrate",
            klass="tricky_fp",
            template_id="calibrate_lyrics_v1",
            notes="Different song template than measure_lyrics_v1",
        )
    )
    cal_fn = textwrap.dedent(
        f"""\
        Redacao parcial (calibracao)
        CPF: {_C_CPF[:3]}.***.***-{_C_CPF[-2:]}
        """
    )
    _w(calibrate / "tricky_fn" / "partial_redaction.txt", cal_fn)
    files.append(
        _entry(
            "calibrate/tricky_fn/partial_redaction.txt",
            split="calibrate",
            klass="tricky_fn",
            template_id="calibrate_partial_redact_v1",
            expected_patterns=["LGPD_CPF"],
            expected_miss=True,
            notes="Partial redaction of calibrate CPF — disjoint from measure masks",
        )
    )

    manifest = {
        "version": 1,
        "issue": 835,
        "methodology": {
            "detector_tuple": (
                "sensitivity_level, pattern_detected, norm_tag, confidence 0-100"
            ),
            "classes": ["pii", "clean", "tricky_fp", "tricky_fn"],
            "splits": {
                "measure": (
                    "Final precision/recall/F1 publication. "
                    "Do not reuse these templates for confidence calibration."
                ),
                "calibrate": (
                    "Reserved for confidence-threshold tuning only. "
                    "Disjoint template_id family and synthetic identifiers "
                    "(Presidio-research anti-leakage)."
                ),
            },
            "anti_leakage": (
                "No template_id and no synthetic identifier may appear in both "
                "measure and calibrate splits."
            ),
        },
        "template_families": {
            "measure": {
                "cpf": _M_CPF,
                "cnpj": _M_CNPJ,
                "email": _M_EMAIL,
            },
            "calibrate": {
                "cpf": _C_CPF,
                "cnpj": _C_CNPJ,
                "email": _C_EMAIL,
            },
        },
        "files": files,
    }
    manifest_path = root / "ground_truth.yaml"
    manifest_path.write_text(
        yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    readme = root / "README.md"
    readme.write_text(
        textwrap.dedent(
            """\
            # F1 validation fixtures (Phase 1)

            Labeled synthetic files for detection precision/recall/F1 (#835).

            - **Manifest:** `ground_truth.yaml`
            - **Splits:** `measure/` (publish metrics) vs `calibrate/` (threshold tuning only)
            - **Harness:** `uv run python scripts/validate_detection_f1.py`
            - **Published baseline:** `docs/VALIDATION.md`

            Regenerate with:

            ```bash
            uv run python scripts/generate_f1_validation_fixtures.py
            ```
            """
        ),
        encoding="utf-8",
    )
    return manifest_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("tests/data/f1_validation"),
        help="Fixture root (default: tests/data/f1_validation)",
    )
    args = parser.parse_args()
    root = args.output.resolve()
    root.mkdir(parents=True, exist_ok=True)
    # Clear prior measure/calibrate trees for idempotent regen
    for sub in ("measure", "calibrate"):
        d = root / sub
        if d.exists():
            for p in sorted(d.rglob("*"), reverse=True):
                if p.is_file():
                    p.unlink()
                elif p.is_dir():
                    p.rmdir()
    path = build(root)
    print(f"Wrote {path} and fixtures under {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
