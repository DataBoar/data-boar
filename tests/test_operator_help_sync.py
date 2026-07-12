"""
Contract tests: operator-facing help (CLI --help, web /help, man §1 source) stays
in rough sync with shipped features. See `tests/operator_help_sync_manifest.py`.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from tests.operator_help_sync_manifest import OPERATOR_HELP_MARKERS

_REPO_ROOT = Path(__file__).resolve().parents[1]
_MAN1_PATH = _REPO_ROOT / "docs" / "data_boar.1"


def _cli_help_stdout() -> str:
    result = subprocess.run(
        [sys.executable, str(_REPO_ROOT / "main.py"), "--help"],
        capture_output=True,
        text=True,
        cwd=str(_REPO_ROOT),
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


def _web_help_html(tmp_path: Path) -> str:
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
        response = client.get("/help")
        assert response.status_code == 200, response.text
        return response.text
    finally:
        routes._config_path = orig_path
        routes._config = orig_cfg
        routes._audit_engine = orig_engine


@pytest.fixture(scope="module")
def cli_help_text() -> str:
    return _cli_help_stdout()


@pytest.fixture(scope="module")
def man1_text() -> str:
    assert _MAN1_PATH.is_file(), f"missing {_MAN1_PATH}"
    return _MAN1_PATH.read_text(encoding="utf-8")


def test_operator_help_markers_in_cli_help(cli_help_text: str) -> None:
    for marker in OPERATOR_HELP_MARKERS:
        if marker.cli_help_substring is None:
            continue
        assert marker.cli_help_substring in cli_help_text, (
            f"CLI --help missing {marker.id!r} "
            f"(expected substring {marker.cli_help_substring!r}); "
            "update main.py and tests/operator_help_sync_manifest.py"
        )


def test_operator_help_markers_in_web_help(tmp_path: Path) -> None:
    html = _web_help_html(tmp_path)
    for marker in OPERATOR_HELP_MARKERS:
        if marker.web_help_substring is None:
            continue
        assert marker.web_help_substring in html, (
            f"GET /help missing {marker.id!r} "
            f"(expected substring {marker.web_help_substring!r}); "
            "update api/templates/help.html and tests/operator_help_sync_manifest.py"
        )


def test_operator_help_markers_in_man1(man1_text: str) -> None:
    for marker in OPERATOR_HELP_MARKERS:
        if marker.man1_troff_substring is None:
            continue
        assert marker.man1_troff_substring in man1_text, (
            f"docs/data_boar.1 missing {marker.id!r} "
            f"(expected troff substring {marker.man1_troff_substring!r}); "
            "update man page and tests/operator_help_sync_manifest.py"
        )


def test_cli_help_uses_dev_canonical_invocation(cli_help_text: str) -> None:
    assert "usage: python main.py" in cli_help_text
    assert "python main.py --config config.yaml" in cli_help_text
    assert "--validate-config" in cli_help_text


def test_web_help_uses_runtime_prog_and_concrete_home_path(tmp_path: Path) -> None:
    html = _web_help_html(tmp_path)
    expected_docs_path = str(Path.home() / "Documents" / "LGPD")
    assert "python main.py --config config.yaml" in html
    assert "uv run python main.py" not in html
    assert expected_docs_path in html
    assert "~/Documents/LGPD" not in html
