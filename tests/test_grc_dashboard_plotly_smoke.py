"""Plotly-side smoke for the GRC dashboard chart (``grc-dashboard`` extra).

``app/dashboard.py`` imports ``plotly.express`` and ``streamlit`` at module top
and builds a ``px.bar`` figure from ``findings_chart_rows``. The default test run
(and ``check-all``) does NOT install the optional ``grc-dashboard`` extra, so
these tests ``importorskip`` plotly/streamlit and only execute where the extra is
present (e.g. ``uv run --extra grc-dashboard pytest``).

Why this exists: the extra was bumped to ``plotly>=6.8.0`` (a major from the 5.x
line). Plotly 6 routes dataframe input through ``narwhals`` and targets pandas 3.
This module reproduces the exact chart-building path the dashboard uses so the
plotly-6 + pandas-3 contract is guarded instead of silently untested.
"""

from __future__ import annotations

from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[1]
_EXAMPLE = _REPO / "schemas" / "grc_executive_report.v1.example.json"


def _build_dashboard_figure():
    """Replicate app/dashboard.py's chart build under the installed plotly."""
    import pandas as pd
    import plotly.express as px

    from app.grc_dashboard_model import findings_chart_rows, load_grc_json

    rows = findings_chart_rows(load_grc_json(_EXAMPLE))
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
            "risk_score": "Risk score (0-100)",
            "remediation_priority": "Priority",
        },
        color_discrete_map=color_map,
    )
    fig.update_layout(xaxis_tickangle=-35, height=420)
    return rows, fig


def test_plotly_major_is_6_or_newer() -> None:
    """The grc-dashboard extra is pinned to plotly>=6.8.0; guard the major line."""
    plotly = pytest.importorskip("plotly")
    major = int(plotly.__version__.split(".", 1)[0])
    assert major >= 6, (
        f"grc-dashboard extra expects plotly>=6 (got {plotly.__version__}). "
        "pyproject declares 'plotly>=6.8.0'."
    )


def test_dashboard_chart_builds_and_serializes() -> None:
    """px.bar + update_layout must build and serialize (Streamlit/plotly.js path)."""
    pytest.importorskip("plotly")
    pytest.importorskip("pandas")

    rows, fig = _build_dashboard_figure()
    assert len(rows) >= 1, "example GRC report should yield at least one finding row"
    # px.bar with a color dimension yields one trace per priority bucket present.
    assert len(fig.data) >= 1
    assert fig.layout.height == 420
    assert fig.layout.xaxis.tickangle == -35
    # to_json is what Streamlit hands to plotly.js; it must not raise under plotly 6.
    payload = fig.to_json()
    assert isinstance(payload, str) and len(payload) > 0


def test_dashboard_module_imports_under_plotly_6() -> None:
    """Importing app.dashboard exercises the plotly + streamlit import chain.

    set_page_config lives inside main(), so importing the module does not start a
    Streamlit runtime; it only validates the top-level imports resolve.
    """
    pytest.importorskip("plotly")
    pytest.importorskip("streamlit")

    import importlib

    module = importlib.import_module("app.dashboard")
    assert hasattr(module, "main")
