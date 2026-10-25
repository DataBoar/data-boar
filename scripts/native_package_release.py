#!/usr/bin/env python3
"""Native package release helpers (#1408).

Validate packager filename conventions, write SHA256SUMS, and merge
``native_packages`` into ``release-manifest.json``.

The hand-built recipe-proof ``.deb`` is not a publish candidate — this module only
handles artifacts produced by ``nfpm`` from the wheelhouse populate script.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

# Issue #1408 naming contract (arch token required; hyphen-only .deb is invalid).
_DEB = re.compile(r"^data-boar_[^/]+_(amd64|arm64|i386)\.deb$")
_RPM = re.compile(r"^data-boar-[^/]+-[^/]+\.(x86_64|aarch64|noarch)\.rpm$")
_APK = re.compile(r"^data-boar-[^/]+-r[0-9]+\.apk$")
# nfpm 2.x apk default: name_version_arch.apk (underscores + arch).
_NFPM_APK = re.compile(
    r"^data-boar_(?P<stem>.+)_(?P<arch>x86_64|amd64|aarch64|arm64|any)\.apk$"
)
_PACMAN = re.compile(
    r"^data-boar-[^/]+-[0-9]+-(x86_64|aarch64|any)\.pkg\.tar(\.zst|\.xz)?$"
)

PACKAGE_GLOBS: tuple[str, ...] = (
    "*.deb",
    "*.rpm",
    "*.apk",
    "*.pkg.tar.zst",
    "*.pkg.tar.xz",
    "*.pkg.tar",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def sha256_file_hex(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def classify_package_name(name: str) -> str | None:
    """Return packager id if ``name`` matches the #1408 convention."""
    if _DEB.fullmatch(name):
        return "deb"
    if _RPM.fullmatch(name):
        return "rpm"
    if _APK.fullmatch(name):
        return "apk"
    if _PACMAN.fullmatch(name):
        return "pacman"
    return None


def reject_reason(name: str) -> str:
    """Explain why a filename is not a publishable native package asset."""
    if name in {"SHA256SUMS", "SHA256SUMS.asc", "native-packages-manifest.json"}:
        return ""
    if name.endswith(".deb") and not _DEB.fullmatch(name):
        return (
            f"{name}: deb must be <name>_<version>_<arch>.deb "
            "(hyphen-only names break apt/reprepro/aptly)"
        )
    if name.endswith(".rpm") and not _RPM.fullmatch(name):
        return f"{name}: rpm must be <name>-<version>-<release>.<arch>.rpm"
    if name.endswith(".apk") and not _APK.fullmatch(name):
        return f"{name}: apk must be <name>-<version>-r<rel>.apk"
    if ".pkg.tar" in name and not _PACMAN.fullmatch(name):
        return f"{name}: pacman must be <name>-<version>-<rel>-<arch>.pkg.tar.zst"
    return f"{name}: unrecognized native package filename"


def alpine_apk_name_from_nfpm(name: str) -> str | None:
    """Map nfpm ``name_ver_arch.apk`` to Alpine ``name-ver-rN.apk``.

    Example: ``data-boar_1.8.0-beta-r1_x86_64.apk`` →
    ``data-boar-1.8.0-beta-r1.apk``. Already-Alpine names return ``None``.
    """
    match = _NFPM_APK.fullmatch(name)
    if match is None:
        return None
    return f"data-boar-{match.group('stem')}.apk"


def normalize_nfpm_apk_filenames(directory: Path) -> list[Path]:
    """Rename nfpm apk artifacts in ``directory`` to the #1408 Alpine contract."""
    renamed: list[Path] = []
    for path in sorted(directory.glob("*.apk")):
        dest_name = alpine_apk_name_from_nfpm(path.name)
        if dest_name is None or dest_name == path.name:
            continue
        dest = path.with_name(dest_name)
        if dest.exists() and dest.resolve() != path.resolve():
            raise FileExistsError(
                f"cannot normalize {path.name}: {dest_name} already exists"
            )
        path.rename(dest)
        renamed.append(dest)
    return renamed


def list_package_files(directory: Path) -> list[Path]:
    files: list[Path] = []
    for pattern in PACKAGE_GLOBS:
        files.extend(p for p in directory.glob(pattern) if p.is_file())
    return sorted({p.resolve() for p in files}, key=lambda p: p.name)


def validate_package_names(directory: Path) -> list[str]:
    """Return error strings; empty list means all package files are valid."""
    errors: list[str] = []
    packages = list_package_files(directory)
    if not packages:
        errors.append(f"no native packages found under {directory}")
        return errors
    for path in packages:
        if classify_package_name(path.name) is None:
            errors.append(reject_reason(path.name))
    return errors


def write_sha256sums(directory: Path, *, out_name: str = "SHA256SUMS") -> Path:
    """Write GNU ``sha256sum``-compatible file for package assets only."""
    packages = list_package_files(directory)
    lines = [f"{sha256_file_hex(path)}  {path.name}\n" for path in packages]
    out = directory / out_name
    out.write_text("".join(lines), encoding="utf-8")
    return out


def native_packages_payload(directory: Path) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for path in list_package_files(directory):
        packager = classify_package_name(path.name)
        if packager is None:
            continue
        entries.append(
            {
                "name": path.name,
                "packager": packager,
                "sha256": sha256_file_hex(path),
            }
        )
    return entries


def merge_native_packages(
    manifest: dict[str, Any],
    entries: list[dict[str, str]],
) -> dict[str, Any]:
    """Return a copy of ``manifest`` with ``native_packages`` replaced."""
    merged = dict(manifest)
    merged["native_packages"] = entries
    return merged


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected JSON object")
    return data


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def maybe_gpg_sign_sums(sums_path: Path) -> Path | None:
    """Detach-sign SHA256SUMS when ``NATIVE_PACKAGE_GPG_PRIVATE_KEY`` is set.

    Key ceremony lives on #1405 / ADR-0089. Without the secret, skip (no fake
    signature). The signed repo (#1405) consumes the same package bytes.
    """
    armored = os.environ.get("NATIVE_PACKAGE_GPG_PRIVATE_KEY", "").strip()
    if not armored:
        return None
    if not sums_path.is_file():
        raise FileNotFoundError(sums_path)
    preexisting = os.environ.get("GNUPGHOME", "").strip()

    def _sign(gnupg_home: Path) -> Path:
        gnupg_home.mkdir(parents=True, exist_ok=True)
        gnupg_home.chmod(0o700)
        env = {**os.environ, "GNUPGHOME": str(gnupg_home)}
        subprocess.run(
            ["gpg", "--batch", "--import"],
            input=armored.encode("utf-8"),
            check=True,
            env=env,
            capture_output=True,
        )
        asc = sums_path.with_name(sums_path.name + ".asc")
        if asc.exists():
            asc.unlink()
        subprocess.run(
            [
                "gpg",
                "--batch",
                "--yes",
                "--detach-sign",
                "--armor",
                "-o",
                str(asc),
                str(sums_path),
            ],
            check=True,
            env=env,
            capture_output=True,
        )
        return asc

    if preexisting:
        return _sign(Path(preexisting))
    with tempfile.TemporaryDirectory(prefix="gnupg-native-") as tmp:
        return _sign(Path(tmp))


def _cmd_normalize_apk(directory: Path) -> int:
    try:
        renamed = normalize_nfpm_apk_filenames(directory)
    except OSError as err:
        print(f"native_package_release normalize-apk: {err}", file=sys.stderr)
        return 1
    if renamed:
        print(f"OK: renamed {len(renamed)} nfpm apk(s) to Alpine name-ver-rN.apk")
        for path in renamed:
            print(f"  {path.name}")
    else:
        print("OK: no nfpm underscore apk names to normalize")
    return 0


def _cmd_names(directory: Path) -> int:
    errors = validate_package_names(directory)
    if errors:
        print("native_package_release names: FAIL", file=sys.stderr)
        for err in errors:
            print(f"  {err}", file=sys.stderr)
        return 1
    found = list_package_files(directory)
    print(f"OK: {len(found)} package(s) match packager naming conventions")
    return 0


def _cmd_checksums(directory: Path) -> int:
    errors = validate_package_names(directory)
    if errors:
        print("native_package_release checksums: names FAIL", file=sys.stderr)
        for err in errors:
            print(f"  {err}", file=sys.stderr)
        return 1
    sums = write_sha256sums(directory)
    sidecar = directory / "native-packages-manifest.json"
    write_json(sidecar, {"native_packages": native_packages_payload(directory)})
    signed = maybe_gpg_sign_sums(sums)
    extra = f" + {signed.name}" if signed else " (no GPG key; SHA256SUMS only)"
    print(f"Wrote {sums.name} and {sidecar.name}{extra}")
    return 0


def _cmd_merge_manifest(manifest_path: Path, directory: Path) -> int:
    """Merge native_packages[] into an existing SBOM/licensing manifest.

    Refuses to synthesize a stub (empty ``files[]``). A missing or empty
    manifest must fail so CI never ``gh release upload --clobber`` a wipe.
    """
    if not manifest_path.is_file():
        print(
            f"native_package_release merge-manifest: missing {manifest_path} "
            "(refusing to synthesize a stub)",
            file=sys.stderr,
        )
        return 1
    payload = load_json(manifest_path)
    files = payload.get("files")
    if not isinstance(files, list) or not files:
        print(
            f"native_package_release merge-manifest: {manifest_path} has no "
            "files[] (refusing to clobber with an empty stub)",
            file=sys.stderr,
        )
        return 1
    merged = merge_native_packages(payload, native_packages_payload(directory))
    write_json(manifest_path, merged)
    count = len(merged.get("native_packages") or [])
    print(f"OK: {manifest_path} now lists {count} native_packages")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dir",
        type=Path,
        default=Path("dist/native-packages"),
        help="Directory of nfpm output (default: dist/native-packages)",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser(
        "normalize-apk",
        help="Rename nfpm name_ver_arch.apk to Alpine name-ver-rN.apk",
    )
    sub.add_parser("names", help="Fail if any package filename breaks convention")
    sub.add_parser("checksums", help="Write SHA256SUMS + native-packages-manifest.json")
    merge = sub.add_parser(
        "merge-manifest",
        help="Add native_packages[] to release-manifest.json",
    )
    merge.add_argument(
        "--manifest",
        type=Path,
        default=Path("release-manifest.json"),
        help="Path to an existing release-manifest.json (must already have files[])",
    )
    args = parser.parse_args(argv)
    directory = args.dir if args.dir.is_absolute() else _repo_root() / args.dir
    directory.mkdir(parents=True, exist_ok=True)
    if args.cmd == "normalize-apk":
        return _cmd_normalize_apk(directory)
    if args.cmd == "names":
        return _cmd_names(directory)
    if args.cmd == "checksums":
        return _cmd_checksums(directory)
    if args.cmd == "merge-manifest":
        manifest = (
            args.manifest
            if args.manifest.is_absolute()
            else _repo_root() / args.manifest
        )
        return _cmd_merge_manifest(manifest, directory)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
