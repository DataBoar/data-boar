"""Common layer of the ``object_storage`` reader (epic #2306, task 2306.2).

Source: ``docs/desenho/2306.md`` (revision 5 and the section 7 arbitration), sections 0, 1,
4, 6 to 12 and 14.

The common layer decides scope, limits, network safety, temporary files, findings, failures,
inventory and coverage. It talks to a provider only through the driver contract of
``connectors/object_storage_driver.py`` and never imports a concrete driver (D2306-65).

Skeleton of the ``test:`` commit: the constructor and ``run()`` have the signatures of the
design and raise ``NotImplementedError``. The type is registered (section 4), so the
registry, the engine and the tier gate already resolve to this class.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from datetime import datetime
from typing import Any

from core.connector_registry import register

# Generic keys (revision 6, R6-8); each driver declares its own ``required_keys``.
REQUIRED_KEYS = ["name", "driver"]


class ObjectStorageConnector:
    """Read-only object storage connector (one target, one driver, one pinned host)."""

    def __init__(
        self,
        target_config: dict[str, Any],
        scanner: Any,
        db_manager: Any,
        extensions: Any = None,
        scan_sqlite_as_db: bool = True,
        sample_limit: int = 5,
        file_sample_max_chars: int = 12_000,
        file_passwords: dict[str, Any] | None = None,
        *,
        _transport: Any = None,
        _sleep: Callable[[float], None] = time.sleep,
        _now: Callable[[], datetime] | None = None,
    ) -> None:
        raise NotImplementedError(
            "2306.2: ObjectStorageConnector is not implemented yet"
        )

    def run(self) -> None:
        raise NotImplementedError(
            "2306.2: ObjectStorageConnector.run is not implemented yet"
        )


register("object_storage", ObjectStorageConnector, REQUIRED_KEYS)
