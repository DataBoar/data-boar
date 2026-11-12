"""SMB connector with a non-default port (#1447 demo: rootless Samba on a high port).

Measured on a rootless Samba published on 127.0.0.1:4450: the session was
registered on 4450, but ``smbclient.walk`` / ``scandir`` / ``open_file`` were
called without ``port`` and opened a new connection to 445 (connection refused),
and the error escaped ``run()`` because the walk generator is consumed outside
the guarded block.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from connectors.smb_connector import SMBConnector


class _DB:
    def __init__(self) -> None:
        self.failures: list[tuple[str, str, str]] = []
        self.findings: list[dict] = []

    def save_failure(self, target_name: str, reason: str, details: str) -> None:
        self.failures.append((target_name, reason, details))

    def save_finding(self, *args, **kwargs) -> None:
        self.findings.append(kwargs)


def _target(**extra) -> dict:
    return {
        "name": "smb-demo",
        "host": "127.0.0.1",
        "port": 4450,
        "share": "corpus",
        "user": "boardemo",
        "pass": "unit-test-only",
        "allow_private_networks": True,
        **extra,
    }


def _run(mock_smb: MagicMock, **extra) -> _DB:
    db = _DB()
    with (
        patch("connectors.smb_connector._SMB_AVAILABLE", True),
        patch("connectors.smb_connector.smbclient", mock_smb),
    ):
        SMBConnector(
            _target(**extra), scanner=MagicMock(), db_manager=db, extensions=[".txt"]
        ).run()
    return db


def test_custom_port_is_used_by_walk_and_open_file():
    mock_smb = MagicMock()
    mock_smb.walk.return_value = [("\\\\127.0.0.1\\corpus", [], ["a.txt"])]
    mock_smb.open_file.return_value.__enter__.return_value.read.return_value = b"x"
    _run(mock_smb)
    assert mock_smb.register_session.call_args.kwargs["port"] == 4450
    assert mock_smb.walk.call_args.kwargs.get("port") == 4450
    assert mock_smb.open_file.call_args.kwargs.get("port") == 4450


def test_custom_port_is_used_by_scandir_when_not_recursive():
    mock_smb = MagicMock()
    mock_smb.scandir.return_value = []
    _run(mock_smb, recursive=False)
    assert mock_smb.scandir.call_args.kwargs.get("port") == 4450


def test_walk_error_during_iteration_is_recorded_not_raised():
    def _failing_walk(*_a, **_k):
        raise ValueError("Failed to connect to '127.0.0.1:4450': refused")
        yield  # pragma: no cover - makes this a generator

    mock_smb = MagicMock()
    mock_smb.walk.side_effect = _failing_walk
    db = _run(mock_smb)
    assert [f for f in db.failures if f[1] == "unreachable"], db.failures
