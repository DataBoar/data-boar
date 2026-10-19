"""Notification ${VAR} interpolation uses the #1977 prefixes (#2087)."""

from __future__ import annotations

import pytest

from config.loader import normalize_config


def test_notification_env_rejects_non_prefixed_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LAB_NOTIFY_SLACK", "https://hooks.attacker.example/hook")
    with pytest.raises(ValueError, match="#1977"):
        normalize_config(
            {
                "targets": [],
                "notifications": {
                    "operator": {"slack_webhook_url": "${LAB_NOTIFY_SLACK}"},
                },
            }
        )


def test_public_base_url_does_not_expand_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("API_PUBLIC_SECRET", "super-secret")
    with pytest.raises(ValueError, match="public_base_url"):
        normalize_config(
            {
                "targets": [],
                "notifications": {"public_base_url": "${API_PUBLIC_SECRET}"},
            }
        )


def test_notification_env_expands_prefixed_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("API_NOTIFY_SLACK", "https://hooks.example/test")
    out = normalize_config(
        {
            "targets": [],
            "notifications": {
                "operator": {"slack_webhook_url": "${API_NOTIFY_SLACK}"},
            },
        }
    )
    assert (
        out["notifications"]["operator"]["slack_webhook_url"]
        == "https://hooks.example/test"
    )
