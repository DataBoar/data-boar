"""maestro#91: RC bench extras derivation, connector failure reason, smoke wiring."""

from __future__ import annotations

import importlib.metadata
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import yaml

from connectors import mongodb_connector, redis_connector
from scripts import rc_bench_extras

_ROOT = Path(__file__).resolve().parents[1]


def _config(name: str) -> dict:
    return yaml.safe_load((_ROOT / "tests" / "config" / name).read_text("utf-8"))


def test_rc_v2_needs_nosql_for_mongo_target() -> None:
    assert rc_bench_extras.extras_for_config(_config("benchmark-rc-v2.yaml")) == [
        "nosql"
    ]


def test_rc_v3_extras_follow_target_drivers() -> None:
    assert rc_bench_extras.extras_for_config(_config("benchmark-rc-v3.yaml")) == [
        "mysql",
        "nosql",
        "postgres",
        "shares",
    ]


def test_distributions_for_extras_reads_pyproject_and_expands_self_refs() -> None:
    deps = {
        "nosql": ["pymongo>=4.0", "redis>=8.1.0"],
        "postgres": ["psycopg2-binary>=2.9.11"],
        "sql-community": ["data-boar[postgres]"],
    }
    got = rc_bench_extras.distributions_for_extras(["nosql", "sql-community"], deps)
    assert got == {"nosql": ["pymongo", "redis"], "sql-community": ["psycopg2-binary"]}


def test_distributions_for_extras_rejects_undeclared_extra() -> None:
    with pytest.raises(KeyError, match="not declared"):
        rc_bench_extras.distributions_for_extras(["nope"], {"nosql": []})


def test_verify_reports_pruned_distribution(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    real = importlib.metadata.distribution

    def _fake(name: str):
        if name == "pymongo":
            raise importlib.metadata.PackageNotFoundError(name)
        return real(name)

    monkeypatch.setattr(importlib.metadata, "distribution", _fake)
    rc = rc_bench_extras.main(
        ["verify", "--config", "tests/config/benchmark-rc-v2.yaml"]
    )
    assert rc == 1
    assert "EXTRA_MISSING extra=nosql dist=pymongo" in capsys.readouterr().err


def test_missing_distributions_detects_absent_package() -> None:
    missing = rc_bench_extras.missing_distributions(
        {"x": ["definitely-not-installed-databoar-91"]}
    )
    assert missing == [("x", "definitely-not-installed-databoar-91")]


def test_list_command_prints_one_extra_per_line(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert (
        rc_bench_extras.main(["list", "--config", "tests/config/benchmark-rc-v3.yaml"])
        == 0
    )
    assert capsys.readouterr().out.split() == ["mysql", "nosql", "postgres", "shares"]


@pytest.mark.parametrize(
    ("module", "cls", "flag", "target"),
    [
        (mongodb_connector, "MongoDBConnector", "_MONGO_AVAILABLE", "Lab_Mongo_RC"),
        (redis_connector, "RedisConnector", "_REDIS_AVAILABLE", "Lab_Redis_RC"),
    ],
)
def test_connector_without_extra_records_missing_optional_dependency(
    monkeypatch: pytest.MonkeyPatch, module, cls: str, flag: str, target: str
) -> None:
    """Missing ``nosql`` must not be stored as ``unreachable`` (maestro#91)."""
    monkeypatch.setattr(module, flag, False)
    dbm = MagicMock()
    connector = getattr(module, cls)(
        {"name": target, "host": "127.0.0.1", "port": 1},
        scanner=MagicMock(),
        db_manager=dbm,
    )
    connector.run()
    dbm.save_failure.assert_called_once()
    name, reason, details = dbm.save_failure.call_args.args
    assert (name, reason) == (target, "missing_optional_dependency")
    assert "data-boar[nosql]" in details


def test_host_smoke_prepare_syncs_config_extras_and_verifies() -> None:
    text = (_ROOT / "scripts" / "lab-completao-host-smoke.sh").read_text("utf-8")
    assert "scripts/rc_bench_extras.py list --config" in text
    assert "scripts/rc_bench_extras.py verify --config" in text
    assert 'uv sync "${extra_args[@]}"' in text
