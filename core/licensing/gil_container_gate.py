"""
Container GIL gate (#1409 / ADR-0091).

The published image is free-threaded CPython (cp314t). ``PYTHON_GIL`` is
process-start only, so this module runs as the distroless ENTRYPOINT, resolves
the same runtime tier as ``get_runtime_tier_for_features``, then ``os.execve``s
the real interpreter:

- **Enterprise** — leave ``PYTHON_GIL`` unset (no-GIL / free-threaded).
- **Any other tier** (including OPEN, Community, Partner) — set ``PYTHON_GIL=1``.

Do **not** call the OPEN-bypass feature helper. Do **not** set
``PYTHON_GIL`` to ``0`` (unsafe C extensions). Distroless has no shell — JSON
ENTRYPOINT only.
"""

from __future__ import annotations

import logging
import os
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from core.licensing.runtime_feature_tier import get_runtime_tier_for_features
from core.licensing.tier_features import Tier

logger = logging.getLogger("data_boar.licensing.gil_gate")

DEFAULT_CONTAINER_PYTHON = "/usr/local/bin/python3.14t"
_INTERPRETER_NAMES = frozenset({"python", "python3", "python3.14", "python3.14t"})


def should_force_gil(tier: Tier) -> bool:
    """True unless the resolved tier is exactly Enterprise."""
    return tier is not Tier.ENTERPRISE


def config_path_from_argv(argv: list[str], environ: Mapping[str, str]) -> Path | None:
    """Resolve ``--config`` / ``CONFIG_PATH`` / default ``/data/config.yaml``."""
    for i, arg in enumerate(argv):
        if arg == "--config" and i + 1 < len(argv):
            return Path(argv[i + 1])
        if arg.startswith("--config="):
            return Path(arg.split("=", 1)[1])
    raw = (environ.get("CONFIG_PATH") or "").strip()
    candidates = []
    if raw:
        candidates.append(Path(raw))
    candidates.append(Path("/data/config.yaml"))
    for path in candidates:
        if path.is_file():
            return path
    return None


def load_yaml_config(path: Path | None) -> dict[str, Any]:
    if path is None or not path.is_file():
        return {}
    try:
        import yaml
    except ImportError:  # pragma: no cover
        return {}
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return data if isinstance(data, dict) else {}


def environ_with_gil_gate(environ: Mapping[str, str], tier: Tier) -> dict[str, str]:
    """Copy ``environ`` and force ``PYTHON_GIL=1`` when not Enterprise."""
    out = dict(environ)
    if should_force_gil(tier):
        out["PYTHON_GIL"] = "1"
    return out


def strip_interpreter_prefix(argv: list[str]) -> list[str]:
    """Drop a leading python binary if the operator replaced CMD with one."""
    if argv and Path(argv[0]).name in _INTERPRETER_NAMES:
        return list(argv[1:])
    return list(argv)


def resolve_python_executable(environ: Mapping[str, str]) -> str:
    """Return the interpreter path to ``execve``.

    ``DATA_BOAR_CONTAINER_PYTHON`` is ignored unless it is exactly the
    distroless binary (``DEFAULT_CONTAINER_PYTHON``). An env-controlled
    executable would be the Semgrep ``tainted-env-args`` primitive.
    """
    default = Path(DEFAULT_CONTAINER_PYTHON)
    configured = (environ.get("DATA_BOAR_CONTAINER_PYTHON") or "").strip()
    if configured:
        cfg = Path(configured)
        try:
            same = cfg.is_file() and cfg.resolve() == default.resolve()
        except OSError:
            same = False
        if same:
            return DEFAULT_CONTAINER_PYTHON
        logger.warning(
            "GIL gate: ignoring DATA_BOAR_CONTAINER_PYTHON (must be %s)",
            DEFAULT_CONTAINER_PYTHON,
        )
    if default.is_file():
        return DEFAULT_CONTAINER_PYTHON
    return sys.executable


def exec_container_python(python: str, argv: list[str], env: dict[str, str]) -> None:
    """Replace PID 1 (Docker JSON ENTRYPOINT/CMD + process env). Not HTTP.

    Semgrep ``python.lang.security.audit.dangerous-os-exec-tainted-env-args``
    treats ``sys.argv`` / ``os.environ`` as taint. Here those are Compose/CMD
    and container startup env (license YAML path), not request handlers.
    """
    # nosemgrep: python.lang.security.audit.dangerous-os-exec-tainted-env-args
    os.execve(python, argv, env)


def resolve_tier(cfg: dict[str, Any]) -> Tier:
    try:
        return get_runtime_tier_for_features(cfg)
    except Exception:
        logger.exception("GIL gate: tier resolution failed — fail closed (GIL on)")
        return Tier.COMMUNITY


def main(argv: list[str] | None = None) -> None:
    rest = strip_interpreter_prefix(list(sys.argv[1:] if argv is None else argv))
    environ = dict(os.environ)
    cfg_path = config_path_from_argv(rest, environ)
    cfg = load_yaml_config(cfg_path)
    tier = resolve_tier(cfg)
    child_env = environ_with_gil_gate(environ, tier)
    python = resolve_python_executable(environ)
    if not rest:
        rest = [
            "main.py",
            "--config",
            "/data/config.yaml",
            "--web",
            "--port",
            "8088",
            "--allow-insecure-http",
        ]
    if should_force_gil(tier):
        logger.info(
            "GIL gate: tier=%s — setting PYTHON_GIL=1 (no-GIL is Enterprise only)",
            tier.value,
        )
    exec_container_python(python, [python, *rest], child_env)


if __name__ == "__main__":
    main()
