"""Config editor redaction and merge (#2093)."""

from __future__ import annotations

from pathlib import Path

from config.redact_config import (
    REDACTED_PLACEHOLDER,
    merge_config_on_save,
    redact_config_for_display,
)


def test_malformed_userinfo_url_does_not_reveal_password() -> None:
    shown = redact_config_for_display({"note": "http://user:senha@host:portaruim/path"})
    blob = str(shown)
    assert "senha" not in blob
    assert shown["note"] == REDACTED_PLACEHOLDER


def test_malformed_url_does_not_reveal_secrets(tmp_path: Path) -> None:
    import api.routes as routes

    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        'api:\n  api_key: dummy-key-123\nnote: "http://[x"\n',
        encoding="utf-8",
    )
    prev = routes._config_path
    routes._config_path = str(cfg)
    try:
        shown = routes._get_config_yaml_for_display()
    finally:
        routes._config_path = prev
    assert "dummy-key-123" not in shown


def test_merge_drops_omitted_non_secret_keys_and_list_items() -> None:
    shortened = merge_config_on_save(
        {"api": {"trusted_proxy_cidrs": ["10.0.0.0/8"]}},
        {"api": {"trusted_proxy_cidrs": ["10.0.0.0/8", "192.0.2.0/24"]}},
    )
    assert shortened["api"]["trusted_proxy_cidrs"] == ["10.0.0.0/8"]

    roles = merge_config_on_save(
        {"api": {"rbac": {"default_roles": ["dashboard", "scanner"]}}},
        {
            "api": {
                "rbac": {
                    "default_roles": [
                        "dashboard",
                        "scanner",
                        "reports_reader",
                        "config_admin",
                    ]
                }
            }
        },
    )
    assert roles["api"]["rbac"]["default_roles"] == ["dashboard", "scanner"]

    dropped = merge_config_on_save(
        {"api": {"require_api_key": True}},
        {"api": {"require_api_key": True, "x_extra": 1}},
    )
    assert "x_extra" not in dropped["api"]

    targets = merge_config_on_save(
        {"targets": [{"name": "b"}]},
        {"targets": [{"name": "a", "pass": "p1", "host": "h1"}, {"name": "b"}]},
    )
    assert targets["targets"] == [{"name": "b"}]


def test_webhook_urls_are_redacted_for_display() -> None:
    shown = redact_config_for_display(
        {
            "notifications": {
                "operator": {
                    "slack_webhook_url": "https://hooks.slack.com/services/T000/B000/XXXXXXXX",
                    "teams_webhook_url": "https://example.invalid/webhook/abc123",
                    "telegram_bot_token": "dummy-token",
                }
            }
        }
    )
    op = shown["notifications"]["operator"]
    assert op["slack_webhook_url"] == REDACTED_PLACEHOLDER
    assert op["teams_webhook_url"] == REDACTED_PLACEHOLDER
    assert op["telegram_bot_token"] == REDACTED_PLACEHOLDER
    assert "XXXXXXXX" not in str(shown)
    assert "abc123" not in str(shown)
