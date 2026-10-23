"""CPU feature pre-flight before importing numpy / sklearn / DL.

PyPI numpy/scipy wheels compile a baseline that SIGILLs on x86 CPUs without
SSE4.2, POPCNT, and (for bundled OpenBLAS) AVX. That crash is native — it cannot
be caught with try/except. Call this module *before* those imports (#929).

On CPUs missing the required flags, the module now probes the *installed* stack
by running a tiny BLAS/NumPy/SciPy/scikit-learn workload in a child process. If
the installed stack (e.g. a wheelhouse x86-64-v1 build) executes without SIGILL,
ML is enabled regardless of the CPU's reported flags.
"""

from __future__ import annotations

import logging
import platform
import re
import subprocess
import sys
from pathlib import Path
from typing import Final

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

# Child process exit codes
_CHILD_EXIT_SAFE: Final = 0  # installed stack ran without SIGILL
_CHILD_EXIT_MODULE_MISSING: Final = 3  # numpy/scipy/sklearn not installed (ImportError)
_CHILD_EXIT_UNSAFE: Final = 1  # SIGILL, timeout, or other failure

# Module-level cache for the probe result
_probe_result_cache: dict[str, bool | None] = {}


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
    a missing required flag is reported so callers can decide whether to probe.
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


def _probe_code() -> str:
    """Python code run in a child process to test the installed stack.

    The probe imports numpy and executes a tiny BLAS-using operation (dot + linalg).
    If importable, it also exercises scipy.linalg and sklearn.ensemble with a tiny fit.
    No imports from core.* are allowed.
    """
    return r"""
import sys
import numpy as np

# Tiny BLAS operation (dot + linalg)
a = np.array([[1.0, 2.0], [3.0, 4.0]])
b = np.array([[5.0, 6.0], [7.0, 8.0]])
np.dot(a, b)
np.linalg.solve(a, b)

# Optional scipy
try:
    import scipy.linalg
    scipy.linalg.det(a)
except ImportError:
    pass

# Optional sklearn
try:
    from sklearn.ensemble import RandomForestClassifier
    import numpy as np
    X = np.array([[0, 0], [1, 1]])
    y = np.array([0, 1])
    RandomForestClassifier(n_estimators=1, max_depth=1, random_state=0).fit(X, y)
except ImportError:
    pass

sys.exit(0)
"""


def _run_probe() -> bool | None:
    """Run the installed-stack probe in a child process.

    Returns:
        True  - probe succeeded (stack is safe)
        False - probe failed (SIGILL, timeout, OSError, etc.)
        None  - numpy/scipy/sklearn not installed (callers' ImportError guards apply)
    """
    probe_code = _probe_code()
    try:
        proc = subprocess.run(
            [sys.executable, "-I", "-c", probe_code],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=20,
        )
        if proc.returncode == 0:
            return True
        if proc.returncode == _CHILD_EXIT_MODULE_MISSING:
            return None
        if proc.returncode < 0:
            # Killed by signal (SIGILL = -4 on Linux)
            return False
        # Any other non-zero
        return False
    except subprocess.TimeoutExpired:
        return False
    except OSError:
        return False


def _cached_probe_result() -> bool | None:
    """Return cached probe result, running the probe if not cached."""
    cache_key = "probe_result"
    if cache_key in _probe_result_cache:
        return _probe_result_cache[cache_key]
    result = _run_probe()
    _probe_result_cache[cache_key] = result
    return result


def _reset_probe_cache() -> None:
    """Reset the probe cache (for testing)."""
    _probe_result_cache.clear()


def numpy_import_safe(
    flags: set[str] | None = None,
    *,
    machine: str | None = None,
) -> bool:
    """True when it is safe to import numpy/sklearn without a likely SIGILL.

    On x86 CPUs missing required flags, this probes the *installed* stack.
    A working wheelhouse build on a no-AVX CPU returns True.
    """
    missing = missing_pypi_numpy_features(flags, machine=machine)
    if not missing:
        return True
    # Flags missing — probe the installed stack
    result = _cached_probe_result()
    if result is True:
        return True
    if result is None:
        # Module not installed: safe to proceed; callers' ImportError guards handle it
        return True
    return False


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


def _probe_failure_message(missing: tuple[str, ...], detail: str) -> str:
    feat = ", ".join(missing) if missing else "required SIMD"
    return (
        f"this CPU does not have {feat} required by the PyPI numpy wheel. "
        f"Installed stack probe {detail}. ML/DL is skipped so the process does not SIGILL; "
        "regex CPF/CNPJ still runs. "
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


def warn_if_numpy_unsafe(
    flags: set[str] | None = None,
    *,
    machine: str | None = None,
) -> bool:
    """Log once and return False when the CPU cannot run the PyPI numpy wheel.

    On x86 CPUs missing required flags, this probes the installed stack.
    A working wheelhouse build returns True. A failed probe (SIGILL/timeout)
    returns False and logs the specific failure reason.
    """
    global _logged_skip
    missing = missing_pypi_numpy_features(flags, machine=machine)
    if not missing:
        return True

    result = _cached_probe_result()
    if result is True:
        return True
    if result is None:
        # Module not installed: callers' ImportError guards handle it
        return True

    if not _logged_skip:
        if result is False:
            _log.warning(_probe_failure_message(missing, "failed (SIGILL or timeout)"))
        _logged_skip = True
    return False
