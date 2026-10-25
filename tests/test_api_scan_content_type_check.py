"""
POST /scan with content_type_check: true enables magic-byte format detection for that run only.
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.mark.parametrize("endpoint", ["/scan", "/start"])
def test_post_scan_content_type_check_overrides_use_content_type_for_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, endpoint: str
) -> None:
    """Dashboard/API can force use_content_type for one run; connector sees .pdf for renamed file."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    fake_pdf = data_dir / "notes.txt"
    fake_pdf.write_bytes(b"%PDF-1.4\n%mock\n")

    out_dir = str(tmp_path).replace("\\", "/")
    scan_path = str(data_dir).replace("\\", "/")
    config_yaml = f"""targets:
  - name: fs1
    type: filesystem
    path: {scan_path}
    recursive: false
file_scan:
  extensions: [.txt]
  recursive: true
  scan_sqlite_as_db: false
  sample_limit: 2
  use_content_type: false
  scan_compressed: false
report:
  output_dir: {out_dir}
api:
  port: 8088
sqlite_path: {out_dir}/audit_results.db
scan:
  max_workers: 1
"""
    config_path = tmp_path / "config.yaml"
    config_path.write_text(config_yaml, encoding="utf-8")

    called_ext: list[str] = []

    def fake_read_text_sample(path: Path, ext: str, *_args, **_kwargs) -> str:
        called_ext.append(ext)
        return ""

    monkeypatch.setattr(
        "connectors.filesystem_connector._read_text_sample",
        fake_read_text_sample,
        raising=True,
    )

    import api.routes as routes

    original_config_path = routes._config_path
    original_config = routes._config
    original_engine = routes._audit_engine
    try:
        routes._config_path = str(config_path)
        routes._config = None
        routes._audit_engine = None

        client = TestClient(routes.app)
        resp = client.post(endpoint, json={"content_type_check": True})
        assert resp.status_code == 200, resp.text
        session_id = resp.json().get("session_id")
        assert session_id

        list_resp = client.get("/list")
        assert list_resp.status_code == 200
        sessions = list_resp.json().get("sessions", [])
        assert any(s.get("session_id") == session_id for s in sessions)

        assert called_ext == [".pdf"], f"expected PDF extraction path, got {called_ext}"
    finally:
        routes._config_path = original_config_path
        routes._config = original_config
        routes._audit_engine = original_engine
