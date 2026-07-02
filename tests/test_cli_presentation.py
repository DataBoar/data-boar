"""Tests for OS-aware CLI help presentation (#1130)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from utils.cli_presentation import (
    DASHBOARD_CLI_PROG,
    build_cli_epilog,
    cli_filesystem_lgpd_example,
    cli_help_context,
    cli_home_example,
    cli_prog_name,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]


def test_cli_prog_name_dev_main_py() -> None:
    assert cli_prog_name("main.py") == "python main.py"
    assert cli_prog_name("/repo/main.py") == "python main.py"


def test_cli_prog_name_installed_entry_point() -> None:
    assert cli_prog_name("data-boar") == "data-boar"
    assert cli_prog_name("/home/user/.local/bin/data-boar") == "data-boar"
    # Synthetic Windows pipx path (<username> is a PII-guard placeholder token).
    win_path = r"C:\Users\<username>\.local\bin\data-boar.exe"
    assert cli_prog_name(win_path) == "data-boar"


def test_home_example_is_concrete_not_tilde() -> None:
    home = cli_home_example()
    assert home
    assert "~" not in home
    assert home == str(Path.home())


def test_filesystem_lgpd_example_under_home() -> None:
    path = cli_filesystem_lgpd_example()
    assert "~" not in path
    assert path.startswith(str(Path.home()))


def test_build_cli_epilog_uses_argparse_prog_placeholder() -> None:
    epilog = build_cli_epilog()
    assert "%(prog)s" in epilog
    assert "python main.py" not in epilog
    assert "data-boar" not in epilog


def test_cli_help_stdout_uses_python_main_when_run_from_repo() -> None:
    result = subprocess.run(
        [sys.executable, str(_REPO_ROOT / "main.py"), "--help"],
        capture_output=True,
        text=True,
        cwd=str(_REPO_ROOT),
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "python main.py --config config.yaml --validate-config" in result.stdout
    assert "uv run" not in result.stdout


def test_web_help_shows_data_boar_and_concrete_home_path(tmp_path: Path) -> None:
    import api.routes as routes

    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        f"""targets: []
report:
  output_dir: {tmp_path}
api:
  port: 8088
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
    try:
        client = TestClient(routes.app)
        html = client.get("/help").text
        assert "uv run python main.py" not in html
        assert "python main.py --help" not in html
        assert f"{DASHBOARD_CLI_PROG} --demo" in html
        assert f"{DASHBOARD_CLI_PROG} --config config.yaml" in html
        assert cli_filesystem_lgpd_example() in html
        assert "~" not in html
    finally:
        routes._config_path = orig_path
        routes._config = orig_cfg
        routes._audit_engine = orig_engine


def test_cli_help_context_keys() -> None:
    ctx = cli_help_context()
    assert "cli_prog" not in ctx
    assert "home_example" in ctx
    assert "filesystem_lgpd_example" in ctx


def test_dashboard_cli_prog_constant() -> None:
    assert DASHBOARD_CLI_PROG == "data-boar"
