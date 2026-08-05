"""Generate nfpm YAML for native Enterprise packages (#1403 / ADR-0084).

Connector subpackage dependency lists are taken from ``EXTRAS_MANIFEST``
(or ``build_manifest``), never hand-authored. Packagers: deb, rpm, apk,
archlinux — not xbps (#1404).
"""

from __future__ import annotations

import json
import tomllib
from pathlib import Path
from typing import Any

import yaml

from core.extras_manifest import (
    EMBEDDED_INTERPRETER_NATIVE,
    build_manifest,
    load_manifest,
    repo_root,
)

# Formats this foundation targets (#1403). xbps is intentionally absent.
NFPM_PACKAGERS: tuple[str, ...] = ("deb", "rpm", "apk", "archlinux")

CORE_PACKAGE = "data-boar"

# Layer-2 plumbing — distro package names differ; overrides supply the truth.
# No p7zip*: .7z scanning uses optional pure-Python py7zr ([compressed] extra),
# not the system 7z binary. Hard-requiring p7zip also breaks Rocky/RHEL (EPEL-only).
LAYER2_DEPENDS: dict[str, list[str]] = {
    "deb": [
        "libc6",
        "libssl3 | libssl1.1",
        "zlib1g",
        "libffi8 | libffi7 | libffi6",
        "tesseract-ocr",
    ],
    "rpm": [
        "openssl-libs",
        "zlib",
        "libffi",
        "tesseract",
    ],
    "apk": [
        "libssl3",
        "zlib",
        "libffi",
        "tesseract-ocr",
    ],
    "archlinux": [
        "openssl",
        "zlib",
        "libffi",
        "tesseract",
    ],
}

_COMMERCIAL_NOTICE = (
    "ADR-0084: embedded cp314t does NOT unlock Enterprise. "
    "Entitlement remains worker caps (#551) + pro_prefilter_accel."
)


def nfpm_dir() -> Path:
    return repo_root() / "packaging" / "nfpm"


def generated_dir() -> Path:
    return nfpm_dir() / "generated"


def staging_dir() -> Path:
    return nfpm_dir() / "staging"


def subpackages_map_path() -> Path:
    return nfpm_dir() / "native_subpackages.toml"


def read_subpackage_map(path: Path | None = None) -> dict[str, str]:
    """Return ``{package_name: extra_name}`` from the naming-contract TOML."""
    data = tomllib.loads((path or subpackages_map_path()).read_text(encoding="utf-8"))
    raw = data.get("subpackages") or {}
    return {str(k): str(v) for k, v in raw.items()}


def project_version(pyproject: Path | None = None) -> str:
    path = pyproject or (repo_root() / "pyproject.toml")
    with path.open("rb") as handle:
        data = tomllib.load(handle)
    return str(data["project"]["version"])


def _dump_yaml(doc: dict[str, Any]) -> str:
    return yaml.safe_dump(
        doc,
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
        width=120,
    )


def build_core_nfpm_doc(*, version: str) -> dict[str, Any]:
    """Core package: embed prefix + layer-1 staging + layer-2 Depends overrides."""
    prefix = EMBEDDED_INTERPRETER_NATIVE["prefix"]
    return {
        "name": CORE_PACKAGE,
        "arch": "${NFPM_ARCH}",
        "platform": "linux",
        "version": version,
        "version_schema": "none",
        "release": "1",
        "section": "utils",
        "priority": "optional",
        "maintainer": "Data Boar maintainers <contact@databoar.com.br>",
        "description": (
            "Data Boar — sensitive-data discovery (native Enterprise channel).\n"
            f"{_COMMERCIAL_NOTICE}"
        ),
        "vendor": "Data Boar",
        "homepage": "https://github.com/DataBoar/data-boar",
        "license": "AGPL-3.0-or-later",
        # No Depends: python3 — interpreter is embedded (ADR-0084 channel a).
        "depends": [],
        "contents": [
            {
                "src": "staging/usr/lib/data-boar/",
                "dst": f"{prefix}/",
                "type": "tree",
            },
            {
                "src": "staging/usr/bin/data-boar",
                "dst": "/usr/bin/data-boar",
            },
            {
                "src": "staging/etc/data-boar/config.example.yaml",
                "dst": "/etc/data-boar/config.example.yaml",
                "type": "config|noreplace",
            },
        ],
        "overrides": {
            packager: {"depends": list(deps)}
            for packager, deps in LAYER2_DEPENDS.items()
        },
    }


def build_subpackage_nfpm_doc(
    *,
    package_name: str,
    extra_name: str,
    packages: list[str],
    modules: list[str],
    version: str,
) -> dict[str, Any]:
    """Connector subpackage: exact-version Depends on core; deps from manifest."""
    return {
        "name": package_name,
        "arch": "${NFPM_ARCH}",
        "platform": "linux",
        "version": version,
        "version_schema": "none",
        "release": "1",
        "section": "utils",
        "priority": "optional",
        "maintainer": "Data Boar maintainers <contact@databoar.com.br>",
        "description": (
            f"Data Boar connector extra [{extra_name}] "
            f"(packages: {', '.join(packages)}).\n"
            f"{_COMMERCIAL_NOTICE}"
        ),
        "vendor": "Data Boar",
        "homepage": "https://github.com/DataBoar/data-boar",
        "license": "AGPL-3.0-or-later",
        # Exact-version pin so subpackage cannot float against a different core ABI.
        "depends": [f"{CORE_PACKAGE} (= {version}-1)"],
        "contents": [
            {
                "src": f"staging/usr/lib/data-boar/extras/{extra_name}/",
                "dst": f"/usr/lib/data-boar/extras/{extra_name}/",
                "type": "tree",
            },
        ],
        "overrides": {
            "deb": {"depends": [f"{CORE_PACKAGE} (= {version}-1)"]},
            "rpm": {"depends": [f"{CORE_PACKAGE} = {version}-1"]},
            "apk": {"depends": [f"{CORE_PACKAGE}={version}-r1"]},
            "archlinux": {"depends": [f"{CORE_PACKAGE}={version}-1"]},
        },
    }


def render_all_nfpm_docs(
    *,
    manifest: dict[str, Any] | None = None,
    version: str | None = None,
) -> dict[str, dict[str, Any]]:
    """Build in-memory nfpm docs keyed by filename (e.g. ``data-boar.yaml``)."""
    data = (
        manifest
        if manifest is not None
        else build_manifest(probe=False, include_embedded_interpreter=True)
    )
    ver = version or project_version()
    extras = data.get("extras") or {}
    out: dict[str, dict[str, Any]] = {
        f"{CORE_PACKAGE}.yaml": build_core_nfpm_doc(version=ver),
    }
    for package_name, extra_name in sorted(read_subpackage_map().items()):
        if extra_name not in extras:
            raise KeyError(
                f"subpackage {package_name!r} maps to extra {extra_name!r}, "
                "but that extra is missing from EXTRAS_MANIFEST / pyproject"
            )
        meta = extras[extra_name]
        out[f"{package_name}.yaml"] = build_subpackage_nfpm_doc(
            package_name=package_name,
            extra_name=extra_name,
            packages=list(meta.get("packages") or []),
            modules=list(meta.get("modules") or []),
            version=ver,
        )
    return out


def build_packages_meta(
    *,
    manifest: dict[str, Any] | None = None,
    version: str | None = None,
) -> dict[str, Any]:
    """Sidecar inventory (not fed to nfpm) — packagers + embed + subpackage map."""
    data = (
        manifest
        if manifest is not None
        else build_manifest(probe=False, include_embedded_interpreter=True)
    )
    ver = version or project_version()
    sub = read_subpackage_map()
    return {
        "schema_version": 1,
        "issue": 1403,
        "adr": "0084",
        "version": ver,
        "packagers": list(NFPM_PACKAGERS),
        "excluded_packagers": ["xbps"],
        "layer1": "vendored_pinned_wheelhouse",
        "layer2": "distro_depends_overrides",
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
    }


def write_generated_nfpm(
    *,
    out_dir: Path | None = None,
    manifest: dict[str, Any] | None = None,
    version: str | None = None,
) -> dict[str, Path]:
    """Write generated/*.yaml + PACKAGES.meta.json; return map filename → path."""
    dest = out_dir or generated_dir()
    dest.mkdir(parents=True, exist_ok=True)
    docs = render_all_nfpm_docs(manifest=manifest, version=version)
    written: dict[str, Path] = {}
    for name, doc in docs.items():
        path = dest / name
        path.write_text(_dump_yaml(doc), encoding="utf-8")
        written[name] = path
    meta_path = dest / "PACKAGES.meta.json"
    meta_path.write_text(
        json.dumps(
            build_packages_meta(manifest=manifest, version=version),
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    written[meta_path.name] = meta_path
    # Drop stale generated YAMLs not in this render set.
    keep = set(docs)
    for stale in dest.glob("*.yaml"):
        if stale.name not in keep:
            stale.unlink()
    return written


def expected_generated_yaml_text(
    *,
    manifest: dict[str, Any] | None = None,
    version: str | None = None,
) -> dict[str, str]:
    docs = render_all_nfpm_docs(manifest=manifest, version=version)
    return {name: _dump_yaml(doc) for name, doc in docs.items()}


def assert_generated_in_sync(
    *,
    generated: Path | None = None,
    manifest: dict[str, Any] | None = None,
) -> None:
    """Fail if committed generated/*.yaml diverge from a fresh render."""
    root = generated or generated_dir()
    expected = expected_generated_yaml_text(manifest=manifest)
    on_disk = {
        p.name: p.read_text(encoding="utf-8") for p in sorted(root.glob("*.yaml"))
    }
    missing = sorted(set(expected) - set(on_disk))
    extra = sorted(set(on_disk) - set(expected))
    if missing or extra:
        raise AssertionError(
            f"nfpm generated set drift: missing={missing} extra={extra}. "
            "Run: uv run python scripts/generate_nfpm_packages.py --write"
        )
    drifted = [n for n in expected if on_disk[n] != expected[n]]
    if drifted:
        raise AssertionError(
            f"nfpm generated content drift: {drifted}. "
            "Run: uv run python scripts/generate_nfpm_packages.py --write"
        )


def load_or_build_native_manifest() -> dict[str, Any]:
    """Prefer repo EXTRAS_MANIFEST; always ensure embedded_interpreter for native."""
    try:
        data = load_manifest(probe_if_missing=False)
    except FileNotFoundError:
        data = build_manifest(probe=False, include_embedded_interpreter=True)
    if "embedded_interpreter" not in data:
        data = {**data, "embedded_interpreter": dict(EMBEDDED_INTERPRETER_NATIVE)}
    return data
