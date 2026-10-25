"""
Artigo I — EvidenceCollector: rastro DBA/SRE do comportamento do produto na amostragem.

Regista afirmações verificáveis alinhadas ao que ``connectors/sql_sampling`` e o conector
SQL documentam (não substitui log por query).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def unique_database_engines(db_rows: list[dict]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for r in db_rows:
        eng = (r.get("engine_details") or "").strip()
        if eng and eng not in seen:
            seen.add(eng)
            out.append(eng)
    return out


def _engine_buckets(engines: list[str]) -> dict[str, bool]:
    blob = " ".join(e.lower() for e in engines)
    return {
        "mssql": "mssql" in blob or "sql server" in blob,
        "postgresql": "postgresql" in blob or "postgres" in blob,
        "mysql": "mysql" in blob or "mariadb" in blob,
        "snowflake": "snowflake" in blob,
        "oracle": "oracle" in blob,
    }


@dataclass(frozen=True)
class EvidenceCollector:
    """
    Coleta bullets para o manifest e para narrativa de “bom cidadão” no banco.

    ``statement_timeout_payload`` deve seguir o formato de
    ``scan_evidence._statement_timeout_manifest`` (first_database_target_explicit_ms,
    resolved_sql_hint_ms, …).
    """

    config: dict[str, Any]
    db_rows: list[dict]
    effective_sample_row_cap: int
    statement_timeout_payload: dict[str, Any]

    def engines(self) -> list[str]:
        return unique_database_engines(self.db_rows)

    def dba_summary_pt(self) -> list[str]:
        """Frases curtas para DBA/cliente técnico (audit trail legível)."""
        lines: list[str] = []
        engines = self.engines()
        b = _engine_buckets(engines)

        lines.append(
            f"Amostragem por coluna com teto de **{self.effective_sample_row_cap}** linhas "
            "(após política `SamplingProvider` / `file_scan.sample_limit` e env "
            "`DATA_BOAR_SQL_SAMPLE_LIMIT`, quando definida)."
        )

        expl = self.statement_timeout_payload.get("first_database_target_explicit_ms")
        resolved = self.statement_timeout_payload.get("resolved_sql_hint_ms")
        if expl is not None and int(expl) > 0:
            lines.append(
                f"Orçamento de timeout **explícito no alvo**: **{int(expl)} ms** por instrução "
                "de amostra (quando o dialeto aplica hints / `SET LOCAL`)."
            )
        elif resolved is not None:
            lines.append(
                f"Hints de execução para amostra com **{int(resolved)} ms** "
                "(origem: env `DATA_BOAR_SAMPLE_STATEMENT_TIMEOUT_MS` ou equivalente)."
            )
        else:
            lines.append(
                "Timeout por amostra: **padrão do conector 5000 ms** quando o campo não é "
                "desabilitado (`0`) — PostgreSQL pode usar `SET LOCAL statement_timeout` em "
                "transação curta; ver USAGE.md."
            )

        if b["mssql"]:
            lines.append(
                "No **SQL Server**, a amostragem usa **`WITH (NOLOCK)`** em leituras de "
                "amostra (postura de compliance read; não garantias transacionais)."
            )
        if b["postgresql"]:
            lines.append(
                "No **PostgreSQL**, leituras usam **`LIMIT`**; em **tabelas grandes** o produto "
                "pode usar **`TABLESAMPLE SYSTEM`** + `LIMIT` (percentual via "
                "`DATA_BOAR_PG_TABLESAMPLE_SYSTEM_PERCENT`)."
            )
        if b["mysql"]:
            lines.append(
                "No **MySQL/MariaDB**, pode aplicar-se hint **`MAX_EXECUTION_TIME`** quando há "
                "orçamento de timeout ativo."
            )
        if b["snowflake"]:
            lines.append(
                "No **Snowflake**, amostras usam **`SAMPLE (n ROWS)`** em visão filtrada "
                "(`IS NOT NULL`)."
            )
        if b["oracle"]:
            lines.append(
                "No **Oracle**, uso de **`ROWNUM`** com subconsulta `IS NOT NULL` (sem `ORDER BY` "
                "na amostragem automática)."
            )

        if not engines:
            lines.append(
                "Nenhum `engine_details` em achados de base nesta sessão — bullets de dialeto "
                "acima aplicam-se quando houver scan relacional com metadados preenchidos."
            )

        lines.append(
            "Todas as instruções geradas para amostragem começam com o comentário "
            "`-- Data Boar Compliance Scan` para rastreio em vistas de atividade do motor."
        )
        return lines

    def to_manifest_dict(self) -> dict[str, Any]:
        return {
            "component": "EvidenceCollector",
            "engines_observed": self.engines(),
            "dba_facing_summary_pt": self.dba_summary_pt(),
        }
