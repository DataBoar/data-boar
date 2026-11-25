"""Criterion for #2253: runtime modules that persist scan results must be signed.

A runtime module that declares a table (a ``__tablename__`` class attribute)
or writes findings or failures (defines ``save_finding`` or ``save_failure``)
is behaviour-critical: the signed integrity manifest must cover it. The legacy
``db/`` package stays outside because no runtime module imports it.
"""

from __future__ import annotations

from pathlib import Path

RUNTIME_DIRS: tuple[str, ...] = ("core", "api", "report", "utils", "config")
RUNTIME_FILES: tuple[str, ...] = ("main.py",)
PERSISTENCE_FUNCTIONS: frozenset[str] = frozenset({"save_finding", "save_failure"})


def is_persistence_source(source: str) -> bool:
    raise NotImplementedError


def imports_legacy_db(source: str) -> bool:
    raise NotImplementedError


def runtime_module_paths(root: Path) -> list[str]:
    raise NotImplementedError


def runtime_persistence_modules(root: Path) -> set[str]:
    raise NotImplementedError


def runtime_modules_importing_legacy_db(root: Path) -> set[str]:
    raise NotImplementedError
