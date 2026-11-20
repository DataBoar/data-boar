"""Toy ``object_storage`` driver and its toy backend (epic #2306, task 2306.3).

Source: ``docs/desenho/2306.md``, section 0 ("Camada comum e driver") and DEC-10. The toy
driver is the proof that the common layer runs a driver other than ``s3`` without any change:
a different listing format (JSON), a page of 2 entries, a ``toy://`` display path and
authentication by one fixed header. The dev tests D-64 to D-68 use it; no acceptance test
(A-1 to A-24) does.

Nothing here touches the network: ``ToyStore`` is an ``httpx.MockTransport`` backend. The
contract types (``ObjectEntry``, ``ListPage``, ``PreparedGet``, ``ErrorClass``) live in
``connectors/object_storage_driver.py``, which does not exist before task 2306.1, so they are
imported inside the methods and this module stays importable today. The shape of
``DriverSettings`` and of ``creds`` is not fixed by section 0: the toy keeps both as plain,
documented values (``ToySettings`` and a mapping from the ``credential_keys`` name to the
value) and the dev adjusts the two spots marked ``CONTRACT-GAP`` if the real shape differs.

The wire logic is in pure helpers (``toy_list_url``, ``toy_parse_listing``,
``toy_classify_status``) so it is testable before the contract module exists.
"""

from __future__ import annotations

import json
import re
import secrets
import urllib.parse
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping

import httpx

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
) -> tuple[list[tuple[str, int | None]], str | None, bool]:
    """(entries as (key, size), next cursor, truncated). ``ValueError`` on a malformed body."""
    try:
        doc = json.loads(body)
        items = doc["items"]
        nxt = doc["next"]
        if not isinstance(items, list) or not (nxt is None or isinstance(nxt, str)):
            raise ValueError("unexpected listing shape")
        entries: list[tuple[str, int | None]] = []
        for it in items:
            size = it.get("bytes")
            entries.append(
                (it["name"], size if isinstance(size, int) and size >= 0 else None)
            )
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError("malformed toy listing") from exc
    return entries, nxt, nxt is not None


def toy_classify_status(
    status: int, *, during: str
) -> tuple[str, str | None, bool, bool]:
    """(reason, code, retryable, ends_target) for the toy protocol."""
    if status == 401:
        return "auth_failed", None, False, True
    if status == 403:
        return (
            ("permission_denied" if during == "list" else "download_failed"),
            None,
            False,
            during == "list",
        )
    if status == 404:
        return (
            ("not_found" if during == "list" else "download_failed"),
            None,
            False,
            during == "list",
        )
    if status == 429 or status >= 500:
        return (
            ("unreachable" if during == "list" else "download_failed"),
            None,
            True,
            False,
        )
    return (
        ("protocol_error" if during == "list" else "download_failed"),
        None,
        False,
        False,
    )


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
class ToySettings:
    """CONTRACT-GAP: stands in for ``DriverSettings`` (its shape is not fixed by section 0)."""

    host: str
    container: str


class ToyDriver:
    name = "toy"
    max_page_size = TOY_PAGE_SIZE
    max_key_bytes = 256
    credential_keys: tuple[tuple[str, bool], ...] = (("token_from_env", True),)
    forbidden_inline_keys = frozenset({"toy_token", "toy_secret"})

    def settings(self, cfg: dict[str, Any]) -> ToySettings:
        from connectors.object_storage_driver import DriverConfigError

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
    def _token(creds: Any) -> str:
        # CONTRACT-GAP: ``creds`` is read as a mapping keyed by the ``credential_keys`` name.
        return str(creds["token_from_env"])

    def list_request(
        self,
        settings: ToySettings,
        creds: Mapping[str, str],
        prefix: str,
        token: str | None,
        page_size: int,
        now: datetime,
    ) -> Any:
        from connectors.object_storage_driver import PreparedGet

        url = toy_list_url(settings.host, settings.container, prefix, token, page_size)
        return PreparedGet(url, {TOY_AUTH_HEADER: self._token(creds)})

    def parse_list(self, body: bytes) -> Any:
        from connectors.object_storage_driver import (
            DriverProtocolError,
            ListPage,
            ObjectEntry,
        )

        try:
            entries, nxt, truncated = toy_parse_listing(body)
        except ValueError as exc:
            raise DriverProtocolError("malformed listing response") from exc
        return ListPage([ObjectEntry(k, s) for k, s in entries], nxt, truncated)

    def get_request(
        self, settings: ToySettings, creds: Mapping[str, str], key: str, now: datetime
    ) -> Any:
        from connectors.object_storage_driver import PreparedGet

        return PreparedGet(
            toy_blob_url(settings.host, settings.container, key),
            {TOY_AUTH_HEADER: self._token(creds)},
        )

    def classify_error(
        self, status: int, headers: Mapping[str, str], body: bytes, *, during: str
    ) -> Any:
        from connectors.object_storage_driver import ErrorClass

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
