"""Tests for Enterprise remediation plugin host (#606 / ADR-0059)."""

from __future__ import annotations

from pathlib import Path

import pytest

from core.licensing.tier_features import Tier, is_feature_available
from core.plugins import PluginError, RemediationPlugin, load_remediation_plugin
from core.plugins.hook import maybe_run_remediation_hook


class _ValidRemediationPlugin:
    """Conformant mock for RemediationPlugin protocol."""

    @property
    def name(self) -> str:
        return "test-remediator"

    @property
    def version(self) -> str:
        return "0.0.1"

    def remediate(self, findings_path: Path, config: dict) -> Path:
        out = findings_path.parent / "remediation_report.json"
        out.write_text("{}", encoding="utf-8")
        return out


class _NonConformantPlugin:
    """Missing remediate / name / version — fails Protocol check."""

    def run(self) -> None:
        return None


def test_load_valid_plugin(monkeypatch: pytest.MonkeyPatch) -> None:
    import types

    mod = types.ModuleType("tests._fake_valid_remediation_plugin")
    mod.ValidPlugin = _ValidRemediationPlugin  # type: ignore[attr-defined]
    monkeypatch.setitem(__import__("sys").modules, mod.__name__, mod)

    plugin = load_remediation_plugin(f"{mod.__name__}:ValidPlugin")
    assert isinstance(plugin, RemediationPlugin)
    assert plugin.name == "test-remediator"
    assert plugin.version == "0.0.1"


def test_load_missing_module_raises_plugin_error() -> None:
    with pytest.raises(PluginError, match="Cannot import"):
        load_remediation_plugin("tests._no_such_module_xyz:Whatever")


def test_load_non_conformant_raises_plugin_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import types

    mod = types.ModuleType("tests._fake_bad_remediation_plugin")
    mod.BadPlugin = _NonConformantPlugin  # type: ignore[attr-defined]
    monkeypatch.setitem(__import__("sys").modules, mod.__name__, mod)

    with pytest.raises(PluginError, match="does not conform"):
        load_remediation_plugin(f"{mod.__name__}:BadPlugin")


def test_load_invalid_format_raises_plugin_error() -> None:
    with pytest.raises(PluginError, match="Invalid plugin_path format"):
        load_remediation_plugin("no_colon_here")


@pytest.mark.parametrize(
    ("tier", "expected"),
    [
        (Tier.OPEN, True),
        (Tier.ENTERPRISE, True),
        (Tier.COMMUNITY, False),
        (Tier.PRO, False),
    ],
)
def test_remediation_plugin_tier_gate(tier: Tier, expected: bool) -> None:
    assert is_feature_available("remediation_plugin", tier) is expected


def test_hook_community_skips_without_exception(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    cfg = {
        "licensing": {"mode": "open", "effective_tier": "community"},
        "report": {"output_dir": str(tmp_path)},
        "remediation": {
            "enabled": True,
            "plugin": "tests._never_loaded:X",
            "verify_after": True,
            "config": {},
        },
    }
    maybe_run_remediation_hook(cfg, "sess-community")
    err = capsys.readouterr().err
    assert "requires Enterprise tier" in err


def test_hook_pro_skips_without_exception(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    cfg = {
        "licensing": {"mode": "open", "effective_tier": "pro"},
        "report": {"output_dir": str(tmp_path)},
        "remediation": {
            "enabled": True,
            "plugin": "tests._never_loaded:X",
            "verify_after": True,
            "config": {},
        },
    }
    maybe_run_remediation_hook(cfg, "sess-pro")
    err = capsys.readouterr().err
    assert "requires Enterprise tier" in err


def test_hook_enterprise_loads_valid_plugin(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    import types

    mod = types.ModuleType("tests._fake_ent_remediation_plugin")
    mod.ValidPlugin = _ValidRemediationPlugin  # type: ignore[attr-defined]
    monkeypatch.setitem(__import__("sys").modules, mod.__name__, mod)

    findings = tmp_path / "findings_sess-ent.jsonl"
    findings.write_text("{}\n", encoding="utf-8")

    cfg = {
        "licensing": {"mode": "open", "effective_tier": "enterprise"},
        "report": {"output_dir": str(tmp_path)},
        "remediation": {
            "enabled": True,
            "plugin": f"{mod.__name__}:ValidPlugin",
            "verify_after": True,
            "config": {},
        },
    }
    maybe_run_remediation_hook(cfg, "sess-ent")
    out = capsys.readouterr().out
    assert "Remediation complete:" in out
    assert "post-remediation verification pending (see #653)" in out
    assert (tmp_path / "remediation_report.json").is_file()


def test_hook_open_tier_loads_valid_plugin(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    import types

    mod = types.ModuleType("tests._fake_open_remediation_plugin")
    mod.ValidPlugin = _ValidRemediationPlugin  # type: ignore[attr-defined]
    monkeypatch.setitem(__import__("sys").modules, mod.__name__, mod)

    findings = tmp_path / "findings_sess-open.jsonl"
    findings.write_text("{}\n", encoding="utf-8")

    cfg = {
        "licensing": {"mode": "open", "effective_tier": ""},
        "report": {"output_dir": str(tmp_path)},
        "remediation": {
            "enabled": True,
            "plugin": f"{mod.__name__}:ValidPlugin",
            "verify_after": False,
            "config": {},
        },
    }
    maybe_run_remediation_hook(cfg, "sess-open")
    out = capsys.readouterr().out
    assert "Remediation complete:" in out


def test_hook_non_conformant_contained_no_crash(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    import types

    mod = types.ModuleType("tests._fake_hook_bad_plugin")
    mod.BadPlugin = _NonConformantPlugin  # type: ignore[attr-defined]
    monkeypatch.setitem(__import__("sys").modules, mod.__name__, mod)

    cfg = {
        "licensing": {"mode": "open", "effective_tier": "enterprise"},
        "report": {"output_dir": str(tmp_path)},
        "remediation": {
            "enabled": True,
            "plugin": f"{mod.__name__}:BadPlugin",
            "verify_after": False,
            "config": {},
        },
    }
    maybe_run_remediation_hook(cfg, "sess-bad")  # must not raise
    err = capsys.readouterr().err
    assert "[remediation] plugin error:" in err
