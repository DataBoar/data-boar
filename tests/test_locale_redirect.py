"""Dashboard locale prefix redirects and negotiation (M-LOCALE-V1)."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient


def _client(tmp_path: Path):
    import api.routes as routes

    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        f"""targets: []
report:
  output_dir: {tmp_path}
api:
  port: 8088
locale:
  default_locale: en
  supported_locales: [en, pt-BR]
sqlite_path: {tmp_path}/audit.db
scan:
  max_workers: 1
""",
        encoding="utf-8",
    )
    orig_path = routes._config_path
    orig_cfg = routes._config
    orig_engine = routes._audit_engine
    routes._config_path = str(config_path)
    routes._config = None
    routes._audit_engine = None
    client = TestClient(routes.app, follow_redirects=False)
    return routes, client, (orig_path, orig_cfg, orig_engine)


def _teardown(routes, orig):
    routes._config_path = orig[0]
    routes._config = orig[1]
    routes._audit_engine = orig[2]


def test_unprefixed_root_redirects_to_default_locale(tmp_path: Path):
    routes, client, orig = _client(tmp_path)
    try:
        r = client.get("/", follow_redirects=False)
        assert r.status_code == 302
        assert r.headers.get("location") == "/en/"
    finally:
        _teardown(routes, orig)


def test_accept_language_pt_br_redirects_to_pt_br_path(tmp_path: Path):
    routes, client, orig = _client(tmp_path)
    try:
        r = client.get(
            "/",
            headers={"Accept-Language": "pt-BR,pt;q=0.9,en;q=0.5"},
            follow_redirects=False,
        )
        assert r.status_code == 302
        assert r.headers.get("location") == "/pt-br/"
    finally:
        _teardown(routes, orig)


def test_prefixed_dashboard_ok(tmp_path: Path):
    routes, client, orig = _client(tmp_path)
    try:
        r = client.get("/en/", follow_redirects=False)
        assert r.status_code == 200
        assert "Audit Dashboard" in r.text or "Painel" in r.text
    finally:
        _teardown(routes, orig)
