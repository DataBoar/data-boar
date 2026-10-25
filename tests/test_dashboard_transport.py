"""Tests for dashboard HTTPS / explicit HTTP transport resolution and env snapshot."""

from __future__ import annotations

import os
import pytest

from core.dashboard_transport import (
    configure_dashboard_transport,
    get_dashboard_transport_snapshot,
    resolve_web_listen_options,
)


def test_resolve_https_when_cert_and_key_exist(tmp_path):
    cert = tmp_path / "srv.pem"
    key = tmp_path / "srv-key.pem"
    cert.write_text("cert\n", encoding="utf-8")
    key.write_text("key\n", encoding="utf-8")
    mode, cpath, kpath, insecure = resolve_web_listen_options(
        allow_insecure_http_cli=False,
        https_cert_file_cli=str(cert),
        https_key_file_cli=str(key),
        api_cfg={},
    )
    assert mode == "https"
    assert cpath == cert.resolve()
    assert kpath == key.resolve()
    assert insecure is False


def test_resolve_http_when_explicit_allow():
    mode, cpath, kpath, insecure = resolve_web_listen_options(
        allow_insecure_http_cli=True,
        https_cert_file_cli=None,
        https_key_file_cli=None,
        api_cfg={},
    )
    assert mode == "http"
    assert cpath is None and kpath is None
    assert insecure is True


def test_resolve_from_api_config_allow_and_paths(tmp_path):
    cert = tmp_path / "c.pem"
    key = tmp_path / "k.pem"
    cert.write_text("x", encoding="utf-8")
    key.write_text("y", encoding="utf-8")
    mode, cpath, kpath, insecure = resolve_web_listen_options(
        allow_insecure_http_cli=False,
        https_cert_file_cli=None,
        https_key_file_cli=None,
        api_cfg={
            "allow_insecure_http": False,
            "https_cert_file": str(cert),
            "https_key_file": str(key),
        },
    )
    assert mode == "https"
    assert insecure is False


def test_resolve_rejects_missing_peer_path(tmp_path):
    cert = tmp_path / "c.pem"
    cert.write_text("x", encoding="utf-8")
    with pytest.raises(ValueError, match="Both https_cert_file"):
        resolve_web_listen_options(
            allow_insecure_http_cli=False,
            https_cert_file_cli=str(cert),
            https_key_file_cli=None,
            api_cfg={},
        )


def test_resolve_rejects_neither_tls_nor_allow():
    with pytest.raises(ValueError, match="choose TLS or explicit insecure"):
        resolve_web_listen_options(
            allow_insecure_http_cli=False,
            https_cert_file_cli=None,
            https_key_file_cli=None,
            api_cfg={"allow_insecure_http": False},
        )


def test_snapshot_not_configured_when_env_unset(monkeypatch):
    monkeypatch.delenv("DATA_BOAR_DASHBOARD_TRANSPORT", raising=False)
    monkeypatch.delenv("DATA_BOAR_DASHBOARD_INSECURE_OPT_IN", raising=False)
    snap = get_dashboard_transport_snapshot()
    assert snap["mode"] == "not_configured"
    assert snap["show_insecure_banner"] is False


def test_snapshot_after_configure():
    configure_dashboard_transport(
        mode="http",
        insecure_explicit_opt_in=True,
        cert_path=None,
        key_path=None,
    )
    try:
        snap = get_dashboard_transport_snapshot()
        assert snap["mode"] == "http"
        assert snap["tls_active"] is False
        assert snap["insecure_http_explicit_opt_in"] is True
        assert snap["show_insecure_banner"] is True
        assert "tls_posture" not in snap
    finally:
        os.environ.pop("DATA_BOAR_DASHBOARD_TRANSPORT", None)
        os.environ.pop("DATA_BOAR_DASHBOARD_INSECURE_OPT_IN", None)
        os.environ.pop("DATA_BOAR_HTTPS_CERT_FILE", None)
        os.environ.pop("DATA_BOAR_HTTPS_KEY_FILE", None)


def test_snapshot_includes_tls_posture_when_set():
    from core.tls_posture import (
        ENV_TLS_POSTURE,
        clear_tls_posture_snapshot,
        set_tls_posture_snapshot,
    )

    configure_dashboard_transport(
        mode="https",
        insecure_explicit_opt_in=False,
        cert_path="/tmp/demo-cert.pem",
        key_path="/tmp/demo-key.pem",
    )
    set_tls_posture_snapshot(
        {
            "checked": True,
            "ok": True,
            "trust_reasons": [],
            "summary": "TLS posture OK",
        }
    )
    try:
        snap = get_dashboard_transport_snapshot()
        assert snap["mode"] == "https"
        assert snap["tls_posture"]["ok"] is True
        assert snap["tls_posture"]["summary"] == "TLS posture OK"
        assert ENV_TLS_POSTURE in os.environ
    finally:
        clear_tls_posture_snapshot()
        os.environ.pop("DATA_BOAR_DASHBOARD_TRANSPORT", None)
        os.environ.pop("DATA_BOAR_DASHBOARD_INSECURE_OPT_IN", None)
        os.environ.pop("DATA_BOAR_HTTPS_CERT_FILE", None)
        os.environ.pop("DATA_BOAR_HTTPS_KEY_FILE", None)
        os.environ.pop(ENV_TLS_POSTURE, None)


def test_snapshot_omits_tls_posture_on_http_even_if_env_set():
    from core.tls_posture import clear_tls_posture_snapshot, set_tls_posture_snapshot

    configure_dashboard_transport(
        mode="http",
        insecure_explicit_opt_in=True,
    )
    set_tls_posture_snapshot(
        {
            "checked": True,
            "ok": False,
            "trust_reasons": ["tls_cipher_baseline_weak"],
            "summary": "stale",
        }
    )
    try:
        snap = get_dashboard_transport_snapshot()
        assert snap["mode"] == "http"
        assert "tls_posture" not in snap
    finally:
        clear_tls_posture_snapshot()
        os.environ.pop("DATA_BOAR_DASHBOARD_TRANSPORT", None)
        os.environ.pop("DATA_BOAR_DASHBOARD_INSECURE_OPT_IN", None)
