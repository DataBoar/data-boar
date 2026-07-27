"""
Tests that encode SonarQube-style quality rules across Python code so regressions are caught.

- S1192 / literal duplication: constants used instead of repeated string literals (routes, report).
- Regex / S5856: session_id pattern uses \\w with re.ASCII.
- S8415: HTTP status codes 400, 404, 429 documented in OpenAPI (validated in test_routes_responses).
- S3776 cognitive complexity: refactored helpers exist in connector_registry and sql_connector; keep functions in this file under 15 (test_sonarqube_cognitive_complexity_under_threshold).
- No bare except (S5706): key modules do not use bare 'except:'.
- S4423: SSL/TLS contexts use strong protocol (minimum TLS 1.2) where create_default_context is used.
- S3981: length of a collection is always >=0; use ==0 or >0 instead (no len(...) >= 0 in code).
"""

import ast
import re
from pathlib import Path


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


# --- Routes: constants and session pattern (S1192, S5856) ---


def test_routes_uses_session_id_pattern_with_ascii():
    """Session ID validation uses \\w with re.ASCII (concise regex, ASCII-only)."""
    import api.routes as routes

    pattern = getattr(routes, "_SESSION_ID_PATTERN", None)
    assert pattern is not None, "api.routes must define _SESSION_ID_PATTERN"
    assert pattern.flags & re.ASCII, (
        "_SESSION_ID_PATTERN must use re.ASCII so \\w is [a-zA-Z0-9_]"
    )
    assert pattern.fullmatch("a1b2c3d4e5f6_20250101")
    assert not pattern.fullmatch("aaaaaaaaaaa-b")


def test_routes_defines_template_config_constant():
    """Config template name is a constant to avoid string literal duplication (S1192)."""
    import api.routes as routes

    name = getattr(routes, "_TEMPLATE_CONFIG", None)
    assert name is not None, "api.routes must define _TEMPLATE_CONFIG"
    assert name == "config.html"


def test_routes_defines_documented_response_constants():
    """Response codes 429, 404, 400 are declared via constants for OpenAPI (S8415)."""
    import api.routes as routes

    assert hasattr(routes, "_RATE_LIMIT_429") and 429 in getattr(
        routes, "_RATE_LIMIT_429", {}
    )
    assert hasattr(routes, "_NOT_FOUND_404") and 404 in getattr(
        routes, "_NOT_FOUND_404", {}
    )
    assert hasattr(routes, "_SESSION_RESPONSES")
    session_resp = getattr(routes, "_SESSION_RESPONSES", {})
    assert 400 in session_resp and 404 in session_resp


# --- Report generator: column/sheet name constants (S1192) ---


def test_report_generator_defines_recommendation_constants():
    """Report generator uses constants for recommendation sheet columns (S1192)."""
    from report import generator

    expected = (
        "_REC_DATA_PATTERN",
        "_REC_BASE_LEGAL",
        "_REC_RISCO",
        "_REC_RECOMENDACAO",
        "_REC_PRIORIDADE",
    )
    for name in expected:
        assert hasattr(generator, name), f"report.generator must define {name}"


def test_report_generator_defines_trend_constants():
    """Report generator uses constants for trends sheet (S1192)."""
    from report import generator

    expected = (
        "_TREND_THIS_RUN_COUNT",
        "_TREND_PREV_RUN_COUNT",
        "_SHEET_DB_FINDINGS",
        "_SHEET_FS_FINDINGS",
    )
    for name in expected:
        assert hasattr(generator, name), f"report.generator must define {name}"


# --- Connector registry: refactored helpers (S3776 complexity) ---


def test_connector_registry_has_complexity_refactor_helpers():
    """connector_for_target complexity was reduced via _try_get_connector and _resolve_database_connector."""
    from core import connector_registry

    assert hasattr(connector_registry, "_try_get_connector")
    assert callable(getattr(connector_registry, "_try_get_connector"))
    assert hasattr(connector_registry, "_resolve_database_connector")
    assert callable(getattr(connector_registry, "_resolve_database_connector"))


# --- SQL connector: refactored helpers (S3776 complexity) ---


def test_sql_connector_has_discover_helpers():
    """SQLConnector.discover complexity reduced via _get_skip_schemas, _should_skip_schema, _tables_from_schema, _discover_fallback_no_schemas."""
    from connectors import sql_connector

    for name in (
        "_get_skip_schemas",
        "_should_skip_schema",
        "_tables_from_schema",
        "_discover_fallback_no_schemas",
    ):
        assert hasattr(sql_connector, name), (
            f"connectors.sql_connector must define {name}"
        )
        assert callable(getattr(sql_connector, name))


def test_sql_connector_has_process_one_finding():
    """SQLConnector.run complexity reduced via _process_one_finding."""
    from connectors.sql_connector import SQLConnector

    assert hasattr(SQLConnector, "_process_one_finding")
    assert callable(getattr(SQLConnector, "_process_one_finding"))


# --- No bare except (S5706): key modules ---


def _has_bare_except(tree: ast.AST) -> list[tuple[int, str]]:
    """Return list of (lineno, handler_repr) for bare except: clauses."""
    result = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            if node.type is None and node.name is None:
                result.append((node.lineno, "except:"))
            elif node.type is None:
                result.append((node.lineno, "except ... :"))
    return result


def test_api_routes_no_bare_except():
    """api.routes must not use bare 'except:' (S5706)."""
    path = _project_root() / "api" / "routes.py"
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    bare = _has_bare_except(tree)
    assert not bare, f"api/routes.py has bare except at line(s) {[b[0] for b in bare]}"


def test_core_engine_no_bare_except():
    """core.engine must not use bare 'except:' (S5706)."""
    path = _project_root() / "core" / "engine.py"
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    bare = _has_bare_except(tree)
    assert not bare, f"core/engine.py has bare except at line(s) {[b[0] for b in bare]}"


def test_config_loader_no_bare_except():
    """config.loader must not use bare 'except:' (S5706)."""
    path = _project_root() / "config" / "loader.py"
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    bare = _has_bare_except(tree)
    assert not bare, (
        f"config/loader.py has bare except at line(s) {[b[0] for b in bare]}"
    )


# --- S4423: Strong SSL/TLS protocol (no weak defaults) ---


def test_ssl_create_default_context_uses_minimum_tls_version():
    """Any Python file that uses ssl.create_default_context() must set minimum_version (S4423)."""
    root = _project_root()
    exclude_dirs = {
        ".cursor",
        ".git",
        ".locust_env",
        ".venv",
        "venv",
        "__pycache__",
        "node_modules",
        "data-boar",
        "_audit_data-boar",
    }
    violations: list[Path] = []
    for path in root.rglob("*.py"):
        try:
            rel = path.relative_to(root)
        except ValueError:
            continue
        if any(part in exclude_dirs for part in rel.parts):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if "ssl.create_default_context()" not in text:
            continue
        # Same file must enforce strong protocol (TLS 1.2+)
        if "minimum_version" not in text or "TLSVersion" not in text:
            violations.append(path)
    assert not violations, (
        "S4423: these files use ssl.create_default_context() but do not set minimum_version (e.g. "
        "ctx.minimum_version = ssl.TLSVersion.TLSv1_2): "
        + ", ".join(str(p.relative_to(root)) for p in violations)
    )


# --- S3981: No redundant len(...) >= 0 (use ==0 or >0) ---

_S3981_EXCLUDE_DIRS = {
    ".cursor",
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    # Nested duplicate worktree (see .gitignore /data-boar/); not part of the product tree.
    "data-boar",
    "_audit_data-boar",
}
_S3981_PATTERN = re.compile(r"len\s*\([^)]*\)\s*>=\s*0")


def _s3981_should_skip_path(path: Path, root: Path) -> bool:
    """True if path is under an excluded directory (S3981 scan)."""
    try:
        rel = path.relative_to(root)
    except ValueError:
        return True
    return any(part in _S3981_EXCLUDE_DIRS for part in rel.parts)


def _s3981_violations_in_file(path: Path, root: Path) -> list[tuple[Path, int, str]]:
    """Return (path, lineno, line) for lines that violate S3981 (len(...) >= 0 in code)."""
    result: list[tuple[Path, int, str]] = []
    for lineno, line in enumerate(
        path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1
    ):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if not _S3981_PATTERN.search(line):
            continue
        if (
            stripped.startswith(("assert ", "if ", "elif ", "while "))
            or " return " in line
        ):
            result.append((path, lineno, line.strip()))
    return result


def test_no_len_ge_zero_s3981():
    """No Python file must use len(...) >= 0; use ==0 or >0 instead (S3981)."""
    root = _project_root()
    violations: list[tuple[Path, int, str]] = []
    for path in root.rglob("*.py"):
        if _s3981_should_skip_path(path, root):
            continue
        violations.extend(_s3981_violations_in_file(path, root))
    assert not violations, (
        "S3981: length is always >=0; use ==0 or >0. Violations: "
        + "; ".join(
            f"{p.relative_to(root)}:{ln} {snippet}" for p, ln, snippet in violations
        )
    )


# --- S3776: Cognitive complexity cap (keep this file's functions under threshold) ---

_S3776_MAX_COMPLEXITY = 15
_S3776_COMPLEXITY_NODES = (
    ast.If,
    ast.For,
    ast.While,
    ast.With,
    ast.ExceptHandler,
    ast.BoolOp,
)


def _ast_complexity_score(node: ast.AST) -> int:
    """Approximate cognitive complexity: count control flow and boolean branches (S3776 proxy)."""
    total = 0
    for child in ast.walk(node):
        if isinstance(child, _S3776_COMPLEXITY_NODES):
            total += 1
    return total


def test_sonarqube_cognitive_complexity_under_threshold():
    """No function in this file must exceed S3776 cognitive complexity threshold (extract helpers if needed)."""
    path = Path(__file__).resolve()
    tree = ast.parse(path.read_text(encoding="utf-8"))
    over: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            score = _ast_complexity_score(node)
            if score > _S3776_MAX_COMPLEXITY:
                over.append((node.name, score))
    assert not over, (
        f"S3776: keep cognitive complexity <={_S3776_MAX_COMPLEXITY}. "
        f"Over threshold: {', '.join(f'{name}({s})' for name, s in over)}. Extract helpers to reduce."
    )
