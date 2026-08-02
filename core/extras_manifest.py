"""EXTRAS_MANIFEST — optional-deps inventory for artifacts and ``--check-extras`` (#1401).

Source of truth for *which extras exist* is ``pyproject.toml``
``[project.optional-dependencies]``. ``in_artifact`` is set by probing imports
at image build (or locally with ``--probe``), not by hand-editing package lists.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import tomllib
from pathlib import Path
from typing import Any

# Base image installs these optional-dependency groups only (lean container; #1399/#1400).
IMAGE_BASE_EXTRAS: frozenset[str] = frozenset({"sql-community", "mssql", "oracle"})

# Package name → importable top-level module (when they differ).
_PACKAGE_IMPORT_ALIASES: dict[str, str] = {
    "psycopg2-binary": "psycopg2",
    "pillow-heif": "pillow_heif",
    "snowflake-connector-python": "snowflake.connector",
    "sentence-transformers": "sentence_transformers",
    "gitpython": "git",
    "webdavclient3": "webdav3.client",
    "requests_ntlm": "requests_ntlm",
    "mysqlclient": "MySQLdb",
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _requirement_name(req: str) -> str:
    raw = req.strip()
    for sep in ("[", ";", ">", "<", "=", "!", "~", " "):
        if sep in raw:
            raw = raw.split(sep, 1)[0]
    return raw.strip()


def module_for_package(package: str) -> str:
    name = _requirement_name(package)
    if name in _PACKAGE_IMPORT_ALIASES:
        return _PACKAGE_IMPORT_ALIASES[name]
    return name.replace("-", "_")


def modules_for_extra(requirements: list[str]) -> list[str]:
    seen: list[str] = []
    for req in requirements:
        mod = module_for_package(req)
        if mod not in seen:
            seen.append(mod)
    return seen


def _module_available(module: str) -> bool:
    try:
        return importlib.util.find_spec(module) is not None
    except (ModuleNotFoundError, ValueError):
        return False


def _module_origin(module: str) -> str:
    """Where an importable module lives: ``/extras``, ``imagem``, or ``ambiente``."""
    try:
        spec = importlib.util.find_spec(module)
    except (ModuleNotFoundError, ValueError):
        return "—"
    if spec is None or not spec.origin:
        return "—"
    origin = str(spec.origin).replace("\\", "/")
    if "/extras/" in origin or origin.startswith("/extras"):
        return "/extras"
    if origin.startswith("/app/") or "/site-packages/" in origin:
        return "imagem" if "/usr/local/" in origin or "/app/" in origin else "ambiente"
    return "ambiente"


def read_optional_dependencies(pyproject: Path | None = None) -> dict[str, list[str]]:
    path = pyproject or (repo_root() / "pyproject.toml")
    with path.open("rb") as handle:
        data = tomllib.load(handle)
    raw = data.get("project", {}).get("optional-dependencies") or {}
    return {str(k): list(v) for k, v in raw.items()}


def expected_abi_tokens() -> list[str]:
    """CPython tag tokens this interpreter accepts (e.g. ``cp314``, ``cp314t``)."""
    major, minor = sys.version_info.major, sys.version_info.minor
    base = f"cp{major}{minor}"
    tokens = [base]
    gil_on = True
    if hasattr(sys, "_is_gil_enabled"):
        try:
            gil_on = bool(sys._is_gil_enabled())
        except Exception:  # noqa: BLE001 — defensive on exotic builds
            gil_on = True
    if not gil_on:
        tokens.append(f"{base}t")
    return tokens


def build_manifest(
    *,
    pyproject: Path | None = None,
    probe: bool = False,
) -> dict[str, Any]:
    extras_raw = read_optional_dependencies(pyproject)
    extras: dict[str, Any] = {}
    for name, reqs in sorted(extras_raw.items()):
        modules = modules_for_extra(reqs)
        present = [_module_available(m) for m in modules]
        if probe:
            in_artifact = all(present) if modules else False
        else:
            in_artifact = name in IMAGE_BASE_EXTRAS
        extras[name] = {
            "packages": list(reqs),
            "modules": modules,
            "in_artifact": bool(in_artifact),
            "modules_present": present if probe else None,
        }
    return {
        "schema_version": 1,
        "source": "pyproject.toml [project.optional-dependencies]",
        "python": f"{sys.version_info.major}.{sys.version_info.minor}",
        "abi_tokens": expected_abi_tokens(),
        "image_base_extras": sorted(IMAGE_BASE_EXTRAS),
        "extras": extras,
    }


def write_manifest(
    path: Path,
    *,
    pyproject: Path | None = None,
    probe: bool = True,
) -> dict[str, Any]:
    manifest = build_manifest(pyproject=pyproject, probe=probe)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return manifest


def manifest_candidates(explicit: Path | None = None) -> list[Path]:
    root = repo_root()
    out: list[Path] = []
    if explicit is not None:
        out.append(explicit)
    out.extend(
        [
            Path("/app/EXTRAS_MANIFEST.json"),
            root / "EXTRAS_MANIFEST.json",
            Path(__file__).resolve().parent / "EXTRAS_MANIFEST.json",
        ]
    )
    return out


def load_manifest(
    path: Path | None = None, *, probe_if_missing: bool = True
) -> dict[str, Any]:
    for candidate in manifest_candidates(path):
        if candidate.is_file():
            return json.loads(candidate.read_text(encoding="utf-8"))
    if probe_if_missing:
        return build_manifest(probe=True)
    raise FileNotFoundError("EXTRAS_MANIFEST.json not found")


def assert_in_artifact_imports(manifest: dict[str, Any] | None = None) -> None:
    """Fail if any extra marked ``in_artifact: true`` cannot import (smoke guard)."""
    data = manifest if manifest is not None else load_manifest()
    missing: list[str] = []
    for name, meta in (data.get("extras") or {}).items():
        if not meta.get("in_artifact"):
            continue
        for mod in meta.get("modules") or []:
            if not _module_available(mod):
                missing.append(f"{name}:{mod}")
    if missing:
        raise RuntimeError(
            "EXTRAS_MANIFEST in_artifact import failed: " + ", ".join(missing)
        )


def check_extras_rows(manifest: dict[str, Any] | None = None) -> list[dict[str, str]]:
    """Rows for ``--check-extras``: extra × estado × origem × ação."""
    data = manifest if manifest is not None else load_manifest()
    rows: list[dict[str, str]] = []
    for name, meta in sorted((data.get("extras") or {}).items()):
        modules = list(meta.get("modules") or [])
        present = [_module_available(m) for m in modules]
        if not modules:
            estado = "OK"
            faltam: list[str] = []
        elif all(present):
            estado = "OK"
            faltam = []
        elif any(present):
            estado = "PARCIAL"
            faltam = [m for m, ok in zip(modules, present, strict=True) if not ok]
        else:
            estado = "AUSENTE"
            faltam = modules

        origins = {
            _module_origin(m) for m, ok in zip(modules, present, strict=True) if ok
        }
        origins.discard("—")
        if not origins:
            origem = "—"
        elif origins == {"/extras"}:
            origem = "/extras"
        elif "imagem" in origins and "/extras" in origins:
            origem = "imagem+/extras"
        elif "imagem" in origins:
            origem = "imagem"
        else:
            origem = "ambiente"

        if estado == "OK":
            acao = "—"
        else:
            acao = (
                f"pip install 'data-boar[{name}]' "
                f'(or: uv pip install -e ".[{name}]"); '
                "container: mount ABI-compatible wheels at /extras "
                "(PYTHONPATH=/extras) — see docs/DOCKER_SETUP.md"
            )
            if faltam:
                acao = f"falta: {', '.join(faltam)}  →  {acao}"
        rows.append(
            {
                "extra": name,
                "estado": estado,
                "origem": origem,
                "acao": acao,
            }
        )
    return rows


def format_check_extras_table(rows: list[dict[str, str]] | None = None) -> str:
    data = rows if rows is not None else check_extras_rows()
    if not data:
        return "extra              estado     origem\n(no extras declared)\n"
    cols = ("extra", "estado", "origem", "acao")
    widths = {c: max(len(c), *(len(r[c]) for r in data)) for c in cols}
    # Cap action column for terminals
    widths["acao"] = min(widths["acao"], 72)
    header = "  ".join(c.ljust(widths[c]) for c in cols)
    lines = [header]
    for row in data:
        parts = []
        for c in cols:
            val = row[c]
            if c == "acao" and len(val) > widths["acao"]:
                val = val[: widths["acao"] - 1] + "…"
            parts.append(val.ljust(widths[c]))
        lines.append("  ".join(parts))
    return "\n".join(lines) + "\n"
