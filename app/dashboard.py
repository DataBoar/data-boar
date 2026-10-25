"""
Streamlit executive view for ``data_boar_grc_executive_report_v1`` JSON.

Install: ``uv sync --extra grc-dashboard`` (Streamlit + Plotly).

Run from repository root::

    streamlit run app/dashboard.py

Default report path: ``schemas/grc_executive_report.v1.example.json``.
Override with env ``DATA_BOAR_GRC_JSON`` or the sidebar path field.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import pandas as pd
import plotly.express as px
import streamlit as st

from app.grc_dashboard_model import (
    compliance_mapping_hints,
    findings_chart_rows,
    load_grc_json,
    peak_asset_risk_score,
)

_DEFAULT_REPORT = _REPO_ROOT / "schemas" / "grc_executive_report.v1.example.json"


def _resolve_report_path() -> Path:
    env = (os.environ.get("DATA_BOAR_GRC_JSON") or "").strip()
    if env:
        return Path(env).expanduser()
    return _DEFAULT_REPORT


@st.cache_data(show_spinner=False)
def _load_cached(path_str: str) -> dict:
    return load_grc_json(Path(path_str))


def main() -> None:
    st.set_page_config(
        page_title="Data Boar | GRC DashBOARd",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.sidebar.header("Report source")
    default_path = str(_resolve_report_path())
    path_in = st.sidebar.text_input(
        "Path to GRC JSON",
        value=default_path,
        help="Contract: data_boar_grc_executive_report_v1. "
        "Tip: set DATA_BOAR_GRC_JSON for a fixed lab path.",
    )
    path = Path(path_in).expanduser()
    if not path.is_file():
        st.error(f"File not found: {path}")
        st.stop()

    try:
        data = _load_cached(str(path.resolve()))
    except ValueError as e:
        st.error(str(e))
        st.stop()

    meta = data["report_metadata"]
    exe = data["executive_summary"]

    st.title("Data Boar | GRC DashBOARd")
    client = meta.get("client_display_name") or "—"
    st.caption(
        f"**Scope:** {meta.get('scope', '—')} · **Client label:** {client} · "
        f"**Report ID:** {meta.get('report_id', '—')} · **Scan:** {meta.get('scan_date', '—')}"
    )

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Compliance score", f"{float(exe.get('compliance_score', 0.0)):.1f}")
    with col2:
        st.metric("Risk level", str(exe.get("risk_level", "—")))
    with col3:
        st.metric(
            "PII instances (metadata hits)", int(exe.get("pii_instances_found", 0))
        )
    with col4:
        st.metric("Critical assets", int(exe.get("critical_assets_at_risk", 0)))
    with col5:
        st.metric("Peak asset risk (0–100)", f"{peak_asset_risk_score(data):.1f}")

    st.metric(
        "Records / cells scanned (reported)",
        int(exe.get("total_records_scanned", 0)),
        help="Unit is as reported by the generator; see GRC schema.",
    )

    hint_line = compliance_mapping_hints(data)
    if hint_line:
        st.info(hint_line)

    rows = findings_chart_rows(data)
    st.divider()
    if rows:
        df = pd.DataFrame(rows)
        color_map = {
            "CRITICAL": "#c0392b",
            "HIGH": "#e67e22",
            "MEDIUM": "#2980b9",
            "LOW": "#7f8c8d",
        }
        fig = px.bar(
            df,
            x="asset_id",
            y="risk_score",
            color="remediation_priority",
            title="Risk score by asset (remediation priority)",
            labels={
                "asset_id": "Asset",
                "risk_score": "Risk score (0–100)",
                "remediation_priority": "Priority",
            },
            color_discrete_map=color_map,
        )
        fig.update_layout(xaxis_tickangle=-35, height=420)
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Detailed findings (matrix rows)")
        show = df[
            [
                "asset_id",
                "asset_class",
                "data_category",
                "risk_score",
                "remediation_priority",
            ]
        ]
        st.dataframe(show, use_container_width=True, hide_index=True)

        with st.expander("Regulatory impact (per row, workshop text)"):
            st.dataframe(
                df[["asset_id", "regulatory_impact"]],
                use_container_width=True,
                hide_index=True,
            )
    else:
        st.warning("No detailed_findings rows in this report.")

    st.subheader("Recommendations")
    for rec in data.get("recommendations") or []:
        if not isinstance(rec, dict):
            continue
        rid = rec.get("id", "—")
        pri = rec.get("priority", "—")
        action = rec.get("action", "")
        effort = rec.get("estimated_effort", "—")
        note = rec.get("regulatory_impact_note", "")
        st.markdown(
            f"**{rid}** ({pri}) — *effort:* {effort}  \n{action}  \n*Note:* {note}"
        )

    st.divider()
    st.caption(
        f"Heuristic compliance method: {exe.get('compliance_score_method', '—')}. "
        "Scores and article hints are workshop signals, not legal adequacy."
    )


if __name__ == "__main__":
    main()
