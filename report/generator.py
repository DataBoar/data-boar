"""
Single report generator: reads database_findings, filesystem_findings, scan_failures from LocalDBManager
for a session; produces Excel with sheets "Report info" (session + about), "Database findings",
optional "Suggested review (LOW)" (SUGGESTED_REVIEW_ID_LIKE rows), etc.,
and heatmap image (sensitivity/risk) with about footer. Returns path to Excel file.

Branding: if api/static/mascot/data_boar_mascote_color_full.png exists, a small mascot is embedded
in the Report info sheet (cell D1, 48×48 px) and in the heatmap PNG (lower-right corner, 8% size).
The heatmap PNG is also embedded in the "Heatmap data" sheet (below the table, no overlap), scaled
to fit letter/A4 when printed (fit to one page).

Structure: generate_report() delegates all sheet writing to _write_excel_sheets() and helpers
(_build_report_info, _build_executive_summary_rows, etc.). Keep sheet logic in those helpers
so branches stay in sync with main and merge conflicts are avoided (see CONTRIBUTING.md).
"""

import logging
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable

import pandas as pd
from openpyxl.drawing.image import Image as OpenpyxlImage
from openpyxl.worksheet.properties import PageSetupProperties

from core.about import get_about_info
from core.aggregated_identification import run_aggregation
from core.database import failure_hint
from core.suggested_review import SUGGESTED_REVIEW_PATTERN
from report.scan_evidence import write_scan_evidence_artifacts

_logger = logging.getLogger(__name__)


def _heatmap_path_under_output_dir(heatmap_path: str, output_dir: str) -> Path | None:
    """
    Return resolved heatmap path only if it lies under output_dir (guards path injection
    for embedded images). Caller must pass the same output_dir used to build the heatmap.
    """
    try:
        base = Path(output_dir).resolve()
        candidate = Path(heatmap_path).resolve()
        candidate.relative_to(base)
    except (ValueError, OSError):
        return None
    return candidate if candidate.is_file() else None


# Cross-ref aggregated sheet: first row explains sampling limits (FN-first; incomplete-data transparency).
_AGGREGATED_CROSSREF_SAMPLE_NOTE_ROW: dict[str, str] = {
    "Target": "— Sample / coverage note —",
    "Source": "",
    "Table / File": "",
    "Columns involved": "",
    "Categories": "",
    "Explanation": (
        "Esta aba resume combinações de categorias quasi-identificadoras com base em achados do escaneamento "
        "(amostras por coluna/arquivo, p.ex. sample_limit), não em uma auditoria exaustiva de todos os valores. "
        "Trate as linhas como risco possível/suggested review e confirme manualmente; ausência de linhas aqui não prova ausência de risco identificável. "
        "/ This sheet reflects sampled/incomplete scanning only—not a full-population audit; treat rows as possible risk (suggested review) and confirm manually."
    ),
}

# Mascot path for report branding (Excel Report info sheet and heatmap PNG)
_REPO_ROOT = Path(__file__).resolve().parent.parent
_MASCOT_PNG = (
    _REPO_ROOT / "api" / "static" / "mascot" / "data_boar_mascote_color_full.png"
)


def _mascot_path() -> Path | None:
    """Return path to mascot PNG for report branding, or None if not found."""
    if _MASCOT_PNG.exists():
        return _MASCOT_PNG
    return None


# Optional matplotlib/seaborn for heatmap
try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import seaborn as sns

    _PLOT_AVAILABLE = True
except ImportError:
    _PLOT_AVAILABLE = False


_SENSITY_RANK = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}


def _excel_safe_sheet_title(title: str) -> str:
    """Return an Excel-safe worksheet title (max 31 chars, no []:*?/\\)."""
    invalid = set("[]:*?/\\")
    cleaned = "".join("-" if c in invalid else c for c in (title or "Sheet"))
    cleaned = cleaned.strip() or "Sheet"
    return cleaned[:31]


_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def _excel_sanitize_cell(value: object) -> object:
    """Prefix formula-like strings so Excel/openpyxl treat them as literal text (CWE-1236)."""
    if isinstance(value, str) and value.startswith(_FORMULA_PREFIXES):
        return "'" + value
    return value


def _excel_safe_dataframe(data: Any) -> pd.DataFrame:
    """Build a DataFrame with cell values sanitized against Excel formula injection."""
    df = pd.DataFrame(data)
    return df.map(_excel_sanitize_cell)


def _filter_by_min_sensitivity(rows: list[dict], min_sensitivity: str) -> list[dict]:
    """Keep only rows with sensitivity_level >= min_sensitivity (HIGH > MEDIUM > LOW)."""
    if not min_sensitivity or (min_sensitivity or "").upper() == "LOW":
        return rows
    min_rank = _SENSITY_RANK.get((min_sensitivity or "").upper(), 1)
    return [
        r
        for r in rows
        if _SENSITY_RANK.get((r.get("sensitivity_level") or "").upper(), 1) >= min_rank
    ]


def _create_heatmap(
    db_rows: list[dict],
    fs_rows: list[dict],
    output_dir: str,
    session_id: str,
    license_footer: str | None = None,
) -> str | None:
    """Build sensitivity/risk heatmap from DB + filesystem findings; save PNG with about footer. Return path or None."""
    if not _PLOT_AVAILABLE:
        return None
    rows = []
    for r in db_rows:
        rows.append(
            {
                "target": r.get("target_name", ""),
                "source": "database",
                "sensitivity": r.get("sensitivity_level", "LOW"),
            }
        )
    for r in fs_rows:
        rows.append(
            {
                "target": r.get("target_name", ""),
                "source": "filesystem",
                "sensitivity": r.get("sensitivity_level", "LOW"),
            }
        )
    if not rows:
        return None
    about = get_about_info()
    df = pd.DataFrame(rows)
    pivot = df.groupby(["target", "sensitivity"]).size().unstack(fill_value=0)
    plt.figure(figsize=(10, 6))
    sns.heatmap(
        pivot, annot=True, cmap="YlOrRd", fmt="d", cbar_kws={"label": "Findings"}
    )
    plt.title("Sensitivity / Risk Heatmap")
    # About footer on the image (detached heatmap carries app credit and license)
    footer = (
        f"{about['name']} v{about['version']} · {about['author']} · {about['license']}"
    )
    if license_footer:
        footer = f"{footer} · {license_footer}"
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.12)
    plt.figtext(0.5, 0.02, footer, ha="center", fontsize=7, style="italic")
    # Small mascot branding in lower-right corner (minimal, professional)
    mascot = _mascot_path()
    if mascot:
        try:
            from matplotlib.image import imread
            from mpl_toolkits.axes_grid1.inset_locator import inset_axes

            img = imread(mascot)
            ax = plt.gca()
            ax_inset = inset_axes(
                ax, width="8%", height="8%", loc="lower right", borderpad=0.35
            )
            ax_inset.imshow(img)
            ax_inset.axis("off")
        except Exception:
            pass
    out_path = Path(output_dir) / f"heatmap_{session_id[:12]}.png"
    plt.savefig(out_path, bbox_inches="tight")
    plt.close()
    return str(out_path)


# Keywords that suggest existing data protection (column name or pattern_detected)
_PRAISE_KEYWORDS = (
    "encrypted",
    "hash",
    "hashed",
    "tokenized",
    "token",
    "masked",
    "mask",
    "pseudonym",
    "anon",
    "redact",
    "hmac",
    "cipher",
)

# Patterns/names that suggest identifier or health (for minor cross-reference: same table has DOB/minor + name/doc/health)
_IDENTIFIER_OR_HEALTH_PATTERNS = ("LGPD_CPF", "CCPA_SSN", "EMAIL", "CPF", "SSN", "RG")
_IDENTIFIER_OR_HEALTH_COLUMN_TOKENS = (
    "nome",
    "name",
    "cpf",
    "rg",
    "ssn",
    "health",
    "saude",
    "cid",
    "prontuario",
    "diagnostic",
    "identidade",
    "identity",
    "documento",
    "document",
    "nascimento",
    "birth",
)

# Recommendation sheet column names (Excel output; avoid string literal duplication for Sonar S1192)
_REC_DATA_PATTERN = "Data / Pattern"
_REC_BASE_LEGAL = "Base legal"
_REC_RISCO = "Risco"
_REC_RECOMENDACAO = "Recomendação"
_REC_PRIORIDADE = "Prioridade"
_REC_RELEVANTE_PARA = "Relevante para"
_REC_DEFAULT_RELEVANTE = "DPO, Segurança da Informação"
_REC_PRIORITY_CRITICA = "CRÍTICA"

# Trends sheet column names and metric labels (S1192)
_TREND_THIS_RUN_COUNT = "This run (count)"
_TREND_THIS_RUN_DATE = "This run (date)"
_TREND_PREV_RUN_COUNT = "Previous run (count)"
_TREND_PREV_RUN_DATE = "Previous run (date)"
_TREND_PREV_1_COUNT = "Prev run 1 (count)"
_TREND_PREV_1_DATE = "Prev run 1 (date)"
_TREND_PREV_2_COUNT = "Prev run 2 (count)"
_TREND_PREV_2_DATE = "Prev run 2 (date)"
_TREND_PREV_3_COUNT = "Prev run 3 (count)"
_TREND_PREV_3_DATE = "Prev run 3 (date)"
_MAX_PREV_RUNS = 3
_METRIC_TOTAL_FINDINGS = "Total findings (DB + filesystem)"
_METRIC_TOTAL_FINDINGS_LABEL = "Total findings"
_METRIC_DB_FINDINGS = "Database findings"
_METRIC_FS_FINDINGS = "Filesystem findings"
_METRIC_SCAN_FAILURES = "Scan failures (targets not scanned)"
_METRIC_SCAN_FAILURES_LABEL = "Scan failures"
_SHEET_DB_FINDINGS = "Database findings"
_SHEET_FS_FINDINGS = "Filesystem findings"
_SHEET_SCAN_FAILURES = "Scan failures"
_SHEET_REPORT_INFO = "Report info"
_SHEET_HEATMAP_DATA = "Heatmap data"
_SHEET_DATA_SOURCE_INVENTORY = "Data source inventory"
# LOW findings persisted for ID-like column names (FN reduction); see core.suggested_review
_SHEET_SUGGESTED_REVIEW = "Suggested review (LOW)"
_SHEET_PRAISE_CONTROLS = _excel_safe_sheet_title("Praise / existing controls")
_REPORT_INFO_CNPJ_FORMAT_COMPAT = "CNPJ format compatibility"


def _change_note(curr: int, prev_val: int | None, metric_label: str) -> str:
    """Build a human-readable note for trends: first run, improvement, new/increased, or no change."""
    if prev_val is None:
        return "First run or no previous session to compare."
    delta = curr - prev_val
    if delta < 0:
        return f"Improvement: {metric_label} reduced by {abs(delta)} (fewer violations or sensitive data exposure)."
    if delta > 0:
        return f"New or increased: {metric_label} increased by {delta} – review sheet for details; may require DPO action."
    return "No change from previous run."


def _change_note_aggregate(
    current_count: int,
    prev_values: list[int],
    metric_label: str,
) -> str:
    """
    Build an insightful note across up to 3 previous runs: first run, improvement, increase, or trend summary.
    Keeps the note helpful for DPO and security team (similar to single-run note where applicable).
    """
    if not prev_values:
        return "First run or no previous session to compare."
    prev_1 = prev_values[0]
    delta_1 = current_count - prev_1
    n = len(prev_values)

    if n == 1:
        return _change_note(current_count, prev_1, metric_label)

    # Two or three previous runs: summarize trend
    if delta_1 < 0:
        # Improvement vs most recent
        if all(current_count <= v for v in prev_values):
            return f"Improvement over last {n} runs: {metric_label} reduced or stable (sustained trend)."
        return f"Improvement: {metric_label} reduced by {abs(delta_1)} vs previous run; compare with earlier runs above."
    if delta_1 > 0:
        increases = sum(1 for v in prev_values if current_count > v)
        if increases >= 2:
            return f"Increase in {increases} of last {n} runs – review sheet for details; may require DPO action."
        return f"New or increased: {metric_label} up by {delta_1} vs previous run – review sheet for details; may require DPO action."
    # No change vs previous
    if all(current_count == v for v in prev_values):
        return f"No change over last {n} runs; trend stable."
    return "No change from previous run."


def _one_trend_row(
    metric_display: str,
    current_count: int,
    current_started_at: str | None,
    prev_runs: list[dict],
    get_prev_value: Callable[[dict], int],
    note_label: str,
) -> dict:
    """Build a single row for the Trends sheet (this run vs up to 3 previous runs)."""
    prev_values = [get_prev_value(p) for p in prev_runs]
    prev_1_val = prev_values[0] if prev_values else None
    # Pad to _MAX_PREV_RUNS for consistent columns
    counts: list[int | str] = [
        prev_values[i] if i < len(prev_values) else "-" for i in range(_MAX_PREV_RUNS)
    ]
    dates: list[str] = [
        (prev_runs[i].get("started_at") or "-") if i < len(prev_runs) else "-"
        for i in range(_MAX_PREV_RUNS)
    ]
    return {
        "Metric": metric_display,
        _TREND_THIS_RUN_COUNT: current_count,
        _TREND_THIS_RUN_DATE: current_started_at or "-",
        _TREND_PREV_1_COUNT: counts[0],
        _TREND_PREV_1_DATE: dates[0],
        _TREND_PREV_2_COUNT: counts[1],
        _TREND_PREV_2_DATE: dates[1],
        _TREND_PREV_3_COUNT: counts[2],
        _TREND_PREV_3_DATE: dates[2],
        "Change": (current_count - prev_1_val) if prev_1_val is not None else "-",
        "Note": _change_note_aggregate(current_count, prev_values, note_label),
    }


def _row_suggests_identifier_or_health(row: dict) -> bool:
    """True if finding suggests name, official doc (CPF/RG/SSN), or health data (for cross-reference with possible minor)."""
    pat = (row.get("pattern_detected") or "").upper()
    col = (row.get("column_name") or row.get("file_name") or "").lower()
    for p in _IDENTIFIER_OR_HEALTH_PATTERNS:
        if p in pat:
            return True
    for t in _IDENTIFIER_OR_HEALTH_COLUMN_TOKENS:
        if t in col:
            return True
    return False


def _high_confidence_keys_for_groups(
    rows: list[dict],
    group_key: Callable[[dict], tuple],
    row_key: Callable[[dict], tuple],
) -> set[tuple]:
    """
    Group rows by group_key; for each group that has both DOB_POSSIBLE_MINOR and identifier/health
    findings, collect row_key(r) for every row in that group with DOB_POSSIBLE_MINOR. Return the set.
    """
    grouped: dict[tuple, list[dict]] = defaultdict(list)
    for r in rows:
        grouped[group_key(r)].append(r)
    result: set[tuple] = set()
    for group_rows in grouped.values():
        has_minor = any(
            "DOB_POSSIBLE_MINOR" in (r.get("pattern_detected") or "")
            for r in group_rows
        )
        has_id_or_health = any(
            _row_suggests_identifier_or_health(r) for r in group_rows
        )
        if not (has_minor and has_id_or_health):
            continue
        for r in group_rows:
            if "DOB_POSSIBLE_MINOR" in (r.get("pattern_detected") or ""):
                result.add(row_key(r))
    return result


def _minor_cross_reference_confidence(
    db_rows: list[dict],
    fs_rows: list[dict],
) -> tuple[set[tuple], set[tuple]]:
    """
    When DOB_POSSIBLE_MINOR appears in the same table (or same file) as identifier/health findings,
    return sets of keys for which to show 'high (cross-ref)' minor confidence.
    Returns (db_keys, fs_keys). DB key = (target_name, schema_name, table_name, column_name); FS key = (target_name, path, file_name).
    """
    db_high = _high_confidence_keys_for_groups(
        db_rows,
        lambda r: (
            r.get("target_name", ""),
            r.get("schema_name", ""),
            r.get("table_name", ""),
        ),
        lambda r: (
            r.get("target_name", ""),
            r.get("schema_name", ""),
            r.get("table_name", ""),
            r.get("column_name", ""),
        ),
    )
    fs_high = _high_confidence_keys_for_groups(
        fs_rows,
        lambda r: (r.get("target_name", ""), r.get("path", "")),
        lambda r: (r.get("target_name", ""), r.get("path", ""), r.get("file_name", "")),
    )
    return db_high, fs_high


def _apply_minor_confidence_column(
    rows: list[dict],
    high_confidence_keys: set[tuple],
    key_getter: Callable[[dict], tuple],
) -> None:
    """Mutate each row to add 'Minor confidence' = 'high (cross-ref)' for keys in high_confidence_keys, else ''."""
    for r in rows:
        k = key_getter(r)
        r["Minor confidence"] = "high (cross-ref)" if k in high_confidence_keys else ""


def _praise_rows(db_rows: list[dict], fs_rows: list[dict]) -> list[dict]:
    """
    Build rows for "Praise / existing controls": findings where column name or pattern_detected
    suggests existing protections (encryption, hashing, tokenization, masking, etc.).
    """
    rows = []
    for r, source in [(x, "database") for x in db_rows] + [
        (x, "filesystem") for x in fs_rows
    ]:
        col = (r.get("column_name") or r.get("file_name") or "").lower()
        pat = (r.get("pattern_detected") or "").lower()
        combined = f"{col} {pat}"
        for kw in _PRAISE_KEYWORDS:
            if kw in combined:
                rows.append(
                    {
                        "Target": r.get("target_name", ""),
                        "Source": source,
                        "Column / File": r.get("column_name")
                        or r.get("file_name")
                        or "-",
                        "Pattern detected": r.get("pattern_detected", ""),
                        "Indication": f"Possible protection: '{kw}'",
                    }
                )
                break
    return rows


def _find_override_row(pat: str, norm: str, overrides: list[dict]) -> dict | None:
    """
    Find first override whose norm_tag_pattern matches norm (substring match both ways).

    Matching uses inclusive substring semantics: the pattern matches if it appears inside
    ``norm`` *or* ``norm`` appears inside the pattern (so short tags still match longer
    ``norm_tag`` text). **List order matters:** put **more specific** ``norm_tag_pattern``
    entries **before** generic ones (e.g. ``UK GDPR`` before ``GDPR``), otherwise a broad
    pattern listed first will win and the specific row is never used.

    Return a recommendation row dict built from that override, or None.
    """
    for o in overrides:
        pattern_str = (o.get("norm_tag_pattern") or "").strip()
        if not pattern_str or (pattern_str not in norm and norm not in pattern_str):
            continue
        return {
            _REC_DATA_PATTERN: pat,
            _REC_BASE_LEGAL: o.get("base_legal", norm or "-"),
            _REC_RISCO: o.get("risk", "-"),
            _REC_RECOMENDACAO: o.get("recommendation", "-"),
            _REC_PRIORIDADE: o.get("priority", "MÉDIA"),
            _REC_RELEVANTE_PARA: o.get("relevant_for", _REC_DEFAULT_RELEVANTE),
        }
    return None


def _recommendation_row_for_pattern(pat: str, norm: str) -> dict:
    """
    Build a single recommendation row from pattern_detected and norm_tag.
    Priority: minor (Art. 14) > PII_AMBIGUOUS (confirm manually) > CPF/SSN/LGPD > EMAIL > CREDIT/CARD > default.
    """
    norm_lower = norm.lower()
    if "FUZZY_COLUMN_MATCH" in pat:
        return {
            _REC_DATA_PATTERN: pat,
            _REC_BASE_LEGAL: norm
            or "Possible personal data (fuzzy column name – confirm manually)",
            _REC_RISCO: "Nome de coluna grafado de forma próxima a um termo sensível da lista ML/DL; confirmação humana recomendada.",
            _REC_RECOMENDACAO: (
                "Confirmar manualmente se a coluna contém dado pessoal. Se for falso positivo, ajuste termos em "
                "ml_patterns_file / dl_patterns_file ou desative fuzzy_column_match / aumente fuzzy_column_match_min_ratio."
            ),
            _REC_PRIORIDADE: "MÉDIA",
            _REC_RELEVANTE_PARA: "Operador, DPO, Segurança da Informação",
        }
    if "PII_AMBIGUOUS" in pat or "Generic identifier" in norm:
        return {
            _REC_DATA_PATTERN: pat,
            _REC_BASE_LEGAL: norm or "Generic identifier – confirm manually",
            _REC_RISCO: "Nome de coluna genérico (doc_id, document_id, id_number, etc.). Pode ser PII ou ID interno.",
            _REC_RECOMENDACAO: (
                "Confirmar manualmente: verificar se a coluna contém dado pessoal (PII) ou apenas identificador interno. "
                "Se for PII, aplicar controles de acesso e base legal; se for interno, pode ser tratado como MÉDIA prioridade."
            ),
            _REC_PRIORIDADE: "MÉDIA",
            _REC_RELEVANTE_PARA: "Operador, DPO, Segurança da Informação",
        }
    if "DOB_POSSIBLE_MINOR" in pat or (
        "LGPD Art. 14" in norm and ("menor" in norm_lower or "minor" in norm_lower)
    ):
        return {
            _REC_DATA_PATTERN: pat,
            _REC_BASE_LEGAL: norm
            or "LGPD Art. 14 (dados de crianças/adolescentes); GDPR Art. 8 (consentimento em serviços da sociedade da informação)",
            _REC_RISCO: "Dados que podem se referir a menores de idade: tratamento sujeito a bases legais específicas, consentimento do titular ou dos pais/responsáveis e restrições de armazenamento, uso e compartilhamento.",
            _REC_RECOMENDACAO: (
                "Caso especial – dados de menores: (1) Garantir base legal e consentimento válido (titular ou responsável, conforme a idade e a lei aplicável). "
                "(2) Restringir armazenamento ao estritamente necessário; evitar retenção além do prazo. "
                "(3) Limitar uso e compartilhamento ao que for autorizado; não compartilhar com terceiros sem base legal e consentimento. "
                "(4) Revisar políticas de privacidade e termos para tratamento de dados de crianças/adolescentes (LGPD Art. 14; GDPR Art. 8). "
                "(5) Priorizar anonimização ou pseudonimização quando possível; controle de acesso rigoroso."
            ),
            _REC_PRIORIDADE: _REC_PRIORITY_CRITICA,
            _REC_RELEVANTE_PARA: "DPO, Compliance, Área jurídica, Segurança da Informação",
        }
    if "CPF" in pat or "SSN" in pat or "LGPD" in norm:
        return {
            _REC_DATA_PATTERN: pat,
            _REC_BASE_LEGAL: norm or "LGPD/GDPR – identificação direta",
            _REC_RISCO: "Identificação direta de pessoa natural (dados de cadastro/identidade).",
            _REC_RECOMENDACAO: "Anonimização ou hashing; restringir acesso (Least Privilege); revisar base legal e minimização.",
            _REC_PRIORIDADE: _REC_PRIORITY_CRITICA,
            _REC_RELEVANTE_PARA: "DPO, Segurança da Informação, Compliance",
        }
    if "EMAIL" in pat:
        return {
            _REC_DATA_PATTERN: pat,
            _REC_BASE_LEGAL: norm or "LGPD/GDPR – contato eletrônico",
            _REC_RISCO: "Vazamento de endereços de e-mail e possível uso indevido em campanhas/comunicações.",
            _REC_RECOMENDACAO: "Criptografia da coluna; revisão de logs de acesso; validação de consentimento e opt-out.",
            _REC_PRIORIDADE: "ALTA",
            _REC_RELEVANTE_PARA: "DPO, Marketing, Segurança da Informação",
        }
    if "CREDIT" in pat or "CARD" in pat:
        return {
            _REC_DATA_PATTERN: pat,
            _REC_BASE_LEGAL: norm or "LGPD/GDPR – dados financeiros / PCI-DSS",
            _REC_RISCO: "Fraude financeira, chargeback e exposição de dados de cartão/conta.",
            _REC_RECOMENDACAO: "Não armazenar número completo; tokenização; mascaramento; conformidade PCI-DSS e políticas internas.",
            _REC_PRIORIDADE: _REC_PRIORITY_CRITICA,
            _REC_RELEVANTE_PARA: "DPO, Segurança da Informação, Risco/Compliance financeiro",
        }
    return {
        _REC_DATA_PATTERN: pat,
        _REC_BASE_LEGAL: norm or "LGPD/GDPR/CCPA – dado pessoal ou sensível",
        _REC_RISCO: "Dado pessoal ou sensível com possível aumento de superfície de exposição.",
        _REC_RECOMENDACAO: "Avaliar necessidade do tratamento; aplicar pseudonimização ou criptografia; reforçar controle de acesso.",
        _REC_PRIORIDADE: "MÉDIA",
        _REC_RELEVANTE_PARA: _REC_DEFAULT_RELEVANTE,
    }


def _is_minor_recommendation_row(row: dict) -> bool:
    """True if row is a minor-related recommendation (for sorting)."""
    pat = (row.get(_REC_DATA_PATTERN) or "").strip()
    base = (row.get(_REC_BASE_LEGAL) or "").lower()
    return "DOB_POSSIBLE_MINOR" in pat or (
        "art. 14" in base and ("menor" in base or "minor" in base or "child" in base)
    )


def _recommendations_rows(
    db_rows: list[dict],
    fs_rows: list[dict],
    recommendation_overrides: list[dict] | None = None,
) -> list[dict]:
    """
    Build recommendations from unique pattern_detected and norm_tag.
    Each row explains what kind of personal/sensitive data was inferred, which legal norm might apply,
    why it matters (risk description), and what action DPO / Security / Compliance teams should consider.
    If recommendation_overrides is provided, entries are matched by norm_tag (substring or exact);
    keys: norm_tag_pattern, base_legal, risk, recommendation, priority, relevant_for.
    """
    overrides = recommendation_overrides or []
    seen: set[tuple[str, str]] = set()
    recs: list[dict] = []
    for r in db_rows + fs_rows:
        pat = r.get("pattern_detected") or ""
        norm = r.get("norm_tag") or ""
        if (pat, norm) in seen or not pat:
            continue
        seen.add((pat, norm))
        override_row = _find_override_row(pat, norm, overrides)
        if override_row is not None:
            recs.append(override_row)
            continue
        recs.append(_recommendation_row_for_pattern(pat, norm))
    if not recs:
        recs.append(
            {
                _REC_DATA_PATTERN: "-",
                _REC_BASE_LEGAL: "-",
                _REC_RISCO: "Nenhum achado crítico nesta sessão",
                _REC_RECOMENDACAO: "Manter boas práticas de proteção de dados.",
                _REC_PRIORIDADE: "INFO",
                _REC_RELEVANTE_PARA: _REC_DEFAULT_RELEVANTE,
            }
        )
    recs.sort(
        key=lambda r: (
            0 if _is_minor_recommendation_row(r) else 1,
            r.get(_REC_DATA_PATTERN, ""),
        )
    )
    return recs


def _trends_rows(
    db_manager: Any,
    session_id: str,
    current_db: int,
    current_fs: int,
    current_fail: int,
    current_started_at: str | None,
) -> list[dict]:
    """
    Build rows for "Trends - Session comparison": compare this run with up to 3 previous runs
    to show improvements (fewer findings) or new or increased findings for DPO and security team.
    Columns include Prev run 1/2/3 (count and date) for better aggregate trend view; Note stays insightful.
    """
    prev_runs: list[dict] = []
    if hasattr(db_manager, "get_previous_sessions"):
        prev_runs = db_manager.get_previous_sessions(session_id, limit=_MAX_PREV_RUNS)
    elif hasattr(db_manager, "get_previous_session"):
        prev = db_manager.get_previous_session(session_id)
        if prev:
            prev_runs = [prev]

    total_current = current_db + current_fs

    def total_findings(s: dict) -> int:
        return (s.get("database_findings") or 0) + (s.get("filesystem_findings") or 0)

    rows: list[dict] = []
    rows.append(
        _one_trend_row(
            _METRIC_TOTAL_FINDINGS,
            total_current,
            current_started_at,
            prev_runs,
            total_findings,
            _METRIC_TOTAL_FINDINGS_LABEL,
        )
    )
    rows.append(
        _one_trend_row(
            _METRIC_DB_FINDINGS,
            current_db,
            current_started_at,
            prev_runs,
            lambda s: s.get("database_findings") or 0,
            _METRIC_DB_FINDINGS,
        )
    )
    rows.append(
        _one_trend_row(
            _METRIC_FS_FINDINGS,
            current_fs,
            current_started_at,
            prev_runs,
            lambda s: s.get("filesystem_findings") or 0,
            _METRIC_FS_FINDINGS,
        )
    )
    rows.append(
        _one_trend_row(
            _METRIC_SCAN_FAILURES,
            current_fail,
            current_started_at,
            prev_runs,
            lambda s: s.get("scan_failures") or 0,
            _METRIC_SCAN_FAILURES_LABEL,
        )
    )
    return rows


def _get_session_metadata(db_manager: Any, session_id: str) -> dict[str, Any]:
    """Return started_at, finished_at, tenant_name, technician_name, config_scope_hash, jurisdiction_hint."""
    for s in db_manager.list_sessions() or []:
        if s.get("session_id") == session_id:
            return {
                "started_at": s.get("started_at"),
                "finished_at": s.get("finished_at"),
                "tenant_name": s.get("tenant_name"),
                "technician_name": s.get("technician_name"),
                "config_scope_hash": s.get("config_scope_hash"),
                "jurisdiction_hint": bool(s.get("jurisdiction_hint")),
            }
    return {
        "started_at": None,
        "finished_at": None,
        "tenant_name": None,
        "technician_name": None,
        "config_scope_hash": None,
        "jurisdiction_hint": False,
    }


def _build_suggested_review_rows(
    db_rows: list[dict],
    fs_rows: list[dict],
    config: dict | None,
) -> list[dict]:
    """
    Rows for the Suggested review sheet: findings stored as LOW with SUGGESTED_REVIEW_ID_LIKE.

    Built from **unfiltered** session rows so they still appear when report.min_sensitivity
    hides LOW from the main findings sheets.
    """
    cfg = config or {}
    report_cfg = cfg.get("report", {}) if isinstance(cfg.get("report"), dict) else {}
    if not report_cfg.get("include_suggested_review_sheet", True):
        return []
    out: list[dict] = []
    for r in db_rows:
        if r.get("pattern_detected") != SUGGESTED_REVIEW_PATTERN:
            continue
        out.append(
            {
                "Source": "database",
                "Target": r.get("target_name", ""),
                "Schema": r.get("schema_name", ""),
                "Table": r.get("table_name", ""),
                "Column": r.get("column_name", ""),
                "Data type": r.get("data_type", ""),
                "Sensitivity": r.get("sensitivity_level", ""),
                "Pattern": r.get("pattern_detected", ""),
                "Norm / note": r.get("norm_tag", ""),
                "ML confidence": r.get("ml_confidence", ""),
            }
        )
    for r in fs_rows:
        if r.get("pattern_detected") != SUGGESTED_REVIEW_PATTERN:
            continue
        out.append(
            {
                "Source": "filesystem",
                "Target": r.get("target_name", ""),
                "Schema": "",
                "Table": "",
                "Column": r.get("file_name", ""),
                "Data type": r.get("data_type", ""),
                "Sensitivity": r.get("sensitivity_level", ""),
                "Pattern": r.get("pattern_detected", ""),
                "Norm / note": r.get("norm_tag", ""),
                "ML confidence": r.get("ml_confidence", ""),
            }
        )
    return out


def _remove_suggested_review_from_main_sheets(
    db_rows: list[dict],
    fs_rows: list[dict],
    report_cfg: dict,
) -> tuple[list[dict], list[dict]]:
    """
    When the Suggested review sheet is enabled, drop SUGGESTED_REVIEW_ID_LIKE rows from
    Database/Filesystem findings so they are not duplicated (they remain on Suggested review).
    """
    if not report_cfg.get("include_suggested_review_sheet", True):
        return db_rows, fs_rows

    def _keep(r: dict) -> bool:
        return r.get("pattern_detected") != SUGGESTED_REVIEW_PATTERN

    return [r for r in db_rows if _keep(r)], [r for r in fs_rows if _keep(r)]


def _get_report_config_and_filtered_rows(
    config: dict | None,
    db_rows: list[dict],
    fs_rows: list[dict],
) -> tuple[dict, list[dict], list[dict]]:
    """Return (report_cfg, db_rows_for_sheets, fs_rows_for_sheets) with min_sensitivity applied."""
    cfg = config or {}
    report_cfg = cfg.get("report", {}) if isinstance(cfg.get("report"), dict) else {}
    min_sens = (report_cfg.get("min_sensitivity") or "LOW").upper()
    if min_sens != "LOW":
        return (
            report_cfg,
            _filter_by_min_sensitivity(db_rows, min_sens),
            _filter_by_min_sensitivity(fs_rows, min_sens),
        )
    return report_cfg, db_rows, fs_rows


def _build_executive_summary_rows(
    db_rows: list[dict], fs_rows: list[dict]
) -> list[dict]:
    """Build rows for Executive summary sheet: by sensitivity, by norm_tag, top targets."""
    all_findings = db_rows + fs_rows
    exec_rows: list[dict] = []
    for level in ("HIGH", "MEDIUM", "LOW"):
        count = sum(
            1
            for r in all_findings
            if (r.get("sensitivity_level") or "").upper() == level
        )
        exec_rows.append(
            {"Metric": "Findings by sensitivity", "Category": level, "Count": count}
        )
    norm_counts: dict[str, int] = {}
    for r in all_findings:
        nt = (r.get("norm_tag") or "").strip() or "(no norm_tag)"
        norm_counts[nt] = norm_counts.get(nt, 0) + 1
    for nt, count in sorted(norm_counts.items(), key=lambda x: -x[1]):
        exec_rows.append(
            {"Metric": "Findings by Framework / Norm", "Category": nt, "Count": count}
        )
    target_counts: dict[str, int] = {}
    for r in all_findings:
        t = (r.get("target_name") or "").strip() or "(unknown)"
        target_counts[t] = target_counts.get(t, 0) + 1
    for t, count in sorted(target_counts.items(), key=lambda x: -x[1])[:10]:
        exec_rows.append(
            {"Metric": "Top targets by finding count", "Category": t, "Count": count}
        )
    return exec_rows


def _apply_minor_confidence_and_return_keys(
    db_rows: list[dict],
    fs_rows: list[dict],
    config: dict | None,
) -> tuple[set[tuple], set[tuple]]:
    """
    If minor_cross_reference is enabled, compute high-confidence keys and set "Minor confidence" on rows; else clear it.
    Returns (db_high_keys, fs_high_keys) for use when prepending recommendation rows.
    """
    detection_cfg = (config or {}).get("detection") or {}
    if not detection_cfg.get("minor_cross_reference", True):
        for r in db_rows + fs_rows:
            r["Minor confidence"] = ""
        return set(), set()
    db_high_keys, fs_high_keys = _minor_cross_reference_confidence(db_rows, fs_rows)
    _apply_minor_confidence_column(
        db_rows,
        db_high_keys,
        lambda r: (
            r.get("target_name", ""),
            r.get("schema_name", ""),
            r.get("table_name", ""),
            r.get("column_name", ""),
        ),
    )
    _apply_minor_confidence_column(
        fs_rows,
        fs_high_keys,
        lambda r: (r.get("target_name", ""), r.get("path", ""), r.get("file_name", "")),
    )
    return db_high_keys, fs_high_keys


def _enrich_failures(fail_rows: list[dict]) -> list[dict]:
    """Add Category, Impact, Suggested next step to each failure row for the Scan failures sheet."""
    return [
        {
            **r,
            "Category": r.get("reason") or "error",
            "Impact": "Target was not fully scanned; overall coverage for this environment is incomplete until this issue is fixed.",
            "Suggested next step": failure_hint(r.get("reason") or "error"),
        }
        for r in fail_rows
    ]


def _aggregated_identification_recommendation_row() -> dict:
    """Recommendation row for aggregated identification risk (cross-category re-identification)."""
    return {
        _REC_DATA_PATTERN: "AGGREGATED_IDENTIFICATION",
        _REC_BASE_LEGAL: "LGPD Art. 5 (dado pessoal); GDPR Recital 26 (identifiability – combination of data may identify individuals)",
        _REC_RISCO: (
            "Dados de múltiplas colunas ou fontes (ex.: gênero, cargo, saúde, endereço, telefone) na mesma tabela/arquivo "
            "podem permitir identificação ou reidentificação de pessoas. "
            "Why flagged: múltiplas categorias detectadas no mesmo alvo. "
            "A detecção baseia-se em amostras de escaneamento (não no universo completo); tratar como risco possível/suggested review para DPO e compliance."
        ),
        _REC_RECOMENDACAO: (
            "Avaliar controles de acesso e limitação de finalidade; considerar anonimização ou pseudonimização; "
            "documentar base legal para o tratamento combinado (LGPD Art. 5; GDPR Recital 26). "
            "What to confirm: validar manualmente se a combinação realmente identifica titulares com os dados reais, "
            "especialmente quando sample_limit for baixo ou houver falhas de scan."
        ),
        _REC_PRIORIDADE: "ALTA",
        _REC_RELEVANTE_PARA: "DPO, Compliance, Segurança da Informação",
    }


def _minor_crossref_recommendation_row() -> dict:
    """Recommendation row when DOB_POSSIBLE_MINOR is cross-referenced with identifier/health findings."""
    return {
        _REC_DATA_PATTERN: "DOB_POSSIBLE_MINOR (high confidence – cross-ref)",
        _REC_BASE_LEGAL: "LGPD Art. 14 (dados de crianças/adolescentes); GDPR Art. 8 (consentimento em serviços da sociedade da informação)",
        _REC_RISCO: "Mesma tabela/arquivo contém data de nascimento sugerindo menor e dados identificadores ou de saúde; tratar como alta prioridade para DPO.",
        _REC_RECOMENDACAO: (
            "Caso especial – dados de menores: confirmar base legal e consentimento (titular ou responsável, conforme a idade e a lei aplicável); "
            "restringir acesso e retenção ao estritamente necessário; priorizar anonimização ou pseudonimização."
        ),
        _REC_PRIORIDADE: _REC_PRIORITY_CRITICA,
        _REC_RELEVANTE_PARA: "DPO, Compliance, Área jurídica, Segurança da Informação",
    }


def _write_excel_sheets(
    writer: Any,
    session_id: str,
    report_cfg: dict,
    db_rows_for_sheets: list[dict],
    fs_rows_for_sheets: list[dict],
    config: dict | None,
    fail_rows: list[dict],
    db_manager: Any,
    current_db: int,
    current_fs: int,
    current_fail: int,
    current_started_at: str | None,
    report_info: list[dict],
    output_dir: str,
    heatmap_path: str | None = None,
    suggested_review_rows: list[dict] | None = None,
) -> None:
    """Write all Excel sheets (Report info, Executive summary, findings, recommendations, trends, heatmap data)."""
    _excel_safe_dataframe(report_info).to_excel(
        writer, sheet_name=_SHEET_REPORT_INFO, index=False
    )
    # Small mascot branding in top-right of Report info (D1), minimal; table stays in A:B
    mascot = _mascot_path()
    if mascot:
        try:
            ws = writer.sheets[_SHEET_REPORT_INFO]
            img = OpenpyxlImage(str(mascot))
            img.width = 48
            img.height = 48
            ws.add_image(img, "D1")
        except Exception:
            pass
    if report_cfg.get("include_executive_summary", False) and (
        db_rows_for_sheets or fs_rows_for_sheets
    ):
        _excel_safe_dataframe(
            _build_executive_summary_rows(db_rows_for_sheets, fs_rows_for_sheets)
        ).to_excel(writer, sheet_name="Executive summary", index=False)
    db_high_keys, fs_high_keys = _apply_minor_confidence_and_return_keys(
        db_rows_for_sheets, fs_rows_for_sheets, config
    )
    if db_rows_for_sheets:
        _excel_safe_dataframe(db_rows_for_sheets).to_excel(
            writer, sheet_name=_SHEET_DB_FINDINGS, index=False
        )
    if fs_rows_for_sheets:
        _excel_safe_dataframe(fs_rows_for_sheets).to_excel(
            writer, sheet_name=_SHEET_FS_FINDINGS, index=False
        )
    sr = suggested_review_rows or []
    if sr:
        _excel_safe_dataframe(sr).to_excel(
            writer, sheet_name=_SHEET_SUGGESTED_REVIEW, index=False
        )
    agg_rows = db_manager.get_aggregated_identification_risks(session_id)
    if agg_rows:
        sheet_data = [
            {
                "Target": r.get("target_name", ""),
                "Source": r.get("source_type", ""),
                "Table / File": r.get("table_or_file", ""),
                "Columns involved": r.get("columns_involved", ""),
                "Categories": r.get("categories", ""),
                "Explanation": r.get("explanation", ""),
            }
            for r in agg_rows
        ]
        sheet_with_note = [_AGGREGATED_CROSSREF_SAMPLE_NOTE_ROW] + sheet_data
        _excel_safe_dataframe(sheet_with_note).to_excel(
            writer, sheet_name="Cross-ref data – ident. risk", index=False
        )
    if fail_rows:
        _excel_safe_dataframe(_enrich_failures(fail_rows)).to_excel(
            writer, sheet_name=_SHEET_SCAN_FAILURES, index=False
        )
    inv_rows = []
    if hasattr(db_manager, "get_data_source_inventory"):
        inv_rows = db_manager.get_data_source_inventory(session_id) or []
    if inv_rows:
        inv_sheet_rows = [
            {
                "Target": r.get("target_name", ""),
                "Source type": r.get("source_type", ""),
                "Product": r.get("product", "") or "",
                "Product version": r.get("product_version", "") or "",
                "Protocol/API version": r.get("protocol_or_api_version", "") or "",
                "Transport security": r.get("transport_security", "") or "",
                "Raw details": r.get("raw_details", "") or "",
            }
            for r in inv_rows
        ]
        _excel_safe_dataframe(inv_sheet_rows).to_excel(
            writer, sheet_name=_SHEET_DATA_SOURCE_INVENTORY, index=False
        )
    overrides = report_cfg.get("recommendation_overrides", [])
    recs = _recommendations_rows(
        db_rows_for_sheets,
        fs_rows_for_sheets,
        recommendation_overrides=overrides if overrides else None,
    )
    if agg_rows:
        recs.insert(0, _aggregated_identification_recommendation_row())
    if db_high_keys or fs_high_keys:
        recs.insert(0, _minor_crossref_recommendation_row())
    _excel_safe_dataframe(recs).to_excel(
        writer, sheet_name="Recommendations", index=False
    )
    praise = _praise_rows(db_rows_for_sheets, fs_rows_for_sheets)
    if praise:
        _excel_safe_dataframe(praise).to_excel(
            writer, sheet_name=_SHEET_PRAISE_CONTROLS, index=False
        )
    trends = _trends_rows(
        db_manager, session_id, current_db, current_fs, current_fail, current_started_at
    )
    _excel_safe_dataframe(trends).to_excel(
        writer, sheet_name="Trends - Session comparison", index=False
    )
    heatmap_rows = [
        {"target": r.get("target_name"), "sensitivity": r.get("sensitivity_level")}
        for r in db_rows_for_sheets + fs_rows_for_sheets
    ]
    if heatmap_rows:
        summary = (
            pd.DataFrame(heatmap_rows)
            .groupby(["target", "sensitivity"])
            .size()
            .unstack(fill_value=0)
        )
        summary.to_excel(writer, sheet_name=_SHEET_HEATMAP_DATA)
        # Embed heatmap image below the table (no overlap); scale to fit letter/A4 when printed
        safe_heatmap = (
            _heatmap_path_under_output_dir(heatmap_path, output_dir)
            if heatmap_path
            else None
        )
        if safe_heatmap:
            try:
                ws = writer.sheets[_SHEET_HEATMAP_DATA]
                n_data_rows = len(summary) + 1  # header + data
                image_anchor_row = n_data_rows + 2  # gap of 2 rows below table
                img = OpenpyxlImage(str(safe_heatmap))
                # Size for ~5"×3" at 96dpi so sheet (table + image) fits one page
                img.width = 480
                img.height = 288
                ws.add_image(img, f"A{image_anchor_row}")
                # Fit sheet to one page when printed (letter/A4)
                ws.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)
                ws.page_setup.fitToWidth = 1
                ws.page_setup.fitToHeight = 1
            except Exception:
                pass


def _apply_trial_row_cap(
    db_rows: list[dict], fs_rows: list[dict], cap: int
) -> tuple[list[dict], list[dict]]:
    """
    Limit combined DB + filesystem finding rows for trial/POC licenses; append one watermark row.
    """
    if cap <= 0:
        return db_rows, fs_rows
    total = len(db_rows) + len(fs_rows)
    if total <= cap:
        return db_rows, fs_rows
    out_db: list[dict] = []
    out_fs: list[dict] = []
    remaining = cap
    for r in db_rows:
        if remaining <= 0:
            break
        out_db.append(r)
        remaining -= 1
    for r in fs_rows:
        if remaining <= 0:
            break
        out_fs.append(r)
        remaining -= 1
    sample = fs_rows[0] if fs_rows else (db_rows[0] if db_rows else {})
    if sample:
        teaser = {k: "" for k in sample}
        teaser["target_name"] = "[Data Boar trial]"
        teaser["file_name"] = teaser.get("file_name", "") or "poc_preview"
        teaser["column_name"] = teaser.get("column_name", "") or "—"
        teaser["pattern_detected"] = "TRIAL_WATERMARK"
        teaser["sensitivity_level"] = "LOW"
        teaser["sample_value"] = (
            "POC: full discovery requires a paid license. Contact sales."
        )
        out_fs = list(out_fs) + [teaser]
    return out_db, out_fs


def _build_report_info(
    session_id: str,
    meta: dict,
    about: dict,
    db_rows: list[dict],
    fs_rows: list[dict],
    license_ctx: Any | None = None,
    config: dict | None = None,
) -> list[dict]:
    """Build the Report info sheet rows (session + tenant/technician + about + brief compatibility notes)."""
    report_info: list[dict] = []
    if license_ctx is not None:
        report_info.extend(
            [
                {"Field": "License state", "Value": getattr(license_ctx, "state", "—")},
                {
                    "Field": "License mode",
                    "Value": getattr(license_ctx, "mode", "—"),
                },
                {
                    "Field": "Licensed customer (token)",
                    "Value": getattr(license_ctx, "customer_name", "") or "—",
                },
                {
                    "Field": "License expiration (UTC)",
                    "Value": getattr(license_ctx, "expires_at_iso", "") or "—",
                },
                {
                    "Field": "License issuer (token)",
                    "Value": getattr(license_ctx, "issuer_id", "") or "—",
                },
                {
                    "Field": "License environment",
                    "Value": getattr(license_ctx, "environment", "") or "—",
                },
            ]
        )
    report_info.extend(
        [
            {"Field": "Session ID", "Value": session_id},
            {"Field": "Started at", "Value": meta["started_at"] or "—"},
            {"Field": "Tenant / Customer", "Value": meta["tenant_name"] or "—"},
            {"Field": "Technician / Operator", "Value": meta["technician_name"] or "—"},
        ]
    )
    from report.jurisdiction_hints import build_jurisdiction_hint_report_rows

    _hint_rows = build_jurisdiction_hint_report_rows(db_rows, fs_rows, config, meta)
    if _hint_rows:
        report_info.extend(_hint_rows)
    if meta.get("config_scope_hash"):
        report_info.append(
            {"Field": "Config scope hash", "Value": meta["config_scope_hash"]}
        )
    report_info.extend(
        [
            {"Field": "Application", "Value": about["name"]},
            {"Field": "Version", "Value": about["version"]},
            # #856 (E.9): auditors must see adulterated vs validated builds.
            {"Field": "Build trust", "Value": about.get("build_trust", "unknown")},
            {
                "Field": "Integrity state",
                "Value": about.get("integrity_state", "unknown"),
            },
            {"Field": "Author", "Value": about["author"]},
            {"Field": "License", "Value": about["license"]},
            {"Field": "Copyright", "Value": about["copyright"]},
        ]
    )

    # Brief CNPJ format compatibility note (legacy numeric vs alphanumeric)
    # Count distinct columns that have findings with LGPD_CNPJ and/or LGPD_CNPJ_ALNUM patterns.
    cnpj_numeric_columns: set[tuple[str, str]] = set()
    cnpj_alnum_columns: set[tuple[str, str]] = set()
    for row in list(db_rows) + list(fs_rows):
        pat = (row.get("pattern_detected") or "").upper()
        if not pat:
            continue
        col_name = (row.get("column_name") or row.get("file_name") or "").strip()
        target = (row.get("target_name") or "").strip()
        key = (target, col_name)
        if "LGPD_CNPJ_ALNUM" in pat:
            cnpj_alnum_columns.add(key)
        if "LGPD_CNPJ" in pat:
            # Note: this also matches LGPD_CNPJ_ALNUM; sets above keep classification by pattern presence.
            cnpj_numeric_columns.add(key)

    if cnpj_numeric_columns or cnpj_alnum_columns:
        legacy_only = len(cnpj_numeric_columns - cnpj_alnum_columns)
        alnum_only = len(cnpj_alnum_columns - cnpj_numeric_columns)
        mixed = len(cnpj_numeric_columns & cnpj_alnum_columns)
        note = (
            "CNPJ formats (legacy numeric vs alphanumeric) – "
            f"Legacy numeric: {legacy_only} columns; "
            f"Alphanumeric: {alnum_only} columns; Mixed: {mixed} columns"
        )
        report_info.append({"Field": _REPORT_INFO_CNPJ_FORMAT_COMPAT, "Value": note})

    if license_ctx is not None:
        report_info.append(
            {
                "Field": "License summary (footer)",
                "Value": (
                    f"state={getattr(license_ctx, 'state', '')}; "
                    f"customer={getattr(license_ctx, 'customer_name', '') or '—'}; "
                    f"expires_utc={getattr(license_ctx, 'expires_at_iso', '') or '—'}"
                ),
            }
        )

    return report_info


def generate_report(
    db_manager: Any,
    session_id: str,
    output_dir: str = ".",
    config: dict | None = None,
) -> str | None:
    """
    Read session from db_manager (database_findings, filesystem_findings, scan_failures);
    write Excel and heatmap. Return path to Excel file or None.
    Includes "Report info" (session + tenant), "Trends - Session comparison" when previous run exists.
    Optional config: if provided, report.recommendation_overrides and other report options are applied.
    """
    db_rows, fs_rows, fail_rows = db_manager.get_findings(session_id)
    if not db_rows and not fs_rows and not fail_rows:
        return None
    if (
        (config or {})
        .get("detection", {})
        .get("aggregated_identification_enabled", True)
    ):
        agg_records = run_aggregation(db_rows, fs_rows, session_id, config)
        db_manager.save_aggregated_identification_risks(session_id, agg_records)
    current_db = len(db_rows)
    current_fs = len(fs_rows)
    current_fail = len(fail_rows)
    report_cfg, db_rows_for_sheets, fs_rows_for_sheets = (
        _get_report_config_and_filtered_rows(config, db_rows, fs_rows)
    )
    suggested_review_rows = _build_suggested_review_rows(db_rows, fs_rows, config)
    lic_ctx = None
    report_rows_capped = False
    if config:
        from core.licensing.guard import get_license_guard

        lic_ctx = get_license_guard(config).context
        cap = None
        if (
            lic_ctx.state in ("VALID", "GRACE", "OPEN")
            and lic_ctx.trial
            and lic_ctx.max_report_rows > 0
        ):
            cap = lic_ctx.max_report_rows
        if cap:
            db_rows_for_sheets, fs_rows_for_sheets = _apply_trial_row_cap(
                db_rows_for_sheets, fs_rows_for_sheets, cap
            )
            report_rows_capped = True
    db_rows_for_sheets, fs_rows_for_sheets = _remove_suggested_review_from_main_sheets(
        db_rows_for_sheets, fs_rows_for_sheets, report_cfg
    )
    meta = _get_session_metadata(db_manager, session_id)
    current_started_at = meta["started_at"]
    about = get_about_info()
    report_info = _build_report_info(
        session_id,
        meta,
        about,
        db_rows_for_sheets,
        fs_rows_for_sheets,
        license_ctx=lic_ctx,
        config=config,
    )
    lic_footer = None
    if lic_ctx is not None:
        lic_footer = f"License: {lic_ctx.state}"
        if lic_ctx.watermark:
            lic_footer = f"{lic_footer} ({lic_ctx.watermark})"
    out_path = Path(output_dir) / f"Relatorio_Auditoria_{session_id[:16]}.xlsx"
    # Create heatmap PNG first so we can embed it in the Heatmap data sheet
    heatmap_path = _create_heatmap(
        db_rows_for_sheets,
        fs_rows_for_sheets,
        output_dir,
        session_id,
        license_footer=lic_footer,
    )
    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        _write_excel_sheets(
            writer,
            session_id,
            report_cfg,
            db_rows_for_sheets,
            fs_rows_for_sheets,
            config,
            fail_rows,
            db_manager,
            current_db,
            current_fs,
            current_fail,
            current_started_at,
            report_info,
            output_dir,
            heatmap_path=heatmap_path,
            suggested_review_rows=suggested_review_rows,
        )
    try:
        write_scan_evidence_artifacts(
            output_dir=output_dir,
            session_id=session_id,
            meta=meta,
            about=about,
            config=config,
            db_rows=db_rows,
            fs_rows=fs_rows,
            fail_rows=fail_rows,
            report_rows_capped=report_rows_capped,
        )
    except Exception:
        _logger.exception(
            "Falha ao gravar manifest/POC_SUMMARY (evidência + APG); Excel já foi emitido."
        )
    return str(out_path)
