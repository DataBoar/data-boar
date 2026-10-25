"""
APG / resumo executivo — agregações só com metadados (sem amostras de conteúdo).

Não importa ``report`` nem conectores: pode ser usado após o scan sem risco de regressão
na detecção. Falhas neste módulo não devem impedir o scan (trate no chamador).
"""

from __future__ import annotations

from collections import Counter
from typing import Any

_SENS_ORDER = ("HIGH", "MEDIUM", "LOW")


def group_findings_by_risk(
    db_rows: list[dict], fs_rows: list[dict]
) -> dict[str, dict[str, Any]]:
    """
    Agrupa achados por ``sensitivity_level`` com contagens por **padrão** apenas.

    Não inclui valores de coluna nem trechos de arquivo — adequado a stakeholders externos.
    """
    out: dict[str, dict[str, Any]] = {}
    for level in _SENS_ORDER:
        out[level] = {"total": 0, "pattern_counts": Counter()}

    def feed(rows: list[dict]) -> None:
        for r in rows:
            s = (r.get("sensitivity_level") or "LOW").strip().upper()
            if s not in out:
                s = "LOW"
            out[s]["total"] += 1
            pat = (
                r.get("pattern_detected") or "(sem padrão)"
            ).strip() or "(sem padrão)"
            out[s]["pattern_counts"][pat] += 1

    feed(db_rows)
    feed(fs_rows)

    for level in _SENS_ORDER:
        out[level]["pattern_counts"] = dict(
            sorted(
                out[level]["pattern_counts"].items(),
                key=lambda x: (-x[1], x[0]),
            )
        )
    return out


__all__ = ["group_findings_by_risk"]
