"""Filesystem connector: symlink loop guard and inode de-duplication."""

from __future__ import annotations

import os
from pathlib import Path

from connectors.filesystem_connector import iter_scan_files


def test_iter_scan_files_skips_circular_directory_symlinks(
    tmp_path: Path,
) -> None:
    root = tmp_path / "root"
    sub = root / "sub"
    sub.mkdir(parents=True)
    # sub/loop -> ..  creates a directory symlink cycle when walked naively.
    os.symlink("..", sub / "loop")

    files = list(iter_scan_files(root, recursive=True))
    assert files == []


def test_iter_scan_files_deduplicates_same_inode_via_symlink(
    tmp_path: Path,
) -> None:
    root = tmp_path / "root"
    root.mkdir()
    real = root / "data.txt"
    real.write_text("ID 123.456.789-00", encoding="utf-8")
    os.symlink(real, root / "alias.txt")

    files = list(iter_scan_files(root, recursive=True))
    assert len(files) == 1
    assert files[0].name == "data.txt"


def test_iter_scan_files_non_recursive_only_top_level(tmp_path: Path) -> None:
    root = tmp_path / "root"
    nested = root / "nested"
    nested.mkdir(parents=True)
    top = root / "top.txt"
    deep = nested / "deep.txt"
    top.write_text("a", encoding="utf-8")
    deep.write_text("b", encoding="utf-8")

    files = {p.name for p in iter_scan_files(root, recursive=False)}
    assert files == {"top.txt"}
