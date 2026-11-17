"""Dev TDD tests for task 2206.1 (``sharepoint_online`` Graph reader, delegated mode).

Source: ``docs/desenho/2206.1.md``, section "Especificacao para o TDD do dev"
(``D2206.1-0a`` .. ``D2206.1-51``). Every test runs against the simulated Graph in
``tests/m365_fake_graph.py`` with ``url_guard._resolve_host_ips`` replaced, an injected
clock and ``sleep``, and closed httpx clients. No test reaches an external network; the
httpcore premise test talks to a local HTTP server on 127.0.0.1 only.
"""

from __future__ import annotations

import ast
import http.server
import io
import json
import logging
import os
import re
import stat
import sys
import threading
import time
import zipfile
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlsplit

import httpx
import pytest

from tests.m365_fake_graph import (
    DEFAULT_DOWNLOAD_HOST,
    DOWNLOAD_HOST_SUFFIXES,
    EVIL_HOST,
    GRAPH_HOST,
    LEAK_MARKERS,
    LOGIN_HOST,
    OTHER_DRIVE_ID,
    SCOPE,
    SECRET,
    TEST_CLIENT_ID,
    USER_CODE,
    VERIFICATION_URI,
    FakeClock,
    FakeDB,
    FakeGraph,
    File,
    Folder,
    RegexScanner,
    Req,
    TtyStream,
    install_fake_dns,
    make_target,
)

ROOT = "/DataBoar-Sintetico"
PREFIX = f"onedrive:{ROOT}"
CPF_TXT = "Cliente cadastrado: CPF 123.456.789-09, ficha 77.\n"
PLAIN_TXT = "Ata da reuniao: revisar o cronograma do galpao.\n"
MAIL_CSV = "nome,contato\nPessoa Teste,pessoa.teste@exemplo.com\n"
GUID_TENANT = "0a1b2c3d-0000-4000-8000-0000000000aa"
REPO = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO / "connectors" / "sharepoint_online_connector.py"

AUTH_REQUIRED_MSG = (
    "delegated sign-in needs an interactive CLI session (run the scan from a "
    "terminal); unattended scans use app-only mode (#2262)"
)


def mod() -> Any:
    import connectors.sharepoint_online_connector as m

    return m


# ----------------------------------------------------------------------------
# Harness
# ----------------------------------------------------------------------------


def tree(**inside: Any) -> dict[str, Any]:
    target = {"a.txt": CPF_TXT, "b.txt": PLAIN_TXT, "sub": {"c.csv": MAIL_CSV}}
    target.update(inside)
    return {
        "DataBoar-Sintetico": target,
        "DataBoar-Sintetico2": {"segredo.txt": CPF_TXT},
        "Documentos": {"pessoal.txt": CPF_TXT},
    }


EXPECTED = {f"{PREFIX}/a.txt", f"{PREFIX}/sub/c.csv"}


class Flag:
    """Mutable switch shared by a stream and a scanner."""

    def __init__(self, value: bool = True) -> None:
        self.value = value


class SwitchTty(io.StringIO):
    def __init__(self, flag: Flag) -> None:
        super().__init__()
        self.flag = flag

    def isatty(self) -> bool:
        return self.flag.value


class HookScanner(RegexScanner):
    """RegexScanner that runs a hook on every scanned file."""

    def __init__(self, hook: Callable[[str, Any], None]) -> None:
        self.hook = hook
        self.seen: list[tuple[str, Any]] = []

    def scan_file_content(self, content: str, file_path: Any) -> dict[str, Any] | None:
        self.seen.append((content, file_path))
        self.hook(content, file_path)
        return super().scan_file_content(content, file_path)


class Out:
    def __init__(self, conn: Any, db: FakeDB, clock: FakeClock, stream: Any) -> None:
        self.conn = conn
        self.db = db
        self.clock = clock
        self.stream = stream

    @property
    def prompt(self) -> str:
        return self.stream.getvalue()

    @property
    def paths(self) -> set[str]:
        return {f["path"] for f in self.db.findings}

    def details(self, reason: str) -> list[str]:
        return [d for _t, r, d in self.db.failures if r == reason]


def build(
    fake: FakeGraph,
    target: dict[str, Any] | None = None,
    *,
    interactive: bool | None = True,
    tty: bool = True,
    stream: Any = None,
    scanner: Any = None,
    transport: Any = None,
    clock: FakeClock | None = None,
    db: FakeDB | None = None,
    **kwargs: Any,
) -> Out:
    m = mod()
    db = db if db is not None else FakeDB()
    clock = clock if clock is not None else FakeClock()
    if stream is None:
        stream = TtyStream() if tty else io.StringIO()
    conn = m.SharePointOnlineConnector(
        target if target is not None else make_target(),
        scanner if scanner is not None else RegexScanner(),
        db,
        _transport=transport if transport is not None else fake.transport,
        _sleep=clock.sleep,
        _monotonic=clock.monotonic,
        _prompt_stream=stream,
        _interactive=interactive,
        **kwargs,
    )
    return Out(conn, db, clock, stream)


def scan(fake: FakeGraph, target: dict[str, Any] | None = None, **kw: Any) -> Out:
    out = build(fake, target, **kw)
    out.conn.run()
    return out


def record(fake: FakeGraph, request: httpx.Request) -> None:
    headers = {k.lower(): v for k, v in request.headers.items()}
    fake.requests.append(Req(request.method, str(request.url), headers))


def wrapped(
    fake: FakeGraph, intercept: Callable[[httpx.Request], httpx.Response | None]
) -> httpx.MockTransport:
    """Transport that lets ``intercept`` answer first, else delegates to the fake."""

    def handler(request: httpx.Request) -> httpx.Response:
        resp = intercept(request)
        if resp is None:
            return fake._handle(request)
        record(fake, request)
        return resp

    return httpx.MockTransport(handler)


def patched_json(
    fake: FakeGraph,
    match: Callable[[httpx.Request], bool],
    mutate: Callable[[dict[str, Any]], None],
) -> httpx.MockTransport:
    """Transport that edits the JSON body of the fake's answers to matching requests."""

    def handler(request: httpx.Request) -> httpx.Response:
        resp = fake._handle(request)
        if not match(request):
            return resp
        body = json.loads(resp.content)
        mutate(body)
        return httpx.Response(resp.status_code, json=body)

    return httpx.MockTransport(handler)


def raw_path(url: str) -> str:
    return urlsplit(url).path


def is_children(r: Any) -> bool:
    url = r.url if isinstance(r, Req) else str(r.url)
    return raw_path(url).endswith("/children")


def is_content(r: Any) -> bool:
    url = r.url if isinstance(r, Req) else str(r.url)
    return raw_path(url).endswith("/content")


def ids_in(fake: FakeGraph, ids: set[str]) -> list[str]:
    return [r.url for r in fake.requests if any(i in r.url for i in ids)]


@pytest.fixture
def make_fake(monkeypatch: pytest.MonkeyPatch):
    made: list[FakeGraph] = []

    def factory(t: dict[str, Any] | None = None, **kw: Any) -> FakeGraph:
        fake = FakeGraph(tree() if t is None else t, **kw)
        install_fake_dns(monkeypatch, fake)
        made.append(fake)
        return fake

    yield factory
    for fake in made:
        assert fake.violations == [], fake.violations


# ----------------------------------------------------------------------------
# Premises
# ----------------------------------------------------------------------------


def test_D2206_1_0a_api_client_does_not_follow_302_and_download_uses_second_client(
    make_fake, monkeypatch
):
    """D2206.1-0a: the API client sees the 302; the download host gets a second client."""
    fake = make_fake({"DataBoar-Sintetico": {"a.txt": CPF_TXT}})
    sent: list[tuple[int, str, bool, int]] = []
    real_send = httpx.Client.send

    def spy(self: httpx.Client, request: httpx.Request, **kw: Any) -> httpx.Response:
        resp = real_send(self, request, **kw)
        sent.append(
            (id(self), request.url.host, self.follow_redirects, resp.status_code)
        )
        return resp

    monkeypatch.setattr(httpx.Client, "send", spy)
    out = scan(fake)

    assert out.paths == {f"{PREFIX}/a.txt"}
    content = [s for s, r in zip(sent, fake.requests) if is_content(r)]
    assert content and all(code == 302 for _c, _h, _f, code in content)
    graph_clients = {c for c, h, _f, _s in sent if h == GRAPH_HOST}
    download_clients = {c for c, h, _f, _s in sent if h == DEFAULT_DOWNLOAD_HOST}
    assert download_clients and not (graph_clients & download_clients)
    assert all(follow is False for _c, _h, follow, _s in sent)
    assert all("authorization" not in r.headers for r in fake.download_requests())


def test_D2206_1_0b_httpx_log_filter_hides_download_path_and_query(caplog):
    """D2206.1-0b: with the filter installed, no record carries the download path/query."""
    m = mod()
    m.install_download_log_filter(list(DOWNLOAD_HOST_SUFFIXES))
    caplog.set_level(logging.DEBUG)

    def ok(_req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"x")

    with httpx.Client(transport=httpx.MockTransport(ok)) as client:
        client.get(f"https://{DEFAULT_DOWNLOAD_HOST}/{SECRET}path?tempauth={SECRET}q")
        client.get(f"https://{GRAPH_HOST}/v1.0/me/drive/items/X/children")

    assert SECRET not in caplog.text
    httpx_records = [r.getMessage() for r in caplog.records if r.name == "httpx"]
    assert any(
        f"https://{DEFAULT_DOWNLOAD_HOST}/<redacted>" in msg for msg in httpx_records
    )
    # Other hosts are untouched.
    assert any(
        f"https://{GRAPH_HOST}/v1.0/me/drive/items/X/children" in msg
        for msg in httpx_records
    )


class _QuietHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 - stdlib name
        body = b"ok"
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args: Any) -> None:
        return


def test_D2206_1_0b_httpcore_debug_does_not_log_path_or_query(caplog):
    """D2206.1-0b (risk note): httpcore DEBUG records do not carry the URL path/query.

    Real httpcore stack against a local server on 127.0.0.1 (the MockTransport bypasses
    httpcore, so this is the only way to observe what it logs).
    """
    server = http.server.HTTPServer(("127.0.0.1", 0), _QuietHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        caplog.set_level(logging.DEBUG)
        port = server.server_address[1]
        with httpx.Client(trust_env=False) as client:
            resp = client.get(
                f"http://127.0.0.1:{port}/{SECRET}path?tempauth={SECRET}q"
            )
            assert resp.status_code == 200
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
    core_records = [r for r in caplog.records if r.name.startswith("httpcore")]
    assert core_records, "httpcore emitted no DEBUG record; premise not observed"
    assert all(SECRET not in r.getMessage() for r in core_records)


# ----------------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------------


def _assert_config_error(fake: FakeGraph, out: Out) -> None:
    assert out.db.reasons() == ["config_error"], out.db.failures
    assert fake.requests == []
    assert out.db.findings == []


@pytest.mark.parametrize("root", [None, "", "/", "///"])
def test_D2206_1_1_root_folder_missing_empty_or_drive_root_is_refused(make_fake, root):
    """D2206.1-1: root_folder absent, empty, / or ///."""
    fake = make_fake()
    target = make_target()
    if root is None:
        del target["root_folder"]
    else:
        target["root_folder"] = root
    _assert_config_error(fake, scan(fake, target))


@pytest.mark.parametrize(
    "root",
    [
        "/a/../b",
        "/a/./b",
        "/a//b",
        "/a\\b",
        "/a:b",
        "/a*b",
        "/a?b",
        "/a|b",
        "/a<b",
        "/a>b",
        "/a\x07b",
        "relative/path",
    ],
)
def test_D2206_1_2_root_folder_with_forbidden_segments_is_refused(make_fake, root):
    """D2206.1-2: .., ., // in the middle, \\, :, *, ?, |, <, >, control char."""
    fake = make_fake()
    _assert_config_error(fake, scan(fake, make_target(root_folder=root)))


@pytest.mark.parametrize(
    "overrides",
    [
        {"root_folder": ROOT, "root_folder_id": "ITEM0001"},
        {"root_folder": None, "root_folder_id": "a/b"},
        {"root_folder": None, "root_folder_id": "a?b"},
        {"root_folder": None, "root_folder_id": "a#b"},
        {"root_folder": None, "root_folder_id": "a%2Fb"},
        {"root_folder": None, "root_folder_id": ".."},
        {"root_folder": None, "root_folder_id": "."},
    ],
)
def test_D2206_1_3_root_folder_id_rules(make_fake, overrides):
    """D2206.1-3: both keys together, or root_folder_id with /, ?, #, % or equal to .."""
    fake = make_fake()
    target = make_target()
    for key, value in overrides.items():
        if value is None:
            target.pop(key, None)
        else:
            target[key] = value
    _assert_config_error(fake, scan(fake, target))


@pytest.mark.parametrize("tenant", ["evil.example", "consumers/x", "../common", ""])
def test_D2206_1_4_tenant_outside_the_allowed_set_is_refused(make_fake, tenant):
    """D2206.1-4 (negative): tenant is never interpolated unless allowed."""
    fake = make_fake()
    target = make_target()
    target["auth"] = {**target["auth"], "tenant": tenant}
    _assert_config_error(fake, scan(fake, target))


@pytest.mark.parametrize(
    "tenant", ["consumers", "organizations", "common", GUID_TENANT]
)
def test_D2206_1_4_allowed_tenant_is_used_verbatim_in_the_login_url(make_fake, tenant):
    """D2206.1-4 (positive): the login URL uses exactly the configured tenant."""
    fake = make_fake(device_script=["declined"])
    target = make_target()
    target["auth"] = {**target["auth"], "tenant": tenant}
    scan(fake, target)
    login = fake.login_requests()
    assert login
    assert all(raw_path(r.url).startswith(f"/{tenant}/oauth2/v2.0/") for r in login)


def test_D2206_1_5_auth_mode_and_drive_are_reserved_for_2262(make_fake):
    """D2206.1-5: app_only and drive != me cite #2262; any other mode is refused."""
    for auth_mode, drive, cites in (
        ("app_only", "me", True),
        ("outra", "me", False),
        ("delegated", "outro", True),
    ):
        fake = make_fake()
        target = make_target(drive=drive)
        target["auth"] = {**target["auth"], "mode": auth_mode}
        out = scan(fake, target)
        _assert_config_error(fake, out)
        if cites:
            assert "#2262" in out.details("config_error")[0]


@pytest.mark.parametrize("client_id", [None, "", f"{SECRET}not-a-guid", "1234"])
def test_D2206_1_6_client_id_missing_or_not_a_guid(make_fake, client_id):
    """D2206.1-6: config_error citing the key, never the value."""
    fake = make_fake()
    target = make_target()
    auth = dict(target["auth"])
    if client_id is None:
        auth.pop("client_id")
    else:
        auth["client_id"] = client_id
    target["auth"] = auth
    out = scan(fake, target)
    _assert_config_error(fake, out)
    detail = out.details("config_error")[0]
    assert "client_id" in detail
    if client_id:
        assert client_id not in detail


# ----------------------------------------------------------------------------
# Loader and credential gate
# ----------------------------------------------------------------------------


def _cfg(auth: dict[str, Any], **target_extra: Any) -> dict[str, Any]:
    return {
        "targets": [
            {
                "name": "onedrive-sintetico",
                "type": "sharepoint_online",
                "auth": auth,
                "root_folder": ROOT,
                **target_extra,
            }
        ],
        "api": {},
        "report": {"output_dir": "."},
    }


def test_D2206_1_7_client_id_is_read_from_the_yaml_only(make_fake, monkeypatch):
    """D2206.1-7 (revised 2026-11-17, operator rule C on #2261).

    The client id is not a secret: it stays in the YAML. ``client_id_from_env`` was
    removed, so the loader no longer resolves it and the reader then fails closed on
    the missing ``auth.client_id``.
    """
    from config.loader import normalize_config

    monkeypatch.setenv("M365_CLIENT_ID", TEST_CLIENT_ID)
    auth = {k: v for k, v in make_target()["auth"].items() if k != "client_id"}
    out = normalize_config(_cfg({**auth, "client_id_from_env": "M365_CLIENT_ID"}))
    target = out["targets"][0]
    assert "client_id" not in target["auth"]

    fake = make_fake()
    full = make_target()
    full["auth"] = target["auth"]
    result = scan(fake, full)
    _assert_config_error(fake, result)
    assert "auth.client_id" in result.details("config_error")[0]


def test_D2206_1_8_strict_mode_checks_the_yaml_hosts_without_a_secret(monkeypatch):
    """D2206.1-8 (revised twice on 2026-11-17: operator rule C, then the security
    finding on ca69f2aa).

    Delegated mode has no env secret, but the bearer token still goes to the YAML
    hosts, so the #2103 operator list approves them: with both hosts listed the
    target loads; with only the login host it is refused.
    """
    from config.loader import normalize_config

    monkeypatch.setenv("DATA_BOAR_CREDENTIAL_STRICT", "1")
    target = make_target()
    config = {"targets": [target], "api": {}, "report": {"output_dir": "."}}
    monkeypatch.setenv(
        "DATA_BOAR_CREDENTIAL_ALLOWED_HOSTS", f"{LOGIN_HOST},{GRAPH_HOST}"
    )
    out = normalize_config(config)
    assert out["targets"][0]["auth"]["client_id"] == TEST_CLIENT_ID

    monkeypatch.setenv("DATA_BOAR_CREDENTIAL_ALLOWED_HOSTS", LOGIN_HOST)
    with pytest.raises(ValueError):
        normalize_config(
            {"targets": [make_target()], "api": {}, "report": {"output_dir": "."}}
        )


# ----------------------------------------------------------------------------
# Registry and tier
# ----------------------------------------------------------------------------


@pytest.fixture
def clean_guard():
    from core.licensing.guard import reset_license_guard_for_tests

    reset_license_guard_for_tests()
    yield reset_license_guard_for_tests
    reset_license_guard_for_tests()
    os.environ.pop("DATA_BOAR_LICENSE_PUBLIC_KEY_PEM", None)


def test_D2206_1_9_tier_is_enterprise_fail_closed(tmp_path, clean_guard):
    """D2206.1-9: feature name, Enterprise in the map, Pro blocked, Enterprise/open allowed."""
    from core.connector_registry import (
        require_connector_allowed,
        tier_feature_for_target,
    )
    from core.licensing.errors import FeatureTierBlockedError
    from core.licensing.tier_features import FEATURE_TIER_MAP, Tier
    from tests.test_connector_tier_gating import _signed_license

    target = {"type": "sharepoint_online"}
    assert tier_feature_for_target(target) == "connector_sharepoint_online"
    assert FEATURE_TIER_MAP["connector_sharepoint_online"] == Tier.ENTERPRISE

    clean_guard()
    with pytest.raises(FeatureTierBlockedError):
        require_connector_allowed(_signed_license(tmp_path, "pro"), target)
    clean_guard()
    require_connector_allowed(_signed_license(tmp_path, "enterprise"), target)
    clean_guard()
    require_connector_allowed({"licensing": {"mode": "open"}}, target)


def test_D2206_1_10_registry_and_engine_instantiation(tmp_path, monkeypatch):
    """D2206.1-10: resolves to the new class; the engine passes the file-connector kwargs."""
    import core.engine  # noqa: F401 - registers the connector modules
    from core import connector_registry as reg

    resolved = reg.connector_for_target({"type": "sharepoint_online"})
    assert resolved is not None
    assert resolved[0] is mod().SharePointOnlineConnector

    seen: dict[str, Any] = {}

    class Spy:
        def __init__(self, target: Any, scanner: Any, db: Any, **kw: Any) -> None:
            seen.update(kw)

        def run(self) -> None:
            seen["ran"] = True

    monkeypatch.setitem(reg._REGISTRY, "sharepoint_online", (Spy, ["name"]))
    from core.engine import AuditEngine

    cfg = {
        "licensing": {"mode": "open"},
        "sqlite_path": str(tmp_path / "audit.db"),
        "targets": [],
    }
    engine = AuditEngine(cfg, db_path=str(tmp_path / "audit.db"))
    try:
        engine._run_target({"type": "sharepoint_online", "name": "x"})
    finally:
        engine.db_manager.dispose()
    assert seen.pop("ran") is True
    assert set(seen) == {
        "extensions",
        "scan_sqlite_as_db",
        "sample_limit",
        "file_sample_max_chars",
        "file_passwords",
    }


def test_D2206_1_11_on_prem_sharepoint_still_resolves_to_its_own_class(monkeypatch):
    """D2206.1-11: type sharepoint keeps resolving to the on-prem connector."""
    import core.engine  # noqa: F401
    from core import connector_registry as reg

    online = reg.connector_for_target({"type": "sharepoint_online"})
    assert online is not None
    on_prem = reg.connector_for_target({"type": "sharepoint"})
    if on_prem is None:  # "shares" extra absent: register a stand-in on-prem class

        class OnPrem:
            pass

        monkeypatch.setitem(reg._REGISTRY, "sharepoint", (OnPrem, ["name"]))
        on_prem = reg.connector_for_target({"type": "sharepoint"})
        assert on_prem is not None and on_prem[0] is OnPrem
    assert on_prem[0] is not online[0]
    assert on_prem[0].__name__ != "SharePointOnlineConnector"


# ----------------------------------------------------------------------------
# Device code
# ----------------------------------------------------------------------------


def test_D2206_1_12_pending_pending_ok(make_fake):
    """D2206.1-12: interval honoured, prompt, form fields, no secret, exact scope."""
    fake = make_fake(device_script=["pending", "pending", "ok"], device_interval=5)
    out = scan(fake)

    assert out.clock.sleeps[:2] == [5, 5]
    assert USER_CODE in out.prompt and VERIFICATION_URI in out.prompt
    assert f"{SECRET}message" not in out.prompt
    assert fake.device_requests[0]["scope"] == SCOPE
    assert fake.device_requests[0]["client_id"] == TEST_CLIENT_ID
    polls = fake.token_requests
    assert len(polls) == 3
    for form in polls:
        assert form["grant_type"] == "urn:ietf:params:oauth:grant-type:device_code"
        assert form["client_id"] == TEST_CLIENT_ID
        assert form["device_code"].startswith(f"{SECRET}DEVCODE-")
    for form in fake.device_requests + fake.token_requests:
        assert "client_secret" not in form
    assert out.paths == EXPECTED


def test_D2206_1_13_slow_down_adds_five_seconds(make_fake):
    """D2206.1-13: pending, slow_down, ok -> sleeps [5, 10]."""
    fake = make_fake(device_script=["pending", "slow_down", "ok"], device_interval=5)
    out = scan(fake)
    assert out.clock.sleeps[:2] == [5, 10]
    assert out.paths == EXPECTED


def test_D2206_1_14_declined(make_fake):
    """D2206.1-14: declined -> auth_failed, no Graph request."""
    fake = make_fake(device_script=["declined"])
    out = scan(fake)
    assert out.details("auth_failed") == ["Microsoft sign-in was declined"]
    assert fake.graph_requests() == []


def test_D2206_1_15_expired(make_fake):
    """D2206.1-15: expired -> auth_failed, no Graph request."""
    fake = make_fake(device_script=["expired"])
    out = scan(fake)
    assert out.details("auth_failed") == ["Microsoft sign-in code expired"]
    assert fake.graph_requests() == []


def test_D2206_1_15_bad_verification_code(make_fake):
    """D2206.1-15 (table, section 4): bad_verification_code stops the sign-in."""
    fake = make_fake(device_script=["bad_code"])
    out = scan(fake)
    assert out.details("auth_failed") == ["device code was not recognised"]
    assert fake.graph_requests() == []


def test_D2206_1_16_local_deadline_is_never_passed(make_fake):
    """D2206.1-16: pending forever, expires_in 60, interval 5 -> at most 12 polls."""
    fake = make_fake(device_script=["pending"], device_expires_in=60, device_interval=5)
    clock = FakeClock()
    start = clock.now
    poll_times: list[float] = []

    def intercept(request: httpx.Request) -> None:
        if request.url.path.endswith("/token"):
            poll_times.append(clock.now)
        return None

    out = scan(fake, transport=wrapped(fake, intercept), clock=clock)
    assert 1 <= len(poll_times) <= 12
    assert all(t < start + 60 for t in poll_times)
    assert out.details("auth_failed") == ["Microsoft sign-in code expired"]
    assert fake.graph_requests() == []


def test_D2206_1_17_oauth_error_keeps_codes_drops_description(make_fake):
    """D2206.1-17: invalid_client + AADSTS7000218, never error_description."""
    fake = make_fake(device_script=["invalid_client"])
    out = scan(fake)
    detail = out.details("auth_failed")[0]
    assert "invalid_client" in detail and "AADSTS7000218" in detail
    assert SECRET not in detail


@pytest.mark.parametrize(("interactive", "tty"), [(False, True), (True, False)])
def test_D2206_1_18_no_interactive_session_fails_before_login(
    make_fake, interactive, tty
):
    """D2206.1-18: auth_required with the fixed message, no login request, no sleep."""
    fake = make_fake()
    out = scan(fake, interactive=interactive, tty=tty)
    assert out.db.failures == [
        ("onedrive-sintetico", "auth_required", AUTH_REQUIRED_MSG)
    ]
    assert fake.requests == []
    assert out.clock.sleeps == []


def test_D2206_1_18_process_state_is_off_until_enabled(make_fake, monkeypatch):
    """D2206.1-18: with _interactive=None the process opt-in decides (off by default)."""
    m = mod()
    monkeypatch.setattr(m, "_interactive_enabled", False)
    fake = make_fake()
    out = scan(fake, interactive=None)
    assert out.db.reasons() == ["auth_required"]
    assert fake.requests == []

    m.enable_interactive_sign_in()
    fake2 = make_fake()
    out2 = scan(fake2, interactive=None)
    assert out2.paths == EXPECTED


def test_D2206_1_19_devicecode_5xx_or_network_error_is_unreachable(make_fake):
    """D2206.1-19: 500 three times, or ConnectError -> unreachable, nothing escapes."""
    fake = make_fake()

    def five_hundred(request: httpx.Request) -> httpx.Response | None:
        if request.url.path.endswith("/devicecode"):
            return httpx.Response(500, json={"error": "server_error"})
        return None

    out = scan(fake, transport=wrapped(fake, five_hundred))
    assert out.db.reasons() == ["unreachable"]
    assert len(fake.login_requests()) == 3
    assert fake.graph_requests() == []

    fake2 = make_fake()

    def boom(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError(f"cannot reach {request.url}", request=request)

    out2 = scan(fake2, transport=httpx.MockTransport(boom))
    assert out2.db.failures == [
        (
            "onedrive-sintetico",
            "unreachable",
            "network error contacting Microsoft login (ConnectError)",
        )
    ]


def test_D2206_1_20_parallel_targets_sign_in_one_at_a_time(make_fake):
    """D2206.1-20: two interactive connectors in threads never overlap device codes."""
    lock = threading.Lock()
    state = {"in_flight": 0, "max": 0}
    fakes = [make_fake(device_script=["pending", "ok"]) for _ in range(2)]
    shared = TtyStream()

    def transport_for(fake: FakeGraph) -> httpx.MockTransport:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path.endswith("/devicecode"):
                with lock:
                    state["in_flight"] += 1
                    state["max"] = max(state["max"], state["in_flight"])
            resp = fake._handle(request)
            if request.url.path.endswith("/token") and resp.status_code == 200:
                with lock:
                    state["in_flight"] -= 1
            return resp

        return httpx.MockTransport(handler)

    class SlowClock(FakeClock):
        def sleep(self, seconds: float) -> None:
            super().sleep(seconds)
            time.sleep(0.01)  # yield to the other thread

    outs: list[Out] = []
    errors: list[BaseException] = []

    def worker(fake: FakeGraph) -> None:
        try:
            out = build(
                fake,
                stream=shared,
                transport=transport_for(fake),
                clock=SlowClock(),
            )
            out.conn.run()
            outs.append(out)
        except BaseException as exc:  # noqa: BLE001 - reported by the assertion below
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(f,)) for f in fakes]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)
    assert errors == []
    assert len(outs) == 2
    assert state["max"] == 1
    lines = [ln for ln in shared.getvalue().splitlines() if ln.strip()]
    assert len(lines) == 2
    assert all(ln.startswith("To sign in to Microsoft for target") for ln in lines)
    assert all(o.paths == EXPECTED for o in outs)


def test_D2206_1_21_keyboard_interrupt_propagates(make_fake):
    """D2206.1-21: KeyboardInterrupt raised by sleep during polling leaves run()."""
    fake = make_fake(device_script=["pending", "ok"])

    class InterruptClock(FakeClock):
        def sleep(self, seconds: float) -> None:
            raise KeyboardInterrupt

    out = build(fake, clock=InterruptClock())
    with pytest.raises(KeyboardInterrupt):
        out.conn.run()


# ----------------------------------------------------------------------------
# Token and refresh
# ----------------------------------------------------------------------------


def three_files() -> dict[str, Any]:
    return {
        "DataBoar-Sintetico": {"a.txt": CPF_TXT, "b.txt": CPF_TXT, "c.txt": CPF_TXT}
    }


def ticking_scanner(clock: FakeClock, step: float) -> HookScanner:
    def hook(_content: str, _path: Any) -> None:
        clock.now += step

    return HookScanner(hook)


def refresh_forms(fake: FakeGraph) -> list[dict[str, str]]:
    return [f for f in fake.token_requests if f.get("grant_type") == "refresh_token"]


def test_D2206_1_22_proactive_refresh_rotates_the_refresh_token(make_fake):
    """D2206.1-22: < 300 s left -> refresh first; the second refresh sends RT-2."""
    fake = make_fake(three_files(), token_expires_in=600)
    clock = FakeClock()
    out = scan(fake, clock=clock, scanner=ticking_scanner(clock, 400))
    forms = refresh_forms(fake)
    assert [f["refresh_token"] for f in forms[:2]] == [
        f"{SECRET}RT-1",
        f"{SECRET}RT-2",
    ]
    for form in forms:
        assert form["client_id"] == TEST_CLIENT_ID
        assert form["scope"] == SCOPE
        assert "client_secret" not in form
    assert len(out.db.findings) == 3


def test_D2206_1_23_one_401_refreshes_and_retries(make_fake):
    """D2206.1-23 (a): a 401 on a listing -> one refresh, one retry, the scan goes on."""
    fake = make_fake()
    fake.expire_access_after(1)  # root resolution ok, the listing gets 401
    out = scan(fake)
    assert fake.refresh_count == 1
    assert out.paths == EXPECTED
    assert out.db.failures == []


def test_D2206_1_23_second_401_ends_the_target(make_fake):
    """D2206.1-23 (b): 401 again on the retry -> auth_failed and the target stops."""
    fake = make_fake()

    def always_401(request: httpx.Request) -> httpx.Response | None:
        if request.url.host == GRAPH_HOST and request.url.path.endswith("/children"):
            return httpx.Response(401, json={"error": {"code": "Invalid"}})
        return None

    out = scan(fake, transport=wrapped(fake, always_401))
    assert out.details("auth_failed") == ["Microsoft Graph rejected the access token"]
    assert len([r for r in fake.graph_requests() if is_children(r)]) == 2
    assert out.db.findings == []
    assert len(refresh_forms(fake)) == 1


def test_D2206_1_24_invalid_grant_interactive_signs_in_again(make_fake):
    """D2206.1-24 (a): refresh invalid_grant + interactive -> a new device code."""
    fake = make_fake()
    fake.refresh_fails = "invalid_grant"
    fake.expire_access_after(1)
    out = scan(fake)
    assert len(fake.device_requests) == 2
    assert out.paths == EXPECTED
    assert out.db.failures == []


def test_D2206_1_24_invalid_grant_without_terminal_fails(make_fake):
    """D2206.1-24 (b): refresh invalid_grant, terminal gone -> auth_failed."""
    fake = make_fake(three_files())
    fake.refresh_fails = "invalid_grant"
    fake.expire_access_after(3)  # resolve, list, a/content ok; b/content gets 401
    flag = Flag(True)

    def hook(_c: str, _p: Any) -> None:
        flag.value = False

    out = scan(fake, stream=SwitchTty(flag), scanner=HookScanner(hook))
    assert len(fake.device_requests) == 1
    assert out.db.reasons() == ["auth_failed"]
    assert len(out.db.findings) == 1


def test_D2206_1_25_token_without_refresh_token_runs_until_expiry(make_fake):
    """D2206.1-25: no refresh_token -> scan until expiry, then the D-24 rule."""
    fake = make_fake(three_files(), token_expires_in=600)
    fake.omit_refresh_token = True
    clock = FakeClock()
    out = scan(fake, clock=clock, scanner=ticking_scanner(clock, 400))
    assert refresh_forms(fake) == []
    assert len(fake.device_requests) == 2
    assert len(out.db.findings) == 3

    fake2 = make_fake(three_files(), token_expires_in=600)
    fake2.omit_refresh_token = True
    clock2 = FakeClock()
    flag = Flag(True)

    def hook(_c: str, _p: Any) -> None:
        clock2.now += 400
        flag.value = False

    out2 = scan(fake2, clock=clock2, stream=SwitchTty(flag), scanner=HookScanner(hook))
    assert len(fake2.device_requests) == 1
    assert "auth_failed" in out2.db.reasons()


# ----------------------------------------------------------------------------
# Scope and traversal
# ----------------------------------------------------------------------------


def test_D2206_1_26_root_resolution_encoding_and_root_checks(make_fake):
    """D2206.1-26: percent-encoding per segment; non-folder or drive root refused; 404."""
    fake = make_fake({"A b": {"c#d": {"a.txt": CPF_TXT}}})
    out = scan(fake, make_target(root_folder="/A b/c#d"))
    first_graph = fake.graph_requests()[0]
    assert raw_path(first_graph.url) == "/v1.0/me/drive/root:/A%20b/c%23d"
    assert out.paths == {"onedrive:/A b/c#d/a.txt"}

    fake2 = make_fake({"arquivo.txt": CPF_TXT})
    out2 = scan(fake2, make_target(root_folder="/arquivo.txt"))
    assert out2.db.reasons() == ["config_error"]
    assert not any(is_children(r) for r in fake2.requests)

    fake3 = make_fake()
    target = make_target(root_folder_id="ROOT0000")
    del target["root_folder"]
    out3 = scan(fake3, target)
    assert out3.db.reasons() == ["config_error"]
    assert not any(is_children(r) for r in fake3.requests)

    fake4 = make_fake()
    out4 = scan(fake4, make_target(root_folder="/nao-existe"))
    assert out4.db.reasons() == ["not_found"]


def test_D2206_1_27_root_must_be_in_the_user_drive(make_fake):
    """D2206.1-27: remoteItem root or root without driveId refused; driveId compared casefolded."""
    fake = make_fake({"atalho": Folder({"x.txt": CPF_TXT}, remote=True)})
    target = make_target(root_folder_id=fake.id_of("/atalho"))
    del target["root_folder"]
    out = scan(fake, target)
    assert out.db.reasons() == ["config_error"]
    assert not any(is_children(r) for r in fake.requests)

    fake2 = make_fake()
    transport = patched_json(
        fake2,
        lambda r: r.url.host == GRAPH_HOST and "/root:" in r.url.path,
        lambda body: body.get("parentReference", {}).pop("driveId", None),
    )
    out2 = scan(fake2, transport=transport)
    assert out2.db.reasons() == ["config_error"]
    assert not any(is_children(r) for r in fake2.requests)

    fake3 = make_fake(
        {"DataBoar-Sintetico": {"a.txt": File(CPF_TXT, drive_id="drive-fake-1")}}
    )
    out3 = scan(fake3)
    assert out3.paths == {f"{PREFIX}/a.txt"}


def test_D2206_1_28_after_resolution_only_item_ids_are_used(make_fake):
    """D2206.1-28: listings are /v1.0/me/drive/items/{id}/children; no path, search, delta."""
    fake = make_fake()
    scan(fake)
    graph = fake.graph_requests()
    assert "/root:" in raw_path(graph[0].url)
    for r in graph[1:]:
        path = raw_path(r.url)
        assert re.fullmatch(r"/v1\.0/me/drive/items/[^/]+/(children|content)", path)
        assert "root:" not in path and "/root/children" not in path
        assert "search" not in r.url and "delta" not in r.url
    assert any(is_children(r) for r in graph)


def test_D2206_1_29_ignored_items_are_counted_and_reported(make_fake, caplog):
    """D2206.1-29: remote, package, malware, deleted, other drive: never opened, counted."""
    caplog.set_level(logging.INFO)
    inside = {
        "remoto": Folder({"x.txt": CPF_TXT}, remote=True),
        "pacote": Folder({"y.txt": CPF_TXT}, package=True),
        "virus.txt": File(CPF_TXT, malware=True),
        "apagado.txt": File(CPF_TXT, deleted=True),
        "outro.txt": File(CPF_TXT, drive_id=OTHER_DRIVE_ID),
    }
    fake = make_fake(tree(**inside))
    out = scan(fake)
    ignored = set()
    for name in inside:
        ignored |= fake.ids_under(f"{ROOT}/{name}")
    assert ids_in(fake, ignored) == []
    assert out.paths == EXPECTED
    assert out.details("skipped") == [
        "5 items skipped: remote=1, package=1, other_drive=1, malware=1, deleted=1, no_facet=0"
    ]
    summary = [r.getMessage() for r in caplog.records if "skipped" in r.getMessage()]
    assert summary
    assert not any(name in "".join(summary) for name in inside)

    fake2 = make_fake({"DataBoar-Sintetico": {"so-atalho": File(CPF_TXT, remote=True)}})
    out2 = scan(fake2)
    assert out2.db.findings == []
    assert out2.details("skipped") == [
        "1 items skipped: remote=1, package=0, other_drive=0, malware=0, deleted=0, no_facet=0"
    ]


def test_D2206_1_30_cycles_and_max_depth(make_fake):
    """D2206.1-30: a repeated folder id is listed once; nothing below max_depth is listed."""
    deep = {"DataBoar-Sintetico": {"l1": {"l2": {"l3": {"z.txt": CPF_TXT}}}}}
    fake = make_fake(deep)
    root_id = fake.id_of(ROOT)
    l1_id = fake.id_of(f"{ROOT}/l1")

    def add_cycle(body: dict[str, Any]) -> None:
        body["value"].append(
            {
                "id": root_id,
                "name": "volta",
                "folder": {"childCount": 1},
                "parentReference": {"driveId": fake.drive_id, "id": root_id},
            }
        )

    transport = patched_json(
        fake,
        lambda r: (
            r.url.host == GRAPH_HOST and f"/items/{root_id}/children" in r.url.path
        ),
        add_cycle,
    )
    scan(fake, make_target(max_depth=2), transport=transport)
    listed = [raw_path(r.url) for r in fake.graph_requests() if is_children(r)]
    assert listed.count(f"/v1.0/me/drive/items/{root_id}/children") == 1
    assert listed.count(f"/v1.0/me/drive/items/{l1_id}/children") == 1
    l2_id = fake.id_of(f"{ROOT}/l1/l2")
    assert not any(l2_id in p for p in listed)


def test_D2206_1_31_sibling_with_same_prefix_is_never_touched(make_fake):
    """D2206.1-31: /Pasta never reaches /Pasta2."""
    fake = make_fake(
        {"Pasta": {"a.txt": PLAIN_TXT}, "Pasta2": {"segredo.txt": CPF_TXT}}
    )
    out = scan(fake, make_target(root_folder="/Pasta"))
    assert ids_in(fake, fake.ids_under("/Pasta2")) == []
    assert out.db.findings == []


# ----------------------------------------------------------------------------
# Paging and limits
# ----------------------------------------------------------------------------


def test_D2206_1_32_three_pages_all_authorized(make_fake):
    """D2206.1-32: 450 children, page of 200 -> three pages with Authorization."""
    many = {f"p{i:03d}.txt": CPF_TXT for i in range(450)}
    fake = make_fake({"DataBoar-Sintetico": many}, page_size=200)
    out = scan(fake)
    pages = [r for r in fake.graph_requests() if is_children(r)]
    assert len(pages) == 3
    assert all(r.headers.get("authorization") for r in pages)
    assert len(out.db.findings) == 450


@pytest.mark.parametrize(
    "link",
    [
        f"https://{EVIL_HOST}/v1.0/me/drive/items/X/children",
        f"http://{GRAPH_HOST}/v1.0/me/drive/items/X/children",
        f"https://{GRAPH_HOST}:8443/v1.0/me/drive/items/X/children",
        f"https://user:pw@{GRAPH_HOST}/v1.0/me/drive/items/X/children",
        f"https://{GRAPH_HOST}/beta/me/drive/items/X/children",
    ],
)
def test_D2206_1_33_unexpected_next_link_is_refused(make_fake, link):
    """D2206.1-33: wrong host, scheme, port, userinfo or prefix: no request at all."""
    fake = make_fake()
    fake.next_link_override = link
    out = scan(fake)
    assert not any(r.url == link or "X/children" in r.url for r in fake.requests)
    assert all(
        r.host == GRAPH_HOST
        for r in fake.requests
        if "authorization" in r.headers and r.host != LOGIN_HOST
    )
    assert "scope_violation" in out.db.reasons()
    assert any(
        "unexpected @odata.nextLink rejected" in d
        for d in out.details("scope_violation")
    )


def test_D2206_1_34_repeated_next_link_stops_the_listing(make_fake):
    """D2206.1-34: a nextLink that repeats ends that listing with scope_violation."""
    fake = make_fake({"DataBoar-Sintetico": {"a.txt": CPF_TXT}})
    root_id = fake.id_of(ROOT)
    fake.next_link_override = (
        f"https://{GRAPH_HOST}/v1.0/me/drive/items/{root_id}/children"
        "?$top=200&$skiptoken=0"
    )
    out = scan(fake)
    pages = [r for r in fake.graph_requests() if is_children(r)]
    assert len(pages) == 2
    assert "scope_violation" in out.db.reasons()


def _throttle_sub(fake: FakeGraph, count: int, retry_after: str | None, status: int):
    sub_id = fake.id_of(f"{ROOT}/sub")
    left = {"n": count}

    def intercept(request: httpx.Request) -> httpx.Response | None:
        if f"/items/{sub_id}/children" in request.url.path and left["n"] > 0:
            left["n"] -= 1
            headers = {"Retry-After": retry_after} if retry_after is not None else {}
            return httpx.Response(
                status, json={"error": {"code": "x"}}, headers=headers
            )
        return None

    return wrapped(fake, intercept)


def test_D2206_1_35_429_retry_after_and_backoff(make_fake):
    """D2206.1-35: Retry-After honoured and capped; backoff 1..16; 5 tries then throttled."""
    fake = make_fake()
    fake.throttle(1, retry_after=7)
    out = scan(fake)
    assert out.clock.sleeps == [7]
    assert out.paths == EXPECTED

    fake = make_fake()
    fake.throttle(1, retry_after=9999)
    out = scan(fake)
    assert out.clock.sleeps == [120]

    fake = make_fake()
    out = scan(fake, transport=_throttle_sub(fake, 99, "7", 429))
    assert out.paths == {f"{PREFIX}/a.txt"}
    assert out.details("throttled") and f"{ROOT}/sub" in out.details("throttled")[0]
    sub_id = fake.id_of(f"{ROOT}/sub")
    assert len([r for r in fake.requests if f"{sub_id}/children" in r.url]) == 5

    fake = make_fake()
    out = scan(fake, transport=_throttle_sub(fake, 99, None, 429))
    assert out.clock.sleeps == [1, 2, 4, 8, 16]
    assert out.details("throttled")

    fake = make_fake()
    out = scan(fake, transport=_throttle_sub(fake, 2, "bogus", 429))
    assert out.clock.sleeps == [1, 2]
    assert out.paths == EXPECTED


def test_D2206_1_36_503_is_treated_like_429(make_fake):
    """D2206.1-36: 503 with Retry-After: 3."""
    fake = make_fake()
    fake.throttle(1, retry_after=3, status=503)
    out = scan(fake)
    assert out.clock.sleeps == [3]
    assert out.paths == EXPECTED


def test_D2206_1_37_403_in_subfolder_vs_root(make_fake):
    """D2206.1-37: 403 on a subfolder listing records its path and goes on; on the root, stops."""
    fake = make_fake()
    fake.forbid(f"{ROOT}/sub")
    out = scan(fake)
    assert out.paths == {f"{PREFIX}/a.txt"}
    assert any(f"{ROOT}/sub" in d for d in out.details("permission_denied"))

    fake2 = make_fake()
    fake2.forbid(ROOT)
    out2 = scan(fake2)
    assert out2.db.reasons() == ["permission_denied"]
    assert not any(is_children(r) for r in fake2.requests)


# ----------------------------------------------------------------------------
# Download
# ----------------------------------------------------------------------------


def test_D2206_1_38_authorization_only_to_graph(make_fake):
    """D2206.1-38: /content carries Authorization; the download host never does."""
    fake = make_fake()
    scan(fake)
    content = [r for r in fake.graph_requests() if is_content(r)]
    assert content and all(r.headers.get("authorization") for r in content)
    downloads = fake.download_requests()
    assert len(downloads) == 3
    assert all("authorization" not in r.headers for r in downloads)
    assert all("cookie" not in r.headers for r in downloads)


def test_D2206_1_39_location_on_unknown_host_is_refused(make_fake):
    """D2206.1-39: no request to evil.example; detail has the host only."""
    fake = make_fake()
    fake.location_override = f"https://{EVIL_HOST}/{SECRET}x?tempauth={SECRET}y"
    out = scan(fake)
    assert fake.requests_to(EVIL_HOST) == []
    details = out.details("scope_violation")
    # The detail ends with ": <host>"; compare the host exactly, not by substring.
    assert details and all(d.rsplit(": ", 1)[-1] == EVIL_HOST for d in details)
    assert all(SECRET not in d and "tempauth" not in d for d in details)
    assert out.db.findings == []


@pytest.mark.parametrize("ip", ["10.0.0.5", "169.254.169.254"])
def test_D2206_1_40_allowlisted_host_resolving_to_private_ip(make_fake, ip):
    """D2206.1-40: url_guard refuses even with allow_private_networks: true."""
    fake = make_fake()
    fake.host_ips[fake.download_host] = [ip]
    out = scan(fake, make_target(allow_private_networks=True))
    assert fake.download_requests() == []
    assert "scope_violation" in out.db.reasons()
    assert out.db.findings == []


@pytest.mark.parametrize(
    "location",
    [
        f"http://{DEFAULT_DOWNLOAD_HOST}/{SECRET}x",
        f"/{SECRET}relative",
        f"https://u:p@{DEFAULT_DOWNLOAD_HOST}/{SECRET}x",
        f"https://{DEFAULT_DOWNLOAD_HOST}:8443/{SECRET}x",
        f"https://files.1drv.com/{SECRET}x",
        f"https://{DEFAULT_DOWNLOAD_HOST}.evil.example/{SECRET}x",
    ],
)
def test_D2206_1_41_malformed_location_is_refused(make_fake, location):
    """D2206.1-41: http, relative, userinfo, port 8443, bare suffix: no request."""
    fake = make_fake()
    fake.location_override = location
    out = scan(fake)
    assert not any(r.host != GRAPH_HOST and r.host != LOGIN_HOST for r in fake.requests)
    assert "scope_violation" in out.db.reasons()
    assert out.db.findings == []


def test_D2206_1_42_direct_200_content_is_scanned(make_fake):
    """D2206.1-42: /content answering 200 -> body scanned, no second request."""
    fake = make_fake()
    fake.direct_content = True
    out = scan(fake)
    assert out.paths == EXPECTED
    assert fake.download_requests() == []
    assert len([r for r in fake.graph_requests() if is_content(r)]) == 3


def test_D2206_1_43_size_cap_before_and_during_download(make_fake):
    """D2206.1-43: advertised size above the cap skips; a stream above the cap aborts."""
    fake = make_fake(
        {
            "DataBoar-Sintetico": {
                "big.txt": File(CPF_TXT, size=10_000),
                "a.txt": CPF_TXT,
            }
        }
    )
    out = scan(fake, make_target(max_file_bytes=1000))
    big_id = fake.id_of(f"{ROOT}/big.txt")
    assert not any(big_id in r.url for r in fake.requests)
    assert any(
        "file larger than max_file_bytes" in d and "big.txt" in d
        for d in out.details("skipped")
    )
    assert out.paths == {f"{PREFIX}/a.txt"}

    lying = File(CPF_TXT + "x" * 5000, size=10)
    fake2 = make_fake({"DataBoar-Sintetico": {"lying.txt": lying}})
    out2 = scan(fake2, make_target(max_file_bytes=1000))
    assert out2.db.findings == []
    assert any("file larger than max_file_bytes" in d for d in out2.details("skipped"))


def test_D2206_1_44_temp_dir_is_private_and_removed(make_fake, monkeypatch):
    """D2206.1-44: mode 0700 during the scan; removed after success and after a crash."""
    m = mod()
    made: list[str] = []
    real_mkdtemp = m.tempfile.mkdtemp

    def spy(*a: Any, **kw: Any) -> str:
        path = real_mkdtemp(*a, **kw)
        made.append(path)
        return path

    monkeypatch.setattr(m.tempfile, "mkdtemp", spy)
    modes: list[int] = []

    def hook(_c: str, _p: Any) -> None:
        modes.append(stat.S_IMODE(os.stat(made[-1]).st_mode))

    fake = make_fake()
    scan(fake, scanner=HookScanner(hook))
    assert made and modes and all(mode == 0o700 for mode in modes)
    assert not os.path.exists(made[-1])

    def explode(*_a: Any, **_kw: Any) -> str:
        raise RuntimeError(f"extractor crash {SECRET}x")

    monkeypatch.setattr(m, "_read_text_sample", explode)
    fake2 = make_fake()
    out2 = scan(fake2)
    assert not os.path.exists(made[-1])
    assert SECRET not in out2.db.as_text()


def test_D2206_1_45_expired_download_url_gets_one_new_content_call(make_fake):
    """D2206.1-45: 403 once -> new /content and scanned; 403 twice -> failure, scan goes on."""
    fake = make_fake({"DataBoar-Sintetico": {"a.txt": CPF_TXT}})
    fake.download_fail_first = True
    out = scan(fake)
    assert out.paths == {f"{PREFIX}/a.txt"}
    assert len([r for r in fake.graph_requests() if is_content(r)]) == 2

    fake2 = make_fake()
    a_id = fake2.id_of(f"{ROOT}/a.txt")

    def deny_a(request: httpx.Request) -> httpx.Response | None:
        if request.url.host == DEFAULT_DOWNLOAD_HOST and a_id in request.url.path:
            return httpx.Response(403, json={"error": "expired"})
        return None

    out2 = scan(fake2, transport=wrapped(fake2, deny_a))
    assert out2.paths == {f"{PREFIX}/sub/c.csv"}
    assert any(f"{ROOT}/a.txt" in d for _t, _r, d in out2.db.failures)
    assert len([r for r in fake2.requests if a_id in r.url and is_content(r)]) == 2


# ----------------------------------------------------------------------------
# Leaks
# ----------------------------------------------------------------------------


def test_D2206_1_46_no_secret_anywhere(make_fake, caplog, capsys):
    """D2206.1-46: every failure knob, DEBUG logs, stdout/stderr, failures, findings, repr."""
    caplog.set_level(logging.DEBUG)
    outs: list[Out] = []

    fake = make_fake(device_script=["pending", "ok"])
    outs.append(scan(fake))

    fake = make_fake(three_files(), token_expires_in=600)  # proactive refresh
    clock = FakeClock()
    outs.append(scan(fake, clock=clock, scanner=ticking_scanner(clock, 400)))

    fake = make_fake()  # 401 -> refresh
    fake.expire_access_after(1)
    outs.append(scan(fake))

    fake = make_fake()  # 403 on a subfolder
    fake.forbid(f"{ROOT}/sub")
    outs.append(scan(fake))

    fake = make_fake()  # 429
    fake.throttle(1, retry_after=7)
    outs.append(scan(fake))

    fake = make_fake()  # wrong nextLink
    fake.next_link_override = f"https://{EVIL_HOST}/{SECRET}n?x={SECRET}q"
    outs.append(scan(fake))

    fake = make_fake()  # wrong download host
    fake.location_override = f"https://{EVIL_HOST}/{SECRET}x?tempauth={SECRET}y"
    outs.append(scan(fake))

    fake = make_fake(device_script=["invalid_client"])  # OAuth error description
    outs.append(scan(fake))

    fake = make_fake()  # HTTPStatusError raised on the download, URL inside its text

    def status_error(request: httpx.Request) -> httpx.Response | None:
        if request.url.host == DEFAULT_DOWNLOAD_HOST:
            resp = httpx.Response(500, request=request)
            raise httpx.HTTPStatusError(
                f"boom for url {request.url}", request=request, response=resp
            )
        return None

    outs.append(scan(fake, transport=wrapped(fake, status_error)))

    captured = capsys.readouterr()
    for marker in LEAK_MARKERS:
        assert marker not in caplog.text, marker
        assert marker not in captured.out + captured.err, marker
        for out in outs:
            assert marker not in out.db.as_text(), marker
            assert marker not in out.prompt, marker
            assert marker not in repr(out.conn) + str(out.conn), marker
    assert USER_CODE in outs[0].prompt
    assert USER_CODE not in caplog.text
    assert USER_CODE not in captured.out + captured.err
    for out in outs:
        assert USER_CODE not in out.db.as_text()


def test_D2206_1_47_module_passes_the_str_e_gate():
    """D2206.1-47: no str(e)-style call site in the new module (#1722)."""
    from tests.str_e_callsite_gate import classify_str_e_in_source

    source = MODULE_PATH.read_text(encoding="utf-8")
    assert classify_str_e_in_source(source, rel_path="connectors/x.py") == []
    tree_ = ast.parse(source)
    for node in ast.walk(tree_):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in {"str", "repr"} and node.args:
                arg = node.args[0]
                assert not (
                    isinstance(arg, ast.Name) and arg.id in {"e", "exc", "err", "error"}
                )


def test_D2206_1_48_no_secret_storage_no_redirect_following():
    """D2206.1-48: no client_secret, no open( for writing, no follow_redirects=True."""
    source = MODULE_PATH.read_text(encoding="utf-8")
    assert "client_secret" not in source
    assert not re.search(r"\bopen\(", source)
    assert "follow_redirects=True" not in source


# ----------------------------------------------------------------------------
# Extraction
# ----------------------------------------------------------------------------


def test_D2206_1_49_extraction_reuses_the_file_connector(make_fake, monkeypatch):
    """D2206.1-49: text via scanner; .sqlite via _scan_sqlite_file_as_db; .zip via archives."""
    m = mod()
    fake = make_fake({"DataBoar-Sintetico": {"a.txt": CPF_TXT}})
    scanner = HookScanner(lambda _c, _p: None)
    out = scan(fake, scanner=scanner)
    assert scanner.seen == [(CPF_TXT, Path("a.txt"))]
    (finding,) = out.db.findings
    assert finding["source_type"] == "filesystem"
    assert finding["path"] == f"{PREFIX}/a.txt"
    assert finding["file_name"] == "a.txt"
    assert finding["data_type"] == "TXT"
    assert finding["target_name"] == "onedrive-sintetico"

    sqlite_calls: list[Path] = []

    def fake_sqlite(path: Path, _scanner: Any, _limit: int) -> list[dict[str, Any]]:
        sqlite_calls.append(path)
        return [
            {
                "file_name": "db.sqlite",
                "data_type": "SQLITE",
                "sensitivity_level": "HIGH",
                "pattern_detected": "LGPD_CPF",
                "norm_tag": "LGPD",
                "ml_confidence": 90,
            }
        ]

    monkeypatch.setattr(m, "_scan_sqlite_file_as_db", fake_sqlite)
    fake2 = make_fake({"DataBoar-Sintetico": {"db.sqlite": b"SQLite format 3\x00"}})
    out2 = scan(fake2)
    assert len(sqlite_calls) == 1
    assert out2.paths == {f"{PREFIX}/db.sqlite"}

    archive_calls: list[dict[str, Any]] = []
    monkeypatch.setattr(
        m, "scan_archive_at_path", lambda **kw: archive_calls.append(kw)
    )
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("dentro.txt", CPF_TXT)
    fake3 = make_fake({"DataBoar-Sintetico": {"pacote.zip": buf.getvalue()}})
    scan(fake3, make_target(file_scan={"scan_compressed": True}))
    assert len(archive_calls) == 1
    assert archive_calls[0]["path_display"] == f"{PREFIX}/pacote.zip"
    assert archive_calls[0]["archive_display_name"] == "pacote.zip"


def test_D2206_1_50_extension_outside_the_filter_is_not_downloaded(make_fake):
    """D2206.1-50: an unsupported extension never gets a /content call."""
    fake = make_fake({"DataBoar-Sintetico": {"prog.exe": b"MZ", "a.txt": CPF_TXT}})
    out = scan(fake)
    exe_id = fake.id_of(f"{ROOT}/prog.exe")
    assert not any(exe_id in r.url for r in fake.requests)
    assert out.paths == {f"{PREFIX}/a.txt"}


# ----------------------------------------------------------------------------
# CLI opt-in
# ----------------------------------------------------------------------------


class _Stop(BaseException):
    """Ends main() right after the call under test."""


def _write_cli_config(tmp_path: Path) -> Path:
    data = tmp_path / "data"
    data.mkdir()
    (data / "a.txt").write_text("nada", encoding="utf-8")
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        "targets:\n"
        "  - name: fs\n"
        "    type: filesystem\n"
        f"    path: {data.as_posix()}\n"
        "report:\n"
        f"  output_dir: {tmp_path.as_posix()}\n"
        f"sqlite_path: {(tmp_path / 'audit.db').as_posix()}\n"
        "api:\n"
        "  port: 8088\n",
        encoding="utf-8",
    )
    return cfg


def test_D2206_1_51_only_the_oneshot_cli_enables_interactive_sign_in(
    tmp_path, monkeypatch
):
    """D2206.1-51: one-shot CLI enables it before start_audit; --web and the API never do."""
    import main as main_mod

    m = mod()
    calls: list[str] = []
    monkeypatch.setattr(m, "enable_interactive_sign_in", lambda: calls.append("enable"))
    monkeypatch.setattr(
        main_mod, "_install_scan_interrupt_signal_handlers", lambda: None
    )

    def fake_start(self: Any, *a: Any, **kw: Any) -> str:
        calls.append("start")
        raise _Stop

    monkeypatch.setattr(main_mod.AuditEngine, "start_audit", fake_start)
    cfg = _write_cli_config(tmp_path)

    monkeypatch.setattr(sys, "argv", ["main.py", "--config", str(cfg)])
    with pytest.raises(_Stop):
        main_mod.main()
    assert calls == ["enable", "start"]

    calls.clear()
    import uvicorn

    def fake_uvicorn_run(*_a: Any, **_kw: Any) -> None:
        calls.append("uvicorn")
        raise _Stop

    monkeypatch.setattr(uvicorn, "run", fake_uvicorn_run)
    monkeypatch.setattr(
        sys,
        "argv",
        ["main.py", "--config", str(cfg), "--web", "--allow-insecure-http"],
    )
    with pytest.raises(_Stop):
        main_mod.main()
    assert calls == ["uvicorn"]

    # The API, the dashboard and the engine never reference the opt-in.
    for rel in ("api", "app", "core"):
        for path in (REPO / rel).rglob("*.py"):
            assert "enable_interactive_sign_in" not in path.read_text(
                encoding="utf-8"
            ), path


# ----------------------------------------------------------------------------
# Nothing environment-specific in the code; every key comes from the YAML
# (operator rule of 2026-11-17 on #2261, items A and B)
# ----------------------------------------------------------------------------

REQUIRED_KEYS = (
    "auth.mode",
    "auth.tenant",
    "auth.client_id",
    "auth.login_host",
    "auth.scopes",
    "graph.base_url",
    "download_host_suffixes",
    "drive",
    "max_depth",
    "max_file_bytes",
    "page_size",
    "max_pages_per_folder",
    "http_timeout_seconds",
    "throttle_max_wait_seconds",
)

# Environment-specific values that must never be literals in the reader.
_FORBIDDEN_LITERALS = (
    ("GUID", re.compile(r"[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}")),
    ("tenant alias", re.compile(r"\b(?:consumers|organizations|common)\b")),
    # offline_access is the OAuth protocol scope for a refresh token (allowed).
    ("scope", re.compile(r"Files\.Read|Sites\.\w+|User\.Read", re.I)),
    (
        "Microsoft host",
        re.compile(
            r"microsoftonline|graph\.microsoft|microsoft\.(?:com|us|cn)\b|"
            r"chinacloudapi|1drv|microsoftpersonalcontent|sharepoint\.(?:com|us|cn)",
            re.I,
        ),
    ),
    ("API version", re.compile(r"\bv1\.0\b|/beta\b")),
    ("folder, site or drive name", re.compile(r"DataBoar-|/sites/|Shared Documents")),
)


def _string_constants(source: str) -> list[str]:
    out: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            out.append(node.value)
    return out


def test_D2206_1_52_no_environment_literal_in_the_reader():
    """D2206.1-52: no GUID, tenant alias, scope, Microsoft host, API version or folder name.

    Protocol constants (OAuth field names, grant types, Graph path segments such as
    ``/me/drive``) are allowed; values that distinguish a cloud, tenant or customer
    must come from the target YAML.
    """
    found = []
    for text in _string_constants(MODULE_PATH.read_text(encoding="utf-8")):
        for label, pattern in _FORBIDDEN_LITERALS:
            if pattern.search(text):
                found.append((label, text))
    assert found == []


def _without(target: dict[str, Any], dotted: str) -> dict[str, Any]:
    import copy

    clone = copy.deepcopy(target)
    parent = clone
    *head, last = dotted.split(".")
    for part in head:
        parent = parent[part]
    del parent[last]
    return clone


@pytest.mark.parametrize("key", REQUIRED_KEYS)
def test_D2206_1_53_every_key_is_required_and_cited(make_fake, key):
    """D2206.1-53: removing a required key fails closed with a message citing it."""
    fake = make_fake()
    out = scan(fake, _without(make_target(), key))
    _assert_config_error(fake, out)
    assert key in out.details("config_error")[0]


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("auth.login_host", "https://login.example/"),
        ("auth.scopes", ""),
        ("graph.base_url", "http://graph.example/v1.0"),
        ("download_host_suffixes", []),
        ("download_host_suffixes", ["files.1drv.example"]),
        ("page_size", 0),
        ("max_pages_per_folder", 0),
        ("http_timeout_seconds", 0),
        ("max_depth", True),
    ],
)
def test_D2206_1_53_invalid_values_fail_closed(make_fake, key, value):
    """D2206.1-53: a present but invalid value is refused, citing the key."""
    fake = make_fake()
    target = make_target()
    parent = target
    *head, last = key.split(".")
    for part in head:
        parent = parent[part]
    parent[last] = value
    out = scan(fake, target)
    _assert_config_error(fake, out)
    assert key in out.details("config_error")[0]


# ----------------------------------------------------------------------------
# The operator, not the YAML, approves the token destinations (security finding on
# ca69f2aa, PM 2026-11-17): DATA_BOAR_CREDENTIAL_ALLOWED_HOSTS through the existing
# #2086/#2103 gate. The read-only rule is enforced on the scope structure.
# ----------------------------------------------------------------------------


def _strict(monkeypatch: pytest.MonkeyPatch, hosts: str | None) -> None:
    monkeypatch.setenv("DATA_BOAR_CREDENTIAL_STRICT", "1")
    monkeypatch.delenv("DATA_BOAR_CREDENTIAL_HOSTS_UNRESTRICTED", raising=False)
    if hosts is None:
        monkeypatch.delenv("DATA_BOAR_CREDENTIAL_ALLOWED_HOSTS", raising=False)
    else:
        monkeypatch.setenv("DATA_BOAR_CREDENTIAL_ALLOWED_HOSTS", hosts)


def test_D2206_1_55_operator_list_approves_login_and_graph(make_fake, monkeypatch):
    """D2206.1-55: in strict mode both configured hosts must be in the operator list,
    at load time (loader gate) and at run time (the reader calls the same gate)."""
    from config.loader import normalize_config

    _strict(monkeypatch, f"{LOGIN_HOST},{GRAPH_HOST}")
    out = normalize_config(
        _cfg(dict(make_target()["auth"]), graph=make_target()["graph"])
    )
    assert out["targets"][0]["graph"]["base_url"]
    fake = make_fake()
    assert scan(fake).paths == EXPECTED

    for hosts in (LOGIN_HOST, GRAPH_HOST, None):
        _strict(monkeypatch, hosts)
        with pytest.raises(ValueError):
            normalize_config(
                _cfg(dict(make_target()["auth"]), graph=make_target()["graph"])
            )
        fake = make_fake()
        result = scan(fake)
        _assert_config_error(fake, result)


def test_D2206_1_55_yaml_cannot_approve_its_own_destination(make_fake, monkeypatch):
    """D2206.1-55: a host chosen in the YAML (even with a YAML allowlist naming it)
    is refused when the operator list does not hold it."""
    from config.loader import normalize_config

    _strict(monkeypatch, f"{LOGIN_HOST},{GRAPH_HOST}")
    target = make_target()
    target["graph"] = {
        "base_url": "https://graph.evil.example/v1.0",
        "allowed_hosts": ["graph.evil.example"],
    }
    target["auth"]["allowed_login_hosts"] = [LOGIN_HOST, "graph.evil.example"]
    target["allowed_hosts"] = [LOGIN_HOST, "graph.evil.example"]
    with pytest.raises(ValueError):
        normalize_config(
            {"targets": [dict(target)], "api": {}, "report": {"output_dir": "."}}
        )
    fake = make_fake()
    result = scan(fake, target)
    _assert_config_error(fake, result)


def test_D2206_1_55_without_strict_mode_the_gate_does_not_run(make_fake, monkeypatch):
    """D2206.1-55 (pins today's #2103 semantics, reported to the PM): without
    DATA_BOAR_CREDENTIAL_STRICT=1 the operator host gate is off for every connector,
    so the YAML hosts are not checked against an operator list. The reader still
    refuses malformed hosts, but nothing approves the destination."""
    from config.loader import normalize_config

    monkeypatch.delenv("DATA_BOAR_CREDENTIAL_STRICT", raising=False)
    monkeypatch.delenv("DATA_BOAR_CREDENTIAL_ALLOWED_HOSTS", raising=False)
    target = make_target()
    target["graph"] = {"base_url": "https://graph.other.example/v1.0"}
    target["auth"]["scopes"] = "Files.Read offline_access"
    out = normalize_config(
        {"targets": [dict(target)], "api": {}, "report": {"output_dir": "."}}
    )
    loaded = out["targets"][0]["graph"]["base_url"]
    assert loaded == "https://graph.other.example/v1.0"
    assert urlsplit(loaded).hostname == "graph.other.example"
    fake = make_fake()
    result = scan(fake, target)
    assert "config_error" not in result.db.reasons()


@pytest.mark.parametrize(
    "scopes",
    [
        "Files.ReadWrite offline_access",
        "Files.ReadWrite.All",
        "Sites.Manage.All",
        "Sites.FullControl.All",
        "Files.Write",
        "Mail.Send",
        "openid",
        "offline_access",
        f"https://{GRAPH_HOST}/Files.ReadWrite offline_access",
        "https://evil.example/Files.Read offline_access",
        "Files.Read.Write",
        "Files.Readx",
    ],
)
def test_D2206_1_56_write_or_unknown_scopes_are_refused(make_fake, scopes):
    """D2206.1-56: the reader is read-only; scopes are validated by structure."""
    fake = make_fake()
    target = make_target()
    target["auth"]["scopes"] = scopes
    result = scan(fake, target)
    _assert_config_error(fake, result)
    assert "auth.scopes" in result.details("config_error")[0]


@pytest.mark.parametrize(
    "scopes",
    [
        f"https://{GRAPH_HOST}/Files.Read offline_access",
        f"https://{GRAPH_HOST}/Files.Read.All offline_access",
        "Files.Read offline_access",
        "Sites.Read.Selected",
    ],
)
def test_D2206_1_56_read_scopes_are_accepted(make_fake, scopes):
    """D2206.1-56: .Read, .Read.All and .Read.Selected pass (plus offline_access)."""
    fake = make_fake()
    target = make_target()
    target["auth"]["scopes"] = scopes
    result = scan(fake, target)
    assert "config_error" not in result.db.reasons()
    assert fake.device_requests[0]["scope"] == " ".join(scopes.split())
