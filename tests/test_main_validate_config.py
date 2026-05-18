"""CLI: main.py --validate-config pre-flight without scan or API."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


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


def test_validate_config_unset_env_var_warns_but_ok(tmp_path):
    env_name = "PG_PASS_TEST_VALIDATE_CONFIG_UNUSED"
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
    assert "[OK] 1 target(s) valid" in r.stdout
    assert env_name in r.stdout
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
