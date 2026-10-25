"""The web process serves the config the bind gate already validated (#2091)."""

from __future__ import annotations

import pytest

from core.host_resolution import resolve_served_config_path


def test_non_loopback_mismatch_fails_closed(tmp_path):
    cli = tmp_path / "secure.yaml"
    other = tmp_path / "other.yaml"
    cli.write_text("api: {}\n", encoding="utf-8")
    other.write_text("api: {}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="config_path_mismatch"):
        resolve_served_config_path(
            cli_config=str(cli),
            env_config=str(other),
            host="0.0.0.0",
        )


def test_served_path_is_the_cli_file_on_loopback(tmp_path):
    cli = tmp_path / "secure.yaml"
    other = tmp_path / "other.yaml"
    cli.write_text("api: {}\n", encoding="utf-8")
    other.write_text("api: {}\n", encoding="utf-8")
    served = resolve_served_config_path(
        cli_config=str(cli),
        env_config=str(other),
        host="127.0.0.1",
    )
    assert served == str(cli.resolve())
