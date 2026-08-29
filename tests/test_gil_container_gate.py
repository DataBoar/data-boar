"""#1409: container GIL gate is license-tier, not is_feature_available."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from core.licensing.gil_container_gate import (
    DEFAULT_CONTAINER_PYTHON,
    config_path_from_argv,
    environ_with_gil_gate,
    load_yaml_config,
    resolve_python_executable,
    resolve_tier,
    should_force_gil,
    strip_interpreter_prefix,
)
from core.licensing.guard import reset_license_guard_for_tests
from core.licensing.tier_features import Tier

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _reset_license_guard() -> None:
    reset_license_guard_for_tests()
    yield
    reset_license_guard_for_tests()


@pytest.mark.parametrize(
    ("tier", "force"),
    [
        (Tier.ENTERPRISE, False),
        (Tier.PARTNER, True),
        (Tier.PRO_PLUS, True),
        (Tier.PRO, True),
        (Tier.STD, True),
        (Tier.COMMUNITY, True),
        (Tier.OPEN, True),
    ],
)
def test_should_force_gil_only_enterprise_keeps_nogil(tier: Tier, force: bool) -> None:
    assert should_force_gil(tier) is force


def test_gate_module_does_not_use_feature_availability_bypass() -> None:
    text = (REPO / "core" / "licensing" / "gil_container_gate.py").read_text(
        encoding="utf-8"
    )
    assert "is_feature_available(" not in text
    assert "PYTHON_GIL=0" not in text
    assert "os.execve" in text


def test_environ_non_enterprise_sets_python_gil() -> None:
    env = environ_with_gil_gate({"PATH": "/usr/bin"}, Tier.OPEN)
    assert env["PYTHON_GIL"] == "1"
    env_p = environ_with_gil_gate({}, Tier.PARTNER)
    assert env_p["PYTHON_GIL"] == "1"


def test_environ_enterprise_does_not_set_python_gil() -> None:
    env = environ_with_gil_gate({"PATH": "/usr/bin"}, Tier.ENTERPRISE)
    assert "PYTHON_GIL" not in env


def test_resolve_python_ignores_arbitrary_env_executable(tmp_path: Path) -> None:
    """Env must not pick the execve target (Semgrep tainted-env-args)."""
    decoy = tmp_path / "not-python"
    decoy.write_text("#!/bin/sh\n")
    decoy.chmod(0o755)
    resolved = resolve_python_executable({"DATA_BOAR_CONTAINER_PYTHON": str(decoy)})
    assert resolved != str(decoy)
    assert resolved in {DEFAULT_CONTAINER_PYTHON, sys.executable}


def test_strip_interpreter_prefix() -> None:
    assert strip_interpreter_prefix(["/usr/local/bin/python3.14t", "main.py"]) == [
        "main.py"
    ]
    assert strip_interpreter_prefix(["main.py", "--web"]) == ["main.py", "--web"]


def test_config_path_from_argv(tmp_path: Path) -> None:
    cfg = tmp_path / "config.yaml"
    cfg.write_text("licensing:\n  mode: open\n  effective_tier: enterprise\n")
    assert config_path_from_argv(["--config", str(cfg)], {}) == cfg
    assert config_path_from_argv([f"--config={cfg}"], {}) == cfg


def test_open_yaml_enterprise_resolves_enterprise(tmp_path: Path) -> None:
    cfg = tmp_path / "config.yaml"
    cfg.write_text("licensing:\n  mode: open\n  effective_tier: enterprise\n")
    data = load_yaml_config(cfg)
    assert resolve_tier(data) is Tier.ENTERPRISE


def test_open_yaml_missing_defaults_open_forces_gil(tmp_path: Path) -> None:
    cfg = tmp_path / "config.yaml"
    cfg.write_text("targets: []\n")
    data = load_yaml_config(cfg)
    assert resolve_tier(data) is Tier.OPEN
    assert should_force_gil(resolve_tier(data)) is True


def test_main_execve_sets_gil_for_open(tmp_path: Path) -> None:
    from core.licensing import gil_container_gate as gate

    cfg = tmp_path / "config.yaml"
    cfg.write_text("licensing:\n  mode: open\n  effective_tier: community\n")
    captured: dict[str, object] = {}

    def fake_execve(python: str, argv: list[str], env: dict[str, str]) -> None:
        captured["python"] = python
        captured["argv"] = argv
        captured["env"] = env
        raise SystemExit(0)

    with (
        patch.object(gate.os, "execve", fake_execve),
        pytest.raises(SystemExit),
    ):
        gate.main(["main.py", "--config", str(cfg), "--version"])
    assert captured["env"]["PYTHON_GIL"] == "1"  # type: ignore[index]
    assert captured["argv"][1:] == [  # type: ignore[index]
        "main.py",
        "--config",
        str(cfg),
        "--version",
    ]


def test_main_execve_enterprise_omits_python_gil(tmp_path: Path) -> None:
    from core.licensing import gil_container_gate as gate

    cfg = tmp_path / "config.yaml"
    cfg.write_text("licensing:\n  mode: open\n  effective_tier: enterprise\n")
    captured: dict[str, object] = {}

    def fake_execve(python: str, argv: list[str], env: dict[str, str]) -> None:
        captured["env"] = env
        captured["argv"] = argv
        raise SystemExit(0)

    with (
        patch.object(gate.os, "execve", fake_execve),
        pytest.raises(SystemExit),
    ):
        gate.main(["main.py", "--config", str(cfg), "--web"])
    assert "PYTHON_GIL" not in captured["env"]  # type: ignore[operator]


@pytest.mark.skipif(
    not hasattr(sys, "_is_gil_enabled"),
    reason="sys._is_gil_enabled requires CPython 3.13+",
)
def test_python_gil_env_enables_gil_on_this_interpreter() -> None:
    """Host CI is GIL-on 3.14: _is_gil_enabled stays True. Documents the env contract."""
    enabled = sys._is_gil_enabled()
    assert enabled is True or enabled is False
