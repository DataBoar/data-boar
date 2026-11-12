"""Guard: the uv version is declared once (``.github/uv-version``) and every pin follows it (#2228).

Why: two uv versions lived in the repo (0.11.2 in CI/lock tooling, 0.12.0 in the native build
images). Lock artifacts (``uv.lock``, ``requirements.txt``, ``pylock.toml``) are regenerated
with the declared version, so a silent drift makes ``check-all`` and CI disagree.

Contract
--------
* ``.github/uv-version`` (plain text, only the version) is the single source.
* Every ``astral-sh/setup-uv`` ``version:`` in ``.github/workflows/*.yml``, the pip fallback
  ``.github/pip-constraints/ci-uv-fallback.txt`` and ``prep_audit.sh`` must equal it.
* **Declared exception (native free-threaded build):** ``native-packages.yml``, ``Dockerfile``,
  ``Dockerfile.nogil`` and ``scripts/native-nfpm-populate-staging.sh`` need a newer uv because
  uv 0.11.x cannot fetch ``cpython-3.14.6+freethreaded`` (measured: ``No download found for
  request``). These four must agree with each other (version and tarball SHA256), carry the
  written justification, and the exception expires on its own: once the source version can
  fetch that interpreter and the pins are aligned, the guard asks to drop it.
* Every tarball SHA256 must match the official release asset digest recorded below.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]

SOURCE_FILE = ".github/uv-version"
FALLBACK_FILE = ".github/pip-constraints/ci-uv-fallback.txt"
PREP_AUDIT = "prep_audit.sh"
NATIVE_WORKFLOW = ".github/workflows/native-packages.yml"
NATIVE_DOCKERFILES = ("Dockerfile", "Dockerfile.nogil")
NATIVE_SCRIPT = "scripts/native-nfpm-populate-staging.sh"
NATIVE_FILES = (NATIVE_WORKFLOW, *NATIVE_DOCKERFILES, NATIVE_SCRIPT)

# Required wording of the written justification inside each native file.
EXCEPTION_REASON = "uv 0.11.x cannot fetch cpython-3.14.6+freethreaded"

# uv-x86_64-unknown-linux-gnu.tar.gz, from the official astral-sh/uv release asset
# (``<asset>.sha256`` and the GitHub API ``digest``; both agree). Checked 2026-11-11.
KNOWN_LINUX_X64_SHA256 = {
    "0.11.2": "7ac2ca0449c8d68dae9b99e635cd3bc9b22a4cb1de64b7c43716398447d42981",
    "0.12.0": "eaf842262aa1c418d8ecc5605f02ee1ebfd369124fa48548e85f9481a47831a9",
}

# Minimum number of pinned setup-uv steps per workflow (a removed pin must not pass silently).
MIN_SETUP_UV_PINS = {
    ".github/workflows/ci.yml": 8,
    ".github/workflows/sbom.yml": 1,
    ".github/workflows/dependabot-sync.yml": 1,
}

_VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")


def _read(root: Path, rel: str) -> str:
    return (root / rel).read_text(encoding="utf-8")


def read_source_version(root: Path) -> str:
    raw = _read(root, SOURCE_FILE)
    value = raw.strip()
    if not _VERSION_RE.match(value) or raw.strip() != raw.rstrip("\n"):
        raise ValueError(
            f"{SOURCE_FILE} must hold only a version like 0.11.2, got {raw!r}"
        )
    return value


def setup_uv_versions(root: Path, rel: str) -> list[str]:
    """``with.version`` of every ``astral-sh/setup-uv`` step in a workflow (pinned ones only)."""
    doc = yaml.safe_load(_read(root, rel)) or {}
    found: list[str] = []
    for job in (doc.get("jobs") or {}).values():
        for step in (job or {}).get("steps") or []:
            if not isinstance(step, dict):
                continue
            if not str(step.get("uses", "")).startswith("astral-sh/setup-uv@"):
                continue
            ver = (step.get("with") or {}).get("version")
            if ver is not None:
                found.append(str(ver))
    return found


def _dockerfile_pin(root: Path, rel: str) -> tuple[str, str]:
    text = _read(root, rel)
    ver = re.search(r"^ARG UV_VERSION=(\S+)\s*$", text, re.M)
    sha = re.search(r"^ARG UV_SHA256=([0-9a-f]{64})\s*$", text, re.M)
    assert ver and sha, f"{rel}: ARG UV_VERSION / ARG UV_SHA256 not found"
    return ver.group(1), sha.group(1)


def _script_pin(root: Path, rel: str) -> tuple[str, str]:
    text = _read(root, rel)
    ver = re.search(r'^UV_VERSION="\$\{UV_VERSION:-([^}]+)\}"', text, re.M)
    sha = re.search(r'^UV_SHA256="\$\{UV_SHA256:-([0-9a-f]{64})\}"', text, re.M)
    assert ver and sha, f"{rel}: UV_VERSION / UV_SHA256 defaults not found"
    return ver.group(1), sha.group(1)


def _workflow_native_pin(root: Path, rel: str) -> tuple[str, str]:
    env = (yaml.safe_load(_read(root, rel)) or {}).get("env") or {}
    return str(env.get("UV_VERSION")), str(env.get("UV_SHA256"))


def _prep_audit_pin(root: Path) -> tuple[str, str]:
    text = _read(root, PREP_AUDIT)
    ver = re.search(r'^\s*UV_VERSION="([^"]+)"', text, re.M)
    sha = re.search(r'^\s*UV_SHA256="([0-9a-f]{64})"', text, re.M)
    assert ver and sha, f"{PREP_AUDIT}: UV_VERSION / UV_SHA256 not found"
    return ver.group(1), sha.group(1)


def _fallback_version(root: Path) -> str:
    m = re.search(r"^uv==(\S+) \\$", _read(root, FALLBACK_FILE), re.M)
    assert m, f"{FALLBACK_FILE}: 'uv==<version> \\' line not found"
    return m.group(1)


def check_uv_pins(root: Path) -> list[str]:
    """Return human-readable problems; empty when every pin follows the single source."""
    problems: list[str] = []
    try:
        source = read_source_version(root)
    except (OSError, ValueError) as exc:
        return [f"cannot read single source: {exc}"]

    workflows_dir = root / ".github" / "workflows"
    for wf in sorted(workflows_dir.glob("*.yml")):
        rel = wf.relative_to(root).as_posix()
        versions = setup_uv_versions(root, rel)
        for ver in versions:
            if ver != source:
                problems.append(
                    f"{rel}: setup-uv version {ver!r} != {SOURCE_FILE} {source!r}"
                )
        floor = MIN_SETUP_UV_PINS.get(rel, 0)
        if len(versions) < floor:
            problems.append(
                f"{rel}: expected >= {floor} pinned setup-uv steps, found {len(versions)}"
            )

    fb = _fallback_version(root)
    if fb != source:
        problems.append(f"{FALLBACK_FILE}: uv=={fb} != {SOURCE_FILE} {source!r}")

    pa_ver, pa_sha = _prep_audit_pin(root)
    if pa_ver != source:
        problems.append(
            f"{PREP_AUDIT}: UV_VERSION {pa_ver!r} != {SOURCE_FILE} {source!r}"
        )
    if KNOWN_LINUX_X64_SHA256.get(pa_ver) != pa_sha:
        problems.append(
            f"{PREP_AUDIT}: SHA256 does not match the recorded official digest for {pa_ver}"
        )

    if source not in KNOWN_LINUX_X64_SHA256:
        problems.append(
            f"{SOURCE_FILE} {source!r} has no recorded official SHA256 in this guard"
        )

    native = {
        NATIVE_WORKFLOW: _workflow_native_pin(root, NATIVE_WORKFLOW),
        **{rel: _dockerfile_pin(root, rel) for rel in NATIVE_DOCKERFILES},
        NATIVE_SCRIPT: _script_pin(root, NATIVE_SCRIPT),
    }
    if len(set(native.values())) != 1:
        problems.append(f"native build pins disagree: {native}")
    for rel, (ver, sha) in native.items():
        if KNOWN_LINUX_X64_SHA256.get(ver) != sha:
            problems.append(
                f"{rel}: SHA256 does not match the recorded official digest for {ver}"
            )
    native_ver = next(iter(native.values()))[0]
    if native_ver == source:
        problems.append(
            "native build pins equal the single source: the declared exception is stale; "
            f"drop EXCEPTION_REASON checks ({EXCEPTION_REASON!r}) from this guard"
        )
    else:
        for rel in NATIVE_FILES:
            if EXCEPTION_REASON not in _read(root, rel):
                problems.append(
                    f"{rel}: pins uv {native_ver} but lacks the written justification"
                )
    return problems


# --------------------------------------------------------------------------- real repository


def test_uv_version_file_is_plain_version() -> None:
    assert read_source_version(REPO_ROOT)


def test_repo_uv_pins_follow_single_source() -> None:
    problems = check_uv_pins(REPO_ROOT)
    assert not problems, "uv pins diverge:\n- " + "\n- ".join(problems)


def test_pyproject_does_not_force_required_version() -> None:
    """Operator decision (#2228): a dev with another uv must not be forced to switch."""
    assert "required-version" not in _read(REPO_ROOT, "pyproject.toml")


# --------------------------------------------------------------------------- guard sensitivity

_TRACKED = (
    SOURCE_FILE,
    FALLBACK_FILE,
    PREP_AUDIT,
    NATIVE_SCRIPT,
    *NATIVE_DOCKERFILES,
)


@pytest.fixture()
def tree(tmp_path: Path) -> Path:
    """Copy only the files the guard reads, so a test can mutate them."""
    rels = list(_TRACKED) + [
        p.relative_to(REPO_ROOT).as_posix()
        for p in (REPO_ROOT / ".github" / "workflows").glob("*.yml")
    ]
    for rel in rels:
        dst = tmp_path / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO_ROOT / rel, dst)
    return tmp_path


def _sub(root: Path, rel: str, old: str, new: str, count: int = 1) -> None:
    p = root / rel
    text = p.read_text(encoding="utf-8")
    assert old in text, f"fixture drift: {old!r} not in {rel}"
    p.write_text(text.replace(old, new, count), encoding="utf-8")


def test_copy_of_repo_is_clean(tree: Path) -> None:
    assert check_uv_pins(tree) == []


def test_detects_workflow_setup_uv_drift(tree: Path) -> None:
    _sub(tree, ".github/workflows/ci.yml", 'version: "0.11.2"', 'version: "0.12.0"')
    assert any("ci.yml" in p and "setup-uv" in p for p in check_uv_pins(tree))


def test_detects_removed_workflow_pin(tree: Path) -> None:
    _sub(
        tree,
        ".github/workflows/sbom.yml",
        'version: "0.11.2"',
        "python-version: '3.12'",
    )
    assert any("sbom.yml" in p for p in check_uv_pins(tree))


def test_detects_pip_fallback_drift(tree: Path) -> None:
    _sub(tree, FALLBACK_FILE, "uv==0.11.2", "uv==0.12.0")
    assert any(FALLBACK_FILE in p for p in check_uv_pins(tree))


def test_detects_source_file_change(tree: Path) -> None:
    (tree / SOURCE_FILE).write_text("0.12.0\n", encoding="utf-8")
    assert check_uv_pins(tree)


def test_detects_prep_audit_sha_tamper(tree: Path) -> None:
    good = KNOWN_LINUX_X64_SHA256["0.11.2"]
    _sub(tree, PREP_AUDIT, good, "0" * 64)
    assert any(PREP_AUDIT in p and "SHA256" in p for p in check_uv_pins(tree))


@pytest.mark.parametrize("rel", NATIVE_DOCKERFILES)
def test_detects_dockerfile_sha_tamper(tree: Path, rel: str) -> None:
    _sub(tree, rel, KNOWN_LINUX_X64_SHA256["0.12.0"], "f" * 64)
    assert any(rel in p for p in check_uv_pins(tree))


def test_detects_native_pins_disagreeing(tree: Path) -> None:
    _sub(
        tree,
        NATIVE_SCRIPT,
        'UV_VERSION="${UV_VERSION:-0.12.0}"',
        'UV_VERSION="${UV_VERSION:-0.11.2}"',
    )
    assert any("disagree" in p for p in check_uv_pins(tree))


def test_detects_missing_exception_justification(tree: Path) -> None:
    for rel in NATIVE_FILES:
        text = (
            (tree / rel)
            .read_text(encoding="utf-8")
            .replace(EXCEPTION_REASON, "reason removed")
        )
        (tree / rel).write_text(text, encoding="utf-8")
    assert sum("justification" in p for p in check_uv_pins(tree)) == len(NATIVE_FILES)


def test_stale_exception_is_reported(tree: Path) -> None:
    (tree / SOURCE_FILE).write_text("0.12.0\n", encoding="utf-8")
    assert any("stale" in p for p in check_uv_pins(tree))


# --------------------------------------------------------------------------- pinned-uv.sh (#2232)

PINNED_UV_SCRIPT = "scripts/pinned-uv.sh"
CHECK_ALL_SH = "scripts/check-all.sh"
linux_x64_only = pytest.mark.skipif(
    not (sys.platform == "linux" and os.uname().machine == "x86_64"),
    reason="the digest registry only covers linux-x86_64",
)


@pytest.fixture()
def pin_tree(tmp_path: Path) -> Path:
    """Minimal repo tree for pinned-uv.sh: the script, the version file and the digest registry."""
    root = tmp_path / "repo"
    for rel in (
        PINNED_UV_SCRIPT,
        SOURCE_FILE,
        "tests/test_uv_version_single_source.py",
    ):
        dst = root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO_ROOT / rel, dst)
    return root


def _run_pinned(
    root: Path, cache: Path, **env: str
) -> subprocess.CompletedProcess[str]:
    full = {
        "PATH": os.environ["PATH"],
        "HOME": str(root.parent / "home"),
        "DATA_BOAR_UV_CACHE_DIR": str(cache),
        **env,
    }
    return subprocess.run(
        ["bash", str(root / PINNED_UV_SCRIPT)],
        capture_output=True,
        text=True,
        env=full,
        check=False,
    )


def _fake_uv(directory: Path, reported: str) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    exe = directory / "uv"
    exe.write_text(f'#!/bin/sh\necho "uv {reported} (fake)"\n', encoding="utf-8")
    exe.chmod(0o755)


def test_pinned_uv_uses_the_version_in_the_file(pin_tree: Path, tmp_path: Path) -> None:
    cache = tmp_path / "cache"
    version = read_source_version(pin_tree)
    _fake_uv(cache / f"uv-{version}", version)
    r = _run_pinned(pin_tree, cache)
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == str(cache / f"uv-{version}")
    assert f"uv {version}" in r.stderr


def test_pinned_uv_follows_a_changed_version_file(
    pin_tree: Path, tmp_path: Path
) -> None:
    cache = tmp_path / "cache"
    (pin_tree / SOURCE_FILE).write_text("0.12.0\n", encoding="utf-8")
    _fake_uv(cache / "uv-0.12.0", "0.12.0")
    _fake_uv(cache / "uv-0.11.2", "0.11.2")
    r = _run_pinned(pin_tree, cache)
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == str(cache / "uv-0.12.0")


def test_pinned_uv_rejects_a_cached_binary_of_another_version(
    pin_tree: Path, tmp_path: Path
) -> None:
    cache = tmp_path / "cache"
    version = read_source_version(pin_tree)
    _fake_uv(cache / f"uv-{version}", "0.13.7")
    r = _run_pinned(pin_tree, cache, PINNED_UV_BASE_URL=f"file://{tmp_path}/missing")
    assert r.returncode != 0
    assert r.stdout.strip() == ""
    assert "ERROR" in r.stderr


@pytest.mark.parametrize("content", ["latest\n", "0.11\n", "", "0.11.2 0.12.0\n"])
def test_pinned_uv_rejects_a_malformed_version_file(
    pin_tree: Path, tmp_path: Path, content: str
) -> None:
    (pin_tree / SOURCE_FILE).write_text(content, encoding="utf-8")
    r = _run_pinned(pin_tree, tmp_path / "cache")
    assert r.returncode != 0
    assert "uv-version" in r.stderr


def test_pinned_uv_refuses_a_version_without_registered_digest(
    pin_tree: Path, tmp_path: Path
) -> None:
    (pin_tree / SOURCE_FILE).write_text("0.99.0\n", encoding="utf-8")
    r = _run_pinned(
        pin_tree, tmp_path / "cache", PINNED_UV_BASE_URL=f"file://{tmp_path}/x"
    )
    assert r.returncode != 0
    assert "no official SHA256" in r.stderr


@linux_x64_only
def test_pinned_uv_fails_on_a_tampered_download(pin_tree: Path, tmp_path: Path) -> None:
    version = read_source_version(pin_tree)
    served = tmp_path / "served" / version
    served.mkdir(parents=True)
    (served / "uv-x86_64-unknown-linux-gnu.tar.gz").write_bytes(
        b"not the official asset"
    )
    cache = tmp_path / "cache"
    r = _run_pinned(pin_tree, cache, PINNED_UV_BASE_URL=f"file://{tmp_path}/served")
    assert r.returncode != 0
    assert "SHA256 mismatch" in r.stderr
    assert not (cache / f"uv-{version}" / "uv").exists()


@linux_x64_only
def test_pinned_uv_fails_when_the_download_is_unreachable(
    pin_tree: Path, tmp_path: Path
) -> None:
    cache = tmp_path / "cache"
    r = _run_pinned(pin_tree, cache, PINNED_UV_BASE_URL=f"file://{tmp_path}/nowhere")
    assert r.returncode != 0
    assert "download" in r.stderr


def test_check_all_sh_resolves_the_pinned_uv_before_using_uv() -> None:
    text = _read(REPO_ROOT, CHECK_ALL_SH)
    resolve = text.index("scripts/pinned-uv.sh")
    assert resolve < text.index("command -v uv")
    assert resolve < text.index("gatekeeper_audit.py")
    assert 'export PATH="$PINNED_UV_DIR:$PATH"' in text
    assert "using $(uv --version)" in text  # prints the version in use
    # no escape hatch around the pin
    assert "|| true" not in text[resolve : text.index("command -v uv")]
    # ~/.local/bin must not shadow the pinned uv after the login-env PATH fix-up
    assert text.count('export PATH="$PINNED_UV_DIR:$PATH"') >= 2


def test_pinned_uv_registry_and_native_exception_are_untouched() -> None:
    """#2232 does not move the declared 0.12.0 exception."""
    assert check_uv_pins(REPO_ROOT) == []
