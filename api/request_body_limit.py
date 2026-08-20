"""ASGI cap on request body bytes (Content-Length and chunked transfer)."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

# JSON/config and scan-start bodies: bound memory before the framework parses them.
MAX_REQUEST_BODY_BYTES = 1_000_000
REQUEST_BODY_TOO_LARGE_DETAIL = "Request body too large. Maximum size is 1 MB."

_SCOPE = dict[str, Any]
_Receive = Callable[[], Awaitable[dict[str, Any]]]
_Send = Callable[[dict[str, Any]], Awaitable[None]]


def _content_length(scope: _SCOPE) -> int | None:
    for key, value in scope.get("headers") or []:
        if key.lower() == b"content-length":
            try:
                return int(value)
            except ValueError:
                return None
    return None


async def send_413(send: _Send) -> None:
    """Emit HTTP 413 JSON matching the historic dashboard error body."""
    payload = ('{"detail":"' + REQUEST_BODY_TOO_LARGE_DETAIL + '"}').encode("ascii")
    await send(
        {
            "type": "http.response.start",
            "status": 413,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(payload)).encode("ascii")),
            ],
        }
    )
    await send({"type": "http.response.body", "body": payload})


class RequestBodySizeLimitMiddleware:
    """
    Outermost ASGI gate: reject bodies over ``max_bytes``.

    ``Content-Length`` over the cap returns 413 without calling the app.
    Chunked (or missing length) requests accumulate real ``http.request``
    bytes and abort at the same cap so Starlette never buffers an unbounded body.
    """

    def __init__(
        self,
        app: Callable[..., Awaitable[None]],
        max_bytes: int = MAX_REQUEST_BODY_BYTES,
    ):
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: _SCOPE, receive: _Receive, send: _Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        declared = _content_length(scope)
        if declared is not None and declared > self.max_bytes:
            await send_413(send)
            return

        received = 0
        oversized = False
        response_started = False

        async def limited_receive() -> dict[str, Any]:
            nonlocal received, oversized
            if oversized:
                return {"type": "http.disconnect"}
            message = await receive()
            if message.get("type") == "http.request":
                received += len(message.get("body") or b"")
                if received > self.max_bytes:
                    oversized = True
                    # Do not raise: Starlette maps receive errors to HTTP 400.
                    return {"type": "http.disconnect"}
            return message

        async def gated_send(message: dict[str, Any]) -> None:
            nonlocal response_started
            if oversized:
                if (
                    message.get("type") == "http.response.start"
                    and not response_started
                ):
                    response_started = True
                    await send_413(send)
                return
            if message.get("type") == "http.response.start":
                response_started = True
            await send(message)

        await self.app(scope, limited_receive, gated_send)
        if oversized and not response_started:
            await send_413(send)
