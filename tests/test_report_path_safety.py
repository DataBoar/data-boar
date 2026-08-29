"""API report/heatmap path containment (aligned with CodeQL py/path-injection patterns)."""

from pathlib import Path

from fastapi.testclient import TestClient


def _write_minimal_config(
    config_path: Path, output_dir: Path, sqlite_path: Path
) -> None:
    config_path.write_text(
        f"""targets: []
report:
  output_dir: {output_dir}
api:
  port: 8088
sqlite_path: {sqlite_path}
scan:
  max_workers: 1
""",
        encoding="utf-8",
    )


def _set_routes_context(tmp_path: Path, output_dir: Path):
    import api.routes as routes

    config_path = tmp_path / "config.yaml"
    sqlite_path = tmp_path / "audit.db"
    _write_minimal_config(config_path, output_dir, sqlite_path)

    orig = (routes._config_path, routes._config, routes._audit_engine)
    routes._config_path = str(config_path)
    routes._config = None
    routes._audit_engine = None
    return routes, orig


def _restore_routes_context(routes, orig):
    routes._config_path, routes._config, routes._audit_engine = orig


class _FakeDBManager:
    current_session_id = None

    @staticmethod
    def list_sessions():
        return []


class _FakeEngine:
    def __init__(self, report_output_dir: Path, report_path: Path):
        self.config = {"report": {"output_dir": str(report_output_dir)}}
        self._report_path = str(report_path)
        self.db_manager = _FakeDBManager()

    def get_last_report_path(self):
        return self._report_path

    def generate_final_reports(self, _session_id, config=None, **_kwargs):
        return self._report_path


def test_download_report_rejects_path_outside_configured_output_dir(tmp_path: Path):
    output_dir = tmp_path / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    outside_report = tmp_path / "outside.xlsx"
    outside_report.write_text("dummy", encoding="utf-8")

    routes, orig = _set_routes_context(tmp_path, output_dir)
    try:
        routes._audit_engine = _FakeEngine(output_dir, outside_report)
        client = TestClient(routes.app)
        resp = client.get("/report")
        assert resp.status_code == 404
    finally:
        _restore_routes_context(routes, orig)


def test_download_report_rejects_non_report_filename_pattern(tmp_path: Path):
    """Basename must match Relatorio_Auditoria_*.xlsx|ods even if file sits under output_dir."""
    output_dir = tmp_path / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    bad_name = output_dir / "not_a_report.xlsx"
    bad_name.write_text("dummy", encoding="utf-8")

    routes, orig = _set_routes_context(tmp_path, output_dir)
    try:
        routes._audit_engine = _FakeEngine(output_dir, bad_name)
        client = TestClient(routes.app)
        resp = client.get("/report")
        assert resp.status_code == 404
    finally:
        _restore_routes_context(routes, orig)


def test_download_report_accepts_ods_basename_under_output_dir(tmp_path: Path):
    """#553: allowlist must accept Relatorio_Auditoria_*.ods (Bugbot HIGH)."""
    output_dir = tmp_path / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    ods = output_dir / "Relatorio_Auditoria_abcdef123456.ods"
    ods.write_bytes(b"ods")

    routes, orig = _set_routes_context(tmp_path, output_dir)
    try:
        routes._audit_engine = _FakeEngine(output_dir, ods)
        client = TestClient(routes.app)
        resp = client.get("/report?format=ods")
        assert resp.status_code == 200
        assert (
            resp.headers["content-type"]
            == "application/vnd.oasis.opendocument.spreadsheet"
        )
    finally:
        _restore_routes_context(routes, orig)


def test_heatmap_session_key_from_ods_report_basename(tmp_path: Path):
    import api.routes as routes

    out = tmp_path / "reports"
    out.mkdir(parents=True, exist_ok=True)
    ods = out / "Relatorio_Auditoria_abcdef123456.ods"
    ods.write_bytes(b"ods")
    (out / "heatmap_abcdef123456.png").write_bytes(b"png")
    engine = _FakeEngine(out, ods)
    resolved = routes._safe_report_path_for_heatmap(engine)
    assert resolved is not None
    path, sid = resolved
    assert path.suffix == ".ods"
    assert sid == "abcdef123456"


def test_resolved_existing_file_under_out_dir_rejects_traversal(tmp_path: Path):
    """Join+normpath+realpath containment must reject escaping the base directory."""
    import api.routes as routes

    base = tmp_path / "out"
    base.mkdir(parents=True, exist_ok=True)
    (base / "good.png").write_bytes(b"x")
    assert routes._resolved_existing_file_under_out_dir(base, "good.png") is not None
    assert routes._resolved_existing_file_under_out_dir(base, "../out/good.png") is None
    assert routes._resolved_existing_file_under_out_dir(base, "..") is None
    assert routes._resolved_existing_file_under_out_dir(base, "nope.png") is None


def test_heatmap_png_path_for_download_matches_allowlist(tmp_path: Path):
    import api.routes as routes

    out = tmp_path / "reports"
    out.mkdir(parents=True, exist_ok=True)
    (out / "heatmap_abcdef123456.png").write_bytes(b"png")
    engine = _FakeEngine(out, out / "Relatorio_Auditoria_abcdef123456.xlsx")
    ok = routes._heatmap_png_path_for_download(engine, "abcdef1234567890")
    assert ok is not None and ok.name == "heatmap_abcdef123456.png"
    assert routes._heatmap_png_path_for_download(engine, "../../etc") is None


def test_download_heatmap_rejects_report_path_outside_configured_output_dir(
    tmp_path: Path,
):
    output_dir = tmp_path / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    outside_report = tmp_path / "Relatorio_Auditoria_abcdef123456.xlsx"
    outside_report.write_text("dummy", encoding="utf-8")
    # Even if a matching heatmap exists beside the report, endpoint must reject the base report path.
    outside_heatmap = tmp_path / "heatmap_abcdef123456.png"
    outside_heatmap.write_bytes(b"png")

    routes, orig = _set_routes_context(tmp_path, output_dir)
    try:
        routes._audit_engine = _FakeEngine(output_dir, outside_report)
        client = TestClient(routes.app)
        resp = client.get("/heatmap")
        assert resp.status_code == 404
    finally:
        _restore_routes_context(routes, orig)


def test_heatmap_helper_does_not_resolve_caller_supplied_path() -> None:
    """#1818: listing output_dir avoids CodeQL py/path-injection on heatmap_path."""
    text = (Path(__file__).resolve().parents[1] / "report" / "generator.py").read_text(
        encoding="utf-8"
    )
    start = text.index("def _heatmap_path_under_output_dir")
    end = text.index("def _mascot_path")
    chunk = text[start:end]
    assert "iterdir()" in chunk
    assert "Path(heatmap_path).resolve()" not in chunk
    assert "Path(heatmap_path).name" in chunk
