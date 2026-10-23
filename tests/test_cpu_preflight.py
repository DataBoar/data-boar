"""CPU pre-flight before numpy/ML imports (#929). SIGILL cannot be try/except."""

from __future__ import annotations

import ast
from pathlib import Path


from core.cpu_preflight import (
    PYPI_NUMPY_X86_REQUIRED,
    WHEELHOUSE_REPO,
    WHEELHOUSE_TAG,
    _reset_probe_cache,
    missing_pypi_numpy_features,
    numpy_cpu_incompatible_message,
    parse_cpuinfo_flags,
    numpy_import_safe,
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


def test_flags_complete_returns_safe_probe_not_called(monkeypatch) -> None:
    """When all required flags are present, numpy_import_safe returns True and probe is NOT called."""
    import core.cpu_preflight as cpu_preflight

    _reset_probe_cache()
    # Mock _run_probe to detect if it's called
    probe_called = {"called": False}
    original_run_probe = cpu_preflight._run_probe

    def mock_run_probe():
        probe_called["called"] = True
        return True

    monkeypatch.setattr(cpu_preflight, "_run_probe", mock_run_probe)

    # AVX CPU has all flags
    flags = parse_cpuinfo_flags(_AVX_CPUINFO)
    assert numpy_import_safe(flags, machine="x86_64") is True
    assert probe_called["called"] is False

    _reset_probe_cache()
    monkeypatch.setattr(cpu_preflight, "_run_probe", original_run_probe)


def test_flags_missing_probe_ok_returns_true(monkeypatch) -> None:
    """When flags missing but probe succeeds, numpy_import_safe returns True."""
    import core.cpu_preflight as cpu_preflight

    _reset_probe_cache()
    monkeypatch.setattr(cpu_preflight, "_run_probe", lambda: True)

    flags = parse_cpuinfo_flags(_NO_AVX_CPUINFO)
    assert numpy_import_safe(flags, machine="x86_64") is True

    # warn_if_numpy_unsafe should also return True (no log)
    cpu_preflight._logged_skip = False
    assert cpu_preflight.warn_if_numpy_unsafe() is True
    assert cpu_preflight._logged_skip is False

    _reset_probe_cache()


def test_flags_missing_probe_sigill_returns_false(monkeypatch) -> None:
    """When probe is killed by SIGILL (returncode == -4), numpy_import_safe returns False."""
    import core.cpu_preflight as cpu_preflight

    _reset_probe_cache()
    monkeypatch.setattr(cpu_preflight, "_run_probe", lambda: False)

    flags = parse_cpuinfo_flags(_NO_AVX_CPUINFO)
    assert numpy_import_safe(flags, machine="x86_64") is False

    # warn_if_numpy_unsafe should log once
    cpu_preflight._logged_skip = False
    assert cpu_preflight.warn_if_numpy_unsafe(flags, machine="x86_64") is False
    assert cpu_preflight._logged_skip is True

    # Second call should not log again (log-once)
    cpu_preflight._logged_skip = True
    assert cpu_preflight.warn_if_numpy_unsafe(flags, machine="x86_64") is False

    _reset_probe_cache()


def test_flags_missing_probe_timeout_returns_false(monkeypatch) -> None:
    """When probe times out, numpy_import_safe returns False."""
    import core.cpu_preflight as cpu_preflight

    _reset_probe_cache()
    monkeypatch.setattr(cpu_preflight, "_run_probe", lambda: False)

    flags = parse_cpuinfo_flags(_NO_AVX_CPUINFO)
    assert numpy_import_safe(flags, machine="x86_64") is False

    _reset_probe_cache()


def test_flags_missing_module_not_installed_returns_true(monkeypatch) -> None:
    """When probe returns 'module not installed' (None), numpy_import_safe returns True.

    This is the chosen behavior: callers' ImportError guards already skip ML
    when numpy/scipy/sklearn are not installed, so we treat missing modules
    as SAFE for the parent preflight.
    """
    import core.cpu_preflight as cpu_preflight

    _reset_probe_cache()
    monkeypatch.setattr(cpu_preflight, "_run_probe", lambda: None)

    flags = parse_cpuinfo_flags(_NO_AVX_CPUINFO)
    assert numpy_import_safe(flags, machine="x86_64") is True

    cpu_preflight._logged_skip = False
    assert cpu_preflight.warn_if_numpy_unsafe() is True

    _reset_probe_cache()


def test_probe_result_is_cached(monkeypatch) -> None:
    """Second call to numpy_import_safe does not run the child again."""
    import core.cpu_preflight as cpu_preflight

    _reset_probe_cache()
    probe_called = {"count": 0}

    def mock_run_probe():
        probe_called["count"] += 1
        return True

    monkeypatch.setattr(cpu_preflight, "_run_probe", mock_run_probe)

    flags = parse_cpuinfo_flags(_NO_AVX_CPUINFO)
    assert numpy_import_safe(flags, machine="x86_64") is True
    assert numpy_import_safe(flags, machine="x86_64") is True
    assert probe_called["count"] == 1

    _reset_probe_cache()


def test_real_probe_on_this_host(monkeypatch) -> None:
    """Run the real probe function on this host with flags forced missing.

    This guards the PROBE_CODE string from syntax or import mistakes.
    It must return True (safe) where numpy is installed.
    """
    import core.cpu_preflight as cpu_preflight

    _reset_probe_cache()
    # Force missing flags to trigger the probe
    monkeypatch.setattr(
        cpu_preflight,
        "missing_pypi_numpy_features",
        lambda flags=None, machine=None: ("avx",),
    )

    # The real probe should succeed on this host (numpy is installed)
    assert cpu_preflight.numpy_import_safe() is True
    assert cpu_preflight.warn_if_numpy_unsafe() is True

    _reset_probe_cache()


def test_warn_if_numpy_unsafe_false_when_probe_fails(monkeypatch) -> None:
    """warn_if_numpy_unsafe returns False and logs when probe fails."""
    import core.cpu_preflight as cpu_preflight

    _reset_probe_cache()
    monkeypatch.setattr(
        cpu_preflight,
        "missing_pypi_numpy_features",
        lambda flags=None, machine=None: ("avx",),
    )
    monkeypatch.setattr(cpu_preflight, "_run_probe", lambda: False)

    cpu_preflight._logged_skip = False
    result = cpu_preflight.warn_if_numpy_unsafe()
    assert result is False
    assert cpu_preflight._logged_skip is True

    _reset_probe_cache()


def test_dl_backend_skips_native_imports_when_cpu_unsafe(monkeypatch) -> None:
    import importlib

    import core.cpu_preflight as cpu_preflight
    import core.dl_backend as dl_backend

    monkeypatch.setattr(
        cpu_preflight,
        "missing_pypi_numpy_features",
        lambda flags=None, machine=None: ("avx",),
    )
    monkeypatch.setattr(cpu_preflight, "_run_probe", lambda: False)
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
        monkeypatch.setattr(cpu_preflight, "_run_probe", lambda: True)
        cpu_preflight._logged_skip = False
        importlib.reload(dl_backend)
        _reset_probe_cache()
