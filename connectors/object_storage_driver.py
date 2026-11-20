"""Driver contract and driver registry of the ``object_storage`` reader (#2306, task 2306.1).

Source: ``docs/desenho/2306.md``, section 0 ("Camada comum e driver"), revision 3.

The boundary: a driver knows how to *talk* to one provider (address, request authentication,
reading the listing, translating provider errors, display path). The common layer
(``connectors/object_storage_connector.py``, task 2306.2) decides what to do with what the
driver returns and never imports a concrete driver.

The registry keeps a **factory** per driver name. Built-in drivers are seeded by name with a
factory that imports the driver module only when the driver is requested, so importing this
module has no side effect (no network, no optional dependency such as ``botocore``).
"""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal, NamedTuple, Protocol


class ObjectEntry(NamedTuple):
    """One listed object. ``key`` is already decoded by the driver."""

    key: str
    size: (
        int | None
    )  # None when the provider does not report it or the value is invalid


class ListPage(NamedTuple):
    entries: list[ObjectEntry]
    next_token: str | None
    truncated: bool


class PreparedGet(NamedTuple):
    url: str  # absolute; the host is always the one of ``destination()``
    headers: dict[str, str]  # already authenticated for this attempt


class ErrorClass(NamedTuple):
    reason: str  # from the closed set of section 11
    code: str | None  # only when it is in the driver vocabulary
    retryable: bool
    ends_target: bool


@dataclass(frozen=True)
class DriverSettings:
    """Empty base. Each driver returns its own frozen subclass (revision 3).

    The common layer never reads a field of it; it only hands it back to the driver. It never
    holds a credential, so its ``repr`` may go to a DEBUG log.
    """


class DriverConfigError(ValueError):
    """Invalid target configuration for a driver; ``str(exc)`` is a fixed message."""


class DriverProtocolError(ValueError):
    """The provider answered something the driver cannot read; fixed message."""


class ResolvedCredentials(Mapping[str, str]):
    """Credential values read from the environment by the common layer (read-only).

    Keys are the ``credential_keys`` names without ``auth.``; an optional key that is not
    configured is absent (never ``""``). ``repr``/``str`` show only the key names. No value
    equality, no pickling, and :meth:`clear` drops the values (the common layer calls it in
    the ``finally`` of ``run()``).
    """

    __slots__ = ("_values",)

    def __init__(self, values: Mapping[str, str]) -> None:
        raise NotImplementedError("2306.1: ResolvedCredentials")

    def __getitem__(self, key: str) -> str:
        raise NotImplementedError("2306.1: ResolvedCredentials")

    def __iter__(self) -> Iterator[str]:
        raise NotImplementedError("2306.1: ResolvedCredentials")

    def __len__(self) -> int:
        raise NotImplementedError("2306.1: ResolvedCredentials")

    def __repr__(self) -> str:
        raise NotImplementedError("2306.1: ResolvedCredentials")

    __str__ = __repr__

    def __eq__(self, other: object) -> bool:
        raise NotImplementedError("2306.1: ResolvedCredentials")

    def __hash__(self) -> int:
        raise NotImplementedError("2306.1: ResolvedCredentials")

    def __reduce__(self) -> Any:
        raise NotImplementedError("2306.1: ResolvedCredentials")

    def clear(self) -> None:
        raise NotImplementedError("2306.1: ResolvedCredentials")


class StorageDriver(Protocol):
    name: str
    max_page_size: int
    max_key_bytes: int
    credential_keys: tuple[tuple[str, bool], ...]  # (auth.*_from_env key, required?)
    forbidden_inline_keys: frozenset[str]

    def settings(self, cfg: dict[str, Any]) -> DriverSettings: ...

    def destination(self, settings: DriverSettings) -> str: ...

    def destination_host(self, cfg: dict[str, Any]) -> str: ...

    def list_request(
        self,
        settings: DriverSettings,
        creds: ResolvedCredentials,
        prefix: str,
        token: str | None,
        page_size: int,
        now: datetime,
    ) -> PreparedGet: ...

    def parse_list(self, body: bytes) -> ListPage: ...

    def get_request(
        self,
        settings: DriverSettings,
        creds: ResolvedCredentials,
        key: str,
        now: datetime,
    ) -> PreparedGet: ...

    def classify_error(
        self,
        status: int,
        headers: Mapping[str, str],
        body: bytes,
        *,
        during: Literal["list", "get"],
    ) -> ErrorClass: ...

    def display_path(self, settings: DriverSettings, key: str) -> str: ...

    def inventory_identity(self, settings: DriverSettings) -> dict[str, str]: ...


# Inline keys refused for every driver (section 3, revision 2). The loader refuses the union
# of this set and ``driver.forbidden_inline_keys``, minus the driver's own credential keys.
COMMON_FORBIDDEN_INLINE_KEYS = frozenset(
    {
        "pass",
        "password",
        "user",
        "username",
        "token",
        "client_secret",
        "api_key",
        "credentials",
        "profile",
        "pass_from_env",
        "password_from_env",
        "user_from_env",
        "token_from_env",
        "client_secret_from_env",
        "api_key_from_env",
    }
)

# Provider names planned but not delivered yet (section 0).
NOT_AVAILABLE_YET = frozenset({"azure_blob", "gcs"})


def _builtin_s3() -> StorageDriver:
    from connectors.object_storage_s3 import S3Driver

    return S3Driver("s3")


def _builtin_s3_compatible() -> StorageDriver:
    from connectors.object_storage_s3 import S3Driver

    return S3Driver("s3_compatible")


_REGISTRY: dict[str, Callable[[], StorageDriver]] = {
    "s3": _builtin_s3,
    "s3_compatible": _builtin_s3_compatible,
}


def register_driver(name: str, factory: Callable[[], StorageDriver]) -> None:
    raise NotImplementedError("2306.1: register_driver")


def get_driver(name: str) -> StorageDriver:
    """Return a driver instance; ``KeyError`` with a fixed message for an unknown name."""
    raise NotImplementedError("2306.1: get_driver")
