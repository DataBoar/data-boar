"""AST helpers for the #1722 str(e) log-call gate (not a pytest module)."""

from __future__ import annotations

import ast
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

LOG_METHODS = frozenset(
    {"debug", "info", "warning", "error", "exception", "critical", "log"}
)
STR_E_NAMES = frozenset({"e", "exc", "err", "error", "exception"})


@dataclass(frozen=True)
class StrESite:
    path: str  # posix relative to repo root
    lineno: int
    kind: str  # logger | persist | inert
    func: str
    snippet: str


def _is_str_e_call(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    if not isinstance(func, ast.Name) or func.id != "str":
        return False
    if len(node.args) != 1:
        return False
    arg = node.args[0]
    return isinstance(arg, ast.Name) and arg.id in STR_E_NAMES


def _attr_root_name(func: ast.Attribute) -> str | None:
    cur: ast.AST = func.value
    while isinstance(cur, ast.Attribute):
        cur = cur.value
    if isinstance(cur, ast.Name):
        return cur.id
    if isinstance(cur, ast.Call) and isinstance(cur.func, ast.Name):
        return cur.func.id
    return None


def _is_log_call(node: ast.AST) -> bool:
    """True for get_logger()/logger.* log methods — not Streamlit ``st.error``."""
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    if not isinstance(func, ast.Attribute):
        return False
    if func.attr not in LOG_METHODS:
        return False
    root = _attr_root_name(func)
    if root in {"st", "print"}:
        return False
    return True


def _is_save_failure_call(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    if isinstance(func, ast.Attribute):
        return func.attr == "save_failure"
    if isinstance(func, ast.Name):
        return func.id == "save_failure"
    return False


def _parent_map(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    parents: dict[ast.AST, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent
    return parents


def _enclosing_function(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> str:
    cur: ast.AST | None = node
    while cur is not None:
        parent = parents.get(cur)
        if parent is None:
            return "<module>"
        if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return parent.name
        cur = parent
    return "<module>"


def classify_str_e_in_source(source: str, *, rel_path: str) -> list[StrESite]:
    tree = ast.parse(source)
    parents = _parent_map(tree)
    sites: list[StrESite] = []
    for node in ast.walk(tree):
        if not _is_str_e_call(node):
            continue
        kind = "inert"
        cur: ast.AST | None = node
        while cur is not None:
            parent = parents.get(cur)
            if parent is None:
                break
            if _is_log_call(parent):
                kind = "logger"
                break
            if _is_save_failure_call(parent):
                kind = "persist"
                break
            cur = parent
        snippet = ast.get_source_segment(source, node) or "str(...)"
        sites.append(
            StrESite(
                path=rel_path,
                lineno=node.lineno,
                kind=kind,
                func=_enclosing_function(node, parents),
                snippet=snippet,
            )
        )
    return sites


SCAN_DIRS: tuple[str, ...] = ("connectors", "core", "app", "api")


def iter_python_files(root: Path, rel_dirs: tuple[str, ...]) -> Iterator[Path]:
    for rel in rel_dirs:
        base = root / rel
        if not base.is_dir():
            continue
        yield from sorted(base.rglob("*.py"))


def scan_tree(repo_root: Path, rel_dirs: tuple[str, ...]) -> list[StrESite]:
    out: list[StrESite] = []
    for path in iter_python_files(repo_root, rel_dirs):
        rel = path.relative_to(repo_root).as_posix()
        text = path.read_text(encoding="utf-8")
        try:
            out.extend(classify_str_e_in_source(source=text, rel_path=rel))
        except SyntaxError:
            continue
    return out
