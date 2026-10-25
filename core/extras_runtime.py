"""Runtime extras extension point: ``/extras`` + PYTHONPATH + ABI fail-closed (#1400/#1402)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from core.extras_manifest import expected_abi_tokens

DEFAULT_EXTRAS_DIR = Path(os.environ.get("DATA_BOAR_EXTRAS_DIR", "/extras"))

# Known connector type / database driver → optional-extra name (#1402).
KNOWN_OPTIONAL_BY_TYPE: dict[str, str] = {
    "smb": "shares",
    "cifs": "shares",
    "webdav": "shares",
}
KNOWN_OPTIONAL_BY_DRIVER: dict[str, str] = {
    "redis": "nosql",
    "mongodb": "nosql",
    "postgresql": "postgres",
    "mysql": "mysql",
    "mariadb": "mariadb",
    "mssql": "mssql",
    "oracle": "oracle",
    "snowflake": "bigdata",
}


def install_hint_for_extra(extra: str) -> str:
    """MSSQL-style install line + container runtime extension path."""
    return (
        f"Install with: pip install 'data-boar[{extra}]' "
        f'(or: uv pip install -e ".[{extra}]"). '
        "Container runtime: mount ABI-compatible prebuilt wheels at /extras "
        "(PYTHONPATH=/extras; nonroot uid 65532; no rebuild) — "
        "see docs/DOCKER_SETUP.md (Extras and pool licensing)."
    )


def missing_optional_message(
    *,
    subject: str,
    extra: str,
) -> str:
    return f"{subject} requires optional dependencies. {install_hint_for_extra(extra)}"


def optional_extra_for_target(target: dict) -> str | None:
    """Return optional-extra name when the target type/driver is a known optional connector."""
    t = (target.get("type") or "").strip().lower()
    if t in KNOWN_OPTIONAL_BY_TYPE:
        return KNOWN_OPTIONAL_BY_TYPE[t]
    if t == "database":
        driver = (target.get("driver") or "").strip().lower()
        engine = driver.split("+", 1)[0] if driver else ""
        return KNOWN_OPTIONAL_BY_DRIVER.get(engine) or KNOWN_OPTIONAL_BY_DRIVER.get(
            driver
        )
    return None


def unresolved_connector_failure(target: dict) -> tuple[str, str]:
    """Return ``(reason_code, detail)`` for a target with no registered connector.

    Distinguishes config typo from missing optional dependency (#1402).
    """
    ttype = target.get("type", "?")
    extra = optional_extra_for_target(target)
    if extra:
        subject = f"Connector type '{ttype}'"
        driver = (target.get("driver") or "").strip()
        if ttype == "database" and driver:
            subject = f"Database connector '{driver.split('+', 1)[0]}'"
        return (
            "missing_optional_dependency",
            missing_optional_message(subject=subject, extra=extra),
        )
    return (
        "unknown_connector_type",
        (
            f"No connector registered for type '{ttype}'. "
            "Check config.yaml — unknown type (typo), not a missing optional package."
        ),
    )


def _wheel_tags_under(extras_dir: Path) -> list[str]:
    tags: list[str] = []
    for wheel_meta in extras_dir.rglob("*.dist-info/WHEEL"):
        try:
            text = wheel_meta.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for line in text.splitlines():
            if line.startswith("Tag:"):
                tags.append(line.split(":", 1)[1].strip())
    return tags


def verify_extras_abi(extras_dir: Path | None = None) -> None:
    """Fail loud when a mounted ``/extras`` pack does not match this interpreter ABI.

    Empty or missing ``/extras`` is OK (lean base image). A non-empty pack with
    incompatible wheel tags / extension filenames raises ``RuntimeError``.
    """
    root = extras_dir if extras_dir is not None else DEFAULT_EXTRAS_DIR
    try:
        if not root.is_dir():
            return
        entries = [p for p in root.iterdir() if p.name not in {".", ".."}]
    except OSError:
        return
    if not entries:
        return

    expected = expected_abi_tokens()
    tags = _wheel_tags_under(root)
    if tags:
        compatible = any(any(tok in tag for tok in expected) for tag in tags)
        if not compatible:
            raise RuntimeError(
                f"Extras pack under {root} is ABI-incompatible with this interpreter "
                f"(expected tags containing {expected!r}; found {sorted(set(tags))!r}). "
                "Rebuild the wheel pack for this Python minor/variant "
                "(e.g. cp314 vs cp314t) and remount /extras."
            )

    # Extension modules often encode the abi in the filename (cp314, cp314t).
    bad_so: list[str] = []
    for so in root.rglob("*.so"):
        name = so.name
        if "cp" not in name:
            continue
        if any(tok in name for tok in expected):
            continue
        # Ignore pure abi3 wheels that advertise abi3 without cpXXX mismatch noise
        if "abi3" in name:
            continue
        bad_so.append(str(so))
    if bad_so and not tags:
        # Only hard-fail on .so heuristic when no WHEEL metadata was present
        raise RuntimeError(
            f"Extras pack under {root} has native extensions that do not match "
            f"this interpreter ({expected!r}): {bad_so[:5]!r}. "
            "Remount an ABI-compatible pack on /extras."
        )


def verify_extras_abi_or_exit(extras_dir: Path | None = None) -> None:
    try:
        verify_extras_abi(extras_dir)
    except RuntimeError as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
