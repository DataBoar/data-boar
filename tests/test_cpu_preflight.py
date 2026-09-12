"""CPU pre-flight before numpy/ML imports (#929). SIGILL cannot be try/except."""

from __future__ import annotations

import ast
from pathlib import Path

from core.cpu_preflight import (
    PYPI_NUMPY_X86_REQUIRED,
    WHEELHOUSE_REPO,
    WHEELHOUSE_TAG,
    missing_pypi_numpy_features,
    numpy_cpu_incompatible_message,
    parse_cpuinfo_flags,
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


def test_warn_if_numpy_unsafe_false_when_flags_missing(monkeypatch) -> None:
    import core.cpu_preflight as cpu_preflight

    monkeypatch.setattr(
        cpu_preflight,
        "missing_pypi_numpy_features",
        lambda: ("avx",),
    )
    cpu_preflight._logged_skip = False
    assert cpu_preflight.warn_if_numpy_unsafe() is False
    cpu_preflight._logged_skip = False


def test_dl_backend_skips_native_imports_when_cpu_unsafe(monkeypatch) -> None:
    import importlib

    import core.cpu_preflight as cpu_preflight
    import core.dl_backend as dl_backend

    monkeypatch.setattr(cpu_preflight, "missing_pypi_numpy_features", lambda: ("avx",))
    cpu_preflight._logged_skip = False
    try:
        reloaded = importlib.reload(dl_backend)
        assert reloaded.is_available() is False
    finally:
        monkeypatch.setattr(cpu_preflight, "missing_pypi_numpy_features", lambda: ())
        cpu_preflight._logged_skip = False
        importlib.reload(dl_backend)
