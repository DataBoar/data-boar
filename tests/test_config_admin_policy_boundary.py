"""config_admin must not rewrite the security-policy subtrees (#2090)."""

from __future__ import annotations

import re
from pathlib import Path

import yaml
from fastapi.testclient import TestClient


def test_config_admin_cannot_grant_itself_admin(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv(
        "DATA_BOAR_WEBAUTHN_TOKEN_SECRET", "unit-test-webauthn-secret-min-16"
    )
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    (log_dir / "audit_20261020.log").write_text("ok\n", encoding="utf-8")
    cfg = tmp_path / "config.yaml"
    db = tmp_path / "audit.db"
    cfg.write_text(
        f"""targets: []
report:
  output_dir: {tmp_path}
sqlite_path: {db}
licensing:
  mode: enforced
  effective_tier: pro
api:
  port: 8088
  api_key: dummy-key
  require_api_key: true
  audit_logs:
    enabled: true
    directory: {log_dir}
  rbac:
    enabled: true
    api_key_roles:
      - config_admin
scan:
  max_workers: 1
""",
        encoding="utf-8",
    )
    import api.routes as routes

    prev_path = routes._config_path
    prev_cfg = routes._config
    prev_eng = routes._audit_engine
    routes._config_path = str(cfg)
    routes._config = None
    routes._audit_engine = None
    try:
        client = TestClient(routes.app)
        headers = {"X-API-Key": "dummy-key"}
        before = client.get("/logs", headers=headers)
        assert before.status_code == 403, before.text
        page = client.get("/en/config", headers=headers)
        assert page.status_code == 200, page.text
        match = re.search(r'name="csrf_token" value="([^"]+)"', page.text)
        assert match
        edited = yaml.safe_load(cfg.read_text(encoding="utf-8"))
        edited["api"]["rbac"]["api_key_roles"] = ["config_admin", "admin"]
        saved = client.post(
            "/en/config",
            headers=headers,
            data={
                "csrf_token": match.group(1),
                "yaml": yaml.safe_dump(edited),
            },
            follow_redirects=False,
        )
        assert saved.status_code == 303, saved.text
        after = client.get("/logs", headers=headers)
        assert after.status_code == 403, after.text
    finally:
        routes._config_path = prev_path
        routes._config = prev_cfg
        routes._audit_engine = prev_eng
        from core.licensing.guard import reset_license_guard_for_tests

        reset_license_guard_for_tests()
