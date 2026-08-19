"""Generate void-packages templates for native xbps (#1404 / ADR-0084).

nfpm does not emit xbps. Connector subpackage *lists* still come from
``EXTRAS_MANIFEST`` via the same ``native_subpackages.toml`` map as #1403.
The product launcher never calls ``systemctl`` — Void is the systemd-coupling canary.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from core.extras_manifest import (
    EMBEDDED_INTERPRETER_NATIVE,
    build_manifest,
)
from core.native_nfpm import (
    CORE_PACKAGE,
    project_version,
    read_subpackage_map,
    repo_root,
)

# Layer-2 Void package names (glibc and musl repos share these names).
# No python3 — interpreter is embedded. No p7zip* (.7z is optional py7zr).
VOID_LAYER2_DEPENDS: tuple[str, ...] = (
    "openssl",
    "zlib",
    "libffi",
    "tesseract-ocr",
)

_COMMERCIAL_NOTICE = (
    "ADR-0084: embedded cp314t does NOT unlock Enterprise. "
    "Entitlement remains worker caps (#551) + pro_prefilter_accel."
)

# void-packages short_desc hard limit is 72 characters.
_SHORT_DESC = "Sensitive-data discovery (native Enterprise channel)"


def void_dir() -> Path:
    return repo_root() / "packaging" / "void"


def generated_dir() -> Path:
    return void_dir() / "generated"


def generated_srcpkg_dir() -> Path:
    return generated_dir() / "srcpkgs" / CORE_PACKAGE


def runit_run_source() -> Path:
    return void_dir() / "files" / "data-boar" / "run"


def pep440_to_xbps_version(pep440: str) -> str:
    """Map PEP 440 to a void-packages ``version=`` token (no hyphen).

    ``1.8.0-beta`` → ``1.8.0beta1``; ``1.8.0-rc1`` → ``1.8.0rc1``; stable unchanged.
    """
    raw = pep440.strip()
    match = re.fullmatch(
        r"(\d+(?:\.\d+)*)(?:-(alpha|beta|rc)(?:\.?(\d+))?)?$",
        raw,
        flags=re.IGNORECASE,
    )
    if not match:
        raise ValueError(f"unsupported native version for xbps: {pep440!r}")
    base, pre, num = match.group(1), match.group(2), match.group(3)
    if not pre:
        return base
    suffix = pre.lower()
    serial = num or "1"
    return f"{base}{suffix}{serial}"


def _subpackage_block(
    *, package_name: str, extra_name: str, packages: list[str]
) -> str:
    pkg_list = ", ".join(packages) if packages else extra_name
    # bash allows hyphenated function names; void-packages relies on that.
    return (
        f"{package_name}_package() {{\n"
        f'\tdepends="${{sourcepkg}}>=${{version}}_${{revision}}"\n'
        f'\tshort_desc+=" - {extra_name} connector extra"\n'
        f"\t# EXTRAS_MANIFEST packages: {pkg_list}\n"
        f"\tpkg_install() {{\n"
        f'\t\tif [ ! -d "${{DESTDIR}}/usr/lib/data-boar/extras/{extra_name}" ]; then\n'
        f'\t\t\tmsg_error "extras/{extra_name} missing from staging — refuse empty subpackage\\n"\n'
        f"\t\tfi\n"
        f"\t\tvmove usr/lib/data-boar/extras/{extra_name}\n"
        f"\t}}\n"
        f"}}\n"
    )


def render_template(
    *,
    manifest: dict[str, Any] | None = None,
    version: str | None = None,
) -> str:
    """Render ``srcpkgs/data-boar/template`` (bash, consumed by xbps-src)."""
    data = (
        manifest
        if manifest is not None
        else build_manifest(probe=False, include_embedded_interpreter=True)
    )
    pep = version or project_version()
    xbps_ver = pep440_to_xbps_version(pep)
    extras = data.get("extras") or {}
    sub_map = read_subpackage_map()
    sub_names = sorted(sub_map)
    python_bin = str(
        (data.get("embedded_interpreter") or EMBEDDED_INTERPRETER_NATIVE)["python_bin"]
    )
    depends = " ".join(VOID_LAYER2_DEPENDS)
    subpackages_line = " ".join(sub_names)

    blocks: list[str] = []
    for package_name in sub_names:
        extra_name = sub_map[package_name]
        if extra_name not in extras:
            raise KeyError(
                f"subpackage {package_name!r} maps to extra {extra_name!r}, "
                "but that extra is missing from EXTRAS_MANIFEST / pyproject"
            )
        meta = extras[extra_name]
        blocks.append(
            _subpackage_block(
                package_name=package_name,
                extra_name=extra_name,
                packages=list(meta.get("packages") or []),
            )
        )

    sub_fn = "\n".join(blocks)
    return (
        f"# Template file for '{CORE_PACKAGE}'\n"
        f"# Generated — do not hand-edit. Run:\n"
        f"#   uv run python scripts/generate_void_xbps_packages.py --write\n"
        f"# {_COMMERCIAL_NOTICE}\n"
        f"# Overlay lives in this product repo (packaging/void/). Upstream\n"
        f"# void-packages submission is out of scope for #1404.\n"
        f"# Validation: Podman Void — not lab metal. glibc staging is x86_64 only.\n"
        f"pkgname={CORE_PACKAGE}\n"
        f"version={xbps_ver}\n"
        f"revision=1\n"
        f'archs="x86_64"\n'
        f"create_wrksrc=yes\n"
        f"nocross=yes\n"
        f'short_desc="{_SHORT_DESC}"\n'
        f'maintainer="Data Boar maintainers <contact@databoar.com.br>"\n'
        f'license="AGPL-3.0-or-later"\n'
        f'homepage="https://github.com/DataBoar/data-boar"\n'
        f'depends="{depends}"\n'
        f'subpackages="{subpackages_line}"\n'
        f"\n"
        f"do_install() {{\n"
        f'\tif [ ! -x "${{FILESDIR}}/staging{python_bin}" ]; then\n'
        f'\t\tmsg_error "missing embedded interpreter in FILESDIR/staging (ADR-0084)\\n"\n'
        f"\tfi\n"
        f"\tvmkdir usr/lib\n"
        f'\tcp -a "${{FILESDIR}}/staging/usr/lib/data-boar" "${{DESTDIR}}/usr/lib/data-boar"\n'
        f'\tvbin "${{FILESDIR}}/staging/usr/bin/data-boar"\n'
        f"\tvmkdir etc/data-boar\n"
        f'\tif [ -f "${{FILESDIR}}/staging/etc/data-boar/config.example.yaml" ]; then\n'
        f'\t\tvinstall "${{FILESDIR}}/staging/etc/data-boar/config.example.yaml" 644 etc/data-boar\n'
        f"\tfi\n"
        f"\tvsv data-boar\n"
        f"}}\n"
        f"\n"
        f"{sub_fn}"
    )


def render_runit_run() -> str:
    """Canonical runit run script (also the committed source under files/)."""
    return runit_run_source().read_text(encoding="utf-8")


def build_packages_meta(
    *,
    manifest: dict[str, Any] | None = None,
    version: str | None = None,
) -> dict[str, Any]:
    data = (
        manifest
        if manifest is not None
        else build_manifest(probe=False, include_embedded_interpreter=True)
    )
    pep = version or project_version()
    sub = read_subpackage_map()
    return {
        "schema_version": 1,
        "issue": 1404,
        "adr": "0084",
        "version_pep440": pep,
        "version_xbps": pep440_to_xbps_version(pep),
        "packager": "xbps",
        "void_packages_overlay": "packaging/void/generated/srcpkgs",
        "upstream_void_packages": "out_of_scope",
        "validation": "podman_void",
        "init": "runit",
        "layer1": "vendored_pinned_wheelhouse",
        "layer2": list(VOID_LAYER2_DEPENDS),
        "commercial_protection": "worker_caps_and_pro_prefilter_accel",
        "embedded_interpreter": dict(
            data.get("embedded_interpreter") or EMBEDDED_INTERPRETER_NATIVE
        ),
        "subpackages": {
            pkg: {
                "extra": extra,
                "packages": list(
                    (data.get("extras") or {}).get(extra, {}).get("packages") or []
                ),
                "modules": list(
                    (data.get("extras") or {}).get(extra, {}).get("modules") or []
                ),
            }
            for pkg, extra in sorted(sub.items())
        },
        "subpackage_symlinks": sorted(sub),
    }


def write_generated_void(
    *,
    out_dir: Path | None = None,
    manifest: dict[str, Any] | None = None,
    version: str | None = None,
) -> dict[str, Path]:
    """Write generated srcpkg + meta. Return map of logical name → path."""
    dest_root = out_dir or generated_dir()
    srcpkg = dest_root / "srcpkgs" / CORE_PACKAGE
    files_sv = srcpkg / "files" / "data-boar"
    srcpkg.mkdir(parents=True, exist_ok=True)
    files_sv.mkdir(parents=True, exist_ok=True)

    template_text = render_template(manifest=manifest, version=version)
    template_path = srcpkg / "template"
    template_path.write_text(template_text, encoding="utf-8")

    run_path = files_sv / "run"
    run_path.write_text(render_runit_run(), encoding="utf-8")
    run_path.chmod(run_path.stat().st_mode | 0o111)

    meta_path = dest_root / "PACKAGES.meta.json"
    meta_path.write_text(
        json.dumps(
            build_packages_meta(manifest=manifest, version=version),
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    links_path = dest_root / "srcpkgs" / "SUBPACKAGE_LINKS.txt"
    links_path.write_text(
        "\n".join(sorted(read_subpackage_map())) + "\n",
        encoding="utf-8",
    )
    return {
        "template": template_path,
        "runit_run": run_path,
        "meta": meta_path,
        "links": links_path,
    }


def expected_generated_text(
    *,
    manifest: dict[str, Any] | None = None,
    version: str | None = None,
) -> dict[str, str]:
    return {
        "template": render_template(manifest=manifest, version=version),
        "runit_run": render_runit_run(),
        "meta": json.dumps(
            build_packages_meta(manifest=manifest, version=version),
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        "links": "\n".join(sorted(read_subpackage_map())) + "\n",
    }


def assert_generated_in_sync(
    *,
    generated: Path | None = None,
    manifest: dict[str, Any] | None = None,
) -> None:
    """Fail if committed generated overlay diverges from a fresh render."""
    root = generated or generated_dir()
    expected = expected_generated_text(manifest=manifest)
    on_disk = {
        "template": (root / "srcpkgs" / CORE_PACKAGE / "template").read_text(
            encoding="utf-8"
        ),
        "runit_run": (
            root / "srcpkgs" / CORE_PACKAGE / "files" / "data-boar" / "run"
        ).read_text(encoding="utf-8"),
        "meta": (root / "PACKAGES.meta.json").read_text(encoding="utf-8"),
        "links": (root / "srcpkgs" / "SUBPACKAGE_LINKS.txt").read_text(
            encoding="utf-8"
        ),
    }
    drifted = [name for name in expected if on_disk[name] != expected[name]]
    if drifted:
        raise AssertionError(
            f"void xbps generated drift: {drifted}. "
            "Run: uv run python scripts/generate_void_xbps_packages.py --write"
        )
