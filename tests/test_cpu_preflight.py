"""CPU pre-flight before numpy/ML imports (#929). SIGILL cannot be try/except."""

from __future__ import annotations

import ast
import logging
import subprocess
import sys
from pathlib import Path

import pytest

import core.cpu_preflight as cpu_preflight
from core.cpu_preflight import (
    PYPI_NUMPY_X86_REQUIRED,
    WHEELHOUSE_REPO,
    WHEELHOUSE_TAG,
    missing_pypi_numpy_features,
    numpy_cpu_incompatible_message,
    numpy_import_safe,
    parse_cpuinfo_flags,
    warn_if_numpy_unsafe,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]

_NO_AVX_CPUINFO = """
processor	: 0
vendor_id	: GenuineIntel
cpu family	: 6
model		: 23
model name	: Intel(R) Celeron(R) CPU          900  @ 2.20GHz
flags		: fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush dts acpi mmx fxsr sse sse2 ss ht tm pbe syscall nx lm constant_tsc arch_perfmon pebs bts rep_good nopl aperfmperf pni dtes64 monitor ds_cpl tm2 ssse3 cx16 xtpr pdcm dca lahf_lm
"""

_AVX_CPUINFO = """
processor	: 0
flags		: fpu sse sse2 ssse3 sse4_1 sse4_2 popcnt avx avx2
"""


def test_parse_cpuinfo_flags_normalizes_sse42_alias() -> None:
    flags = parse_cpuinfo_flags("flags\t: sse4.2 popcnt AVX\n")
    assert "sse4_2" in flags
    assert "popcnt" in flags
    assert "avx" in flags


def test_missing_features_on_no_avx_cpuinfo() -> None:
    flags = parse_cpuinfo_flags(_NO_AVX_CPUINFO)
    missing = missing_pypi_numpy_features(flags, machine="x86_64")
    assert "avx" in missing
    assert "popcnt" in missing
    assert "sse4_2" in missing
    assert missing == tuple(f for f in PYPI_NUMPY_X86_REQUIRED if f in missing)


def test_missing_features_empty_when_baseline_present() -> None:
    flags = parse_cpuinfo_flags(_AVX_CPUINFO)
    assert missing_pypi_numpy_features(flags, machine="x86_64") == ()


def test_non_x86_is_import_safe() -> None:
    flags = parse_cpuinfo_flags(_NO_AVX_CPUINFO)
    assert missing_pypi_numpy_features(flags, machine="aarch64") == ()


def test_incompatible_message_leads_with_wheelhouse() -> None:
    msg = numpy_cpu_incompatible_message(("avx",))
    assert "avx" in msg
    assert WHEELHOUSE_TAG in msg
    assert WHEELHOUSE_REPO in msg
    assert "[noavx]" in msg
    primary = msg[: msg.find("Fallback only")]
    assert "gh release download" in primary
    assert f"--repo {WHEELHOUSE_REPO}" in primary
    assert "pip install --no-index --find-links" in primary
    assert "Primary" in primary
    assert primary.find("Primary") < primary.find("pip install --no-index")
    assert "apk add py3-numpy" in msg
    assert msg.find("Primary") < msg.find("Fallback only")
    assert "-Dcpu-baseline=min" in msg[msg.find("Fallback only") :]


def test_detector_has_no_eager_dl_backend_import() -> None:
    """core.engine → scanner → detector must not import numpy via dl_backend at load."""
    source = (_REPO_ROOT / "core" / "detector.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == "core.dl_backend":
            raise AssertionError(
                "detector.py must not import core.dl_backend at module level (#929)"
            )
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "core.dl_backend" or alias.name.startswith(
                    "core.dl_backend."
                ):
                    raise AssertionError(
                        "detector.py must not import core.dl_backend at module level (#929)"
                    )


_NO_AVX_FLAGS = {"sse2", "ssse3"}
_CAPABLE_FLAGS = {"sse4_2", "popcnt", "avx"}
_X86 = "x86_64"


@pytest.fixture(autouse=True)
def _fresh_preflight_state():
    cpu_preflight._reset_probe_cache()
    cpu_preflight._logged_skip = False
    yield
    cpu_preflight._reset_probe_cache()
    cpu_preflight._logged_skip = False


def _fake_child(monkeypatch, *, returncode=0, stderr="", raises=None):
    """Replace the probe's subprocess.run; return the list of recorded commands."""
    calls: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        if raises is not None:
            raise raises
        return subprocess.CompletedProcess(cmd, returncode, stdout="", stderr=stderr)

    monkeypatch.setattr(cpu_preflight.subprocess, "run", fake_run)
    return calls


def test_capable_cpu_never_probes(monkeypatch) -> None:
    calls = _fake_child(monkeypatch)
    assert numpy_import_safe(_CAPABLE_FLAGS, machine=_X86) is True
    assert warn_if_numpy_unsafe(_CAPABLE_FLAGS, machine=_X86) is True
    assert calls == []


def test_probe_ok_means_safe_silent_and_cached(monkeypatch, caplog) -> None:
    calls = _fake_child(monkeypatch, returncode=0)
    with caplog.at_level(logging.WARNING, logger="data_boar.cpu_preflight"):
        assert numpy_import_safe(_NO_AVX_FLAGS, machine=_X86) is True
        assert warn_if_numpy_unsafe(_NO_AVX_FLAGS, machine=_X86) is True
    assert len(calls) == 1
    assert caplog.records == []


def test_probe_killed_by_sigill_skips_ml_and_logs_once(monkeypatch, caplog) -> None:
    calls = _fake_child(monkeypatch, returncode=-4)
    with caplog.at_level(logging.WARNING, logger="data_boar.cpu_preflight"):
        assert warn_if_numpy_unsafe(_NO_AVX_FLAGS, machine=_X86) is False
        assert warn_if_numpy_unsafe(_NO_AVX_FLAGS, machine=_X86) is False
    assert len(calls) == 1
    assert len(caplog.records) == 1
    assert "killed by SIGILL" in caplog.records[0].getMessage()
    assert numpy_import_safe(_NO_AVX_FLAGS, machine=_X86) is False


def test_probe_killed_by_other_signal_names_it(monkeypatch, caplog) -> None:
    _fake_child(monkeypatch, returncode=-11)
    with caplog.at_level(logging.WARNING, logger="data_boar.cpu_preflight"):
        assert warn_if_numpy_unsafe(_NO_AVX_FLAGS, machine=_X86) is False
    assert "killed by SIGSEGV" in caplog.records[0].getMessage()


def test_probe_timeout_is_unsafe_with_detail(monkeypatch, caplog) -> None:
    _fake_child(monkeypatch, raises=subprocess.TimeoutExpired(cmd="probe", timeout=20))
    with caplog.at_level(logging.WARNING, logger="data_boar.cpu_preflight"):
        assert warn_if_numpy_unsafe(_NO_AVX_FLAGS, machine=_X86) is False
    assert "timed out after 20 s" in caplog.records[0].getMessage()


def test_probe_oserror_is_unsafe_with_detail(monkeypatch, caplog) -> None:
    _fake_child(monkeypatch, raises=OSError("no interpreter"))
    with caplog.at_level(logging.WARNING, logger="data_boar.cpu_preflight"):
        assert warn_if_numpy_unsafe(_NO_AVX_FLAGS, machine=_X86) is False
    assert "could not start: no interpreter" in caplog.records[0].getMessage()


def test_probe_nonzero_exit_reports_last_stderr_line(monkeypatch, caplog) -> None:
    stderr = "Traceback (most recent call last):\n  ...\nImportError: NumPy was built with baseline optimizations\n"
    _fake_child(monkeypatch, returncode=1, stderr=stderr)
    with caplog.at_level(logging.WARNING, logger="data_boar.cpu_preflight"):
        assert warn_if_numpy_unsafe(_NO_AVX_FLAGS, machine=_X86) is False
    message = caplog.records[0].getMessage()
    assert "exited with code 1" in message
    assert "NumPy was built with baseline optimizations" in message


def test_probe_module_missing_is_safe_and_silent(monkeypatch, caplog) -> None:
    _fake_child(monkeypatch, returncode=cpu_preflight._CHILD_EXIT_MODULE_MISSING)
    with caplog.at_level(logging.WARNING, logger="data_boar.cpu_preflight"):
        assert numpy_import_safe(_NO_AVX_FLAGS, machine=_X86) is True
        assert warn_if_numpy_unsafe(_NO_AVX_FLAGS, machine=_X86) is True
    assert caplog.records == []


def test_real_child_without_numpy_exits_with_the_missing_module_code() -> None:
    """-S drops site-packages, so numpy cannot be imported: the benign path is reachable."""
    proc = subprocess.run(
        [sys.executable, "-I", "-S", "-c", cpu_preflight._probe_code()],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert proc.returncode == cpu_preflight._CHILD_EXIT_MODULE_MISSING, proc.stderr


def test_real_child_with_numpy_that_refuses_to_import_is_unsafe(tmp_path) -> None:
    pkg = tmp_path / "numpy"
    pkg.mkdir()
    (pkg / "__init__.py").write_text(
        'raise ImportError("NumPy was built with baseline optimizations: '
        '(X86_V2) but your machine does not support: (X86_V2).")\n',
        encoding="utf-8",
    )
    runner = (
        f"import sys; sys.path.insert(0, {str(tmp_path)!r}); "
        f"exec({cpu_preflight._probe_code()!r})"
    )
    proc = subprocess.run(
        [sys.executable, "-S", "-c", runner],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert proc.returncode not in (0, cpu_preflight._CHILD_EXIT_MODULE_MISSING)
    result = cpu_preflight._classify_probe(proc.returncode, proc.stderr)
    assert result.status is cpu_preflight.ProbeStatus.UNSAFE
    assert "baseline optimizations" in result.detail


def test_real_probe_on_this_host_is_not_unsafe() -> None:
    """Runs the real child: guards the probe program against syntax/import mistakes."""
    result = cpu_preflight._run_probe()
    assert result.status is not cpu_preflight.ProbeStatus.UNSAFE, result.detail


def test_probe_program_imports_nothing_from_core() -> None:
    assert "core." not in cpu_preflight._probe_code()
    assert str(cpu_preflight._CHILD_EXIT_MODULE_MISSING) in cpu_preflight._probe_code()


def test_both_skip_messages_share_the_same_remedy_text() -> None:
    plain = numpy_cpu_incompatible_message(("avx",))
    detailed = numpy_cpu_incompatible_message(("avx",), "killed by SIGILL")
    remedy = cpu_preflight._remedy_text()
    assert plain.endswith(remedy)
    assert detailed.endswith(remedy)
    assert "safety probe" not in plain
    assert "safety probe (killed by SIGILL)" in detailed


def test_warn_if_numpy_unsafe_false_when_flags_missing_and_probe_fails(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        cpu_preflight,
        "missing_pypi_numpy_features",
        lambda flags=None, machine=None: ("avx",),
    )
    monkeypatch.setattr(
        cpu_preflight,
        "_run_probe",
        lambda: cpu_preflight.ProbeResult(
            cpu_preflight.ProbeStatus.UNSAFE, "killed by SIGILL"
        ),
    )
    assert cpu_preflight.warn_if_numpy_unsafe() is False


def test_dl_backend_skips_native_imports_when_cpu_unsafe(monkeypatch) -> None:
    import importlib

    import core.dl_backend as dl_backend

    monkeypatch.setattr(
        cpu_preflight,
        "missing_pypi_numpy_features",
        lambda flags=None, machine=None: ("avx",),
    )
    monkeypatch.setattr(
        cpu_preflight,
        "_run_probe",
        lambda: cpu_preflight.ProbeResult(
            cpu_preflight.ProbeStatus.UNSAFE, "killed by SIGILL"
        ),
    )
    cpu_preflight._reset_probe_cache()
    cpu_preflight._logged_skip = False
    try:
        reloaded = importlib.reload(dl_backend)
        assert reloaded.is_available() is False
    finally:
        monkeypatch.setattr(
            cpu_preflight,
            "missing_pypi_numpy_features",
            lambda flags=None, machine=None: (),
        )
        cpu_preflight._reset_probe_cache()
        cpu_preflight._logged_skip = False
        importlib.reload(dl_backend)
