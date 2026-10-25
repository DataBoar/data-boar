"""
Governance Lens — render pandoc-ready Markdown from session findings (Pro tier).

See docs/plans/PLAN_GOVERNANCE_LENS.md Phase C and config/pandoc_governance.yaml.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from core.about import get_about_info
from report.governance_lens import (
    GovernanceLensGenerator,
    enterprise_lens_enabled,
    governance_lens_feature_allowed,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEMPLATE_PATH = (
    _REPO_ROOT / "docs" / "templates" / "GRC_GOVERNANCE_LENS_REPORT.md.j2"
)
DEFAULT_TOP_GAPS = 10


class GovernanceReportError(Exception):
    """Base error for governance report generation."""


class GovernanceReportSessionError(GovernanceReportError):
    """Session resolution failed (unknown id or empty database)."""


def resolve_governance_session_id(
    db_manager: Any,
    session_id: str | None,
) -> str:
    """Return explicit session id or the most recent session in SQLite."""
    if session_id and str(session_id).strip():
        sid = str(session_id).strip()
        known = {row["session_id"] for row in db_manager.list_sessions()}
        if sid not in known:
            raise GovernanceReportSessionError(f"Unknown session: {sid}")
        return sid
    sessions = db_manager.list_sessions()
    if not sessions:
        raise GovernanceReportSessionError("No scan sessions found in SQLite")
    return str(sessions[0]["session_id"])


def _session_metadata(db_manager: Any, session_id: str) -> dict[str, Any]:
    for row in db_manager.list_sessions() or []:
        if row.get("session_id") == session_id:
            return {
                "started_at": row.get("started_at"),
                "finished_at": row.get("finished_at"),
                "tenant_name": row.get("tenant_name"),
                "technician_name": row.get("technician_name"),
            }
    return {
        "started_at": None,
        "finished_at": None,
        "tenant_name": None,
        "technician_name": None,
    }


def _priority_band(max_sensitivity: str, risk_level: str) -> str:
    if (max_sensitivity or "").upper() == "HIGH" or risk_level == "alto":
        return "P0"
    if (max_sensitivity or "").upper() == "MEDIUM" or risk_level == "medio":
        return "P1"
    return "P2"


def _framework_bucket(framework_id: str) -> str:
    fid = (framework_id or "").upper()
    if "BACEN" in fid or "4893" in fid:
        return "bacen"
    if "PCI" in fid:
        return "pci"
    if "FEBRABAN" in fid or "CPS004" in fid:
        return "febraban"
    if fid.startswith("ISO38500"):
        return "iso38500"
    if fid.startswith("ISO27014"):
        return "iso27014"
    if fid.startswith("COBIT"):
        return "cobit"
    if "ITIL" in fid or "SECMAN" in fid:
        return "itil"
    if fid.startswith("ISO27001"):
        return "iso27001"
    return "other"


def _group_gaps_by_bucket(gaps: list[Any]) -> dict[str, list[dict[str, str]]]:
    buckets: dict[str, list[dict[str, str]]] = {
        "iso38500": [],
        "iso27014": [],
        "cobit": [],
        "itil": [],
        "iso27001": [],
        "bacen": [],
        "pci": [],
        "febraban": [],
        "other": [],
    }
    for gap in gaps:
        row = {
            "framework_id": gap.framework_id,
            "framework_name": gap.framework_name,
            "title": gap.control_gap_title,
            "body": gap.control_gap_body,
            "recommendation": gap.recommendation,
            "deadline_days": gap.deadline_days,
            "finding_count": gap.finding_count,
            "max_sensitivity": gap.max_sensitivity,
        }
        buckets[_framework_bucket(gap.framework_id)].append(row)
    return buckets


def _iso38500_principles(gaps: list[dict[str, str]]) -> list[dict[str, str]]:
    principles = [
        ("Responsabilidade", "Avaliar e direcionar uso de TI alinhado ao negócio"),
        ("Estratégia", "Garantir que planos de TI suportem objetivos organizacionais"),
        ("Aquisição", "Assegurar aquisição justa e transparente de recursos de TI"),
        ("Desempenho", "Medir desempenho e conformidade dos serviços de TI"),
        ("Conformidade", "Cumprir leis, regulamentos e políticas aplicáveis"),
        ("Cooperação humana", "Promover competências e conduta ética"),
    ]
    rows: list[dict[str, str]] = []
    for name, desc in principles:
        related = [
            g
            for g in gaps
            if "conform" in g["title"].lower() or "govern" in g["title"].lower()
        ]
        situation = "Gap identificado" if related else "Sem gap mapeado nesta sessão"
        evidence = related[0]["title"] if related else "—"
        rows.append(
            {
                "principle": name,
                "description": desc,
                "situation": situation,
                "evidence": evidence,
            }
        )
    return rows


def _iso27014_processes(gaps: list[dict[str, str]]) -> list[dict[str, str]]:
    labels = [
        "Monitorar o desempenho de segurança",
        "Comunicar questões de segurança",
        "Avaliar desempenho de segurança",
        "Orientar atividades de segurança",
        "Assegurar alinhamento com objetivos de negócio",
    ]
    rows: list[dict[str, str]] = []
    for idx, label in enumerate(labels, start=1):
        match = gaps[idx % len(gaps)] if gaps else None
        rows.append(
            {
                "process": f"{idx}. {label}",
                "gap": match["title"] if match else "—",
                "control": match["recommendation"]
                if match
                else "Manter monitoramento contínuo",
            }
        )
    return rows


def build_governance_report_context(
    config: dict[str, Any],
    db_manager: Any,
    session_id: str,
    *,
    top_gaps: int = DEFAULT_TOP_GAPS,
) -> dict[str, Any]:
    """Assemble Jinja context for the GRC governance report template."""
    meta = _session_metadata(db_manager, session_id)
    db_rows, fs_rows, app_rows, fail_rows = db_manager.get_findings(session_id)
    lens = GovernanceLensGenerator(config).generate_from_rows(
        db_rows, fs_rows, app_rows
    )
    about = get_about_info()
    buckets = _group_gaps_by_bucket(lens.control_gaps)

    targets: list[dict[str, str]] = []
    seen: set[str] = set()
    for source, rows in (
        ("database", db_rows),
        ("filesystem", fs_rows),
        ("application", app_rows),
    ):
        for row in rows:
            name = str(row.get("target_name") or "").strip()
            if not name or name in seen:
                continue
            seen.add(name)
            targets.append(
                {
                    "name": name,
                    "source": source,
                    "sensitivity": str(row.get("sensitivity_level") or ""),
                }
            )

    risk_matrix = {"P0": 0, "P1": 0, "P2": 0}
    for gap in lens.control_gaps:
        band = _priority_band(gap.max_sensitivity, lens.risk_level)
        risk_matrix[band] = risk_matrix.get(band, 0) + 1

    top_detail = lens.control_gaps[: max(1, top_gaps)] if lens.control_gaps else []
    roadmap = [
        {
            "priority": _priority_band(g.max_sensitivity, lens.risk_level),
            "action": g.recommendation,
            "framework": g.framework_id,
            "deadline_days": g.deadline_days if g.deadline_days is not None else "—",
            "owner": "A definir",
        }
        for g in top_detail
    ]

    frameworks_enabled = sorted(
        {g.framework_name for g in lens.control_gaps}
        or ["COBIT 2019", "ISO/IEC 27001", "ISO/IEC 38500"]
    )

    started = meta.get("started_at") or ""
    report_date = started[:10] if started else datetime.now(UTC).strftime("%Y-%m-%d")

    return {
        "organization": meta.get("tenant_name") or "Organização (informar)",
        "scope": "Levantamento técnico de dados sensíveis — escopo definido pelos targets da sessão",
        "report_date": report_date,
        "product_version": about.get("version") or "",
        "session_id": session_id,
        "technician": meta.get("technician_name") or "—",
        "frameworks_enabled": frameworks_enabled,
        "risk_level": lens.risk_level,
        "risk_matrix": risk_matrix,
        "total_gaps": len(lens.control_gaps),
        "total_findings": len(db_rows) + len(fs_rows) + len(app_rows),
        "scan_failures": len(fail_rows),
        "framework_buckets": buckets,
        "iso38500_principles": _iso38500_principles(
            buckets["iso38500"] + buckets["other"]
        ),
        "iso27014_processes": _iso27014_processes(buckets["iso27014"]),
        "top_gaps": top_detail,
        "roadmap": roadmap,
        "targets": targets,
        "framework_summary": lens.framework_summary,
        "enterprise_enabled": enterprise_lens_enabled(config),
    }


def render_governance_report_markdown(
    config: dict[str, Any],
    db_manager: Any,
    session_id: str,
    *,
    template_path: Path | None = None,
) -> str:
    """Render filled Markdown (with pandoc YAML frontmatter) for a session."""
    if not governance_lens_feature_allowed(config):
        raise GovernanceReportError(
            "Governance Lens report requires governance.enabled: true and Pro+ license tier"
        )
    ctx = build_governance_report_context(config, db_manager, session_id)
    tpl_path = template_path or DEFAULT_TEMPLATE_PATH
    if not tpl_path.is_file():
        raise GovernanceReportError(f"Governance report template not found: {tpl_path}")
    env = Environment(
        loader=FileSystemLoader(str(tpl_path.parent)),
        autoescape=select_autoescape(default_for_string=False),
    )
    template = env.get_template(tpl_path.name)
    return template.render(**ctx)


def write_governance_report(
    output_path: Path | str,
    config: dict[str, Any],
    db_manager: Any,
    session_id: str | None = None,
    *,
    template_path: Path | None = None,
) -> Path:
    """Resolve session, render MD, write to disk; return absolute path."""
    sid = resolve_governance_session_id(db_manager, session_id)
    body = render_governance_report_markdown(
        config, db_manager, sid, template_path=template_path
    )
    dest = Path(output_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(body, encoding="utf-8")
    return dest.resolve()


def default_governance_report_path(config: dict[str, Any], session_id: str) -> Path:
    """Default MD path under report.output_dir when --governance-report has no PATH."""
    report_cfg = config.get("report") or {}
    out_dir = Path(str(report_cfg.get("output_dir") or "."))
    short = session_id.replace("-", "")[:8]
    return out_dir / f"Governance_Lens_{short}.md"
