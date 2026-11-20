"""Driver contract and driver registry of the ``object_storage`` reader (#2306, task 2306.1).

Source: ``docs/desenho/2306.md``, section 0 ("Camada comum e driver"), revision 3.

The boundary: a driver knows how to *talk* to one provider (address, request authentication,
reading the listing, translating provider errors, display path). The common layer
(``connectors/object_storage_connector.py``, task 2306.2) decides what to do with what the
driver returns and never imports a concrete driver.

The registry keeps a **factory** per driver name. Built-in drivers are seeded by name with a
factory that imports the driver module only when the driver is requested, so importing this
module has no side effect (no network).
"""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal, NamedTuple, Protocol


class ObjectEntry(NamedTuple):
    """One listed object (revision 5).

    ``key`` is already decoded by the driver. ``None`` means the key does not decode or the
    entry is invalid for the driver; the common layer counts it as ``invalid_key``.
    ``size`` is ``None`` when the provider does not report the size.
    """

    key: str | None
    size: int | None


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
    # Fixed driver text, recorded as is (revision 5): fixed phrases of the driver, validated
    # config values and a code of its vocabulary; never server body, header or URL text.
    message: str


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
        self._values: dict[str, str] = {str(k): str(v) for k, v in values.items()}

    def __getitem__(self, key: str) -> str:
        return self._values[key]

    def __iter__(self) -> Iterator[str]:
        return iter(list(self._values))

    def __len__(self) -> int:
        return len(self._values)

    def __repr__(self) -> str:
        return f"<ResolvedCredentials redacted keys={sorted(self._values)}>"

    __str__ = __repr__

    def __eq__(self, other: object) -> bool:
        return self is other

    def __hash__(self) -> int:
        return id(self)

    def __reduce__(self) -> Any:
        raise TypeError("ResolvedCredentials cannot be pickled or copied")

    def __reduce_ex__(self, protocol: Any) -> Any:
        raise TypeError("ResolvedCredentials cannot be pickled or copied")

    def __copy__(self) -> ResolvedCredentials:
        raise TypeError("ResolvedCredentials cannot be pickled or copied")

    def __deepcopy__(self, memo: Any) -> ResolvedCredentials:
        raise TypeError("ResolvedCredentials cannot be pickled or copied")

    def clear(self) -> None:
        for key in list(self._values):
            self._values[key] = ""
        self._values.clear()


class StorageDriver(Protocol):
    name: str
    max_page_size: int
    max_key_bytes: int
    credential_keys: tuple[tuple[str, bool], ...]  # (auth.*_from_env key, required?)
    forbidden_inline_keys: frozenset[str]
    misnamed_keys: Mapping[str, str]  # destination key under another name -> hint

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


# Inline keys refused for every driver (section 3, revision 2). At the ``auth`` level the
# loader refuses (this set | driver.forbidden_inline_keys) - names of driver.credential_keys;
# at the target level nothing is subtracted (revision 5).
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
    """Register (or replace) the factory of a driver; the factory is not called here."""
    if not isinstance(name, str) or not name or not callable(factory):
        raise ValueError(
            "register_driver needs a non-empty name and a callable factory"
        )
    _REGISTRY[name] = factory


def get_driver(name: str) -> StorageDriver:
    """Return a new driver instance; ``KeyError`` with a fixed message for an unknown name.

    ``args[0]`` of the ``KeyError`` is the message of section 0: planned providers give
    "driver <x> is not available yet"; any other value gives the registry names, sorted.
    The value itself is never echoed (only the fixed planned names are).
    """
    factory = _REGISTRY.get(name) if isinstance(name, str) else None
    if factory is not None:
        return factory()
    if isinstance(name, str) and name in NOT_AVAILABLE_YET:
        raise KeyError(f"driver {name} is not available yet")
    raise KeyError("driver must be one of: " + ", ".join(sorted(_REGISTRY)))
