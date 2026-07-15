"""CLI: main.py --validate-config pre-flight without scan or API."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest


def _base_config(tmp_path: Path, targets_yaml: str) -> Path:
    cfg = tmp_path / "c.yaml"
    db = tmp_path / "a.db"
    cfg.write_text(
        f"""targets:
{targets_yaml}
report:
  output_dir: {tmp_path.as_posix()}
sqlite_path: {db.as_posix()}
api:
  port: 8765
scan:
  max_workers: 1
""",
        encoding="utf-8",
    )
    return cfg


def _run_validate(
    cfg: Path, *, extra_args: list[str] | None = None
) -> subprocess.CompletedProcess[str]:
    repo = Path(__file__).resolve().parents[1]
    cmd = [
        sys.executable,
        str(repo / "main.py"),
        "--config",
        str(cfg),
        "--validate-config",
    ]
    if extra_args:
        cmd.extend(extra_args)
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(repo),
        timeout=60,
        check=False,
    )


def test_validate_config_ok_filesystem_target(tmp_path):
    cfg = _base_config(
        tmp_path,
        """  - name: files-share
    type: filesystem
    path: /tmp/data-boar-validate""",
    )
    r = _run_validate(cfg)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "Validating config:" in r.stdout
    assert "[OK] 1 target(s) valid" in r.stdout
    assert 'OK    target[0] "files-share"' in r.stdout


def test_validate_config_invalid_yaml(tmp_path):
    cfg = tmp_path / "bad.yaml"
    cfg.write_text("targets: [\n", encoding="utf-8")
    r = _run_validate(cfg)
    assert r.returncode == 1, r.stdout + r.stderr
    assert "Config error:" in r.stdout


def test_validate_config_unknown_type_exits_invalid(tmp_path):
    cfg = _base_config(
        tmp_path,
        """  - name: salesforce-crm
    type: sfdc""",
    )
    r = _run_validate(cfg)
    assert r.returncode == 1, r.stdout + r.stderr
    assert "[INVALID]" in r.stdout
    assert "unknown type/driver" in r.stdout
    assert "salesforce-crm" in r.stdout


def test_validate_config_missing_required_key(tmp_path):
    cfg = _base_config(
        tmp_path,
        """  - name: files-share
    type: filesystem""",
    )
    r = _run_validate(cfg)
    assert r.returncode == 1, r.stdout + r.stderr
    assert 'required key "path" missing' in r.stdout


def test_mask_env_name_sensitive_vs_non_sensitive() -> None:
    repo = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo))
    import main as main_module

    assert main_module._mask_env_name("pass_from_env", "PG_SECRET") == "***"
    assert main_module._mask_env_name("api_key_from_env", "API_KEY") == "***"
    assert main_module._mask_env_name("user_from_env", "DB_USER") == "DB_USER"


def test_validate_config_unset_env_var_warns_but_ok(tmp_path):
    env_name = "DB_USER_TEST_VALIDATE_CONFIG_UNUSED"
    cfg = _base_config(
        tmp_path,
        f"""  - name: prod-postgres
    type: database
    driver: postgresql+psycopg2
    user_from_env: {env_name}""",
    )
    child_env = os.environ.copy()
    child_env.pop(env_name, None)
    repo = Path(__file__).resolve().parents[1]
    r = subprocess.run(
        [
            sys.executable,
            str(repo / "main.py"),
            "--config",
            str(cfg),
            "--validate-config",
        ],
        capture_output=True,
        text=True,
        cwd=str(repo),
        timeout=60,
        check=False,
        env=child_env,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "[OK] 1 target(s) valid" in r.stdout
    assert env_name in r.stdout
    assert "WARN" in r.stdout


def test_validate_config_masks_sensitive_env_name_in_warning(tmp_path):
    env_name = "PG_PASS_TEST_VALIDATE_CONFIG_MASK"
    cfg = _base_config(
        tmp_path,
        f"""  - name: prod-postgres
    type: database
    driver: postgresql+psycopg2
    pass_from_env: {env_name}""",
    )
    child_env = os.environ.copy()
    child_env.pop(env_name, None)
    repo = Path(__file__).resolve().parents[1]
    r = subprocess.run(
        [
            sys.executable,
            str(repo / "main.py"),
            "--config",
            str(cfg),
            "--validate-config",
        ],
        capture_output=True,
        text=True,
        cwd=str(repo),
        timeout=60,
        check=False,
        env=child_env,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "pass_from_env='***'" in r.stdout
    assert env_name not in r.stdout
    assert "WARN" in r.stdout


def test_validate_config_rejects_web_combo(tmp_path):
    cfg = _base_config(tmp_path, "  []")
    r = _run_validate(cfg, extra_args=["--web"])
    assert r.returncode == 2, r.stdout + r.stderr
    assert "Cannot combine --validate-config" in r.stderr


def test_validate_config_rejects_reset_data_combo(tmp_path):
    cfg = _base_config(tmp_path, "  []")
    r = _run_validate(cfg, extra_args=["--reset-data"])
    assert r.returncode == 2, r.stdout + r.stderr
    assert "Cannot combine --validate-config" in r.stderr


def test_validate_config_warns_when_sql_driver_dep_missing(
    tmp_path, monkeypatch, capsys
):
    """Offline probe: missing optional SQL driver → WARN, exit 0 (#1246)."""
    import yaml

    import main as main_module

    monkeypatch.setattr(
        "connectors.sql_driver_deps._module_available",
        lambda _name: False,
    )
    cfg_path = _base_config(
        tmp_path,
        """  - name: Demo_Postgres
    type: database
    driver: postgresql+psycopg2
    user: demo
    pass: demo
    host: 127.0.0.1
    database: demo""",
    )
    config = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    with pytest.raises(SystemExit) as ei:
        main_module._validate_config_and_exit(config, str(cfg_path))
    assert ei.value.code == 0
    out = capsys.readouterr().out
    assert "WARN" in out
    assert "data-boar[postgres]" in out
    assert "1 warning(s)" in out
    assert "0 warning(s)" not in out


def test_validate_config_ok_when_sql_driver_dep_present(tmp_path, monkeypatch, capsys):
    """Driver module present → no optional-dep WARN (#1246)."""
    import yaml

    import main as main_module

    monkeypatch.setattr(
        "connectors.sql_driver_deps._module_available",
        lambda _name: True,
    )
    cfg_path = _base_config(
        tmp_path,
        """  - name: Demo_Postgres
    type: database
    driver: postgresql+psycopg2
    user: demo
    pass: demo
    host: 127.0.0.1
    database: demo""",
    )
    config = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    with pytest.raises(SystemExit) as ei:
        main_module._validate_config_and_exit(config, str(cfg_path))
    assert ei.value.code == 0
    out = capsys.readouterr().out
    assert "[OK] 1 target(s) valid. 0 warning(s)." in out
    assert "data-boar[postgres]" not in out
