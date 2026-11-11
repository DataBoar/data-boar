"""#2175: scripts/wheelhouse/haiku_build_wheels.sh, exercised with a fake interpreter (no Haiku needed)."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "wheelhouse"
    / "haiku_build_wheels.sh"
)

pytestmark = pytest.mark.skipif(
    sys.platform == "win32"
    or shutil.which("bash") is None
    or shutil.which("timeout") is None,
    reason="needs bash and coreutils timeout",
)

FAKE_PY = r"""#!/usr/bin/env bash
# fake interpreter: -c prints the platform tag; -m pip wheel creates a wheel named after the pin
if [ "$1" = "-c" ]; then echo "haiku_r1~beta6_x86_64"; exit 0; fi
args=("$@"); out=""; spec=""; isol=1
for ((i=0;i<${#args[@]};i++)); do
  case "${args[$i]}" in
    -w) out="${args[$((i+1))]}" ;;
    --no-build-isolation) isol=0 ;;
  esac
done
spec="${args[$((${#args[@]}-1))]}"
name="${spec%%==*}"
case "$name" in
  badpkg) exit 1 ;;
  slowpkg) sleep 5; exit 0 ;;
  needsiso) [ "$isol" = 0 ] || exit 1 ;;
  markered) case "$spec" in *win32*) exit 0 ;; esac ;;
esac
touch "$out/${name//-/_}-1.0-py3-none-any.whl"
"""


def _run(
    tmp_path: Path, reqs: str, **env: str
) -> tuple[subprocess.CompletedProcess, Path]:
    fake = tmp_path / "fakepy"
    fake.write_text(FAKE_PY, encoding="utf-8")
    fake.chmod(0o755)
    req = tmp_path / "requirements.txt"
    req.write_text(reqs, encoding="utf-8")
    out = tmp_path / "out"
    proc = subprocess.run(
        ["bash", str(SCRIPT), str(req), str(out)],
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHON": str(fake), "PER_PKG_TIMEOUT": "1", **env},
        check=False,
    )
    return proc, out


def _results(out: Path) -> dict[str, str]:
    rows = (out / "results.tsv").read_text(encoding="utf-8").splitlines()[1:]
    return {r.split("\t")[0]: r.split("\t")[1] for r in rows}


def test_all_pins_build_records_platform_and_checksums(tmp_path: Path) -> None:
    reqs = "# comment\nalpha==1.0 ; python_version >= '3.9' \\\n    --hash=sha256:aa\nbeta==2.0 \\\n    --hash=sha256:bb\n"
    proc, out = _run(tmp_path, reqs)
    assert proc.returncode == 0, proc.stderr
    assert _results(out) == {"alpha": "OK", "beta": "OK"}
    assert (out / "platform.txt").read_text(
        encoding="utf-8"
    ).strip() == "haiku_r1~beta6_x86_64"
    sums = (out / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
    assert len(sums) == 2 and all(line.endswith(".whl") for line in sums)


def test_failure_and_timeout_are_reported_and_exit_2(tmp_path: Path) -> None:
    proc, out = _run(tmp_path, "alpha==1.0\nbadpkg==1.0\nslowpkg==1.0\n")
    assert proc.returncode == 2
    assert _results(out) == {"alpha": "OK", "badpkg": "FAIL", "slowpkg": "TIMEOUT"}


def test_no_isolation_fallback_only_for_listed_packages(tmp_path: Path) -> None:
    proc, out = _run(
        tmp_path,
        "needsiso==1.0\nbadpkg==1.0\n",
        NO_ISOLATION_PKGS="needsiso",
    )
    assert (
        proc.returncode == 2
    )  # badpkg is not in the list, so no second attempt rescues it
    assert _results(out) == {"needsiso": "OK_NO_ISOLATION", "badpkg": "FAIL"}


def test_pin_whose_marker_does_not_match_is_skipped_not_ok(tmp_path: Path) -> None:
    proc, out = _run(
        tmp_path, "markered==1.0 ; sys_platform == 'win32' \\\n    --hash=sha256:cc\n"
    )
    assert proc.returncode == 0
    assert _results(out) == {"markered": "SKIP"}
    assert not (out / "SHA256SUMS").exists()
