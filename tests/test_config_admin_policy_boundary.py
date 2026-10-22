"""config_admin must not rewrite the security-policy subtrees (#2090)."""

from __future__ import annotations

import ast
import copy
import re
from pathlib import Path

import pytest
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


def test_merge_and_save_requires_request() -> None:
    """Omitting the request fails. The freeze cannot be skipped by default."""
    import api.routes as routes

    with pytest.raises(TypeError):
        routes._merge_and_save_config_yaml("targets: []\n")


def _expr_is_api_mapping(node: ast.AST, api_names: set[str]) -> bool:
    if isinstance(node, ast.Name):
        return node.id in api_names
    if isinstance(node, ast.IfExp):
        return _expr_is_api_mapping(node.body, api_names) or _expr_is_api_mapping(
            node.orelse, api_names
        )
    if isinstance(node, ast.BoolOp):
        return any(_expr_is_api_mapping(value, api_names) for value in node.values)
    if isinstance(node, ast.Subscript):
        return isinstance(node.slice, ast.Constant) and node.slice.value == "api"
    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
        return False
    if node.func.attr != "get" or not node.args:
        return False
    arg = node.args[0]
    return isinstance(arg, ast.Constant) and arg.value == "api"


def _record_api_names(tree: ast.AST) -> set[str]:
    api_names = {"api_cfg"}
    for node in ast.walk(tree):
        target = value = None
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target, value = node.targets[0], node.value
        elif isinstance(node, ast.AnnAssign):
            target, value = node.target, node.value
        if (
            isinstance(target, ast.Name)
            and value is not None
            and _expr_is_api_mapping(value, api_names)
        ):
            api_names.add(target.id)
    return api_names


def _string_const(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _api_key_literals(node: ast.AST, api_names: set[str]) -> set[str]:
    """Keys read by .get, api_cfg["k"], or ``"k" in api_cfg``."""
    found: set[str] = set()
    if (
        isinstance(node, ast.Call)
        and node.args
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "get"
    ):
        key = _string_const(node.args[0])
        receiver = node.func.value
        if key and (
            (isinstance(receiver, ast.Name) and receiver.id in api_names)
            or _expr_is_api_mapping(receiver, api_names)
        ):
            found.add(key)
    if isinstance(node, ast.Subscript):
        key = _string_const(node.slice)
        if key and isinstance(node.value, ast.Name) and node.value.id in api_names:
            found.add(key)
    if (
        isinstance(node, ast.Compare)
        and len(node.ops) == 1
        and isinstance(node.ops[0], ast.In)
        and node.comparators
    ):
        key = _string_const(node.left)
        right = node.comparators[0]
        if key and isinstance(right, ast.Name) and right.id in api_names:
            found.add(key)
    return found


def _api_keys_read_by_source(root: Path) -> set[str]:
    keys: set[str] = set()
    for folder in ("api", "config", "core"):
        for path in (root / folder).rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            api_names = _record_api_names(tree)
            for node in ast.walk(tree):
                keys.update(_api_key_literals(node, api_names))
    return keys


def test_every_api_key_the_code_reads_is_classified() -> None:
    """Default config keys and api reads must be editable or admin-only."""
    from config.loader import normalize_config
    import api.routes as routes

    root = Path(__file__).resolve().parents[1]
    default = yaml.safe_load(
        (root / "data" / "config.yaml").read_text(encoding="utf-8")
    )
    normalized = normalize_config(default if isinstance(default, dict) else {})
    api = normalized.get("api") if isinstance(normalized.get("api"), dict) else {}
    keys = set(api) | _api_keys_read_by_source(root)
    classified = routes.API_EDITABLE_KEYS | routes.API_ADMIN_ONLY_KEYS
    assert keys
    assert not (routes.API_EDITABLE_KEYS & routes.API_ADMIN_ONLY_KEYS)
    assert not (keys - classified), sorted(keys - classified)


def _clear_operator_license_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "CONFIG_PATH",
        "DATA_BOAR_LICENSE_PATH",
        "DATA_BOAR_LICENSE_MODE",
        "DATA_BOAR_LICENSE_PUBLIC_KEY_PATH",
        "DATA_BOAR_LICENSE_PUBLIC_KEY_PEM",
        "DATA_BOAR_LICENSE_MLDSA_PUBLIC_KEY_PATH",
        "DATA_BOAR_LICENSE_MLDSA_PUBLIC_KEY_PEM",
    ):
        monkeypatch.delenv(name, raising=False)


def _tamper(value: object) -> object:
    if isinstance(value, dict):
        copied = copy.deepcopy(value)
        copied["tamper"] = True
        return copied
    if isinstance(value, bool):
        return not value
    if isinstance(value, int):
        return value + 1
    if isinstance(value, str):
        return value + "-tampered"
    if isinstance(value, list):
        return [*value, "tampered"]
    return "tampered"


def _config_document(tmp_path: Path, api: dict) -> dict:
    log_dir = tmp_path / "logs"
    log_dir.mkdir(exist_ok=True)
    (log_dir / "audit_20261020.log").write_text("ok\n", encoding="utf-8")
    return {
        "targets": [],
        "report": {"output_dir": str(tmp_path)},
        "sqlite_path": str(tmp_path / "audit.db"),
        "licensing": {"mode": "enforced", "effective_tier": "pro"},
        "api": api,
        "scan": {"max_workers": 1},
    }


def _save_edited_api(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, api: dict, edited_api: dict
) -> dict:
    """POST /config as config_admin and return the api mapping written to disk."""
    _clear_operator_license_env(monkeypatch)
    monkeypatch.setenv(
        "DATA_BOAR_WEBAUTHN_TOKEN_SECRET", "unit-test-webauthn-secret-min-16"
    )
    cfg = tmp_path / "config.yaml"
    cfg.write_text(yaml.safe_dump(_config_document(tmp_path, api)), encoding="utf-8")
    import api.routes as routes

    prev = (routes._config_path, routes._config, routes._audit_engine)
    routes._config_path, routes._config, routes._audit_engine = str(cfg), None, None
    try:
        client = TestClient(routes.app)
        headers = {"X-API-Key": "dummy-key"}
        page = client.get("/en/config", headers=headers)
        assert page.status_code == 200, page.text
        match = re.search(r'name="csrf_token" value="([^"]+)"', page.text)
        assert match
        saved = client.post(
            "/en/config",
            headers=headers,
            data={
                "csrf_token": match.group(1),
                "yaml": yaml.safe_dump(_config_document(tmp_path, edited_api)),
            },
            follow_redirects=False,
        )
        assert saved.status_code == 303, saved.text
        written = yaml.safe_load(cfg.read_text(encoding="utf-8"))
        return written["api"]
    finally:
        routes._config_path, routes._config, routes._audit_engine = prev
        from core.licensing.guard import reset_license_guard_for_tests

        reset_license_guard_for_tests()


def _base_api(*, rbac_enabled: bool) -> dict:
    return {
        "port": 8088,
        "api_key": "dummy-key",
        "require_api_key": True,
        "audit_logs": {"enabled": True, "directory": "logs"},
        "rbac": {"enabled": rbac_enabled, "api_key_roles": ["config_admin"]},
        "host": "127.0.0.1",
        "trusted_hosts": ["localhost"],
        "trusted_proxy_cidrs": ["127.0.0.1/32"],
        "https_cert_file": "cert.pem",
        "https_key_file": "key.pem",
        "https_cert_fingerprint_sha256": "ab",
        "allow_insecure_http": False,
        "allow_adhoc_targets": False,
        "api_key_from_env": "DATA_BOAR_DEMO_API_KEY",
        "auth_failure_throttle": {"max_failures": 5, "window_seconds": 60},
        "maturity_assessment_pack_path": "pack",
        "maturity_integrity_secret_from_env": "DATA_BOAR_DEMO_INTEGRITY",
        "maturity_self_assessment_poc_enabled": False,
        "webauthn": {"enabled": False},
    }


def _admin_only_keys() -> list[str]:
    import api.routes as routes

    return sorted(routes.API_ADMIN_ONLY_KEYS)


@pytest.mark.parametrize("key", _admin_only_keys())
def test_config_admin_cannot_change_admin_only_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, key: str
) -> None:
    api = _base_api(rbac_enabled=True)
    edited = copy.deepcopy(api)
    edited[key] = _tamper(api[key])
    saved = _save_edited_api(tmp_path, monkeypatch, api, edited)
    assert saved.get(key) == api[key]


def test_config_admin_cannot_add_unclassified_api_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    api = _base_api(rbac_enabled=True)
    edited = copy.deepcopy(api)
    edited["unclassified_policy"] = "changed"
    saved = _save_edited_api(tmp_path, monkeypatch, api, edited)
    assert "unclassified_policy" not in saved


def test_config_admin_cannot_persist_non_string_api_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    api = _base_api(rbac_enabled=True)
    edited = copy.deepcopy(api)
    edited[True] = "changed"
    saved = _save_edited_api(tmp_path, monkeypatch, api, edited)
    assert True not in saved


def test_config_admin_can_change_listen_port(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    api = _base_api(rbac_enabled=True)
    edited = copy.deepcopy(api)
    edited["port"] = 8090
    saved = _save_edited_api(tmp_path, monkeypatch, api, edited)
    assert saved["port"] == 8090


def test_inactive_rbac_does_not_freeze_api_keys(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    api = _base_api(rbac_enabled=False)
    edited = copy.deepcopy(api)
    edited["require_api_key"] = False
    saved = _save_edited_api(tmp_path, monkeypatch, api, edited)
    assert saved["require_api_key"] is False
