"""Toy ``object_storage`` driver and its toy backend (epic #2306, task 2306.3).

Source: ``docs/desenho/2306.md``, section 0 ("Camada comum e driver") and DEC-10. The toy
driver is the proof that the common layer runs a driver other than ``s3`` without any change:
a different listing format (JSON), a page of 2 entries, a ``toy://`` display path and
authentication by one fixed header. The dev tests D-64 to D-68 use it; no acceptance test
(A-1 to A-24) does.

Nothing here touches the network: ``ToyStore`` is an ``httpx.MockTransport`` backend. The
contract types live in ``connectors/object_storage_driver.py`` (design revision 3):
``ToySettings`` inherits the frozen ``DriverSettings`` base (the common layer never reads it),
and ``creds`` is a read-only ``ResolvedCredentials`` read by name (``creds["token_from_env"]``).
The classes and NamedTuples are imported at module level (they exist in the skeleton). What
still depends on 2306.1: building a ``ResolvedCredentials`` (its constructor is a stub today),
``register_driver`` and ``get_driver``, so ``register_toy_driver`` imports ``register_driver``
inside the function and only works after 2306.1.

The wire logic is in pure helpers (``toy_list_url``, ``toy_parse_listing``,
``toy_classify_status``) so it is testable before the contract module exists.
"""

from __future__ import annotations

import json
import re
import secrets
import urllib.parse
from dataclasses import dataclass
from collections.abc import Mapping
from datetime import datetime
from typing import Any, Literal

import httpx

from connectors.object_storage_driver import (
    DriverConfigError,
    DriverProtocolError,
    DriverSettings,
    ErrorClass,
    ListPage,
    ObjectEntry,
    PreparedGet,
    ResolvedCredentials,
)

TOY_HOST = "toy.lab.example"
TOY_PAGE_SIZE = 2
TOY_AUTH_HEADER = "X-Toy-Auth"
TOY_TOKEN_ENV = "DATA_BOAR_TOY_TOKEN"
_CONTAINER_RE = re.compile(r"^[a-z0-9-]{3,30}$")


def new_toy_token() -> str:
    """Synthetic token, built at run time (no literal with the shape of a secret)."""
    return "SYNTHTK" + secrets.token_hex(12)


# ----------------------------------------------------------------------------
# Pure wire helpers
# ----------------------------------------------------------------------------


def toy_list_url(
    host: str, container: str, prefix: str, token: str | None, page_size: int
) -> str:
    query = [("prefix", prefix), ("limit", str(min(page_size, TOY_PAGE_SIZE)))]
    if token:
        query.append(("cursor", token))
    return f"https://{host}/v1/{container}/list?{urllib.parse.urlencode(query)}"


def toy_blob_url(host: str, container: str, key: str) -> str:
    return f"https://{host}/v1/{container}/blob/{urllib.parse.quote(key, safe='/')}"


def toy_parse_listing(
    body: bytes,
) -> tuple[list[tuple[str | None, int | None]], str | None, bool]:
    """(entries as (key, size), next cursor, truncated). ``ValueError`` on a malformed body.

    Design revision 5: an entry the driver cannot use (name not a string, or ``bytes`` absent,
    not an integer or negative) comes back with ``key=None`` and the common layer counts it
    as ``invalid_key``; the other entries of the page are normal.
    """
    try:
        doc = json.loads(body)
        items = doc["items"]
        nxt = doc["next"]
        if not isinstance(items, list) or not (nxt is None or isinstance(nxt, str)):
            raise ValueError("unexpected listing shape")
        entries: list[tuple[str | None, int | None]] = []
        for it in items:
            name = it.get("name")
            size = it.get("bytes")
            bad_size = not isinstance(size, int) or isinstance(size, bool) or size < 0
            if not isinstance(name, str) or bad_size:
                entries.append((None, None))
            else:
                entries.append((name, size))
    except (KeyError, TypeError, AttributeError, json.JSONDecodeError) as exc:
        raise ValueError("malformed toy listing") from exc
    return entries, nxt, nxt is not None


def toy_classify_status(
    status: int, *, during: str
) -> tuple[str, str | None, bool, bool, str]:
    """(reason, code, retryable, ends_target, message): fixed texts of the toy driver."""
    if status == 401:
        return "auth_failed", None, False, True, "toy provider refused the token"
    if status == 403:
        if during == "list":
            return "permission_denied", None, False, True, "toy listing denied"
        return "download_failed", None, False, False, "toy blob denied"
    if status == 404:
        if during == "list":
            return "not_found", None, False, True, "toy container not found"
        return "download_failed", None, False, False, "toy blob not found"
    if status == 429 or status >= 500:
        if during == "list":
            return "unreachable", None, True, False, "toy provider unavailable"
        return "download_failed", None, True, False, "toy blob unavailable"
    if during == "list":
        return "protocol_error", None, False, False, f"toy error HTTP {status}"
    return "download_failed", None, False, False, f"toy error HTTP {status}"


# ----------------------------------------------------------------------------
# The toy provider backend (MockTransport)
# ----------------------------------------------------------------------------


class ToyStore:
    """A toy provider: JSON listing in pages of 2, blobs, one fixed auth header."""

    def __init__(
        self,
        container: str,
        objects: dict[str, bytes],
        token: str,
        host: str = TOY_HOST,
    ) -> None:
        self.container = container
        self.objects = dict(objects)
        self.token = token
        self.host = host
        self.requests: list[tuple[str, str, dict[str, str]]] = []
        self.violations: list[str] = []
        self.transport = httpx.MockTransport(self._handle)

    def _handle(self, request: httpx.Request) -> httpx.Response:
        headers = {k.lower(): v for k, v in request.headers.items()}
        self.requests.append((request.method, str(request.url), headers))
        if request.url.host != self.host:
            self.violations.append(f"unexpected host {request.url.host}")
            return httpx.Response(599)
        if headers.get(TOY_AUTH_HEADER.lower()) != self.token:
            return httpx.Response(401, json={"error": "unauthorized"})
        base = f"/v1/{self.container}/"
        path = request.url.raw_path.decode("ascii").partition("?")[0]
        if not path.startswith(base):
            return httpx.Response(404, json={"error": "no such container"})
        tail = path[len(base) :]
        if tail == "list":
            params = dict(urllib.parse.parse_qsl(request.url.query.decode("ascii")))
            prefix = params.get("prefix", "")
            limit = min(int(params.get("limit", TOY_PAGE_SIZE)), TOY_PAGE_SIZE)
            start = int(params["cursor"].removeprefix("c")) if "cursor" in params else 0
            names = sorted(k for k in self.objects if k.startswith(prefix))
            page = names[start : start + limit]
            more = start + limit < len(names)
            return httpx.Response(
                200,
                json={
                    "items": [{"name": n, "bytes": len(self.objects[n])} for n in page],
                    "next": f"c{start + limit}" if more else None,
                },
            )
        if tail.startswith("blob/"):
            key = urllib.parse.unquote(tail[len("blob/") :], errors="strict")
            if key not in self.objects:
                return httpx.Response(404, json={"error": "no such blob"})
            return httpx.Response(200, content=self.objects[key])
        return httpx.Response(400, json={"error": "bad request"})


# ----------------------------------------------------------------------------
# The toy driver (implements the StorageDriver protocol of section 0)
# ----------------------------------------------------------------------------


@dataclass(frozen=True)
class ToySettings(DriverSettings):
    """Frozen settings of the toy driver (a ``DriverSettings`` subclass, design revision 3)."""

    host: str
    container: str


class ToyDriver:
    name = "toy"
    max_page_size = TOY_PAGE_SIZE
    max_key_bytes = 256
    credential_keys: tuple[tuple[str, bool], ...] = (("token_from_env", True),)
    forbidden_inline_keys = frozenset({"toy_token", "toy_secret"})
    # Design revision 5: the toy uses ``host`` (the S3 drivers refuse it as misnamed), so it
    # declares only its own wrong spellings. The credential lives in ``auth.token_from_env``;
    # ``token_from_env`` at target level is refused by the loader (D-83).
    misnamed_keys: Mapping[str, str] = {"url": "use host", "endpoint": "use host"}

    def settings(self, cfg: dict[str, Any]) -> ToySettings:
        host = cfg.get("host")
        container = cfg.get("container")
        if not isinstance(host, str) or not host:
            raise DriverConfigError("toy host is required")
        if not isinstance(container, str) or not _CONTAINER_RE.match(container):
            raise DriverConfigError("toy container is invalid")
        return ToySettings(host.lower(), container)

    def destination(self, settings: ToySettings) -> str:
        return f"https://{settings.host}"

    def destination_host(self, cfg: dict[str, Any]) -> str:
        host = cfg.get("host")
        return host.lower() if isinstance(host, str) else ""

    @staticmethod
    def _token(creds: ResolvedCredentials) -> str:
        # Read by name, as the design says (revision 3); the driver keeps no reference.
        return creds["token_from_env"]

    def list_request(
        self,
        settings: ToySettings,
        creds: ResolvedCredentials,
        prefix: str,
        token: str | None,
        page_size: int,
        now: datetime,
    ) -> PreparedGet:
        url = toy_list_url(settings.host, settings.container, prefix, token, page_size)
        return PreparedGet(url, {TOY_AUTH_HEADER: self._token(creds)})

    def parse_list(self, body: bytes) -> ListPage:
        try:
            entries, nxt, truncated = toy_parse_listing(body)
        except ValueError as exc:
            raise DriverProtocolError("malformed listing response") from exc
        return ListPage([ObjectEntry(k, s) for k, s in entries], nxt, truncated)

    def get_request(
        self, settings: ToySettings, creds: ResolvedCredentials, key: str, now: datetime
    ) -> PreparedGet:
        return PreparedGet(
            toy_blob_url(settings.host, settings.container, key),
            {TOY_AUTH_HEADER: self._token(creds)},
        )

    def classify_error(
        self,
        status: int,
        headers: Mapping[str, str],
        body: bytes,
        *,
        during: Literal["list", "get"],
    ) -> ErrorClass:
        return ErrorClass(*toy_classify_status(status, during=during))

    def display_path(self, settings: ToySettings, key: str) -> str:
        return f"toy://{settings.container}/{key}"

    def inventory_identity(self, settings: ToySettings) -> dict[str, str]:
        return {
            "product": "ToyStore",
            "protocol_or_api_version": "toy-json-1",
            "engine": "toy",
            "container": settings.container,
        }


def register_toy_driver() -> None:
    """Register the toy driver in the driver registry (needs task 2306.1)."""
    from connectors.object_storage_driver import register_driver

    register_driver("toy", ToyDriver)
