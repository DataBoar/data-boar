"""CPU feature pre-flight before importing numpy / sklearn / DL.

PyPI numpy/scipy wheels compile a baseline that SIGILLs on x86 CPUs without
SSE4.2, POPCNT, and (for bundled OpenBLAS) AVX. That crash is native — it cannot
be caught with try/except. Call this module *before* those imports (#929).
"""

from __future__ import annotations

import logging
import platform
import re
from pathlib import Path

# Typical PyPI numpy/scipy wheel floor on x86_64: x86-64-v2 (sse4_2 + popcnt)
# plus AVX in bundled OpenBLAS. Missing any one is enough to skip the ML stack.
PYPI_NUMPY_X86_REQUIRED: tuple[str, ...] = ("sse4_2", "popcnt", "avx")

# Hosted, SHA256SUMS-verified ML stack for x86-64-v1 (product path [noavx] — not a
# PyPI extra). Canonical recipe: docs/TROUBLESHOOTING.md § x86-64-v1 / wheelhouse.
WHEELHOUSE_TAG = "wheelhouse-x86-64-v1-2026-07-29"
WHEELHOUSE_REPO = "DataBoar/data-boar-site"

_X86_MACHINES = frozenset({"x86_64", "amd64", "x64", "i386", "i686", "i586", "i486"})

_logged_skip = False
_log = logging.getLogger("data_boar.cpu_preflight")

_CPUINFO_FLAGS_RE = re.compile(
    r"^(?:flags|Features)\s*:\s*(.+)$",
    re.IGNORECASE | re.MULTILINE,
)


def _normalize_flag(flag: str) -> str:
    return flag.strip().lower().replace(".", "_")


def parse_cpuinfo_flags(cpuinfo_text: str) -> set[str]:
    """Parse Linux ``/proc/cpuinfo`` ``flags`` / ARM ``Features`` into a set."""
    flags: set[str] = set()
    for match in _CPUINFO_FLAGS_RE.finditer(cpuinfo_text):
        flags.update(_normalize_flag(part) for part in match.group(1).split())
    return flags


def _linux_cpu_flags() -> set[str] | None:
    path = Path("/proc/cpuinfo")
    if not path.is_file():
        return None
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    parsed = parse_cpuinfo_flags(text)
    return parsed if parsed else None


def _is_x86(machine: str | None = None) -> bool:
    raw = (machine or platform.machine() or "").strip().lower()
    return raw in _X86_MACHINES


def cpu_flags() -> set[str] | None:
    """Return lowercase CPU feature flags, or None when they cannot be read."""
    if not _is_x86():
        return None
    return _linux_cpu_flags()


def missing_pypi_numpy_features(
    flags: set[str] | None = None,
    *,
    machine: str | None = None,
) -> tuple[str, ...]:
    """Features required by typical PyPI numpy wheels that this CPU lacks.

    Empty tuple means: import is treated as safe (non-x86, unreadable flags, or
    all required bits present). On Linux x86 with a readable ``/proc/cpuinfo``,
    a missing required flag is reported so callers skip numpy.
    """
    if not _is_x86(machine):
        return ()
    present = flags if flags is not None else cpu_flags()
    if present is None:
        # Fail open when we cannot inspect (macOS/Windows without /proc): CI
        # and capable hosts keep the ML path. Linux min-spec hosts have cpuinfo.
        return ()
    missing = [feat for feat in PYPI_NUMPY_X86_REQUIRED if feat not in present]
    return tuple(missing)


def numpy_cpu_incompatible_message(missing: tuple[str, ...]) -> str:
    feat = ", ".join(missing) if missing else "required SIMD"
    return (
        f"this CPU does not have {feat} required by the PyPI numpy wheel. "
        "ML/DL is skipped so the process does not SIGILL; regex CPF/CNPJ still runs. "
        "Primary (restore working ML on this CPU — product path [noavx], not a "
        f"PyPI extra): hosted wheelhouse {WHEELHOUSE_TAG} on {WHEELHOUSE_REPO} "
        "(SHA256SUMS). docs/TROUBLESHOOTING.md section "
        "'x86-64-v1 / wheelhouse install'. "
        f"gh release download {WHEELHOUSE_TAG} --repo {WHEELHOUSE_REPO} "
        "--pattern '*musllinux*' --pattern '*-none-any.whl' --dir ~/wheelhouse-v1 "
        "(glibc: swap *musllinux* for *manylinux*); then "
        "pip install --no-index --find-links $HOME/wheelhouse-v1 "
        "--force-reinstall numpy scipy scikit-learn pandas "
        "(pipx: pipx runpip data-boar install --no-index --find-links "
        "$HOME/wheelhouse-v1 --force-reinstall numpy scipy scikit-learn pandas). "
        "Fallback only: distro numpy (`apk add py3-numpy` / "
        "`apt install python3-numpy`) or a source build with `-Dcpu-baseline=min`."
    )


def numpy_import_safe() -> bool:
    """True when it is safe to import numpy/sklearn without a likely SIGILL."""
    return not missing_pypi_numpy_features()


def warn_if_numpy_unsafe() -> bool:
    """Log once and return False when the CPU cannot run the PyPI numpy wheel."""
    global _logged_skip
    missing = missing_pypi_numpy_features()
    if not missing:
        return True
    if not _logged_skip:
        _log.warning(numpy_cpu_incompatible_message(missing))
        _logged_skip = True
    return False
