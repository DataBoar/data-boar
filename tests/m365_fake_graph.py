"""Simulated Microsoft login + Graph for the ``sharepoint_online`` acceptance tests (2206.1).

Support module, not a test file. Everything here is synthetic: no network, no tenant,
no real credential. The fake runs in-process behind an ``httpx.MockTransport``.

Contract (docs/desenho/2206.1.md, section 11):

* ``FakeGraph(tree=..., page_size=200)``: in-memory folder/file tree.
* ``.transport``: serves only ``login.microsoftonline.com``, ``graph.microsoft.com``
  and the configured download host. Any other host is recorded in ``.violations``
  (a handler that raised would be swallowed by the connector, which must never let
  an exception escape ``run()``, so violations are collected and asserted by the tests).
* ``.requests``: every request seen, as ``Req(method, url, headers)`` (unpackable).
* Device-code script, knobs and markers as described below.

Markers: tokens, ``device_code``, the Microsoft ``message``/``error_description`` and the
path and query of the download URL contain ``SECRET-``. The test ``client_id`` is a
syntactically valid GUID (the design requires GUID format), so it is tracked in
``LEAK_MARKERS`` as an exact string instead. The ``user_code`` is ``UCODE-1`` and may
appear in the human prompt stream only.
"""

from __future__ import annotations

import io
import ipaddress
import json
import re
from collections.abc import Callable
from typing import Any, NamedTuple
from urllib.parse import parse_qs, quote, unquote, urlsplit

import httpx

LOGIN_HOST = "login.microsoftonline.com"
GRAPH_HOST = "graph.microsoft.com"
DEFAULT_DOWNLOAD_HOST = "dl.files.1drv.com"
EVIL_HOST = "evil.example"

SECRET = "SECRET-"
USER_CODE = "UCODE-1"
VERIFICATION_URI = "https://microsoft.com/devicelogin"
# Obviously fake, valid GUID shape (the design validates client_id as a GUID).
TEST_CLIENT_ID = "5ec2e700-0000-4000-8000-00000000c11d"
TEST_TENANT = "consumers"
DRIVE_ID = "DRIVE-FAKE-1"
OTHER_DRIVE_ID = "DRIVE-OTHER-9"

# Strings that must never appear in logs, output, failures, findings or repr().
LEAK_MARKERS = (SECRET, TEST_CLIENT_ID)

SCOPE = "https://graph.microsoft.com/Files.Read offline_access"
DOWNLOAD_HOST_SUFFIXES = (
    ".files.1drv.com",
    ".microsoftpersonalcontent.com",
    ".sharepoint.com",
)


class Req(NamedTuple):
    method: str
    url: str
    headers: dict[str, str]

    @property
    def host(self) -> str:
        return (urlsplit(self.url).hostname or "").lower()

    @property
    def path(self) -> str:
        return urlsplit(self.url).path


# ----------------------------------------------------------------------------
# Tree description
# ----------------------------------------------------------------------------


class File:
    """A file node. ``size`` overrides the advertised size (the body is unchanged)."""

    def __init__(
        self,
        content: bytes | str = b"",
        *,
        size: int | None = None,
        remote: bool = False,
        package: bool = False,
        malware: bool = False,
        deleted: bool = False,
        drive_id: str | None = None,
    ) -> None:
        self.content = content.encode() if isinstance(content, str) else content
        self.size = size
        self.remote = remote
        self.package = package
        self.malware = malware
        self.deleted = deleted
        self.drive_id = drive_id


class Folder:
    """A folder node. Facet flags make it a shortcut / package / other-drive item."""

    def __init__(
        self,
        children: dict[str, Any] | None = None,
        *,
        remote: bool = False,
        package: bool = False,
        malware: bool = False,
        deleted: bool = False,
        drive_id: str | None = None,
    ) -> None:
        self.children = children or {}
        self.remote = remote
        self.package = package
        self.malware = malware
        self.deleted = deleted
        self.drive_id = drive_id


def _as_node(value: Any) -> File | Folder:
    if isinstance(value, (File, Folder)):
        return value
    if isinstance(value, dict):
        return Folder(value)
    if isinstance(value, (bytes, str)):
        return File(value)
    raise TypeError(f"unsupported tree node: {type(value).__name__}")


class _Item:
    def __init__(
        self, item_id: str, name: str, node: File | Folder, parent: _Item | None
    ) -> None:
        self.id = item_id
        self.name = name
        self.node = node
        self.parent = parent
        self.is_folder = isinstance(node, Folder)
        self.children: list[_Item] = []

    @property
    def path(self) -> str:
        if self.parent is None:
            return ""
        return f"{self.parent.path}/{self.name}"


def _json(
    status: int, body: Any, headers: dict[str, str] | None = None
) -> httpx.Response:
    return httpx.Response(status, json=body, headers=headers)


class FakeGraph:
    """In-process Microsoft login + Graph (+ pre-authenticated download host)."""

    def __init__(
        self,
        tree: dict[str, Any] | None = None,
        *,
        page_size: int = 200,
        download_host: str = DEFAULT_DOWNLOAD_HOST,
        device_script: list[str] | None = None,
        device_interval: int = 5,
        device_expires_in: int = 900,
        token_expires_in: int = 3600,
    ) -> None:
        self.page_size = page_size
        self.download_host = download_host.lower()
        self.drive_id = DRIVE_ID
        self.device_script = list(device_script or ["ok"])
        self.device_interval = device_interval
        self.device_expires_in = device_expires_in
        self.token_expires_in = token_expires_in

        self.requests: list[Req] = []
        self.violations: list[str] = []
        self.token_requests: list[dict[str, str]] = []
        self.device_requests: list[dict[str, str]] = []

        # Host -> IPs used by the patched ``url_guard._resolve_host_ips``.
        self.host_ips: dict[str, list[str]] = {
            LOGIN_HOST: ["1.1.1.1"],
            GRAPH_HOST: ["1.1.1.1"],
            self.download_host: ["1.1.1.1"],
        }

        # Knobs.
        self.omit_refresh_token = False
        self.refresh_fails: str | None = None  # e.g. "invalid_grant"
        self.direct_content = False  # /content answers 200 instead of 302
        self.location_override: str | Callable[[str], str] | None = None
        self.next_link_override: str | Callable[[str], str] | None = None
        self.download_fail_first = False  # download host answers 403 once
        self._forbidden: set[str] = set()
        self._throttle: dict[str, Any] | None = None
        self._expire_after: int | None = None

        self._counter = 0
        self._token_serial = 0
        self._device_serial = 0
        self._device_polls = 0
        self._graph_ok_calls = 0
        self.refresh_count = 0
        self._access: str | None = None
        self._refresh: str | None = None
        self._issued_device_code: str | None = None

        self.items: dict[str, _Item] = {}
        self.root = _Item("ROOT0000", "", Folder({}), None)
        self.items[self.root.id] = self.root
        self._build(self.root, tree or {})

        self.transport = httpx.MockTransport(self._handle)

    # -- tree ----------------------------------------------------------------

    def _build(self, parent: _Item, children: dict[str, Any]) -> None:
        for name, raw in children.items():
            node = _as_node(raw)
            self._counter += 1
            item = _Item(f"ITEM{self._counter:04d}", name, node, parent)
            self.items[item.id] = item
            parent.children.append(item)
            if isinstance(node, Folder):
                self._build(item, node.children)

    def id_of(self, path: str) -> str:
        """Item id of a ``/a/b`` path inside the tree."""
        cur = self.root
        for seg in [s for s in path.split("/") if s]:
            cur = next(c for c in cur.children if c.name == seg)
        return cur.id

    def ids_under(self, path: str) -> set[str]:
        """The id of ``path`` and of every descendant."""
        out: set[str] = set()
        stack = [self.items[self.id_of(path)]]
        while stack:
            it = stack.pop()
            out.add(it.id)
            stack.extend(it.children)
        return out

    # -- knobs ----------------------------------------------------------------

    def forbid(self, path_or_id: str) -> None:
        """Answer 403 to every request about this item (metadata, children, content)."""
        self._forbidden.add(
            path_or_id if path_or_id in self.items else self.id_of(path_or_id)
        )

    def throttle(
        self, count: int, retry_after: int | None = None, status: int = 429
    ) -> None:
        """The next ``count`` children listings answer 429/503 (with ``Retry-After``)."""
        self._throttle = {"left": count, "retry_after": retry_after, "status": status}

    def expire_access_after(self, calls: int) -> None:
        """After ``calls`` authenticated Graph calls the access token stops working (401)."""
        self._expire_after = calls

    # -- request views for assertions ------------------------------------------

    def requests_to(self, host: str) -> list[Req]:
        return [r for r in self.requests if r.host == host.lower()]

    def graph_requests(self) -> list[Req]:
        return self.requests_to(GRAPH_HOST)

    def login_requests(self) -> list[Req]:
        return self.requests_to(LOGIN_HOST)

    def download_requests(self) -> list[Req]:
        return self.requests_to(self.download_host)

    # -- dispatch ----------------------------------------------------------------

    def _handle(self, request: httpx.Request) -> httpx.Response:
        headers = {k.lower(): v for k, v in request.headers.items()}
        self.requests.append(Req(request.method, str(request.url), headers))
        host = (request.url.host or "").lower()
        if host == LOGIN_HOST:
            return self._login(request)
        if host == GRAPH_HOST:
            return self._graph(request, headers)
        if host == self.download_host:
            return self._download(request, headers)
        self.violations.append(f"unexpected host: {host}")
        return _json(400, {"error": "unexpected-host"})

    # -- login ---------------------------------------------------------------------

    def _form(self, request: httpx.Request) -> dict[str, str]:
        body = request.content.decode("utf-8", "replace")
        return {k: v[0] for k, v in parse_qs(body, keep_blank_values=True).items()}

    def _login(self, request: httpx.Request) -> httpx.Response:
        form = self._form(request)
        if "client_secret" in form:
            self.violations.append("client_secret sent to the login endpoint")
        path = request.url.path
        if request.method != "POST":
            self.violations.append(f"login endpoint called with {request.method}")
            return _json(405, {"error": "method"})
        if path.endswith("/oauth2/v2.0/devicecode"):
            self.device_requests.append(form)
            self._device_serial += 1
            self._issued_device_code = f"{SECRET}DEVCODE-{self._device_serial}"
            return _json(
                200,
                {
                    "device_code": self._issued_device_code,
                    "user_code": USER_CODE,
                    "verification_uri": VERIFICATION_URI,
                    "expires_in": self.device_expires_in,
                    "interval": self.device_interval,
                    "message": f"To sign in, open {VERIFICATION_URI} and enter {USER_CODE}. {SECRET}message",
                },
            )
        if path.endswith("/oauth2/v2.0/token"):
            self.token_requests.append(form)
            grant = form.get("grant_type", "")
            if grant == "urn:ietf:params:oauth:grant-type:device_code":
                return self._device_poll(form)
            if grant == "refresh_token":
                return self._refresh_grant(form)
            return _json(400, {"error": "unsupported_grant_type"})
        self.violations.append(f"unexpected login path: {path}")
        return _json(404, {"error": "not_found"})

    def _oauth_error(self, error: str, code: int | None = None) -> httpx.Response:
        body: dict[str, Any] = {
            "error": error,
            "error_description": f"AADSTS{code or 70000}: detail {SECRET}desc",
        }
        if code:
            body["error_codes"] = [code]
        return _json(400, body)

    def _device_poll(self, form: dict[str, str]) -> httpx.Response:
        if form.get("device_code") != self._issued_device_code:
            return self._oauth_error("bad_verification_code", 70000)
        step = (
            self.device_script[self._device_polls]
            if self._device_polls < len(self.device_script)
            else self.device_script[-1]
        )
        self._device_polls += 1
        table = {
            "pending": ("authorization_pending", 70016),
            "slow_down": ("slow_down", None),
            "declined": ("authorization_declined", 70001),
            "expired": ("expired_token", 70019),
            "bad_code": ("bad_verification_code", 70000),
            "invalid_client": ("invalid_client", 7000218),
        }
        if step in table:
            return self._oauth_error(*table[step])
        return self._issue_tokens()

    def _issue_tokens(self) -> httpx.Response:
        self._token_serial += 1
        self._access = f"{SECRET}AT-{self._token_serial}"
        self._expire_countdown_reset()
        body: dict[str, Any] = {
            "token_type": "Bearer",
            "scope": SCOPE,
            "expires_in": self.token_expires_in,
            "access_token": self._access,
        }
        if not self.omit_refresh_token:
            self._refresh = f"{SECRET}RT-{self._token_serial}"
            body["refresh_token"] = self._refresh
        else:
            self._refresh = None
        return _json(200, body)

    def _refresh_grant(self, form: dict[str, str]) -> httpx.Response:
        if self.refresh_fails:
            return self._oauth_error(self.refresh_fails, 70008)
        if self._refresh is None or form.get("refresh_token") != self._refresh:
            return self._oauth_error("invalid_grant", 70008)
        self.refresh_count += 1
        return self._issue_tokens()

    def _expire_countdown_reset(self) -> None:
        self._graph_ok_calls = 0

    # -- graph -----------------------------------------------------------------------

    def _unauthorized(self) -> httpx.Response:
        return _json(
            401,
            {
                "error": {
                    "code": "InvalidAuthenticationToken",
                    "message": f"expired {SECRET}401",
                }
            },
        )

    def _graph(self, request: httpx.Request, headers: dict[str, str]) -> httpx.Response:
        if request.method != "GET":
            self.violations.append(
                f"graph called with {request.method} (read-only reader)"
            )
            return _json(405, {"error": "method"})
        auth = headers.get("authorization", "")
        if not auth:
            self.violations.append("graph request without Authorization")
            return self._unauthorized()
        if self._access is None or auth != f"Bearer {self._access}":
            return self._unauthorized()
        if (
            self._expire_after is not None
            and self._graph_ok_calls >= self._expire_after
        ):
            self._expire_after = None
            self._access = None  # the issued token is now invalid
            return self._unauthorized()
        self._graph_ok_calls += 1

        raw = request.url.raw_path.decode("ascii").split("?", 1)[0]
        base = "/v1.0/me/drive"
        if not raw.startswith(base):
            self.violations.append(f"unexpected graph path: {raw}")
            return _json(404, {"error": {"code": "itemNotFound"}})
        rest = raw[len(base) :]
        if rest in ("", "/"):
            return _json(200, {"id": self.drive_id, "driveType": "personal"})
        if rest.startswith("/root:"):
            return self._by_path(rest[len("/root:") :])
        m = re.fullmatch(r"/items/([^/]+)(/children|/content)?", rest)
        if not m:
            self.violations.append(f"unexpected graph path: {raw}")
            return _json(404, {"error": {"code": "itemNotFound"}})
        item = self.items.get(unquote(m.group(1)))
        if item is None:
            return _json(404, {"error": {"code": "itemNotFound"}})
        if item.id in self._forbidden:
            return _json(403, {"error": {"code": "accessDenied", "message": "denied"}})
        if m.group(2) == "/children":
            return self._children(request, item)
        if m.group(2) == "/content":
            return self._content(item)
        return _json(200, self._item_json(item))

    def _by_path(self, tail: str) -> httpx.Response:
        tail = tail.rstrip(":")
        cur = self.root
        for seg in [unquote(s) for s in tail.split("/") if s]:
            nxt = next((c for c in cur.children if c.name == seg), None)
            if nxt is None:
                return _json(404, {"error": {"code": "itemNotFound"}})
            cur = nxt
        if cur.id in self._forbidden:
            return _json(403, {"error": {"code": "accessDenied", "message": "denied"}})
        return _json(200, self._item_json(cur))

    def _item_json(self, it: _Item) -> dict[str, Any]:
        node = it.node
        body: dict[str, Any] = {"id": it.id, "name": it.name}
        if it.parent is None:
            body["root"] = {}
            body["parentReference"] = {"driveId": self.drive_id}
            return body
        parent_path = "/drive/root:" + quote(it.parent.path, safe="/")
        body["parentReference"] = {
            "driveId": node.drive_id or self.drive_id,
            "id": it.parent.id,
            "path": parent_path,
        }
        if isinstance(node, Folder):
            body["folder"] = {"childCount": len(node.children)}
            body["size"] = 0
        else:
            body["file"] = {"mimeType": "application/octet-stream"}
            body["size"] = node.size if node.size is not None else len(node.content)
        if node.remote:
            body["remoteItem"] = {
                "id": f"REMOTE-{it.id}",
                "parentReference": {"driveId": OTHER_DRIVE_ID},
            }
        if node.package:
            body["package"] = {"type": "oneNote"}
        if node.malware:
            body["malware"] = {"description": "synthetic"}
        if node.deleted:
            body["deleted"] = {"state": "deleted"}
        return body

    def _children(self, request: httpx.Request, item: _Item) -> httpx.Response:
        if not item.is_folder:
            return _json(400, {"error": {"code": "invalidRequest"}})
        if self._throttle and self._throttle["left"] > 0:
            self._throttle["left"] -= 1
            hdrs = {}
            if self._throttle["retry_after"] is not None:
                hdrs["Retry-After"] = str(self._throttle["retry_after"])
            return _json(
                self._throttle["status"],
                {
                    "error": {
                        "code": "activityLimitReached",
                        "message": f"slow down {SECRET}429",
                    }
                },
                hdrs,
            )
        params = request.url.params
        top = int(params.get("$top", self.page_size))
        size = max(1, min(top, self.page_size))
        offset = int(params.get("$skiptoken", "0"))
        page = item.children[offset : offset + size]
        body: dict[str, Any] = {"value": [self._item_json(c) for c in page]}
        more = offset + size < len(item.children)
        link = (
            f"https://{GRAPH_HOST}/v1.0/me/drive/items/{item.id}/children"
            f"?$top={size}&$skiptoken={offset + size}"
        )
        override = self.next_link_override
        if override is not None and offset == 0:
            link = override(link) if callable(override) else override
            more = True
        if more:
            body["@odata.nextLink"] = link
        return _json(200, body)

    def _content(self, item: _Item) -> httpx.Response:
        if item.is_folder:
            return _json(400, {"error": {"code": "invalidRequest"}})
        node = item.node
        assert isinstance(node, File)
        if self.direct_content:
            return httpx.Response(200, content=node.content)
        default = (
            f"https://{self.download_host}/{SECRET}dl/{item.id}?tempauth={SECRET}q"
        )
        loc = self.location_override
        if loc is not None:
            default = loc(item.id) if callable(loc) else loc
        return httpx.Response(302, headers={"Location": default})

    # -- download host ------------------------------------------------------------------

    def _download(
        self, request: httpx.Request, headers: dict[str, str]
    ) -> httpx.Response:
        if "authorization" in headers:
            self.violations.append("Authorization sent to the download host")
            return _json(400, {"error": "authorization-not-allowed"})
        if "cookie" in headers:
            self.violations.append("Cookie sent to the download host")
            return _json(400, {"error": "cookie-not-allowed"})
        if self.download_fail_first:
            self.download_fail_first = False
            return _json(403, {"error": "expired"})
        m = re.fullmatch(rf"/{re.escape(SECRET)}dl/([^/]+)", unquote(request.url.path))
        item = self.items.get(m.group(1)) if m else None
        if item is None or not isinstance(item.node, File):
            return _json(404, {"error": "not_found"})
        return httpx.Response(200, content=item.node.content)


# ----------------------------------------------------------------------------
# Test doubles around the connector
# ----------------------------------------------------------------------------


class FakeClock:
    """Injectable ``_monotonic`` / ``_sleep``: sleeping advances time, never waits."""

    def __init__(self) -> None:
        self.now = 1000.0
        self.sleeps: list[float] = []

    def monotonic(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


class TtyStream(io.StringIO):
    """Human prompt stream that looks like a terminal."""

    def isatty(self) -> bool:
        return True


class FakeDB:
    """Stand-in for ``db_manager``: records findings and failures."""

    def __init__(self) -> None:
        self.findings: list[dict[str, Any]] = []
        self.failures: list[tuple[str, str, str]] = []

    def save_finding(self, source_type: str, **kwargs: Any) -> None:
        self.findings.append({"source_type": source_type, **kwargs})

    def save_failure(
        self, target_name: str, reason: str, details: str | None = None
    ) -> None:
        self.failures.append((target_name, reason, details or ""))

    def reasons(self) -> list[str]:
        return [r for _, r, _ in self.failures]

    def as_text(self) -> str:
        return json.dumps(
            {"findings": self.findings, "failures": self.failures}, default=str
        )


_CPF = re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b")
_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b")


class RegexScanner:
    """Deterministic detector (CPF, e-mail). The real ML scanner flags every text here."""

    def scan_file_content(self, content: str, file_path: Any) -> dict[str, Any] | None:
        if _CPF.search(content or ""):
            pattern, norm = "LGPD_CPF", "LGPD Art. 5"
        elif _EMAIL.search(content or ""):
            pattern, norm = "EMAIL", "GDPR Art. 4(1)"
        else:
            return None
        return {
            "sensitivity_level": "HIGH",
            "pattern_detected": pattern,
            "norm_tag": norm,
            "ml_confidence": 100,
        }


def install_fake_dns(monkeypatch: Any, fake: FakeGraph) -> None:
    """Replace ``url_guard._resolve_host_ips`` with the fake's host -> IP map."""
    import connectors.url_guard as url_guard

    def resolve(host: str) -> list[Any]:
        ips = fake.host_ips.get(host.lower())
        if ips is None:
            raise OSError(f"synthetic DNS: no such host {host}")
        return [ipaddress.ip_address(ip) for ip in ips]

    monkeypatch.setattr(url_guard, "_resolve_host_ips", resolve)


def make_target(**overrides: Any) -> dict[str, Any]:
    """A valid ``sharepoint_online`` target with obviously fake values."""
    # Every key is required by the reader (no default anywhere, operator rule
    # of 2026-11-17 on #2261): the test target spells all of them out.
    target: dict[str, Any] = {
        "name": "onedrive-sintetico",
        "type": "sharepoint_online",
        "auth": {
            "mode": "delegated",
            "tenant": TEST_TENANT,
            "client_id": TEST_CLIENT_ID,
            "login_host": LOGIN_HOST,
            "scopes": SCOPE,
        },
        "graph": {"base_url": f"https://{GRAPH_HOST}/v1.0"},
        "download_host_suffixes": list(DOWNLOAD_HOST_SUFFIXES),
        "drive": "me",
        "root_folder": "/DataBoar-Sintetico",
        "max_depth": 32,
        "max_file_bytes": 100 * 1024 * 1024,
        "page_size": 200,
        "max_pages_per_folder": 10_000,
        "http_timeout_seconds": 30,
        "throttle_max_wait_seconds": 120,
    }
    target.update(overrides)
    return target
