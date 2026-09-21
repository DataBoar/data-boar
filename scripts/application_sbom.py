#!/usr/bin/env python3
"""Merge Cargo.lock crates into the application CycloneDX BOM (#1950).

The application SBOM remains one artifact: Python (uv export + cyclonedx-py)
plus the resolved Rust graph from ``rust/boar_fast_filter/Cargo.lock``.
The image/runtime SBOM stays a separate Syft inventory. There is no third
SBOM source of truth.
"""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path
from typing import Any

CARGO_LOCK_REL = Path("rust") / "boar_fast_filter" / "Cargo.lock"
APP_PROPERTY = "data-boar:application-sbom"
APP_PROPERTY_VALUE = "python+rust-cargo-lock"
LOCKFILE_PROPERTY = "data-boar:rust-lockfile"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_cargo_lock(lock_path: Path) -> list[dict[str, Any]]:
    raw = tomllib.loads(lock_path.read_text(encoding="utf-8"))
    packages = raw.get("package") or []
    if not isinstance(packages, list):
        raise ValueError(f"{lock_path}: expected [[package]] list")
    out: list[dict[str, Any]] = []
    for pkg in packages:
        if not isinstance(pkg, dict):
            continue
        name = pkg.get("name")
        version = pkg.get("version")
        if not name or not version:
            continue
        out.append(pkg)
    if not out:
        raise ValueError(f"{lock_path}: no packages parsed")
    return out


def cargo_component(pkg: dict[str, Any]) -> dict[str, Any]:
    name = str(pkg["name"])
    version = str(pkg["version"])
    component: dict[str, Any] = {
        "type": "library",
        "name": name,
        "version": version,
        "purl": f"pkg:cargo/{name}@{version}",
        "bom-ref": f"cargo:{name}@{version}",
    }
    checksum = pkg.get("checksum")
    if isinstance(checksum, str) and checksum:
        component["hashes"] = [{"alg": "SHA-256", "content": checksum}]
    source = pkg.get("source")
    if isinstance(source, str) and source:
        component["properties"] = [{"name": "cargo:source", "value": source}]
    return component


def _component_key(component: dict[str, Any]) -> tuple[str, str]:
    return (
        str(component.get("name") or "").lower(),
        str(component.get("version") or ""),
    )


def merge_cargo_into_bom(
    bom: dict[str, Any],
    packages: list[dict[str, Any]],
    *,
    lock_rel: str,
) -> dict[str, Any]:
    components = bom.get("components")
    if components is None:
        components = []
        bom["components"] = components
    if not isinstance(components, list):
        raise ValueError("CycloneDX components must be a list")
    existing = {_component_key(c) for c in components if isinstance(c, dict)}
    added: list[dict[str, Any]] = []
    for pkg in packages:
        comp = cargo_component(pkg)
        key = _component_key(comp)
        if key in existing:
            continue
        existing.add(key)
        added.append(comp)
    added.sort(key=lambda c: (c["name"].lower(), c["version"]))
    components.extend(added)

    metadata = bom.setdefault("metadata", {})
    if not isinstance(metadata, dict):
        raise ValueError("CycloneDX metadata must be an object")
    props = metadata.setdefault("properties", [])
    if not isinstance(props, list):
        raise ValueError("CycloneDX metadata.properties must be a list")

    def _upsert(name: str, value: str) -> None:
        for item in props:
            if isinstance(item, dict) and item.get("name") == name:
                item["value"] = value
                return
        props.append({"name": name, "value": value})

    _upsert(APP_PROPERTY, APP_PROPERTY_VALUE)
    _upsert(LOCKFILE_PROPERTY, lock_rel)
    return bom


def check_rust_lock_coverage(
    bom: dict[str, Any],
    packages: list[dict[str, Any]],
) -> list[str]:
    components = bom.get("components") or []
    if not isinstance(components, list):
        return ["application SBOM components is not a list"]
    present = {_component_key(c) for c in components if isinstance(c, dict)}
    missing: list[str] = []
    for pkg in packages:
        key = (str(pkg["name"]).lower(), str(pkg["version"]))
        if key not in present:
            missing.append(f"{pkg['name']}@{pkg['version']}")
    return missing


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected JSON object")
    return data


def _dump_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, sort_keys=False, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def cmd_merge(args: argparse.Namespace) -> int:
    repo = args.repo_root or _repo_root()
    lock_path = repo / CARGO_LOCK_REL
    packages = parse_cargo_lock(lock_path)
    bom = _load_json(args.python_bom)
    merge_cargo_into_bom(bom, packages, lock_rel=CARGO_LOCK_REL.as_posix())
    out = args.out or args.python_bom
    _dump_json(out, bom)
    if args.canonical:
        canon = repo / "sbom" / "sbom-application.cdx.json"
        _dump_json(canon, bom)
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    repo = args.repo_root or _repo_root()
    lock_path = repo / CARGO_LOCK_REL
    packages = parse_cargo_lock(lock_path)
    bom = _load_json(args.application)
    if bom.get("bomFormat") != "CycloneDX":
        print("application SBOM missing bomFormat=CycloneDX", file=sys.stderr)
        return 1
    missing = check_rust_lock_coverage(bom, packages)
    if missing:
        print(
            "application SBOM missing Cargo.lock components:\n  "
            + "\n  ".join(missing),
            file=sys.stderr,
        )
        return 1
    metadata = bom.get("metadata") or {}
    props = metadata.get("properties") if isinstance(metadata, dict) else None
    values = {
        p.get("name"): p.get("value") for p in (props or []) if isinstance(p, dict)
    }
    if values.get(APP_PROPERTY) != APP_PROPERTY_VALUE:
        print(
            f"application SBOM missing property {APP_PROPERTY}={APP_PROPERTY_VALUE}",
            file=sys.stderr,
        )
        return 1
    if args.runtime:
        runtime = _load_json(args.runtime)
        if runtime.get("bomFormat") != "CycloneDX":
            print("runtime SBOM missing bomFormat=CycloneDX", file=sys.stderr)
            return 1
        comps = runtime.get("components") or []
        if not isinstance(comps, list) or not comps:
            print("runtime SBOM has no components", file=sys.stderr)
            return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repository root (default: parent of scripts/)",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    merge_p = sub.add_parser(
        "merge", help="Merge Cargo.lock crates into a Python CDX JSON"
    )
    merge_p.add_argument("--python-bom", type=Path, required=True)
    merge_p.add_argument("--out", type=Path, default=None)
    merge_p.add_argument(
        "--canonical",
        action="store_true",
        help="Also write sbom/sbom-application.cdx.json (copy, not a third inventory)",
    )
    merge_p.set_defaults(func=cmd_merge)

    check_p = sub.add_parser(
        "check", help="Fail if Cargo.lock crates are missing from the application BOM"
    )
    check_p.add_argument("--application", type=Path, required=True)
    check_p.add_argument(
        "--runtime",
        type=Path,
        default=None,
        help="Optional Syft/runtime CycloneDX to schema-check (not a Rust graph)",
    )
    check_p.set_defaults(func=cmd_check)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
