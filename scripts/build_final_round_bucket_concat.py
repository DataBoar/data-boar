#!/usr/bin/env python3
"""Build one concatenated text blob from a \"final round\" recovery folder for sliding-window forensics.

Typical layout (gitignored): ``docs/private/mess_concatenated_gemini_sanity_check/final_round_bucket/``.
Files collected: ``.md``, ``.yaml``, ``.yml``, ``.htm``, ``.html``. Each file is wrapped with a
``--- FILE: <relative-path> ---`` line so ``audit_concat_sliding_window.py --strip-bundle-markers``
can drop markers while keeping stable boundaries for manual inspection.

HTML/HTM: strip tags and collapse whitespace to approximate line-oriented text for the window matcher
(exported browser snapshots are not byte-identical to Markdown sources).

Optional: print how many bucket files share an exact basename with a tracked file outside
``docs/private/``, and optionally run the multi-pass sliding-window sweep (subprocess to
``audit_concat_sliding_window.py``).

Examples (repo root)::

  uv run python scripts/build_final_round_bucket_concat.py
  uv run python scripts/build_final_round_bucket_concat.py --map-names
  uv run python scripts/build_final_round_bucket_concat.py --sweep --quiet-gaps

Exit: 0 on success; 2 on usage/IO errors; 3 if subprocess audit fails.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

_HTML_TAG = re.compile(r"<[^>]+>", re.IGNORECASE)
_TEXT_EXT = frozenset({".md", ".yaml", ".yml", ".htm", ".html"})
_SKIP_DIR_NAMES = frozenset({".git", ".venv", "node_modules", "__pycache__"})
_DEFAULT_BUCKET_REL = (
    "docs/private/mess_concatenated_gemini_sanity_check/final_round_bucket"
)
_DEFAULT_OUT_NAME = "_concat_for_sliding_window.md"


def _html_to_lines(html: str) -> str:
    t = _HTML_TAG.sub(" ", html)
    t = re.sub(r"\s+", " ", t)
    return t.replace("\r\n", "\n")


def _iter_trackedish_files(repo_root: Path) -> list[Path]:
    """Paths under repo excluding docs/private and usual junk (mirrors informal recovery checks)."""
    out: list[Path] = []
    for dirpath, dirnames, filenames in repo_root.walk(
        top_down=True,
        follow_symlinks=False,
    ):
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIR_NAMES]
        pdir = Path(dirpath)
        try:
            rel = pdir.relative_to(repo_root)
        except ValueError:
            continue
        parts = rel.parts
        if parts[:2] == ("docs", "private"):
            continue
        for name in filenames:
            out.append(pdir / name)
    return out


def _build_by_name_index(paths: list[Path], repo_root: Path) -> dict[str, list[Path]]:
    by_name: dict[str, list[Path]] = {}
    for p in paths:
        by_name.setdefault(p.name, []).append(p.relative_to(repo_root))
    return by_name


def _normalize_stem(filename: str) -> str:
    stem = Path(filename).stem
    if " (" in stem:
        stem = stem.split(" (", 1)[0]
    return stem.casefold()


def _build_by_stem_index(paths: list[Path], repo_root: Path) -> dict[str, list[Path]]:
    by_stem: dict[str, list[Path]] = {}
    for p in paths:
        key = _normalize_stem(p.name)
        by_stem.setdefault(key, []).append(p.relative_to(repo_root))
    return by_stem


def write_concat(
    bucket: Path,
    output: Path,
    *,
    text_ext: frozenset[str],
) -> tuple[int, int]:
    """Return (source_files, blob_lines)."""
    parts: list[str] = []
    seen = 0
    out_resolved = output.resolve()
    for p in sorted(bucket.rglob("*")):
        if not p.is_file():
            continue
        if p.resolve() == out_resolved:
            continue
        if p.name == _DEFAULT_OUT_NAME or p.name.startswith(
            "_concat_for_sliding_window"
        ):
            continue
        if p.suffix.lower() not in text_ext:
            continue
        rel = p.relative_to(bucket).as_posix()
        raw = p.read_text(encoding="utf-8", errors="replace")
        if p.suffix.lower() in (".htm", ".html"):
            raw = _html_to_lines(raw)
        parts.append(f"--- FILE: {rel} ---\n" + raw.rstrip() + "\n")
        seen += 1
    blob = "\n".join(parts)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(blob, encoding="utf-8")
    return seen, len(blob.splitlines())


def map_bucket_names(bucket: Path, repo_root: Path) -> tuple[int, Counter[str]]:
    """Return (n_bucket_files, status counts: match_name | match_stem | no_tracked)."""
    repo_files = _iter_trackedish_files(repo_root)
    by_name = _build_by_name_index(repo_files, repo_root)
    by_stem = _build_by_stem_index(repo_files, repo_root)
    c: Counter[str] = Counter()
    n = 0
    for p in sorted(bucket.rglob("*")):
        if not p.is_file():
            continue
        if p.name == _DEFAULT_OUT_NAME or p.name.startswith(
            "_concat_for_sliding_window"
        ):
            continue
        n += 1
        if p.name in by_name:
            c["match_name"] += 1
        elif _normalize_stem(p.name) in by_stem:
            c["match_stem"] += 1
        else:
            c["no_tracked"] += 1
    return n, c


def run_sweep(
    repo_root: Path,
    blob: Path,
    *,
    sweep_windows: str,
    quiet_gaps: bool,
    rstrip_lines: bool,
) -> int:
    audit = repo_root / "scripts" / "audit_concat_sliding_window.py"
    if not audit.is_file():
        print(f"ERROR: missing {audit}", file=sys.stderr)
        return 2
    cmd: list[str] = [
        sys.executable,
        str(audit),
        "-i",
        str(blob.resolve()),
        "--repo-root",
        str(repo_root.resolve()),
        "--strip-bundle-markers",
        "--sweep-windows",
        sweep_windows,
    ]
    if quiet_gaps:
        cmd.append("--quiet-gaps")
    if rstrip_lines:
        cmd.append("--rstrip-lines")
    proc = subprocess.run(cmd, cwd=str(repo_root))
    return 0 if proc.returncode == 0 else 3


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass

    repo_root = Path.cwd().resolve()
    default_bucket = repo_root / _DEFAULT_BUCKET_REL

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--repo-root",
        type=Path,
        default=repo_root,
        help="Repository root (default: cwd)",
    )
    p.add_argument(
        "--bucket",
        type=Path,
        default=None,
        help=f"Recovery folder (default: {_DEFAULT_BUCKET_REL})",
    )
    p.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help=f"Concat output path (default: <bucket>/{_DEFAULT_OUT_NAME})",
    )
    p.add_argument(
        "--map-names",
        action="store_true",
        help="Print per-file basename match against tracked files (excludes docs/private)",
    )
    p.add_argument(
        "--sweep",
        action="store_true",
        help="After writing concat, run audit_concat_sliding_window.py multi-pass sweep",
    )
    p.add_argument(
        "--sweep-windows",
        default="12,15,18,22,25,30",
        help="Comma-separated window sizes for --sweep (default: 12,15,18,22,25,30)",
    )
    p.add_argument(
        "--quiet-gaps",
        action="store_true",
        help="Pass --quiet-gaps to sliding-window (compact table only)",
    )
    p.add_argument(
        "--rstrip-lines",
        action="store_true",
        help="Pass --rstrip-lines to sliding-window",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print plan (and optional --map-names); do not write the concat file",
    )

    args = p.parse_args()
    root = args.repo_root.resolve()
    bucket = (args.bucket or default_bucket).resolve()
    output = (args.output or (bucket / _DEFAULT_OUT_NAME)).resolve()

    if not bucket.is_dir():
        print(f"ERROR: bucket not a directory: {bucket}", file=sys.stderr)
        return 2

    if args.dry_run:
        if args.map_names:
            n, c = map_bucket_names(bucket, root)
            print(f"bucket: {bucket}")
            print(f"repo_root: {root}")
            print(f"bucket_files (excl. output artefacts): {n}")
            print(f"by_status: {dict(c)}")
        print(f"dry-run: would write {output} from {bucket.as_posix()}")
        return 0

    if args.map_names and not args.sweep:
        n, c = map_bucket_names(bucket, root)
        print(f"bucket: {bucket}")
        print(f"repo_root: {root}")
        print(f"bucket_files (excl. output artefacts): {n}")
        print(f"by_status: {dict(c)}")
        return 0

    nfiles, nlines = write_concat(bucket, output, text_ext=_TEXT_EXT)
    print(
        f"wrote {output.as_posix()} | source_files={nfiles} | blob_lines={nlines}",
        flush=True,
    )

    if args.map_names:
        n, c = map_bucket_names(bucket, root)
        print(f"bucket_files (excl. output artefacts): {n} | by_status: {dict(c)}")

    if args.sweep:
        return run_sweep(
            root,
            output,
            sweep_windows=args.sweep_windows,
            quiet_gaps=args.quiet_gaps,
            rstrip_lines=args.rstrip_lines,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
