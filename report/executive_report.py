"""
Relatório de mesa — Markdown executivo (mitigação de risco, sem detalhe de código).

Usa :func:`core.advisor.group_findings_by_risk` e o ranking APG de ``core.recommendations``.

Doctrinal references (behaviour-preserving comments -- do not remove in refactors):

- ``docs/ops/inspirations/ACTIONABLE_GOVERNANCE_AND_TRUST.md`` -- the executive
  Markdown is part of the customer "trust triangle" (Markdown + manifest YAML
  + reproducible CLI). Sections **3** (methodology / segurança) and **4** (APG)
  are not optional: removing them turns the deliverable into a slide deck,
  which is *not* what the customer paid for.
- ``docs/ops/inspirations/DEFENSIVE_SCANNING_MANIFESTO.md`` -- the
  Methodology-of-Safety proof block under section 3 narrates *why* the
  sample row cap and statement timeout protect the customer DB. The values
  it surfaces come from the ``manifest['safety_tags']`` dictionary built in
  ``report/scan_evidence.py``; they are *clamped* in
  ``connectors/sql_sampling.py`` and must not be re-derived here.
- ``docs/ops/inspirations/THE_ART_OF_THE_FALLBACK.md`` -- when the manifest
  lacks fields (e.g. older sessions), this module degrades gracefully (``cap
  is None``, ``resolved is None``) instead of crashing -- the executive report
  is a read-only consumer of evidence; it never invents numbers.
"""

from __future__ import annotations

from typing import Any

from core.advisor import group_findings_by_risk
from report.recommendation_engine import sort_apg_rows, top_n_recommendations
from report.safe_prefix import safe_session_prefix


def _executive_status_emoji_and_label(
    db_rows: list[dict],
    apg_rows: list[dict[str, Any]],
    filesystem_findings: int,
    application_findings: int = 0,
) -> tuple[str, str]:
    critical_patterns = {
        "CREDIT_CARD",
        "LGPD_CPF",
        "CPF",
        "CCPA_SSN",
        "SSN",
        "LGPD_CNPJ",
        "LGPD_CNPJ_ALNUM",
        "CNPJ",
    }
    patterns = {(r.get("pattern_detected") or "").strip().upper() for r in db_rows}
    high_sens = any(
        (r.get("sensitivity_level") or "").strip().upper() == "HIGH" for r in db_rows
    )
    if patterns & critical_patterns or high_sens:
        return (
            "🔴",
            "Risco elevado detectado (dados sensíveis / PCI / identificadores fortes).",
        )
    crit_from_apg = any(
        (r.get("pattern_detected") or "").upper() in critical_patterns
        or "Bloqueante" in str(r.get("risk_band", ""))
        for r in apg_rows
    )
    if crit_from_apg:
        return (
            "🔴",
            "Risco elevado detectado (dados sensíveis / PCI / identificadores fortes).",
        )
    if apg_rows or db_rows or filesystem_findings > 0 or application_findings > 0:
        return "🟡", "Risco moderado — priorizar mitigação e validação com negócio/DPO."
    return "🟢", "Nenhum achado catalogado nesta sessão."


def generate_executive_report(
    *,
    session_id: str,
    about: dict[str, str],
    manifest: dict[str, Any],
    db_rows: list[dict],
    fs_rows: list[dict],
    _fail_rows: list[dict],
    apg_rows: list[dict[str, Any]],
    report_rows_capped: bool,
    app_rows: list[dict] | None = None,
) -> str:
    """
    Produz Markdown executivo: status, achados agregados por sensibilidade (só padrões e
    contagens), Top 3 recomendações APG, postura SRE resumida.

    Não inclui código interno, SQL gerado nem amostras de dados.

    ``_fail_rows`` reserva-se para alinhar a assinatura ao armazenamento da sessão; as contagens
    de falha expostas ao stakeholder vêm do manifest (sem detalhes de erro crus).
    """
    app_rows = list(app_rows or [])
    fc = manifest["scope_snapshot"]["findings_counts"]
    app_count = int(fc.get("application_findings") or len(app_rows) or 0)
    emoji, status_label = _executive_status_emoji_and_label(
        db_rows,
        apg_rows,
        int(fc.get("filesystem_findings") or 0),
        application_findings=app_count,
    )
    tables_n = manifest["scope_snapshot"]["unique_database_tables_with_findings"]
    dur = manifest["scan_window"].get("duration_minutes")
    audit = manifest.get("audit_trail", {})
    bullets = audit.get("dba_facing_summary_pt") or []
    dur_txt = (
        f"{dur} minutos"
        if dur is not None
        else "— (defina `finished_at` na sessão para estimar duração)"
    )

    by_risk = group_findings_by_risk(db_rows, list(fs_rows) + app_rows)
    labels = {
        "HIGH": "Alta sensibilidade",
        "MEDIUM": "Média sensibilidade",
        "LOW": "Baixa sensibilidade",
    }

    product = about.get("name", "Data Boar")
    version = about.get("version", "")
    sid_show = safe_session_prefix(session_id, max_len=16)
    lines: list[str] = [
        f"# {product} — inteligência e governança de risco (relatório executivo)",
        "",
        "*Enterprise data discovery & risk governance engine — executive desk output.*",
        "",
        f"**Versão:** `{version}` · **Sessão:** `{sid_show}…` · **Emitido (UTC):** `{manifest['engine_signature']['manifest_generated_at_utc']}`",
        "",
        "**Foco:** redução de risco e próximos passos de governança — não substitui parecer jurídico nem runbook de mudança em produção.",
        "",
        "## 1. Status",
        "",
        f"{emoji} **{status_label}**",
        "",
        f"- **Tabelas (BD) com pelo menos um achado:** {tables_n}",
        f"- **Volume agregado:** {fc['database_findings']} achados em base · "
        f"{fc['filesystem_findings']} em arquivos · "
        f"{app_count} em aplicações/API/CRM · "
        f"{fc['scan_failures']} falhas de alvo",
        "",
        "## 2. Achados por nível de sensibilidade (apenas padrões e contagens)",
        "",
        "*Não são listados nomes de colunas nem conteúdo amostrado — reduz exposição desnecessária para quem não tem acesso ao detalhe operacional.*",
        "",
    ]

    for key in ("HIGH", "MEDIUM", "LOW"):
        block = by_risk.get(key) or {"total": 0, "pattern_counts": {}}
        total = int(block.get("total") or 0)
        pats: dict[str, int] = block.get("pattern_counts") or {}
        if total == 0:
            lines.append(f"### {labels[key]}")
            lines.append("_Nenhum achado nesta faixa._")
            lines.append("")
            continue
        lines.append(f"### {labels[key]} — **{total}** achado(s)")
        parts = [f"`{name}`: **{cnt}**" for name, cnt in list(pats.items())[:12]]
        lines.append(
            "- " + "; ".join(parts) if parts else "- _(padrão não classificado)_"
        )
        if len(pats) > 12:
            lines.append(
                f"- _… +{len(pats) - 12} padrões adicionais (ver relatório completo interno)._"
            )
        lines.append("")

    st = manifest.get("safety_tags") or {}
    timeout_block = st.get("statement_timeout") or {}
    resolved = timeout_block.get("resolved_sql_hint_ms")
    explicit = timeout_block.get("first_database_target_explicit_ms")
    cap = st.get("sampling_row_cap_resolved")
    lead_comment = st.get("leading_sql_comment") or "-- Data Boar Compliance Scan"

    lines.extend(
        [
            "## 3. Metodologia e segurança",
            "",
            f"- **Duração aproximada do scan:** {dur_txt}",
            (
                "- **Contenção de I/O (sampling):** leituras usam **amostragem** com tetos por coluna "
                "após política de configuração (`SamplingProvider` / `file_scan.sample_limit`) e, "
                "quando definida, a variável de ambiente **`DATA_BOAR_SQL_SAMPLE_LIMIT`** — reduz "
                "pressão de leitura na heap de negócio."
            ),
        ]
    )
    if cap is not None:
        lines.append(f"- **Teto de linhas (valor resolvido):** `{cap}`.")
    if resolved is not None:
        lines.append(
            f"- **Orçamento de timeout por instrução de amostra (hint/env):** `{int(resolved)}` ms."
        )
    if explicit is not None and int(explicit or 0) > 0:
        lines.append(
            f"- **Timeout explícito no primeiro alvo `database` da config:** `{int(explicit)}` ms."
        )
    lines.extend(
        [
            (
                "- **Isolamento transacional e leitura:** o produto **não** promete isolamento "
                "serializável global; aplica **timeouts** e **amostragem** por dialeto. Em "
                "**PostgreSQL**, costuma usar **`SET LOCAL statement_timeout`** em transação curta. "
                "Em **Microsoft SQL Server**, leituras de amostra **podem** incluir **`WITH (NOLOCK)`** "
                "quando esse motor participa da sessão (leitura não bloqueante; sem garantias ACID "
                "estritas) — confira os bullets abaixo e `docs/USAGE.md`. Valide com DBA antes de "
                "aumentar carga em produção."
            ),
            (
                f"- **Rastreabilidade:** instruções de amostra levam o comentário de linha "
                f"`{lead_comment}` onde o dialeto aplica — útil em visões de atividade do motor."
            ),
            "",
            "**Bullets técnicos (evidência do manifesto):**",
            "",
        ]
    )
    for b in bullets[:12]:
        lines.append(f"- {b}")
    if len(bullets) > 12:
        lines.append(f"- *(+{len(bullets) - 12} itens no `scan_manifest_*.yaml`.)*")

    # Methodology-of-Safety proof block.
    #
    # Doctrine: the scanner is a guest in the customer database (see
    # docs/ops/inspirations/DEFENSIVE_SCANNING_MANIFESTO.md). The block below
    # narrates *why* the values above (row cap, timeout hint, leading SQL
    # comment) protect the customer instance and what the operator should
    # check during DBA review. We surface only the values already on the
    # manifest -- this is a reading guide, not a behavior change. Sample caps
    # and timeouts remain enforced in connectors/sql_sampling.py
    # (_HARD_MAX_SAMPLE = 10_000, statement timeout clamp <= 60_000 ms).
    lines.extend(
        [
            "",
            "**Compromisso de segurança operacional (proof block):**",
            "",
            (
                "- **Não-bloqueio em produção:** sampling leituras evitam locks "
                "exclusivos. Em SQL Server isso aparece como `WITH (NOLOCK)` no "
                "bullet técnico acima quando o motor participa da sessão; em "
                "PostgreSQL como timeout curto por transação. Validação: o DBA "
                f"pode grepar `{lead_comment}` em `pg_stat_activity` / DMVs."
            ),
            (
                "- **Caps são clamps, não sugestões:** o teto por coluna acima é "
                "sempre clampado a `1..10_000` em código "
                "(`connectors/sql_sampling.py` -> `_HARD_MAX_SAMPLE`). Mesmo se "
                "alguém configurar valores absurdos via YAML ou variável de "
                "ambiente `DATA_BOAR_SQL_SAMPLE_LIMIT`, o motor não excede esse "
                "limite — uma das *relief valves* do manifesto defensivo."
            ),
            (
                "- **Timeouts são clamps, não sugestões:** o orçamento de "
                "timeout acima é sempre clampado a `1..60_000` ms via "
                "`resolve_statement_timeout_ms_for_sampling`. Sem isso, "
                "`DATA_BOAR_SAMPLE_STATEMENT_TIMEOUT_MS` ou um YAML mal "
                "preenchido poderia fixar uma sessão indefinidamente — "
                "incompatível com a regra de não bloqueio."
            ),
            (
                "- **Sem `ORDER BY` em sampling automático:** a camada de "
                "composição (`connectors/sql_sampling.py`) não injeta `ORDER BY` "
                "em SQL de amostra; um `ORDER BY` em coluna não indexada força "
                "um sort de tabela inteira — exatamente o oposto de leitura "
                "estilo *compliance scan*. Caso futuro pedido de ordenação "
                "determinística surja, será via ADR + flag explícita "
                "(`--ordered-sample`), nunca silenciosamente."
            ),
            (
                "- **Doctrinal references:** "
                "`docs/ops/inspirations/DEFENSIVE_SCANNING_MANIFESTO.md` "
                "(NASA / Cloudflare / Steve Gibson), "
                "`docs/ops/inspirations/THE_ART_OF_THE_FALLBACK.md` "
                "(Usagi Electric / The 8-Bit Guy), "
                "`docs/ops/inspirations/ACTIONABLE_GOVERNANCE_AND_TRUST.md` "
                "(Tailscale / Charity Majors / Cloudflare post-mortems)."
            ),
        ]
    )

    sorted_apg = sort_apg_rows(apg_rows)
    lines.extend(
        [
            "",
            "## 4. Plano de ação (APG)",
            "",
            "### 4.1 Prioridades imediatas (Top 3)",
            "",
        ]
    )
    top3 = top_n_recommendations(apg_rows, 3)
    if not top3:
        lines.append(
            "_Sem recomendações agregadas — reexecutar com alvos configurados._"
        )
    else:
        for i, row in enumerate(top3, 1):
            pat = row.get("pattern_detected", "")
            lines.append(
                f"{i}. **`{pat}`** — {row.get('risk_band', '')}: {row.get('recommended_action', '')}"
            )

    lines.extend(
        [
            "",
            "### 4.2 Inventário por tipo de dado (achado → risco → recomendação técnica)",
            "",
        ]
    )
    if not sorted_apg:
        lines.append("_Nenhum tipo agregado para o inventário APG nesta sessão._")
    else:
        for row in sorted_apg:
            pat = str(row.get("pattern_detected") or "(empty)")
            n = int(row.get("finding_count") or 0)
            risk = str(row.get("risk_band", "") or "—")
            action = str(row.get("recommended_action", "") or "—")
            impact = str(row.get("business_impact", "") or "").strip()
            shadow_n = int(row.get("shadow_name_heuristic_count") or 0)
            lines.append(f"#### `{pat}` — **{n}** ocorrência(s)")
            lines.append(f"- **Risco:** {risk}")
            if impact:
                lines.append(f"- **Impacto:** {impact}")
            lines.append(f"- **Recomendação técnica:** {action}")
            if shadow_n > 0:
                lines.append(
                    f"- *Heurística “shadow/staging” no nome do objeto:* **{shadow_n}** achado(s) "
                    "— validar se o ativo ainda é necessário em produção."
                )
            lines.append("")

    lines.extend(
        [
            "",
            "---",
            "",
            f"**Evidência técnica:** `scan_manifest_{sid_show}.yaml`",
            "",
        ]
    )
    if report_rows_capped:
        lines.append(
            "_Nota: licença de avaliação pode limitar linhas no Excel; contagens acima refletem "
            "a sessão completa na base local._"
        )
    return "\n".join(lines) + "\n"


__all__ = ["generate_executive_report"]
