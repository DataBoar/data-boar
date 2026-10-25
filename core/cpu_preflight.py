"""CPU feature pre-flight before importing numpy / sklearn / DL.

PyPI numpy/scipy wheels compile a baseline that SIGILLs on x86 CPUs without
SSE4.2, POPCNT, and (for bundled OpenBLAS) AVX. That crash is native — it cannot
be caught with try/except. Call this module *before* those imports (#929).

The CPU flags alone do not decide (#2125): a wheelhouse x86-64-v1 build of
numpy/scipy/scikit-learn runs on those CPUs. When a required flag is missing the
module probes the *installed* stack in a child process (a native crash only kills
the child) and fails closed when safety cannot be proven.
"""

from __future__ import annotations

import enum
import logging
import platform
import re
import signal
import subprocess
import sys
from pathlib import Path
from typing import Final, NamedTuple

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

# Probe child contract (#2125). The child exits 0 when the installed stack ran,
# _CHILD_EXIT_MODULE_MISSING when numpy itself is not installed, and anything else
# (a traceback, or a death by signal such as SIGILL) means the stack is unsafe.
_CHILD_EXIT_MODULE_MISSING: Final = 3
_PROBE_TIMEOUT_SECONDS: Final = 20
_STDERR_DETAIL_MAX: Final = 200


class ProbeStatus(enum.Enum):
    """Outcome class of the installed-stack probe."""

    SAFE = "safe"
    MODULE_MISSING = "module_missing"
    UNSAFE = "unsafe"


class ProbeResult(NamedTuple):
    """Probe outcome plus a human-readable, precise detail for the warning."""

    status: ProbeStatus
    detail: str


# One probe per process: detector and dl_backend both ask.
_probe_cache: ProbeResult | None = None


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


# Child program. Only a *missing* module is benign: a numpy/scipy/sklearn that
# imports but refuses to run on this CPU raises a plain ImportError/RuntimeError
# (newer wheels) or dies by SIGILL (older ones); both must stay a failure.
# The child imports nothing from core.*.
_PROBE_TEMPLATE: Final = r"""
import sys


def _top(exc):
    return (exc.name or "").split(".")[0]


try:
    import numpy as np
except ModuleNotFoundError as exc:
    if _top(exc) == "numpy":
        sys.exit(__MODULE_MISSING_EXIT__)
    raise

a = np.array([[1.0, 2.0], [3.0, 4.0]])
b = np.array([[5.0, 6.0], [7.0, 8.0]])
np.dot(a, b)
np.linalg.solve(a, b)

try:
    import scipy.linalg
except ModuleNotFoundError as exc:
    if _top(exc) != "scipy":
        raise
else:
    scipy.linalg.det(a)

try:
    from sklearn.ensemble import RandomForestClassifier
except ModuleNotFoundError as exc:
    if _top(exc) not in ("sklearn", "scipy"):
        raise
else:
    x = np.array([[0.0, 0.0], [1.0, 1.0]])
    y = np.array([0, 1])
    RandomForestClassifier(n_estimators=1, max_depth=1, random_state=0).fit(x, y)
"""


def _probe_code() -> str:
    """Child program text, with the missing-module exit code from the constant."""
    return _PROBE_TEMPLATE.replace(
        "__MODULE_MISSING_EXIT__", str(_CHILD_EXIT_MODULE_MISSING)
    )


def _signal_name(signum: int) -> str:
    try:
        return signal.Signals(signum).name
    except ValueError:
        return f"signal {signum}"


def _classify_probe(returncode: int, stderr: str) -> ProbeResult:
    """Map a finished child to a ProbeResult with a precise detail."""
    if returncode == 0:
        return ProbeResult(ProbeStatus.SAFE, "installed stack ran")
    if returncode == _CHILD_EXIT_MODULE_MISSING:
        return ProbeResult(ProbeStatus.MODULE_MISSING, "numpy is not installed")
    if returncode < 0:
        return ProbeResult(ProbeStatus.UNSAFE, f"killed by {_signal_name(-returncode)}")
    lines = [line.strip() for line in stderr.splitlines() if line.strip()]
    tail = f": {lines[-1][:_STDERR_DETAIL_MAX]}" if lines else ""
    return ProbeResult(ProbeStatus.UNSAFE, f"exited with code {returncode}{tail}")


def _run_probe() -> ProbeResult:
    """Run the installed-stack probe once in a child process (fail closed)."""
    try:
        proc = subprocess.run(
            [sys.executable, "-I", "-c", _probe_code()],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=_PROBE_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return ProbeResult(
            ProbeStatus.UNSAFE, f"timed out after {_PROBE_TIMEOUT_SECONDS} s"
        )
    except OSError as exc:
        return ProbeResult(ProbeStatus.UNSAFE, f"could not start: {exc}")
    return _classify_probe(proc.returncode, proc.stderr or "")


def _cached_probe() -> ProbeResult:
    global _probe_cache
    if _probe_cache is None:
        _probe_cache = _run_probe()
    return _probe_cache


def _reset_probe_cache() -> None:
    """Forget the probe outcome (tests)."""
    global _probe_cache
    _probe_cache = None


def numpy_import_safe(
    flags: set[str] | None = None,
    *,
    machine: str | None = None,
) -> bool:
    """True when it is safe to import numpy/sklearn without a likely SIGILL.

    Capable CPUs (no required flag missing) return True without any probe. On a
    CPU missing flags the installed stack is probed: a working wheelhouse
    x86-64-v1 build is safe, a stack that is simply not installed is left to the
    callers' ImportError guards, anything else is unsafe.
    """
    if not missing_pypi_numpy_features(flags, machine=machine):
        return True
    return _cached_probe().status is not ProbeStatus.UNSAFE


def _remedy_text() -> str:
    """Wheelhouse remediation shared by every skip message."""
    return (
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


def numpy_cpu_incompatible_message(
    missing: tuple[str, ...],
    probe_detail: str | None = None,
) -> str:
    feat = ", ".join(missing) if missing else "required SIMD"
    head = f"this CPU does not have {feat} required by the PyPI numpy wheel. "
    if probe_detail:
        head += (
            f"The installed numpy stack also failed a safety probe ({probe_detail}). "
        )
    return (
        head
        + "ML/DL is skipped so the process does not SIGILL; regex CPF/CNPJ still runs. "
        + _remedy_text()
    )


def warn_if_numpy_unsafe(
    flags: set[str] | None = None,
    *,
    machine: str | None = None,
) -> bool:
    """Log once and return False when the installed stack cannot run on this CPU.

    Capable CPUs return True without a probe. On a CPU missing required flags the
    installed stack is probed once per process; only an UNSAFE probe skips ML, and
    the warning states the real reason (signal, timeout, exit code, start error).
    """
    global _logged_skip
    missing = missing_pypi_numpy_features(flags, machine=machine)
    if not missing:
        return True
    result = _cached_probe()
    if result.status is not ProbeStatus.UNSAFE:
        return True
    if not _logged_skip:
        _log.warning(numpy_cpu_incompatible_message(missing, result.detail))
        _logged_skip = True
    return False
