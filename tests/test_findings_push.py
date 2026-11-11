"""Post-scan findings push to a SIEM / webhook (#838). No external network:
every endpoint is a loopback server on an ephemeral port."""

from __future__ import annotations

import logging
import ssl
import threading
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from config.loader import normalize_config
from core import findings_push
from core.database import LocalDBManager
from core.findings_push import (
    build_push_body,
    push_findings_for_session,
    push_settings,
    redacted_destination,
)
from core.licensing.guard import reset_license_guard_for_tests
from tests.governance_fixtures import (
    SESSION_NEW,
    SESSION_OLD,
    RecordingServer,
    assert_valid_sarif,
    no_sleep,
    push_config,
    seed_two_sessions,
)

TOKEN = "tok-S3cr3t-VALUE-9f2c"


@pytest.fixture(autouse=True)
def _env_and_guard(monkeypatch):
    reset_license_guard_for_tests()
    monkeypatch.setenv("API_TEST_SIEM_TOKEN", TOKEN)
    yield
    reset_license_guard_for_tests()


@pytest.fixture
def db(tmp_path):
    path = str(tmp_path / "audit.db")
    seed_two_sessions(path)
    mgr = LocalDBManager(path)
    yield mgr
    mgr.dispose()


# --- delta in the payload ---------------------------------------------------


def test_json_envelope_carries_delta(db):
    with RecordingServer() as srv:
        cfg = push_config(srv.url)
        res = push_findings_for_session(cfg, db, SESSION_NEW, sleep=no_sleep())
        assert res.ok, res.detail
        body = srv.json_bodies()[0]
    assert body["schema"] == "data-boar.findings-push"
    assert body["event"] == "scan_complete"
    assert body["previous_session_id"] == SESSION_OLD
    assert body["new_findings_count"] == 1
    assert body["resolved_count"] == 1
    assert body["delta_available"] is True
    assert body["findings_scope"] == "new"
    assert [f["location"] for f in body["findings"]] == ["public.users.cpf"]
    assert body["findings"][0]["is_new"] is True
    assert body["summary"]["total_findings"] == 3
    assert body["metadata_only"] is True


def test_first_session_sends_null_delta_and_full_baseline(db):
    with RecordingServer() as srv:
        res = push_findings_for_session(
            push_config(srv.url), db, SESSION_OLD, sleep=no_sleep()
        )
        assert res.ok
        body = srv.json_bodies()[0]
    assert body["previous_session_id"] is None
    assert body["new_findings_count"] is None
    assert body["resolved_count"] is None
    assert body["delta_available"] is False
    assert body["findings_scope"] == "all"  # no baseline: everything is baseline
    assert body["findings_included"] == 3


def test_findings_scope_all_marks_which_are_new(db):
    with RecordingServer() as srv:
        cfg = push_config(srv.url, findings_scope="all")
        assert push_findings_for_session(cfg, db, SESSION_NEW, sleep=no_sleep()).ok
        body = srv.json_bodies()[0]
    assert body["findings_included"] == 3
    assert sorted(f["is_new"] for f in body["findings"]) == [False, False, True]
    assert body["new_findings_count"] == 1  # count stays row-based as in --diff


def test_delta_matches_session_diff_command(db):
    diff = db.diff_sessions(SESSION_OLD, SESSION_NEW)
    new = sum(len(diff[k]["new"]) for k in ("database", "filesystem", "application"))
    res = sum(
        len(diff[k]["resolved"]) for k in ("database", "filesystem", "application")
    )
    with RecordingServer() as srv:
        assert push_findings_for_session(
            push_config(srv.url), db, SESSION_NEW, sleep=no_sleep()
        ).ok
        body = srv.json_bodies()[0]
    assert (body["new_findings_count"], body["resolved_count"]) == (new, res)


def test_baseline_skips_unfinished_sessions(tmp_path):
    path = str(tmp_path / "audit.db")
    seed_two_sessions(path)
    mgr = LocalDBManager(path)
    try:
        mgr.create_session_record("govsess-stuck-0003")
        mgr.set_current_session_id("govsess-stuck-0003")
        mgr.save_finding(
            "database",
            target_name="crm-db",
            schema_name="public",
            table_name="t",
            column_name="c",
            sensitivity_level="LOW",
            pattern_detected="EMAIL",
        )
        mgr.finish_session("govsess-stuck-0003", status="interrupted")
        mgr.create_session_record("govsess-last-0004")
        mgr.set_current_session_id("govsess-last-0004")
        mgr.finish_session("govsess-last-0004")
        from core.findings_common import select_baseline_session

        # the interrupted run is not a baseline; the last finished one is
        assert select_baseline_session(mgr, "govsess-last-0004") == SESSION_NEW
    finally:
        mgr.dispose()


def test_sarif_envelope_valid_and_carries_delta(db):
    with RecordingServer() as srv:
        cfg = push_config(srv.url, format="sarif", findings_scope="all")
        assert push_findings_for_session(cfg, db, SESSION_NEW, sleep=no_sleep()).ok
        doc = srv.json_bodies()[0]
    assert_valid_sarif(doc)
    props = doc["runs"][0]["properties"]
    assert props["new_findings_count"] == 1
    assert props["resolved_count"] == 1
    assert props["previous_session_id"] == SESSION_OLD
    assert {r["baselineState"] for r in doc["runs"][0]["results"]} == {
        "new",
        "unchanged",
    }


# --- adapters / auth ---------------------------------------------------------


def test_generic_webhook_bearer_auth_from_env(db):
    with RecordingServer() as srv:
        assert push_findings_for_session(
            push_config(srv.url), db, SESSION_NEW, sleep=no_sleep()
        ).ok
        req = srv.requests[0]
    assert req["headers"]["authorization"] == f"Bearer {TOKEN}"
    assert req["headers"]["content-type"] == "application/json"
    assert TOKEN.encode() not in req["body"]
    assert req["path"] == "/services/collector/event"


def test_custom_header_and_empty_scheme(db):
    with RecordingServer() as srv:
        cfg = push_config(srv.url, auth_header="X-Api-Key", auth_scheme="")
        assert push_findings_for_session(cfg, db, SESSION_NEW, sleep=no_sleep()).ok
        assert srv.requests[0]["headers"]["x-api-key"] == TOKEN


def test_splunk_hec_adapter(db):
    with RecordingServer() as srv:
        cfg = push_config(
            srv.url, adapter="splunk_hec", hec_index="privacy", hec_source="boar-lab"
        )
        assert push_findings_for_session(cfg, db, SESSION_NEW, sleep=no_sleep()).ok
        req = srv.requests[0]
        evt = srv.json_bodies()[0]
    assert req["headers"]["authorization"] == f"Splunk {TOKEN}"
    assert evt["sourcetype"] == "data_boar:findings"
    assert evt["source"] == "boar-lab"
    assert evt["index"] == "privacy"
    assert isinstance(evt["time"], float)
    assert evt["event"]["new_findings_count"] == 1


def test_splunk_hec_with_sarif_event(db):
    with RecordingServer() as srv:
        cfg = push_config(srv.url, adapter="splunk_hec", format="sarif")
        assert push_findings_for_session(cfg, db, SESSION_NEW, sleep=no_sleep()).ok
        evt = srv.json_bodies()[0]
    assert evt["sourcetype"] == "data_boar:sarif"
    assert_valid_sarif(evt["event"])


def test_no_auth_env_sends_no_authorization_header(db):
    with RecordingServer() as srv:
        cfg = push_config(srv.url, auth_env="")
        assert push_findings_for_session(cfg, db, SESSION_NEW, sleep=no_sleep()).ok
        assert "authorization" not in srv.requests[0]["headers"]


def test_missing_token_env_fails_without_sending(db, monkeypatch):
    monkeypatch.delenv("API_TEST_SIEM_TOKEN")
    with RecordingServer() as srv:
        res = push_findings_for_session(
            push_config(srv.url), db, SESSION_NEW, sleep=no_sleep()
        )
        assert srv.requests == []
    assert res.status == "failed"
    assert "environment variable" in res.detail


def test_token_with_control_characters_is_refused(db, monkeypatch):
    monkeypatch.setenv("API_TEST_SIEM_TOKEN", "abc\r\nX-Injected: 1")
    with RecordingServer() as srv:
        res = push_findings_for_session(
            push_config(srv.url), db, SESSION_NEW, sleep=no_sleep()
        )
        assert srv.requests == []
    assert res.status == "failed"
    assert "illegal characters" in res.detail


# --- secrets never leak -------------------------------------------------------


def test_token_and_url_never_appear_in_logs_or_result(db, caplog):
    secret_path = "/hook/SECRETPATHPART"
    with RecordingServer(statuses=[500, 500, 500]) as srv:
        url = srv.url.replace("/services/collector/event", secret_path)
        url += "?sig=SECRETQUERYSIG"
        with caplog.at_level(logging.DEBUG, logger="LGPDAudit"):
            res = push_findings_for_session(
                push_config(url), db, SESSION_NEW, sleep=no_sleep()
            )
    assert res.status == "failed" and res.attempts == 3
    blob = caplog.text + res.detail + repr(res)
    for needle in (TOKEN, "SECRETPATHPART", "SECRETQUERYSIG", "sig="):
        assert needle not in blob
    assert redacted_destination(url) in caplog.text  # scheme://host:port only


def test_audit_row_for_push_carries_no_secret(db, caplog):
    from utils import notify

    with RecordingServer(statuses=[401]) as srv:
        cfg = push_config(srv.url)
        notify._FINDINGS_PUSH_OK_SESSIONS.clear()
        notify.notify_scan_complete_sync(cfg, db, SESSION_NEW)
    from core.database import NotificationSendLog

    session = db._session_factory()
    try:
        rows = (
            session.query(NotificationSendLog)
            .filter(NotificationSendLog.trigger == "findings_push")
            .all()
        )
        assert len(rows) == 1
        row = rows[0]
        assert row.recipient == "siem" and row.success is False
        assert row.error_summary == "HTTP 401"
        assert TOKEN not in (row.error_summary or "")
    finally:
        session.close()


# --- SSRF / scheme / redirects ------------------------------------------------


def test_loopback_requires_explicit_private_opt_in(db):
    with RecordingServer() as srv:
        cfg = push_config(srv.url, allow_private_networks=False)
        res = push_findings_for_session(cfg, db, SESSION_NEW, sleep=no_sleep())
        assert srv.requests == []
    assert res.status == "failed"
    assert "SSRF guard" in res.detail
    assert "127.0.0.1" not in res.detail


def test_link_local_metadata_address_rejected_without_opt_in(db):
    cfg = push_config("https://169.254.169.254/latest", allow_private_networks=False)
    res = push_findings_for_session(cfg, db, SESSION_NEW, sleep=no_sleep())
    assert res.status == "failed" and "SSRF guard" in res.detail


@pytest.mark.parametrize(
    ("url", "match"),
    [
        ("http://siem.example.test/hook", "https"),
        ("ftp://siem.example.test/hook", "http"),
        ("https://user:pw@siem.example.test/hook", "credentials"),
        ("https://siem.example.test/hook#frag", "fragment"),
        ("https:///nohost", "host"),
        ("https://siem.example.test:notaport/", "port"),
    ],
)
def test_url_rules_enforced_at_config_load(url, match):
    with pytest.raises(ValueError, match=match):
        normalize_config(
            {
                "targets": [],
                "notifications": {
                    "enabled": True,
                    "findings_push": {"enabled": True, "url": url},
                },
            }
        )


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1:8088/x",
        "http://localhost:8088/x",
        "http://[::1]:8088/x",
        "https://siem.example.test/x",
    ],
)
def test_http_only_allowed_for_loopback(url):
    out = normalize_config(
        {
            "targets": [],
            "notifications": {"findings_push": {"enabled": True, "url": url}},
        }
    )
    assert out["notifications"]["findings_push"]["url"] == url


def test_hostname_url_dials_pinned_ip_and_keeps_host_header(db):
    with RecordingServer() as srv:
        url = f"http://localhost:{srv.port}/x"
        assert push_findings_for_session(
            push_config(url), db, SESSION_NEW, sleep=no_sleep()
        ).ok
        assert srv.requests[0]["headers"]["host"] == f"localhost:{srv.port}"


def test_redirects_are_not_followed(db):
    with RecordingServer() as target:
        with RecordingServer(
            statuses=[302], extra_headers={"Location": target.url}
        ) as hop:
            res = push_findings_for_session(
                push_config(hop.url), db, SESSION_NEW, sleep=no_sleep()
            )
            assert len(hop.requests) == 1
        assert target.requests == []
    assert res.status == "failed"
    assert "redirect not followed" in res.detail
    assert res.attempts == 1


@pytest.mark.parametrize(
    "bad",
    [
        {"token": "x"},
        {"authorization": "Bearer x"},
        {"password": "x"},
        {"api_key": "x"},
    ],
)
def test_literal_secret_in_config_is_refused(bad):
    with pytest.raises(ValueError, match="literal secret"):
        normalize_config(
            {
                "targets": [],
                "notifications": {
                    "findings_push": {
                        "enabled": True,
                        "url": "https://siem.example.test/x",
                        **bad,
                    }
                },
            }
        )


def test_auth_env_must_use_credential_prefix():
    with pytest.raises(ValueError, match="#1977"):
        normalize_config(
            {
                "targets": [],
                "notifications": {
                    "findings_push": {
                        "enabled": True,
                        "url": "https://siem.example.test/x",
                        "auth_env": "HOME",
                    }
                },
            }
        )


def test_unknown_key_and_bad_enums_rejected():
    base = {"enabled": True, "url": "https://siem.example.test/x"}
    for extra, match in (
        ({"colour": 1}, "unknown key"),
        ({"format": "xml"}, "format"),
        ({"adapter": "kafka"}, "adapter"),
        ({"findings_scope": "some"}, "findings_scope"),
        ({"auth_header": "Bad Header"}, "header name"),
        ({"adapter": "splunk_hec", "auth_header": "X-A"}, "fixed by adapter"),
        ({"hec_index": "a b"}, "unsupported characters"),
    ):
        with pytest.raises(ValueError, match=match):
            normalize_config(
                {
                    "targets": [],
                    "notifications": {"findings_push": {**base, **extra}},
                }
            )


def test_enabled_without_url_is_rejected():
    with pytest.raises(ValueError, match="url is required"):
        normalize_config(
            {"targets": [], "notifications": {"findings_push": {"enabled": True}}}
        )


def test_url_can_come_from_prefixed_env(monkeypatch):
    monkeypatch.setenv("API_SIEM_URL", "https://siem.example.test/ingest?sig=abc")
    out = normalize_config(
        {
            "targets": [],
            "notifications": {
                "findings_push": {"enabled": True, "url": "${API_SIEM_URL}"}
            },
        }
    )
    assert out["notifications"]["findings_push"]["url"].endswith("sig=abc")


# --- retries, timeouts, size limits --------------------------------------------


def test_retries_on_5xx_then_succeeds_with_backoff(db):
    sleeper = no_sleep()
    with RecordingServer(statuses=[503, 502, 200]) as srv:
        res = push_findings_for_session(
            push_config(srv.url), db, SESSION_NEW, sleep=sleeper
        )
        assert len(srv.requests) == 3
    assert res.ok and res.attempts == 3
    assert sleeper.calls == [0.5, 1.0]


def test_4xx_is_not_retried(db):
    with RecordingServer(statuses=[403]) as srv:
        res = push_findings_for_session(
            push_config(srv.url), db, SESSION_NEW, sleep=no_sleep()
        )
        assert len(srv.requests) == 1
    assert res.status == "failed" and res.detail == "HTTP 403" and res.attempts == 1


def test_429_is_retried(db):
    with RecordingServer(statuses=[429, 200]) as srv:
        res = push_findings_for_session(
            push_config(srv.url), db, SESSION_NEW, sleep=no_sleep()
        )
    assert res.ok and res.attempts == 2


def test_max_attempts_is_honoured(db):
    with RecordingServer(statuses=[500]) as srv:
        res = push_findings_for_session(
            push_config(srv.url, max_attempts=2), db, SESSION_NEW, sleep=no_sleep()
        )
        assert len(srv.requests) == 2
    assert res.status == "failed" and res.attempts == 2


def test_real_timeout_is_reported_and_retried(db):
    with RecordingServer(delay=2.5) as srv:
        res = push_findings_for_session(
            push_config(srv.url, timeout_seconds=1, max_attempts=2),
            db,
            SESSION_NEW,
            sleep=no_sleep(),
        )
    assert res.status == "failed"
    assert res.detail == "timeout"
    assert res.attempts == 2


def test_connection_refused_is_a_fixed_error_class(db):
    srv = RecordingServer()
    port = srv.port
    srv.httpd.server_close()  # nothing listens on this port any more
    res = push_findings_for_session(
        push_config(f"http://127.0.0.1:{port}/x", max_attempts=2),
        db,
        SESSION_NEW,
        sleep=no_sleep(),
    )
    assert res.status == "failed" and res.detail == "connection error"
    assert res.attempts == 2


def test_huge_response_body_is_read_with_a_cap(db):
    big = b"x" * (2 * 1024 * 1024)
    with RecordingServer(response_body=big) as srv:
        res = push_findings_for_session(
            push_config(srv.url), db, SESSION_NEW, sleep=no_sleep()
        )
    assert res.ok


def test_payload_is_trimmed_to_max_findings_and_flagged(tmp_path):
    path = str(tmp_path / "audit.db")
    mgr = LocalDBManager(path)
    try:
        mgr.create_session_record("big-1")
        mgr.set_current_session_id("big-1")
        for i in range(40):
            mgr.save_finding(
                "filesystem",
                target_name="share",
                path="/srv/data",
                file_name=f"f{i:03d}.csv",
                sensitivity_level="HIGH" if i % 2 else "LOW",
                pattern_detected="EMAIL",
            )
        mgr.finish_session("big-1")
        settings = push_settings(push_config("http://127.0.0.1:1/x", max_findings=10))
        body, included, truncated = build_push_body(settings, mgr, "big-1")
    finally:
        mgr.dispose()
    import json

    doc = json.loads(body)
    assert included == 10 and truncated is True
    assert doc["findings_truncated"] is True
    assert doc["findings_total_in_scope"] == 40
    # most sensitive are kept first
    assert {f["sensitivity"] for f in doc["findings"]} == {"HIGH"}


def test_payload_is_halved_until_it_fits_max_payload_bytes(tmp_path):
    path = str(tmp_path / "audit.db")
    mgr = LocalDBManager(path)
    try:
        mgr.create_session_record("big-2")
        mgr.set_current_session_id("big-2")
        for i in range(200):
            mgr.save_finding(
                "filesystem",
                target_name="share",
                path="/srv/data/some/long/path/segment",
                file_name=f"file_{i:04d}.csv",
                sensitivity_level="MEDIUM",
                pattern_detected="EMAIL",
            )
        mgr.finish_session("big-2")
        settings = push_settings(
            push_config("http://127.0.0.1:1/x", max_payload_bytes=6000)
        )
        body, included, truncated = build_push_body(settings, mgr, "big-2")
    finally:
        mgr.dispose()
    assert len(body) <= 6000
    assert truncated is True and 0 <= included < 200


def test_sarif_payload_respects_size_limit(tmp_path):
    path = str(tmp_path / "audit.db")
    seed_two_sessions(path)
    mgr = LocalDBManager(path)
    try:
        settings = push_settings(
            push_config(
                "http://127.0.0.1:1/x",
                format="sarif",
                findings_scope="all",
                max_payload_bytes=4096,
            )
        )
        body, _inc, _trunc = build_push_body(settings, mgr, SESSION_NEW)
    finally:
        mgr.dispose()
    assert len(body) <= 4096


# --- tier gate --------------------------------------------------------------


@pytest.mark.parametrize("tier", ["community", "std", "pro"])
def test_push_blocked_below_pro_plus(db, tier):
    reset_license_guard_for_tests()
    with RecordingServer() as srv:
        res = push_findings_for_session(
            push_config(srv.url, tier=tier), db, SESSION_NEW, sleep=no_sleep()
        )
        assert srv.requests == []
    assert res.status == "skipped" and res.detail == "feature tier blocked"


@pytest.mark.parametrize("tier", ["pro_plus", "enterprise", None])
def test_push_allowed_at_pro_plus_enterprise_and_open(db, tier):
    reset_license_guard_for_tests()
    with RecordingServer() as srv:
        res = push_findings_for_session(
            push_config(srv.url, tier=tier), db, SESSION_NEW, sleep=no_sleep()
        )
        assert len(srv.requests) == 1
    assert res.ok


def test_push_off_unless_both_switches_are_on(db):
    with RecordingServer() as srv:
        cfg = push_config(srv.url)
        cfg["notifications"]["enabled"] = False
        assert push_findings_for_session(cfg, db, SESSION_NEW).status == "skipped"
        cfg = push_config(srv.url, enabled=False)
        assert push_findings_for_session(cfg, db, SESSION_NEW).status == "skipped"
        assert srv.requests == []


# --- notify integration ---------------------------------------------------------


def test_notify_hook_pushes_once_and_dedupes(db):
    from utils import notify

    notify._FINDINGS_PUSH_OK_SESSIONS.clear()
    with RecordingServer() as srv:
        cfg = push_config(srv.url)
        notify.notify_scan_complete_sync(cfg, db, SESSION_NEW)
        notify.notify_scan_complete_sync(cfg, db, SESSION_NEW)
        assert len(srv.requests) == 1
    notify._FINDINGS_PUSH_OK_SESSIONS.clear()


def test_failed_push_does_not_block_the_human_brief(db, monkeypatch):
    from utils import notify

    notify._FINDINGS_PUSH_OK_SESSIONS.clear()
    sent: list[str] = []
    monkeypatch.setattr(
        notify,
        "send_all_operator_notifications",
        lambda n, text, **_k: sent.append(text) or [("generic", True, None)],
    )
    with RecordingServer(statuses=[500]) as srv:
        cfg = push_config(srv.url, max_attempts=1)
        cfg["notifications"]["operator"]["generic_webhook_url"] = "https://x.test/h"
        notify.notify_scan_complete_sync(cfg, db, SESSION_NEW)
        assert len(srv.requests) == 1
    assert len(sent) == 1


def test_push_runs_even_when_human_brief_filters_would_skip(db, monkeypatch):
    from utils import notify

    notify._FINDINGS_PUSH_OK_SESSIONS.clear()
    monkeypatch.setattr(
        notify, "send_all_operator_notifications", lambda *a, **k: pytest.fail("sent")
    )
    with RecordingServer() as srv:
        cfg = push_config(srv.url)
        cfg["notifications"]["on_scan_complete"] = False
        notify.notify_scan_complete_sync(cfg, db, SESSION_NEW)
        assert len(srv.requests) == 1
    notify._FINDINGS_PUSH_OK_SESSIONS.clear()


def test_background_returns_joinable_thread(db):
    from utils import notify

    notify._FINDINGS_PUSH_OK_SESSIONS.clear()
    with RecordingServer() as srv:
        thread = notify.notify_scan_complete_background(
            push_config(srv.url), db, SESSION_NEW
        )
        assert isinstance(thread, threading.Thread)
        thread.join(timeout=30)
        assert not thread.is_alive()
        assert len(srv.requests) == 1
    notify._FINDINGS_PUSH_OK_SESSIONS.clear()


# --- TLS fails closed ---------------------------------------------------------


def _self_signed(tmp_path):
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.x509.oid import NameOID
    import ipaddress

    key = ec.generate_private_key(ec.SECP256R1())
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "127.0.0.1")])
    now = datetime.now(timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(days=1))
        .not_valid_after(now + timedelta(days=1))
        .add_extension(
            x509.SubjectAlternativeName(
                [x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]
            ),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )
    cert_path = tmp_path / "cert.pem"
    key_path = tmp_path / "key.pem"
    cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    key_path.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    return cert_path, key_path


class _OkHandler(BaseHTTPRequestHandler):
    def do_POST(self):  # noqa: N802
        n = int(self.headers.get("Content-Length") or 0)
        self.rfile.read(n)
        self.send_response(200)
        self.send_header("Content-Length", "2")
        self.end_headers()
        self.wfile.write(b"{}")

    def log_message(self, *_a):
        return


def _https_server(tmp_path):
    cert, key = _self_signed(tmp_path)
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), _OkHandler)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(cert, key)
    httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd, t, cert


def test_untrusted_certificate_fails_closed_without_retry(db, tmp_path):
    httpd, t, _cert = _https_server(tmp_path)
    try:
        url = f"https://127.0.0.1:{httpd.server_address[1]}/x"
        res = push_findings_for_session(
            push_config(url), db, SESSION_NEW, sleep=no_sleep()
        )
    finally:
        httpd.shutdown()
        httpd.server_close()
        t.join(timeout=5)
    assert res.status == "failed"
    assert res.detail == "TLS error"
    assert res.attempts == 1


def test_trusted_certificate_over_pinned_ip_succeeds(db, tmp_path, monkeypatch):
    httpd, t, cert = _https_server(tmp_path)
    real = findings_push._tls_context

    def _ctx():
        ctx = real()
        ctx.load_verify_locations(cafile=str(cert))
        return ctx

    monkeypatch.setattr(findings_push, "_tls_context", _ctx)
    try:
        url = f"https://127.0.0.1:{httpd.server_address[1]}/x"
        res = push_findings_for_session(
            push_config(url), db, SESSION_NEW, sleep=no_sleep()
        )
    finally:
        httpd.shutdown()
        httpd.server_close()
        t.join(timeout=5)
    assert res.ok, res.detail


def test_tls_context_enforces_modern_protocol_and_verification():
    ctx = findings_push._tls_context()
    assert ctx.minimum_version >= ssl.TLSVersion.TLSv1_2
    assert ctx.verify_mode == ssl.CERT_REQUIRED
    assert ctx.check_hostname is True


def test_plain_http_requires_every_resolved_address_to_be_loopback(db, monkeypatch):
    import ipaddress

    monkeypatch.setattr(
        findings_push,
        "resolve_and_validate_outbound_url",
        lambda *_a, **_k: (None, [ipaddress.ip_address("10.0.0.5")]),
    )
    with RecordingServer() as srv:
        res = push_findings_for_session(
            push_config(f"http://localhost:{srv.port}/x"),
            db,
            SESSION_NEW,
            sleep=no_sleep(),
        )
        assert srv.requests == []
    assert res.status == "failed"
    assert "loopback" in res.detail
