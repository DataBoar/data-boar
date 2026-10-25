#!/usr/bin/env python3
"""Optional extras a Maestro RC bench config needs in the baremetal scan venv.

``uv sync`` is exact: any extra not named on the command line is pruned. The host
smoke used a fixed ``--extra compressed`` and lost ``pymongo`` (extra ``nosql``),
so the Mongo target failed while the sentinel read it as a lab outage (maestro#91).

``list``   — print the extras the config's targets need, one per line, from
             ``core.extras_runtime.optional_extra_for_target`` (type/driver map).
``verify`` — after the sync, confirm every distribution declared by those extras
             (plus any ``--extra``) in ``pyproject.toml`` is installed. Exit 1 with
             ``EXTRA_MISSING`` lines otherwise, so the prepare fails loud before
             the scan instead of recording connector failures.

Exit 0 = ok, 1 = missing distribution, 2 = usage/config error.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import re
import sys
import tomllib
from pathlib import Path
from typing import Any

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from core.extras_runtime import optional_extra_for_target  # noqa: E402

_PROJECT_NAME = "data-boar"
_REQ_NAME = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)(?:\[([^\]]*)\])?")


def _normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def extras_for_config(config: dict[str, Any]) -> list[str]:
    found: set[str] = set()
    for target in config.get("targets") or []:
        if isinstance(target, dict):
            extra = optional_extra_for_target(target)
            if extra:
                found.add(extra)
    return sorted(found)


def _optional_dependencies(pyproject: Path) -> dict[str, list[str]]:
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    return dict((data.get("project") or {}).get("optional-dependencies") or {})


def distributions_for_extras(
    extras: list[str], optional_deps: dict[str, list[str]]
) -> dict[str, list[str]]:
    """Map extra -> distribution names; self-references (``data-boar[x]``) expand."""
    out: dict[str, list[str]] = {}
    for extra in extras:
        if extra not in optional_deps:
            raise KeyError(f"extra {extra!r} not declared in pyproject.toml")
        dists: list[str] = []
        pending = [extra]
        seen: set[str] = set()
        while pending:
            current = pending.pop()
            if current in seen:
                continue
            seen.add(current)
            for req in optional_deps.get(current) or []:
                m = _REQ_NAME.match(req)
                if not m:
                    continue
                name, sub = m.group(1), m.group(2)
                if _normalize(name) == _PROJECT_NAME:
                    pending.extend(
                        s.strip() for s in (sub or "").split(",") if s.strip()
                    )
                elif name not in dists:
                    dists.append(name)
        out[extra] = dists
    return out


def missing_distributions(dist_map: dict[str, list[str]]) -> list[tuple[str, str]]:
    missing: list[tuple[str, str]] = []
    for extra, dists in dist_map.items():
        for dist in dists:
            try:
                importlib.metadata.distribution(dist)
            except importlib.metadata.PackageNotFoundError:
                missing.append((extra, dist))
    return missing


def _load_config(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected mapping in {path}")
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("command", choices=("list", "verify"))
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument(
        "--extra",
        action="append",
        default=[],
        help="Extra synced regardless of the config (repeatable; verify only).",
    )
    parser.add_argument("--pyproject", type=Path, default=_REPO_ROOT / "pyproject.toml")
    args = parser.parse_args(argv)

    config_path = args.config if args.config.is_absolute() else _REPO_ROOT / args.config
    try:
        extras = extras_for_config(_load_config(config_path))
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(
            f"rc_bench_extras: cannot read config {config_path}: {exc}", file=sys.stderr
        )
        return 2

    if args.command == "list":
        for extra in extras:
            print(extra)
        return 0

    wanted = sorted(set(extras) | set(args.extra))
    try:
        dist_map = distributions_for_extras(
            wanted, _optional_dependencies(args.pyproject)
        )
    except (OSError, KeyError, tomllib.TOMLDecodeError) as exc:
        print(f"rc_bench_extras: {exc}", file=sys.stderr)
        return 2
    missing = missing_distributions(dist_map)
    for extra, dist in missing:
        print(f"EXTRA_MISSING extra={extra} dist={dist}", file=sys.stderr)
    if missing:
        return 1
    print(f"rc_bench_extras: OK ({', '.join(wanted) or 'none'})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
