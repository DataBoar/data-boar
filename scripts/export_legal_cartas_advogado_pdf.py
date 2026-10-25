"""One-off export of legal_dossier CARTA *.pt_BR.md to versioned PDFs for counsel."""

from __future__ import annotations

import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT_DIR = REPO / "docs/private/legal_dossier/exports_advogado_ptBR_2026-04-08"

PAIRS: list[tuple[str, Path]] = [
    (
        "01-CISO",
        REPO
        / "docs/private/legal_dossier/CARTA_CISO_Corporate-Entity-A_CONSOLIDADA_2026-04-10.pt_BR.md",
    ),
    (
        "02-HR-Global",
        REPO
        / "docs/private/legal_dossier/CARTA_HR_GLOBAL_CONSOLIDADA_2026-04-10.pt_BR.md",
    ),
    (
        "03-Juridico-RBT-local",
        REPO
        / "docs/private/legal_dossier/CARTA_JURIDICO_RBT_LOCAL_CONSOLIDADA_2026-04-08.pt_BR.md",
    ),
    (
        "04-Lideranca-Exec",
        REPO
        / "docs/private/legal_dossier/CARTA_LIDERANCA_Corporate-Entity-A_GLOBAL_EXEC_CONSOLIDADA_2026-04-08.pt_BR.md",
    ),
    (
        "05-Risk-ERM",
        REPO
        / "docs/private/legal_dossier/CARTA_RISK_ER_Corporate-Entity-A_GLOBAL_CONSOLIDADA_2026-04-08.pt_BR.md",
    ),
    (
        "06-IR-Board-opcional",
        REPO
        / "docs/private/legal_dossier/CARTA_ESCALACAO_IR_BOARD_OPCIONAL_2026-04-08.pt_BR.md",
    ),
]


def _load_md_pdf():
    spec = importlib.util.spec_from_file_location(
        "mdpdf", REPO / "scripts/md_to_pdf_reportlab.py"
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    mdpdf = _load_md_pdf()
    for label, md in PAIRS:
        if not md.is_file():
            raise FileNotFoundError(md)
        pdf = OUT_DIR / f"advogado-2026-04-08-{label}.pdf"
        mdpdf.md_to_pdf(md, pdf)
        print(f"OK {pdf.relative_to(REPO)}")
        # Same PDF next to the source .md (e.g. CARTA_RISK_*.pt_BR.pdf) for IDE / working tree parity.
        companion = md.with_suffix(".pdf")
        mdpdf.md_to_pdf(md, companion)
        print(f"OK {companion.relative_to(REPO)}")


if __name__ == "__main__":
    main()
