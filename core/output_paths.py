"""Pre-flight creation of configured output directories before scan or report."""

from __future__ import annotations

import errno
from pathlib import Path
from typing import Any


class OutputPathError(OSError):
    """Cannot create or access a configured output directory."""


def output_directory_specs(
    config: dict[str, Any], *, sqlite_path: str | None = None
) -> list[tuple[str, Path]]:
    """
    Return (config label, directory path) pairs that must exist before scan/report.

    Covers ``report.output_dir``, the parent of ``sqlite_path``, and (when
    ``learned_patterns.enabled``) the parent of ``learned_patterns.output_file``.
    """
    specs: list[tuple[str, Path]] = []

    report_dir = (config.get("report") or {}).get("output_dir", ".")
    specs.append(("report.output_dir", Path(report_dir)))

    db = sqlite_path or config.get("sqlite_path", "audit_results.db")
    specs.append(("sqlite_path directory", Path(db).expanduser().parent))

    lp = config.get("learned_patterns") or {}
    if lp.get("enabled", False):
        out_file = Path(lp.get("output_file", "learned_patterns.yaml"))
        specs.append(
            ("learned_patterns.output_file directory", out_file.expanduser().parent)
        )

    return specs


def ensure_config_output_directories(
    config: dict[str, Any], *, sqlite_path: str | None = None
) -> list[str]:
    """
    ``mkdir -p`` for configured output directories (process umask applies).

    Returns human-readable messages for paths created in this call.
    Raises ``OutputPathError`` when a path cannot be created or is not a directory.
    """
    created: list[str] = []
    seen: set[Path] = set()

    for label, raw in output_directory_specs(config, sqlite_path=sqlite_path):
        path = Path(raw).expanduser()
        try:
            resolved = path.resolve()
        except OSError:
            resolved = path

        if resolved in seen:
            continue
        seen.add(resolved)

        if path.exists():
            if not path.is_dir():
                raise OutputPathError(
                    f"{label} ({path}): path exists but is not a directory"
                )
            continue

        try:
            path.mkdir(parents=True, exist_ok=True)
            created.append(f"{label}: created {path}")
        except PermissionError as e:
            raise OutputPathError(
                f"Cannot create {label} ({path}): permission denied. "
                "Ensure the process user can write to the parent directory."
            ) from e
        except OSError as e:
            if e.errno == errno.EACCES:
                raise OutputPathError(
                    f"Cannot create {label} ({path}): permission denied."
                ) from e
            raise OutputPathError(f"Cannot create {label} ({path}): {e}") from e

    return created
