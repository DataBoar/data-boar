#!/usr/bin/env python3
"""Heuristic audit: split headerless concatenated Markdown and match chunks to repo .md files.

Two strategies:

1. **H1 split** (default): break on lines that look like a document title (``# `` not ``##``),
   then match each chunk to a repo file by exact content. Good when cat order is unknown.

2. **Cat order / byte split** (``--cat-order``): you provide the list of paths in the **exact**
   order bash expanded globs (e.g. alphabetical). Chunks are cut by **file byte length**, like
   ``cat a.md b.md`` with no delimiter — the most faithful when the bundle was built that way.

Usage:
  uv run python scripts/audit_concatenated_markdown.py -i bundle.md
  uv run python scripts/audit_concatenated_markdown.py -i bundle.md \\
      --cat-order paths_in_cat_order.txt
  uv run python scripts/audit_concatenated_markdown.py --emit-order-glob "docs/**/*.md"

``paths_in_cat_order.txt``: one path per line, relative to repo root (``/`` separators), UTF-8.

Exit: 0 always for H1 mode; cat-order mode exits 1 if byte sum != bundle size or any mismatch
(unless ``--lenient``).
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
from pathlib import Path


def _is_doc_h1(line: str) -> bool:
    """True if line starts a plausible document title (exclude one-line comment-style '# or:' etc.)."""
    if not line.startswith("# ") or line.startswith("## "):
        return False
    rest = line[2:].strip()
    lower = rest.lower()
    false_starts = (
        "or:",
        "smoke:",
        "curl ",
        "uv run ",
        "git ",
        "export ",
        "set ",
        "python ",
        "docker ",
        "pytest ",
    )
    return not lower.startswith(false_starts)


def split_by_h1(text: str) -> list[str]:
    """Split on H1 lines (# space..., not ##), with guardrails for false positives."""
    lines = text.replace("\r\n", "\n").split("\n")
    chunks: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if _is_doc_h1(line):
            if current:
                chunks.append(current)
            current = [line]
        else:
            current.append(line)
    if current:
        chunks.append(current)
    return ["\n".join(c).strip() for c in chunks if any(s.strip() for s in c)]


def normalize(s: str) -> str:
    return s.replace("\r\n", "\n").strip()


def load_markdown_index(repo_root: Path, *, skip_private: bool) -> dict[str, Path]:
    """Map normalized content -> path (first wins)."""
    content_to_path: dict[str, Path] = {}
    skip_parts = {".git", ".venv", "node_modules", "__pycache__"}
    for dirpath, dirnames, filenames in os.walk(repo_root):
        dirnames[:] = [d for d in dirnames if d not in skip_parts]
        rel = Path(dirpath).relative_to(repo_root)
        if skip_private and "docs" in rel.parts and "private" in rel.parts:
            continue
        for name in filenames:
            if not name.endswith(".md"):
                continue
            p = Path(dirpath) / name
            try:
                body = normalize(p.read_text(encoding="utf-8"))
            except OSError:
                continue
            if body not in content_to_path:
                content_to_path[body] = p
    return content_to_path


def read_order_list(order_file: Path, repo_root: Path) -> list[Path]:
    """Paths relative to repo root (as written in file)."""
    lines = order_file.read_text(encoding="utf-8").splitlines()
    out: list[Path] = []
    for line in lines:
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        out.append(Path(s))
    return out


def emit_order_glob(repo_root: Path, glob_pat: str) -> list[Path]:
    """Sorted repo-relative paths (code-point order of ``as_posix()``, close to ``LC_ALL=C sort``)."""
    glob_pat = glob_pat.lstrip("/")
    paths = sorted(
        (p for p in repo_root.glob(glob_pat) if p.is_file()),
        key=lambda p: p.as_posix(),
    )
    out: list[Path] = []
    for p in paths:
        try:
            out.append(p.relative_to(repo_root))
        except ValueError:
            continue
    return out


def audit_cat_order(
    bundle_path: Path,
    repo_root: Path,
    rel_paths: list[Path],
    *,
    normalize_crlf: bool,
    line_report: bool,
    lenient: bool,
    limit: int | None,
) -> int:
    """Split bundle by consecutive file byte lengths; verify each chunk matches disk."""
    if limit is not None:
        rel_paths = rel_paths[:limit]
    bundle_raw = bundle_path.read_bytes()
    bundle = bundle_raw.replace(b"\r\n", b"\n") if normalize_crlf else bundle_raw

    offset = 0
    ok = 0
    mismatches = 0
    print(f"Input: {bundle_path}")
    print(f"Repo root: {repo_root}")
    print(f"Mode: cat-order ({len(rel_paths)} paths) normalize_crlf={normalize_crlf}")
    if line_report:
        print("line counts (splitlines, UTF-8): path | lines | cumulative_end_line")
    print()

    cum_lines = 0
    for i, rel in enumerate(rel_paths, 1):
        abs_p = (repo_root / rel).resolve()
        if not abs_p.is_file():
            print(f"ERROR: path not in repo (fix order list): {rel}", file=sys.stderr)
            return 1
        data_raw = abs_p.read_bytes()
        data = data_raw.replace(b"\r\n", b"\n") if normalize_crlf else data_raw
        chunk = bundle[offset : offset + len(data)]

        text_for_lines = data.decode("utf-8", errors="replace")
        nlines = len(text_for_lines.splitlines())
        cum_lines += nlines
        if line_report:
            print(f"    {rel.as_posix()}\t{nlines}\t{cum_lines}")

        if chunk == data:
            print(f"--- {i}: BYTE MATCH {rel} ({len(data)} bytes)")
            ok += 1
        else:
            print(f"--- {i}: BYTE MISMATCH {rel}")
            print(f"    expected {len(data)} bytes, slice len {len(chunk)}")
            mismatches += 1
        offset += len(data)

    print()
    tail = len(bundle) - offset
    if tail != 0:
        msg = (
            f"NOTE: consumed {offset} bytes, bundle has {len(bundle)} "
            f"(unexamined tail {tail} bytes — expected if --cat-order-limit or partial cat list)"
        )
        if limit is None:
            print(f"ERROR: {msg}")
            if not lenient:
                return 1
        else:
            print(msg)

    print("--- summary (cat-order) ---")
    print(f"byte_match: {ok}")
    print(f"mismatch: {mismatches}")
    if mismatches:
        return 1 if not lenient else 0
    if tail != 0 and limit is None:
        return 1 if not lenient else 0
    return 0


def run_h1_audit(
    bundle_path: Path,
    repo_root: Path,
    *,
    include_private: bool,
) -> None:
    raw = bundle_path.read_text(encoding="utf-8")
    chunks = split_by_h1(raw)
    index = load_markdown_index(repo_root, skip_private=not include_private)

    matched = 0
    ambiguous = 0
    missing = 0

    print(f"Input: {bundle_path}")
    print(f"Repo root: {repo_root}")
    print(f"Chunks (H1 split): {len(chunks)}")
    print()

    for i, chunk in enumerate(chunks, 1):
        n = normalize(chunk)
        h = hashlib.sha256(n.encode("utf-8")).hexdigest()[:12]
        first = (chunk.split("\n")[0] if chunk else "")[:72]
        if not n:
            print(f"--- chunk {i}: empty skip ---")
            continue
        path = index.get(n)
        if path:
            rel = (
                path.relative_to(repo_root) if path.is_relative_to(repo_root) else path
            )
            print(f"--- chunk {i}: EXACT MATCH sha256[:12]={h} ---")
            print(f"    H1: {first!r}")
            print(f"    -> {rel}")
            matched += 1
        else:
            prefix_lines = "\n".join(n.split("\n")[:5])
            min_plen = min(800, len(prefix_lines))
            prefix = prefix_lines[:min_plen] if min_plen > 20 else ""
            candidates: list[Path] = []
            if prefix:
                for body, p in index.items():
                    if body.startswith(prefix):
                        candidates.append(p)
            unique = list(dict.fromkeys(candidates))
            print(f"--- chunk {i}: NO EXACT MATCH sha256[:12]={h} len={len(n)} ---")
            print(f"    H1: {first!r}")
            if len(unique) == 1:
                rel = unique[0].relative_to(repo_root)
                print(f"    ~ prefix hint (first ~5 lines): likely -> {rel}")
                ambiguous += 1
            elif len(unique) > 1:
                print(
                    f"    ~ ambiguous prefix: {len(unique)} files share start; examples:"
                )
                for p in unique[:5]:
                    print(f"        {p.relative_to(repo_root)}")
                ambiguous += 1
            else:
                missing += 1
            print()

    print("--- summary ---")
    print(f"exact_match: {matched}")
    print(f"no_exact (prefix ambiguous): {ambiguous}")
    print(f"no_exact (unmatched): {missing}")


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        "-i",
        type=Path,
        help="Concatenated Markdown file (required unless --emit-order-glob only)",
    )
    parser.add_argument(
        "--repo-root",
        "-r",
        type=Path,
        default=Path.cwd(),
        help="Repository root (default: cwd)",
    )
    parser.add_argument(
        "--include-private",
        action="store_true",
        help="Also scan docs/private when matching (H1 mode only)",
    )
    parser.add_argument(
        "--cat-order",
        type=Path,
        metavar="PATHS.TXT",
        help="One repo-relative path per line, in exact cat order; enables byte-split mode",
    )
    parser.add_argument(
        "--normalize-crlf",
        action="store_true",
        help="Treat CRLF as LF when comparing (cat-order mode)",
    )
    parser.add_argument(
        "--line-report",
        action="store_true",
        help="Print per-file line counts and cumulative lines (cat-order mode)",
    )
    parser.add_argument(
        "--lenient",
        action="store_true",
        help="Do not exit 1 on cat-order size / mismatch (print only)",
    )
    parser.add_argument(
        "--cat-order-limit",
        type=int,
        metavar="N",
        help="Cat-order mode: verify only the first N paths (bundle may have more bytes after)",
    )
    parser.add_argument(
        "--emit-order-glob",
        metavar="GLOB",
        help="Print sorted repo-relative paths (C-style string sort) and exit; "
        'e.g. "docs/**/*.md". Save output as --cat-order input.',
    )
    parser.add_argument(
        "--emit-order-out",
        type=Path,
        help="With --emit-order-glob, write list to this file instead of stdout",
    )
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()

    if args.emit_order_glob:
        paths = emit_order_glob(repo_root, args.emit_order_glob)
        text = "\n".join(p.as_posix() for p in paths) + "\n"
        if args.emit_order_out:
            args.emit_order_out.write_text(text, encoding="utf-8")
            print(f"Wrote {len(paths)} paths to {args.emit_order_out}", file=sys.stderr)
        else:
            sys.stdout.write(text)
        return

    if not args.input:
        parser.error("--input is required unless --emit-order-glob")

    bundle_path = args.input.resolve()
    if not bundle_path.is_file():
        print(f"ERROR: not a file: {bundle_path}", file=sys.stderr)
        sys.exit(2)

    if args.cat_order:
        rels = read_order_list(args.cat_order.resolve(), repo_root)
        raise SystemExit(
            audit_cat_order(
                bundle_path,
                repo_root,
                rels,
                normalize_crlf=args.normalize_crlf,
                line_report=args.line_report,
                lenient=args.lenient,
                limit=args.cat_order_limit,
            )
        )

    run_h1_audit(bundle_path, repo_root, include_private=args.include_private)


if __name__ == "__main__":
    main()
