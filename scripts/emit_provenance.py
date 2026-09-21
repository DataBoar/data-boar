#!/usr/bin/env python3
"""Emit and verify a local provenance record (#1950).

This is **not** signed SLSA. GitHub OIDC attestation remains
``actions/attest-build-provenance`` in ``.github/workflows/sbom.yml``
(``data-boar.intoto.jsonl``). The local record binds source commit, version,
toolchain, workflow inputs, artifact digests, and SBOM digests so wrappers
can fail closed without inventing a signature.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

KIND = "data-boar:local-unsigned-provenance-record"
DEFAULT_OUT = Path("sbom") / "provenance-local.json"
DEFAULT_APP = Path("sbom-python.cdx.json")
DEFAULT_RUNTIME = Path("sbom-docker-image.cdx.json")
DEFAULT_ATTESTATION = Path("data-boar.intoto.jsonl")
REQUIRED_TOP = (
    "kind",
    "signed_slsa",
    "source_commit",
    "version",
    "toolchain",
    "workflow_inputs",
    "artifact_digests",
    "sbom_digests",
    "signed_attestation",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run_text(cmd: list[str], *, cwd: Path) -> str | None:
    if not shutil.which(cmd[0]):
        return None
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd),
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except OSError:
        return None
    if proc.returncode != 0:
        return None
    return (proc.stdout or "").strip() or None


def read_project_version(root: Path) -> str:
    data = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    version = (data.get("project") or {}).get("version")
    if not version:
        raise ValueError("pyproject.toml: missing [project].version")
    return str(version)


def git_head(root: Path) -> str:
    text = _run_text(["git", "rev-parse", "HEAD"], cwd=root)
    if not text or len(text) != 40:
        raise ValueError("git rev-parse HEAD did not return a 40-char SHA")
    return text


def collect_toolchain(root: Path) -> dict[str, str]:
    out: dict[str, str] = {"python": sys.version.split()[0]}
    uv_ver = _run_text(["uv", "--version"], cwd=root)
    if uv_ver:
        out["uv"] = uv_ver
    rustc = _run_text(["rustc", "--version"], cwd=root)
    if rustc:
        out["rustc"] = rustc
    return out


def collect_workflow_inputs() -> dict[str, str]:
    keys = (
        "GITHUB_EVENT_NAME",
        "GITHUB_WORKFLOW",
        "GITHUB_SHA",
        "GITHUB_REF",
        "GITHUB_RUN_ID",
    )
    inputs = {key.lower(): os.environ.get(key, "") for key in keys}
    if not any(inputs.values()):
        inputs["event_name"] = "local"
    return inputs


def _optional_digest(path: Path) -> str | None:
    if not path.is_file():
        return None
    return sha256_file(path)


def build_record(
    root: Path,
    *,
    source_commit: str | None,
    version: str | None,
    application: Path,
    runtime: Path,
    attestation: Path,
    require_sboms: bool,
    require_signed_attestation: bool,
) -> dict[str, Any]:
    app = application if application.is_absolute() else root / application
    run = runtime if runtime.is_absolute() else root / runtime
    att = attestation if attestation.is_absolute() else root / attestation

    if require_sboms:
        missing = [str(p) for p in (app, run) if not p.is_file()]
        if missing:
            raise FileNotFoundError(
                "SBOM files required but missing: " + ", ".join(missing)
            )
    if require_signed_attestation and not att.is_file():
        raise FileNotFoundError(
            f"signed attestation required but missing: {att} "
            "(GitHub OIDC only; local runs must not claim SLSA)"
        )

    sbom_digests: dict[str, str] = {}
    app_hash = _optional_digest(app)
    run_hash = _optional_digest(run)
    if app_hash:
        sbom_digests["application"] = app_hash
    if run_hash:
        sbom_digests["runtime"] = run_hash

    artifact_digests: dict[str, str] = {}
    for rel in ("build-digest.txt", "release-manifest.json"):
        digest = _optional_digest(root / rel)
        if digest:
            artifact_digests[rel] = digest

    signed: dict[str, str] | None = None
    if att.is_file():
        signed = {"path": str(att.name), "sha256": sha256_file(att)}

    return {
        "kind": KIND,
        "signed_slsa": False,
        "source_commit": source_commit or git_head(root),
        "version": version or read_project_version(root),
        "toolchain": collect_toolchain(root),
        "workflow_inputs": collect_workflow_inputs(),
        "artifact_digests": artifact_digests,
        "sbom_digests": sbom_digests,
        "signed_attestation": signed,
    }


def verify_record(
    record: dict[str, Any],
    *,
    require_sboms: bool,
    require_signed_attestation: bool,
) -> None:
    for key in REQUIRED_TOP:
        if key not in record:
            raise ValueError(f"provenance record missing {key!r}")
    if record.get("kind") != KIND:
        raise ValueError(f"unexpected kind: {record.get('kind')!r}")
    if record.get("signed_slsa") is not False:
        raise ValueError(
            "local record must set signed_slsa=false; "
            "do not claim SLSA without data-boar.intoto.jsonl from CI"
        )
    commit = str(record.get("source_commit") or "")
    if len(commit) != 40 or any(c not in "0123456789abcdef" for c in commit.lower()):
        raise ValueError("source_commit must be a 40-char hex SHA")
    if not str(record.get("version") or "").strip():
        raise ValueError("version is empty")
    toolchain = record.get("toolchain")
    if not isinstance(toolchain, dict) or not toolchain.get("python"):
        raise ValueError("toolchain.python is required")
    if not isinstance(record.get("workflow_inputs"), dict):
        raise ValueError("workflow_inputs must be an object")
    if not isinstance(record.get("artifact_digests"), dict):
        raise ValueError("artifact_digests must be an object")
    sboms = record.get("sbom_digests")
    if not isinstance(sboms, dict):
        raise ValueError("sbom_digests must be an object")
    if require_sboms:
        for name in ("application", "runtime"):
            digest = sboms.get(name)
            if not isinstance(digest, str) or len(digest) != 64:
                raise ValueError(f"sbom_digests.{name} SHA-256 required")
    signed = record.get("signed_attestation")
    if require_signed_attestation:
        if not isinstance(signed, dict):
            raise ValueError("signed_attestation object required")
        digest = signed.get("sha256")
        if not isinstance(digest, str) or len(digest) != 64:
            raise ValueError("signed_attestation.sha256 required")


def emit_to_path(record: dict[str, Any], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=("emit", "verify"),
        help="emit writes the record; verify validates JSON (file or stdin-shaped path)",
    )
    parser.add_argument("--root", type=Path, default=_repo_root())
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--application", type=Path, default=DEFAULT_APP)
    parser.add_argument("--runtime", type=Path, default=DEFAULT_RUNTIME)
    parser.add_argument("--attestation", type=Path, default=DEFAULT_ATTESTATION)
    parser.add_argument("--source-commit", default=None)
    parser.add_argument("--version", default=None)
    parser.add_argument("--require-sboms", action="store_true")
    parser.add_argument("--require-signed-attestation", action="store_true")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    out = args.out if args.out.is_absolute() else root / args.out

    try:
        if args.command == "emit":
            record = build_record(
                root,
                source_commit=args.source_commit,
                version=args.version,
                application=args.application,
                runtime=args.runtime,
                attestation=args.attestation,
                require_sboms=args.require_sboms,
                require_signed_attestation=args.require_signed_attestation,
            )
            verify_record(
                record,
                require_sboms=args.require_sboms,
                require_signed_attestation=args.require_signed_attestation,
            )
            emit_to_path(record, out)
            print(out)
            return 0
        if not out.is_file():
            raise FileNotFoundError(f"missing provenance record: {out}")
        record = json.loads(out.read_text(encoding="utf-8"))
        if not isinstance(record, dict):
            raise ValueError("provenance record must be a JSON object")
        verify_record(
            record,
            require_sboms=args.require_sboms,
            require_signed_attestation=args.require_signed_attestation,
        )
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"emit-provenance: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
