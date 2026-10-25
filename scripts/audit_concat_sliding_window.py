#!/usr/bin/env python3
"""Sliding-window overlap: find N-line spans in a concatenated file that exist in the repo corpus.

Use when a headerless ``cat``-style blob lost file boundaries: lines that are never part of any
N-line window matching a tracked ``.md`` / YAML sample may be **unique glue**, **edited**, or
**missing-from-disk** relative to the corpus snapshot — heuristic only, not proof.

Typical flow (repo root)::

  uv run python scripts/audit_concat_sliding_window.py \\
      -i docs/private/mess_concatenated_gemini_sanity_check/sobre-data-boar.md \\
      --window 25 --strip-bundle-markers

Pair with ``scripts/audit_concatenated_markdown.py`` (H1 / byte-split) and Git history for recovery.

**Multi-pass (compare noise barriers):** same normalization, several window sizes in one run::

  uv run python scripts/audit_concat_sliding_window.py -i blob.md \\
      --strip-bundle-markers --sweep-windows 12,15,18,22,25
  uv run python scripts/audit_concat_sliding_window.py -i blob.md \\
      --strip-bundle-markers --rstrip-lines --sweep-windows 12,15,18,22,30

Exit: 0 unless ``--fail-if-uncovered-pct-above`` threshold is exceeded (then 3).
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


_FILE_MARKER = re.compile(r"^--- FILE: .+ ---\s*$")

# Corpus extensions (keep narrow: doc-like text; add flags if you need more)
_DEFAULT_SUFFIXES = (".md", ".yaml", ".yml")
_SKIP_DIR_NAMES = frozenset({".git", ".venv", "node_modules", "__pycache__"})


def normalize_lines(text: str, *, rstrip_each: bool) -> list[str]:
    raw = text.replace("\r\n", "\n").split("\n")
    if rstrip_each:
        return [ln.rstrip("\r\n") for ln in raw]
    return raw


def strip_bundle_marker_lines(lines: list[str]) -> list[str]:
    return [ln for ln in lines if not _FILE_MARKER.match(ln)]


def _should_skip_private(rel_parts: tuple[str, ...]) -> bool:
    return "docs" in rel_parts and "private" in rel_parts


def iter_corpus_files(
    repo_root: Path,
    *,
    skip_private: bool,
    suffixes: tuple[str, ...],
) -> list[Path]:
    out: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(repo_root):
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIR_NAMES]
        pdir = Path(dirpath)
        try:
            rel_parts = pdir.relative_to(repo_root).parts
        except ValueError:
            continue
        if skip_private and _should_skip_private(rel_parts):
            continue
        for name in filenames:
            low = name.lower()
            if any(low.endswith(s) for s in suffixes):
                out.append(pdir / name)
    return sorted(out, key=lambda p: p.as_posix())


def add_file_windows(
    path: Path,
    repo_root: Path,
    window: int,
    *,
    rstrip_each: bool,
    inv: dict[bytes, list[tuple[str, int]]],
) -> None:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return
    lines = normalize_lines(text, rstrip_each=rstrip_each)
    if len(lines) < window:
        return
    rel = path.relative_to(repo_root).as_posix()
    for i in range(0, len(lines) - window + 1):
        chunk = "\n".join(lines[i : i + window])
        h = hashlib.sha256(chunk.encode("utf-8")).digest()
        inv[h].append((rel, i + 1))


def mark_concat_coverage(
    lines: list[str],
    window: int,
    inv: dict[bytes, list[tuple[str, int]]],
    *,
    match_cap: int | None,
) -> tuple[list[bool], int, list[tuple[int, str, int]]]:
    """Return (covered per line, match_count, sample matches as (concat_line, relpath, file_line))."""
    n = len(lines)
    covered = [False] * n
    matches = 0
    samples: list[tuple[int, str, int]] = []
    if n < window:
        return covered, 0, samples
    stop = n - window + 1
    for i in range(0, stop):
        chunk = "\n".join(lines[i : i + window])
        h = hashlib.sha256(chunk.encode("utf-8")).digest()
        hits = inv.get(h)
        if not hits:
            continue
        matches += 1
        for j in range(i, i + window):
            covered[j] = True
        if match_cap is not None and len(samples) < match_cap:
            rel, line1 = hits[0]
            samples.append((i + 1, rel, line1))
    return covered, matches, samples


def uncovered_ranges(covered: list[bool]) -> list[tuple[int, int]]:
    """1-based inclusive line ranges where no line is covered."""
    gaps: list[tuple[int, int]] = []
    n = len(covered)
    i = 0
    while i < n:
        if covered[i]:
            i += 1
            continue
        start = i
        while i < n and not covered[i]:
            i += 1
        gaps.append((start + 1, i))  # 1-based [start+1, i]
    return gaps


@dataclass
class PassResult:
    window: int
    nlines: int
    covered_n: int
    pct_uncovered: float
    gap_blocks: int
    gap_ranges: list[tuple[int, int]]
    index_entries: int
    match_windows: int


def run_pass(
    lines: list[str],
    corpus: list[Path],
    repo_root: Path,
    window: int,
    *,
    rstrip_each: bool,
    match_cap: int | None,
) -> tuple[PassResult, list[tuple[int, str, int]]]:
    inv: dict[bytes, list[tuple[str, int]]] = defaultdict(list)
    for fp in corpus:
        add_file_windows(fp, repo_root, window, rstrip_each=rstrip_each, inv=inv)
    nlines = len(lines)
    if nlines < window:
        return (
            PassResult(
                window=window,
                nlines=nlines,
                covered_n=0,
                pct_uncovered=100.0 if nlines else 0.0,
                gap_blocks=1 if nlines else 0,
                gap_ranges=[(1, nlines)] if nlines else [],
                index_entries=len(inv),
                match_windows=0,
            ),
            [],
        )
    covered, match_windows, samples = mark_concat_coverage(
        lines, window, inv, match_cap=match_cap
    )
    covered_n = sum(1 for c in covered if c)
    uncovered_n = nlines - covered_n
    pct_uncovered = 100.0 * uncovered_n / nlines if nlines else 0.0
    gaps = uncovered_ranges(covered)
    pr = PassResult(
        window=window,
        nlines=nlines,
        covered_n=covered_n,
        pct_uncovered=pct_uncovered,
        gap_blocks=len(gaps),
        gap_ranges=gaps,
        index_entries=len(inv),
        match_windows=match_windows,
    )
    return pr, samples


def preview_gap(lines: list[str], start: int, end: int, *, max_lines: int) -> str:
    """start/end are 1-based inclusive indices into lines."""
    slice_ = lines[start - 1 : end]
    show = slice_[:max_lines]
    body = "\n".join(show)
    if len(slice_) > max_lines:
        body += "\n…"
    return body[:2000]


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--input", "-i", type=Path, required=True, help="Concatenated text file"
    )
    p.add_argument(
        "--repo-root",
        "-r",
        type=Path,
        default=Path.cwd(),
        help="Repository root (default: cwd)",
    )
    p.add_argument(
        "--window",
        "-w",
        type=int,
        default=None,
        metavar="N",
        help="Lines per window (default: 20 when not using --sweep-windows)",
    )
    p.add_argument(
        "--sweep-windows",
        metavar="W,W,…",
        help="Comma-separated window sizes (e.g. 15,18,22,25,30); prints a compact comparison "
        "table. Reindexes the corpus per size (slower but catches different noise barriers).",
    )
    p.add_argument(
        "--include-private-corpus",
        action="store_true",
        help="Also index docs/private/** in the corpus (off by default)",
    )
    p.add_argument(
        "--strip-bundle-markers",
        action="store_true",
        help="Remove lines matching --- FILE: ... --- before analysis",
    )
    p.add_argument(
        "--rstrip-lines",
        action="store_true",
        help="Strip trailing spaces on each line (both corpus and input)",
    )
    p.add_argument(
        "--min-gap-lines",
        type=int,
        default=1,
        metavar="N",
        help="Only report gaps with at least this many lines (default: 1)",
    )
    p.add_argument(
        "--max-gaps",
        type=int,
        default=30,
        help="Max gap blocks to print previews for (default: 30)",
    )
    p.add_argument(
        "--preview-lines",
        type=int,
        default=8,
        help="Lines of preview per gap (default: 8)",
    )
    p.add_argument(
        "--show-sample-matches",
        type=int,
        default=0,
        metavar="K",
        help="Print K sample windows that matched (0=off)",
    )
    p.add_argument(
        "--fail-if-uncovered-pct-above",
        type=float,
        default=None,
        metavar="PCT",
        help="Exit 3 if uncovered line %% exceeds this (e.g. 1.0 means any gap fails)",
    )
    p.add_argument(
        "--quiet-gaps",
        action="store_true",
        help="Skip gap previews (and sample matches); with --sweep-windows prints table only",
    )
    args = p.parse_args()

    repo_root = args.repo_root.resolve()
    bundle_path = args.input.resolve()
    if not bundle_path.is_file():
        print(f"ERROR: not a file: {bundle_path}", file=sys.stderr)
        return 2

    if args.sweep_windows:
        raw_ws = [x.strip() for x in args.sweep_windows.split(",") if x.strip()]
        try:
            windows = [int(x) for x in raw_ws]
        except ValueError:
            print(
                "ERROR: --sweep-windows must be integers like 15,18,25", file=sys.stderr
            )
            return 2
    elif args.window is not None:
        windows = [args.window]
    else:
        windows = [20]

    for window in windows:
        if window < 3:
            print(f"ERROR: window size must be >= 3 (got {window})", file=sys.stderr)
            return 2

    corpus = iter_corpus_files(
        repo_root,
        skip_private=not args.include_private_corpus,
        suffixes=_DEFAULT_SUFFIXES,
    )
    raw_text = bundle_path.read_text(encoding="utf-8", errors="replace")
    lines = normalize_lines(raw_text, rstrip_each=args.rstrip_lines)
    if args.strip_bundle_markers:
        lines = strip_bundle_marker_lines(lines)
    nlines = len(lines)
    if nlines == 0:
        print("Input: empty after normalization; nothing to do.")
        return 0

    quiet = args.quiet_gaps or (args.sweep_windows is not None)
    match_cap = (
        None if quiet or args.show_sample_matches <= 0 else args.show_sample_matches
    )

    if args.sweep_windows:
        strip_yes = bool(args.strip_bundle_markers)
        rstrip_yes = bool(args.rstrip_lines)
        print(f"Input: {bundle_path}")
        print(f" Repo root: {repo_root}")
        print(
            f" Sweep: strip_markers={strip_yes} rstrip_lines={rstrip_yes} | "
            f"corpus_files={len(corpus)} | input_lines={nlines}"
        )
        print()
        print(
            "| window | covered % | uncovered % | gap_blocks | idx_entries | match_windows "
            "| gap ranges (1-based) |"
        )
        print(
            "| -----: | --------: | ----------: | ---------: | ----------: | "
            "------------: | -------------------- |"
        )
        worst_pct = 0.0
        for window in windows:
            pr, _samples = run_pass(
                lines,
                corpus,
                repo_root,
                window,
                rstrip_each=args.rstrip_lines,
                match_cap=None,
            )
            pct_cov = 100.0 - pr.pct_uncovered
            worst_pct = max(worst_pct, pr.pct_uncovered)
            ranges_s = ", ".join(f"{a}-{b}" for a, b in pr.gap_ranges[:12])
            if len(pr.gap_ranges) > 12:
                ranges_s += f", …(+{len(pr.gap_ranges) - 12})"
            if not ranges_s:
                ranges_s = "—"
            print(
                f"| {pr.window} | {pct_cov:.2f} | {pr.pct_uncovered:.2f} | "
                f"{pr.gap_blocks} | {pr.index_entries} | {pr.match_windows} | {ranges_s} |"
            )
        if args.fail_if_uncovered_pct_above is not None:
            if worst_pct > args.fail_if_uncovered_pct_above + 1e-9:
                print(
                    f"\nFAIL: worst uncovered {worst_pct:.2f}% > "
                    f"{args.fail_if_uncovered_pct_above}%",
                    file=sys.stderr,
                )
                return 3
        return 0

    window = windows[0]
    pr, samples = run_pass(
        lines,
        corpus,
        repo_root,
        window,
        rstrip_each=args.rstrip_lines,
        match_cap=match_cap,
    )
    covered_n = pr.covered_n
    nlines = pr.nlines
    pct_uncovered = pr.pct_uncovered
    pct_covered = 100.0 - pct_uncovered
    match_windows = pr.match_windows

    print(f"Input: {bundle_path}")
    print(f"Repo root: {repo_root}")
    print(
        f"Corpus files indexed: {len(corpus)} (suffixes: {', '.join(_DEFAULT_SUFFIXES)})"
    )
    print(f"Index entries (unique windows): {pr.index_entries}")
    print(f"Window size: {window} lines")
    print(f"Input lines: {nlines}  covered: {covered_n} ({pct_covered:.2f}%)")
    print(f"Uncovered lines: {nlines - covered_n} ({pct_uncovered:.2f}%)")
    print(f"Matching windows in input (with overlap): {match_windows}")
    print()

    if args.show_sample_matches and samples and not quiet:
        print("--- sample matching windows (concat line -> corpus file:line) ---")
        for cl, rel, fl in samples:
            print(f"  @{cl} -> {rel}:{fl}")
        print()

    gaps = [g for g in pr.gap_ranges if g[1] - g[0] + 1 >= args.min_gap_lines]
    reported = 0
    if gaps and not quiet:
        print(f"--- gaps (uncovered line ranges, 1-based): {len(gaps)} blocks ---")
        for start, end in gaps:
            if reported >= args.max_gaps:
                rem = len(gaps) - reported
                print(f"… {rem} more gap(s); raise --max-gaps to see previews")
                break
            n_in_gap = end - start + 1
            print(f"  lines {start}-{end} ({n_in_gap} lines)")
            pv = preview_gap(lines, start, end, max_lines=args.preview_lines)
            for pl in pv.split("\n")[: args.preview_lines + 2]:
                print(f"    | {pl}")
            reported += 1
    elif gaps and quiet:
        print(f"--- gaps (quiet): {len(gaps)} blocks ---")
        print(", ".join(f"{a}-{b}" for a, b in gaps))
    elif not gaps:
        print("--- no uncovered gaps (full coverage at this window size) ---")

    if args.fail_if_uncovered_pct_above is not None:
        if pct_uncovered > args.fail_if_uncovered_pct_above + 1e-9:
            print(
                f"\nFAIL: uncovered {pct_uncovered:.2f}% > "
                f"{args.fail_if_uncovered_pct_above}%",
                file=sys.stderr,
            )
            return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
