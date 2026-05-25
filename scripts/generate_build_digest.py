#!/usr/bin/env python3
"""Compute canonical SHA-256 build digest for licensing tamper checks.

Concatenates raw bytes of critical source files in sorted path order (POSIX
relative paths), hashes with SHA-256, writes hex digest to
core/licensing/_build_digest.txt.

Run before release Docker builds; set DATA_BOAR_EXPECTED_BUILD_DIGEST to the
same value in deployment (see docs/RELEASE_INTEGRITY.md).
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

DIGEST_REL = Path("core") / "licensing" / "_build_digest.txt"
SOURCE_ROOTS = ("core", "connectors", "scanners", "cli")
EXCLUDE_FILE_NAMES = frozenset({"_build_digest.txt"})


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def collect_source_paths(repo_root: Path) -> list[Path]:
    """Return sorted critical *.py paths (repo-relative sort key)."""
    paths: list[Path] = []

    main_py = repo_root / "main.py"
    if main_py.is_file():
        paths.append(main_py)

    for rel_root in SOURCE_ROOTS:
        base = repo_root / rel_root
        if not base.is_dir():
            continue
        for candidate in base.rglob("*.py"):
            if "__pycache__" in candidate.parts:
                continue
            if candidate.name in EXCLUDE_FILE_NAMES:
                continue
            paths.append(candidate)

    def _sort_key(path: Path) -> str:
        return path.relative_to(repo_root).as_posix()

    return sorted(set(paths), key=_sort_key)


def compute_build_digest_hex(repo_root: Path, paths: list[Path]) -> str:
    """SHA-256 over concatenated file contents in ``paths`` order."""
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.read_bytes())
    return digest.hexdigest()


def write_build_digest(repo_root: Path, digest_hex: str) -> Path:
    out = repo_root / DIGEST_REL
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(digest_hex.strip().lower(), encoding="utf-8")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate core/licensing/_build_digest.txt")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repository root (default: parent of scripts/)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 if on-disk digest differs from recomputed value",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress stdout on success",
    )
    args = parser.parse_args(argv)

    repo_root = (args.repo_root or _repo_root()).resolve()
    paths = collect_source_paths(repo_root)
    if not paths:
        print("generate_build_digest: no source files matched", file=sys.stderr)
        return 2

    computed = compute_build_digest_hex(repo_root, paths)
    out_path = repo_root / DIGEST_REL

    if args.check:
        if not out_path.is_file():
            print(f"generate_build_digest: missing {DIGEST_REL.as_posix()}", file=sys.stderr)
            return 1
        existing = out_path.read_text(encoding="utf-8").strip().lower()
        if existing != computed:
            print(
                f"generate_build_digest: digest drift (disk={existing[:16]}... "
                f"computed={computed[:16]}...)",
                file=sys.stderr,
            )
            return 1
        if not args.quiet:
            print(f"OK: {DIGEST_REL.as_posix()} matches ({len(paths)} files)")
        return 0

    write_build_digest(repo_root, computed)
    if not args.quiet:
        print(f"Wrote {DIGEST_REL.as_posix()} ({len(paths)} files, sha256={computed})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
