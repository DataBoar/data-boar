#!/usr/bin/env python3
"""Bump or check the Homebrew formula against PyPI (#1425).

The formula tracks the **published PyPI** sdist (host pip install), not the
git-only ``1.8.0-beta`` line and not the Linux nfpm embedded-CPython payload.

Examples::

    uv run python scripts/homebrew_formula_bump.py --check
    uv run python scripts/homebrew_formula_bump.py --write
    uv run python scripts/homebrew_formula_bump.py --write --version 1.7.4.post12
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path
from typing import Any

PYPI_PROJECT = "data-boar"
FORMULA_REL = Path("packaging/homebrew/Formula/data-boar.rb")
_URL_RE = re.compile(
    r'^  url "(https://files\.pythonhosted\.org/[^"]+)"\s*$', re.MULTILINE
)
_SHA_RE = re.compile(r'^  sha256 "([0-9a-f]{64})"\s*$', re.MULTILINE)
_SDIST_VER_RE = re.compile(r"data_boar-(.+)\.tar\.gz$")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def formula_path(root: Path | None = None) -> Path:
    return (root or _repo_root()) / FORMULA_REL


def parse_formula(text: str) -> tuple[str, str, str]:
    url_m = _URL_RE.search(text)
    sha_m = _SHA_RE.search(text)
    if not url_m or not sha_m:
        raise SystemExit("formula is missing url or sha256 stanzas")
    url = url_m.group(1)
    sha = sha_m.group(1)
    file_m = _SDIST_VER_RE.search(url.rsplit("/", 1)[-1])
    if not file_m:
        raise SystemExit(f"cannot parse version from sdist url: {url}")
    return file_m.group(1), url, sha


def fetch_pypi_sdist(version: str | None) -> tuple[str, str, str]:
    """Return (version, sdist_url, sha256) from PyPI JSON."""
    url = f"https://pypi.org/pypi/{PYPI_PROJECT}/json"
    if version:
        url = f"https://pypi.org/pypi/{PYPI_PROJECT}/{version}/json"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload: dict[str, Any] = json.load(resp)
    ver = str(payload["info"]["version"])
    sdists = [
        u
        for u in payload.get("urls") or []
        if u.get("packagetype") == "sdist"
        and str(u.get("filename", "")).endswith(".tar.gz")
    ]
    if not sdists:
        raise SystemExit(f"PyPI has no sdist for data-boar {ver}")
    item = sdists[0]
    sha = str((item.get("digests") or {}).get("sha256") or "")
    if len(sha) != 64:
        raise SystemExit(f"PyPI sdist is missing sha256 for data-boar {ver}")
    return ver, str(item["url"]), sha


def render_formula(text: str, url: str, sha256: str) -> str:
    if not _URL_RE.search(text) or not _SHA_RE.search(text):
        raise SystemExit("formula is missing url or sha256 stanzas")
    text = _URL_RE.sub(f'  url "{url}"', text, count=1)
    text = _SHA_RE.sub(f'  sha256 "{sha256}"', text, count=1)
    return text


def cmd_check(*, root: Path, expect_latest: bool) -> int:
    path = formula_path(root)
    text = path.read_text(encoding="utf-8")
    ver, url, sha = parse_formula(text)
    pypi_ver, pypi_url, pypi_sha = fetch_pypi_sdist(None if expect_latest else ver)
    if expect_latest and pypi_ver != ver:
        print(
            f"formula version {ver} is behind PyPI {pypi_ver} (run --write)",
            file=sys.stderr,
        )
        return 1
    if url != pypi_url or sha != pypi_sha:
        print(
            "formula url/sha256 does not match PyPI sdist for "
            f"{ver}:\n  formula {url} {sha}\n  pypi    {pypi_url} {pypi_sha}",
            file=sys.stderr,
        )
        return 1
    print(f"ok: Formula/data-boar.rb matches PyPI sdist {ver}")
    return 0


def cmd_write(*, root: Path, version: str | None) -> int:
    path = formula_path(root)
    text = path.read_text(encoding="utf-8")
    ver, url, sha = fetch_pypi_sdist(version)
    new = render_formula(text, url, sha)
    if new == text:
        print(f"unchanged: already at PyPI sdist {ver}")
        return 0
    path.write_text(new, encoding="utf-8")
    print(f"wrote {path.relative_to(root)} -> {ver}")
    print(f"  url    {url}")
    print(f"  sha256 {sha}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--check",
        action="store_true",
        help="Verify formula url/sha256 match the PyPI sdist for that version.",
    )
    mode.add_argument(
        "--write",
        action="store_true",
        help="Rewrite formula url/sha256 from PyPI (latest, or --version).",
    )
    parser.add_argument(
        "--version",
        help="Pin a published PyPI version (with --write). Default: latest.",
    )
    parser.add_argument(
        "--latest",
        action="store_true",
        help="With --check, fail if the formula is not the latest PyPI version.",
    )
    args = parser.parse_args(argv)
    root = _repo_root()
    if args.check:
        return cmd_check(root=root, expect_latest=bool(args.latest))
    return cmd_write(root=root, version=args.version)


if __name__ == "__main__":
    raise SystemExit(main())
