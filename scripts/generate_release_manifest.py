#!/usr/bin/env python3
"""Generate SHA-256 release manifest JSON for licensing integrity checks.

Lists critical source files (same roots as generate_build_digest.py) plus
boar_fast_filter*.so when present. Used at release time; operators point
DATA_BOAR_RELEASE_MANIFEST_PATH or licensing.manifest_path at the file.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.generate_build_digest import collect_source_paths

DEFAULT_OUT = Path("dist") / "release-manifest.json"
NATIVE_GLOB = "boar_fast_filter*.so"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _manifest_path_key(repo_root: Path, path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return resolved.as_posix()


def collect_native_extension_paths(repo_root: Path) -> list[Path]:
    """Return sorted boar_fast_filter*.so paths (repo tree + importlib when built)."""
    paths: list[Path] = []
    seen: set[str] = set()

    def add(candidate: Path) -> None:
        if not candidate.is_file():
            return
        key = str(candidate.resolve())
        if key in seen:
            return
        seen.add(key)
        paths.append(candidate)

    for candidate in repo_root.rglob(NATIVE_GLOB):
        if ".git" in candidate.parts or "__pycache__" in candidate.parts:
            continue
        add(candidate)

    try:
        spec = importlib.util.find_spec("boar_fast_filter")
        if spec and spec.origin:
            origin = Path(spec.origin)
            if origin.suffix in {".so", ".pyd"}:
                add(origin)
    except (ImportError, ModuleNotFoundError, ValueError, OSError):
        pass

    return sorted(paths, key=lambda p: _manifest_path_key(repo_root, p))


def collect_release_file_paths(repo_root: Path) -> list[Path]:
    """Sorted critical release paths (.py sources + optional Rust .so)."""
    combined = collect_source_paths(repo_root) + collect_native_extension_paths(
        repo_root
    )
    seen: set[str] = set()
    unique: list[Path] = []
    for path in combined:
        key = _manifest_path_key(repo_root, path)
        if key in seen:
            continue
        seen.add(key)
        unique.append(path)
    return sorted(unique, key=lambda p: _manifest_path_key(repo_root, p))


def sha256_file_hex(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_project_version(repo_root: Path) -> str:
    pyproject = repo_root / "pyproject.toml"
    if not pyproject.is_file():
        return "unknown"
    import tomllib

    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    project = data.get("project") or {}
    version = project.get("version")
    return str(version) if version else "unknown"


def build_manifest_payload(
    repo_root: Path,
    *,
    version: str | None = None,
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    when = generated_at or datetime.now(timezone.utc)
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    generated_at_iso = when.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    paths = collect_release_file_paths(repo_root)
    files = [
        {
            "path": _manifest_path_key(repo_root, path),
            "sha256": sha256_file_hex(path),
        }
        for path in paths
    ]
    return {
        "generated_at": generated_at_iso,
        "data_boar_version": version or read_project_version(repo_root),
        "files": files,
    }


def write_release_manifest(
    repo_root: Path,
    out_path: Path,
    *,
    version: str | None = None,
) -> Path:
    payload = build_manifest_payload(repo_root, version=version)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return out_path


def verify_manifest_on_disk(
    manifest_path: Path,
    repo_root: Path | None = None,
) -> tuple[bool, str]:
    """Verify each manifest entry against files on disk (repo-relative or absolute)."""
    if not manifest_path.is_file():
        return False, f"manifest_missing:{manifest_path}"
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return False, f"manifest_invalid:{exc}"
    files = data.get("files")
    if not isinstance(files, list):
        return False, "manifest_no_files_array"
    root = (repo_root or Path.cwd()).resolve()
    for item in files:
        if not isinstance(item, dict):
            continue
        rel = item.get("path")
        want = (item.get("sha256") or "").strip().lower()
        if not rel or not want:
            continue
        fp = Path(str(rel))
        if not fp.is_absolute():
            fp = root / fp
        if not fp.is_file():
            return False, f"missing_file:{fp}"
        got = sha256_file_hex(fp)
        if got.lower() != want:
            return False, f"hash_mismatch:{fp}"
    return True, "manifest_ok"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate or verify dist/release-manifest.json"
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repository root (default: parent of scripts/)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help=f"Output JSON path (default: {DEFAULT_OUT.as_posix()})",
    )
    parser.add_argument(
        "--version",
        type=str,
        default=None,
        help="Override data_boar_version in the manifest",
    )
    parser.add_argument(
        "--check",
        type=Path,
        metavar="MANIFEST.json",
        default=None,
        help="Verify on-disk files against an existing manifest; exit 1 on drift",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress stdout on success",
    )
    args = parser.parse_args(argv)

    repo_root = (args.repo_root or _repo_root()).resolve()

    if args.check is not None:
        ok, msg = verify_manifest_on_disk(args.check.resolve(), repo_root)
        if not ok:
            print(f"generate_release_manifest: {msg}", file=sys.stderr)
            return 1
        if not args.quiet:
            print(f"OK: {args.check.as_posix()} ({msg})")
        return 0

    paths = collect_release_file_paths(repo_root)
    if not paths:
        print("generate_release_manifest: no release files matched", file=sys.stderr)
        return 2

    out_path = (args.out if args.out.is_absolute() else repo_root / args.out).resolve()
    write_release_manifest(repo_root, out_path, version=args.version)
    if not args.quiet:
        print(
            f"Wrote {out_path.relative_to(repo_root).as_posix()} "
            f"({len(paths)} files, version={read_project_version(repo_root)})"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
