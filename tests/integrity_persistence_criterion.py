"""Criterion for #2253: runtime modules that persist scan results must be signed.

A runtime module that declares a table (a ``__tablename__`` class attribute)
or writes findings or failures (defines ``save_finding`` or ``save_failure``)
is behaviour-critical: the signed integrity manifest must cover it. The legacy
``db/`` package stays outside because no runtime module imports it.
"""

from __future__ import annotations

import ast
from pathlib import Path

RUNTIME_DIRS: tuple[str, ...] = ("core", "api", "report", "utils", "config")
RUNTIME_FILES: tuple[str, ...] = ("main.py",)
PERSISTENCE_FUNCTIONS: frozenset[str] = frozenset({"save_finding", "save_failure"})


def _declares_table(node: ast.ClassDef) -> bool:
    for stmt in node.body:
        if isinstance(stmt, ast.Assign):
            if any(
                isinstance(t, ast.Name) and t.id == "__tablename__"
                for t in stmt.targets
            ):
                return True
        if isinstance(stmt, ast.AnnAssign):
            target = stmt.target
            if isinstance(target, ast.Name) and target.id == "__tablename__":
                return True
    return False


def is_persistence_source(source: str) -> bool:
    """True when the source declares a table or defines a findings/failures writer."""
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.ClassDef) and _declares_table(node):
            return True
        if (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name in PERSISTENCE_FUNCTIONS
        ):
            return True
    return False


def _is_legacy_db(module: str) -> bool:
    return module == "db" or module.startswith("db.")


def imports_legacy_db(source: str) -> bool:
    """True when the source imports the legacy top-level ``db`` package."""
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            if any(_is_legacy_db(alias.name) for alias in node.names):
                return True
        if isinstance(node, ast.ImportFrom) and node.level == 0:
            if _is_legacy_db(node.module or ""):
                return True
    return False


def runtime_module_paths(root: Path) -> list[str]:
    """Repo-relative POSIX paths of every runtime Python module."""
    paths: set[str] = set()
    for folder in RUNTIME_DIRS:
        for path in (root / folder).rglob("*.py"):
            if "__pycache__" in path.parts:
                continue
            paths.add(path.relative_to(root).as_posix())
    for name in RUNTIME_FILES:
        if (root / name).is_file():
            paths.add(name)
    return sorted(paths)


def _read(root: Path, rel: str) -> str:
    return (root / rel).read_text(encoding="utf-8")


def runtime_persistence_modules(root: Path) -> set[str]:
    return {
        rel
        for rel in runtime_module_paths(root)
        if is_persistence_source(_read(root, rel))
    }


def runtime_modules_importing_legacy_db(root: Path) -> set[str]:
    return {
        rel for rel in runtime_module_paths(root) if imports_legacy_db(_read(root, rel))
    }
