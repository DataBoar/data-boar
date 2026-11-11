"""One-shot CLI scan waits for the findings push before exiting (#838).

The notification runs in a daemon thread; without the bounded join in
``main.py`` the interpreter could exit before the POST is sent.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from tests.governance_fixtures import RecordingServer

REPO = Path(__file__).resolve().parents[1]


def test_oneshot_scan_delivers_findings_push_before_exit(tmp_path):
    data = tmp_path / "corpus"
    data.mkdir()
    # Synthetic personal-data-shaped content (example values, not real people).
    (data / "contacts.csv").write_text(
        "name,email\nAna Example,ana@example.test\nBeto Example,beto@example.test\n",
        encoding="utf-8",
    )
    with RecordingServer() as srv:
        cfg = tmp_path / "config.yaml"
        cfg.write_text(
            f"""targets:
  - name: corpus
    type: filesystem
    path: {data}
file_scan:
  extensions: [.csv]
sqlite_path: {tmp_path / "audit.db"}
report:
  output_dir: {tmp_path / "out"}
api:
  audit_logs_dir: {tmp_path / "logs"}
licensing:
  mode: open
  effective_tier: pro_plus
notifications:
  enabled: true
  findings_push:
    enabled: true
    url: {srv.url}
    auth_env: API_TEST_SIEM_TOKEN
    allow_private_networks: true
""",
            encoding="utf-8",
        )
        env = {**os.environ, "API_TEST_SIEM_TOKEN": "tok-oneshot-123"}
        proc = subprocess.run(
            [sys.executable, str(REPO / "main.py"), "--config", str(cfg)],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
            env=env,
            timeout=300,
            check=False,
        )
        assert proc.returncode == 0, proc.stderr + proc.stdout
        assert len(srv.requests) == 1, "push must be delivered before the process exits"
        body = srv.json_bodies()[0]
        req = srv.requests[0]
    assert body["event"] == "scan_complete"
    assert body["delta_available"] is False  # first scan: no baseline
    assert body["previous_session_id"] is None
    assert req["headers"]["authorization"] == "Bearer tok-oneshot-123"
    assert "tok-oneshot-123" not in proc.stdout + proc.stderr
