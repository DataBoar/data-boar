"""Contract of the prospect pod units and templates (task 2280.2, epic #2280, issue #2283).

Source of truth: ``docs/desenho/2280.1.md``, items D2280.1-31 to D2280.1-35. Parses the
Quadlet units and templates without Podman. D2280.1-34 runs the real ``quadlet -dryrun``
and is *defined* only where Podman 5+ and its quadlet generator exist; D2280.1-34b runs a
container and is defined only when ``PROSPECT_D34B_IMAGE`` names a Data Boar image (never
``PROSPECT_TEST_IMAGE``, which turns on the acceptance suite). No skip is counted (#2233).
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

import yaml

from tests.test_deploy_demo_contract import _containers, _parse_unit, _values

REPO = Path(__file__).resolve().parents[1]
DEMO = REPO / "deploy" / "demo"
QUADLET = DEMO / "quadlet"
PROSPECT = DEMO / "prospect"
TEMPLATE = QUADLET / "demo-prospect@.container"

FORBIDDEN_SOURCES = ("demo/env", "demo/certs", "m365-token", "demo/data")
FORBIDDEN_SOURCES += ("apresentacao/data",)


def _unit() -> list[tuple[str, str, str]]:
    return _parse_unit(TEMPLATE)


def test_D2280_1_31_template_do_pod() -> None:
    """D2280.1-31: network, loopback port, limits, hardening, tmpfs, no HostName, no host
    secret mounts, same Image as the dashboard, Restart=no, TTL, pre/post hooks, no Install."""
    u = _unit()
    assert _values(u, "Container", "Network") == ["prospect-%i"]
    ports = _values(u, "Container", "PublishPort")
    assert len(ports) == 1 and ports[0].startswith("127.0.0.1:${PROSPECT_PORT}:8088")
    args = " ".join(_values(u, "Container", "PodmanArgs"))
    for flag in ("--memory 700m", "--memory-swap 700m", "--cpus ", "--pids-limit "):
        assert flag in args, flag
    assert "--ulimit core=0" in args
    assert _values(u, "Container", "DropCapability") == ["all"]
    assert _values(u, "Container", "NoNewPrivileges") == ["true"]
    assert _values(u, "Container", "ReadOnly") == ["true"]
    assert _values(u, "Container", "LogDriver") == ["none"]
    tmpfs = _values(u, "Container", "Tmpfs")
    assert {t.split(":", 1)[0] for t in tmpfs} == {"/data", "/tmp"}  # noqa: S108
    assert all("size=" in t for t in tmpfs)
    assert not [k for s, k, _v in u if k == "HostName"]
    for key in ("Volume", "EnvironmentFile"):
        for value in _values(u, "Container", key) + _values(u, "Service", key):
            for bad in FORBIDDEN_SOURCES:
                assert bad not in value, (key, value)
    dash = _parse_unit(QUADLET / "dashboard.container")
    assert _values(u, "Container", "Image") == _values(dash, "Container", "Image")
    assert _values(u, "Service", "Restart") == ["no"]
    assert _values(u, "Service", "RuntimeMaxSec") == ["5400"]
    pre = " ".join(_values(u, "Service", "ExecStartPre"))
    assert "network create --internal" in pre and "prospect-%i" in pre
    post = " ".join(_values(u, "Service", "ExecStopPost"))
    assert "prospect.py teardown %i --from-unit" in post
    assert not [s for s, _k, _v in u if s == "Install"]
    assert "[Install]" not in TEMPLATE.read_text(encoding="utf-8")


def test_D2280_1_31_volumes_e_env_do_slug() -> None:
    """Section 5 (revision 1): slug files ro,Z from %t; shared folders ro without Z via
    state.env; pod.env as the container env-file; the slice."""
    u = _unit()
    vols = _values(u, "Container", "Volume")
    assert "${PROSPECT_CORPUS_DIR}:/corpus:ro" in vols
    assert "${PROSPECT_EXTRAS_DIR}:/extras:ro" in vols
    for v in vols:
        if v.startswith("%t/demo-prospect/%i/"):
            assert v.endswith(":ro,Z"), v
    targets = {v.split(":")[1] for v in vols}
    assert {
        "/cfg/config.yaml",
        "/cfg/profile.yaml",
        "/cfg/recommendations.yaml",
    } <= targets
    assert {"/certs/tls.crt", "/certs/tls.key", "/lic", "/corpus", "/extras"} <= targets
    assert _values(u, "Container", "EnvironmentFile") == ["%t/demo-prospect/%i/pod.env"]
    assert _values(u, "Service", "EnvironmentFile") == ["%t/demo-prospect/%i/state.env"]
    assert _values(u, "Service", "Slice") == ["demo-prospect.slice"]
    assert _values(u, "Container", "ContainerName") == ["prospect-%i"]
    assert _values(u, "Container", "Label") == ["databoar.prospect=%i"]
    exec_line = " ".join(_values(u, "Container", "Exec"))
    assert "--config /cfg/config.yaml --web" in exec_line
    slice_ = _parse_unit(QUADLET / "demo-prospect.slice")
    assert _values(slice_, "Slice", "MemoryMax") == ["720M"]


def test_D2280_1_32_reaper_e_restore() -> None:
    """D2280.1-32: reaper oneshot runs only `prospect.py reap`; timer <= 2 min, not
    persistent; demo-slot-restore oneshot runs only `prospect.py restore-slot`."""
    reap = _parse_unit(QUADLET / "demo-prospect-reap.service")
    assert _values(reap, "Service", "Type") == ["oneshot"]
    execs = _values(reap, "Service", "ExecStart")
    assert len(execs) == 1 and execs[0].endswith("/prospect.py reap")
    assert not any("podman" in v for _s, _k, v in reap)
    timer = _parse_unit(QUADLET / "demo-prospect-reap.timer")

    def minutes(v: str) -> float:
        m = re.fullmatch(r"(\d+)(min|s)", v)
        assert m, v
        return int(m.group(1)) / (60 if m.group(2) == "s" else 1)

    assert 0 < minutes(_values(timer, "Timer", "OnBootSec")[0]) <= 2
    assert 0 < minutes(_values(timer, "Timer", "OnUnitActiveSec")[0]) <= 2
    assert _values(timer, "Timer", "Persistent") == ["false"]
    restore = _parse_unit(QUADLET / "demo-slot-restore.service")
    assert _values(restore, "Service", "Type") == ["oneshot"]
    execs = _values(restore, "Service", "ExecStart")
    assert len(execs) == 1 and execs[0].endswith("/prospect.py restore-slot")
    assert not any("podman" in v for _s, _k, v in restore)


def test_D2280_1_33_contrato_da_demo_cobre_o_pod() -> None:
    """D2280.1-33: the existing demo contract (unchanged) now also scans the pod template."""
    assert "demo-prospect@" in _containers()


def test_D2280_1_35_extensoes_do_template() -> None:
    """D2280.1-35: file_scan.extensions == sorted(SUPPORTED_EXTENSIONS)."""
    from connectors.filesystem_connector import SUPPORTED_EXTENSIONS

    data = yaml.safe_load((PROSPECT / "config.prospect.yaml").read_text("utf-8"))
    assert data["file_scan"]["extensions"] == sorted(SUPPORTED_EXTENSIONS)


def _podman_major() -> int:
    if not shutil.which("podman"):
        return 0
    r = subprocess.run(
        ["podman", "version", "--format", "{{.Client.Version}}"],
        capture_output=True,
        text=True,
        check=False,
    )
    m = re.match(r"(\d+)\.", r.stdout.strip())
    return int(m.group(1)) if r.returncode == 0 and m else 0


_QUADLET = Path("/usr/libexec/podman/quadlet")

if os.name != "nt" and _QUADLET.exists() and _podman_major() >= 5:

    def test_D2280_1_34_quadlet_dryrun(tmp_path: Path) -> None:
        """D2280.1-34: quadlet -dryrun -user with a sample 10-host.conf."""
        shutil.copy(TEMPLATE, tmp_path / TEMPLATE.name)
        d = tmp_path / f"{TEMPLATE.name}.d"
        d.mkdir()
        (d / "10-host.conf").write_text(
            "[Container]\nImage=localhost/data_boar:exemplo\nHostName=pod.prospect.test\n",
            encoding="utf-8",
        )
        r = subprocess.run(
            [str(_QUADLET), "-dryrun", "-user"],
            env={**os.environ, "QUADLET_UNIT_DIRS": str(tmp_path)},
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
        assert r.returncode == 0, r.stderr[-500:]
        out = r.stdout
        start = [ln for ln in out.splitlines() if ln.startswith("ExecStart=")]
        assert len(start) == 1
        line = start[0]
        for piece in (
            "--network prospect-%i",
            "--hostname pod.prospect.test",
            "--read-only",
            "--log-driver none",
            "--env-file %t/demo-prospect/%i/pod.env",
            "${PROSPECT_PORT}",
            "-v ${PROSPECT_CORPUS_DIR}:/corpus:ro ",
            "-v ${PROSPECT_EXTRAS_DIR}:/extras:ro ",
        ):
            assert piece in line, piece
        assert " localhost/data_boar:exemplo main.py " in line
        service = out.split("[Service]", 1)[1]
        assert "pod.env" not in "\n".join(
            ln for ln in service.splitlines() if not ln.startswith("ExecStart=")
        )


_D34B_IMAGE = os.environ.get("PROSPECT_D34B_IMAGE", "")

if os.name != "nt" and _D34B_IMAGE and _podman_major() >= 5:

    def test_D2280_1_34b_tmpfs_noexec_conclui_scan(tmp_path: Path) -> None:
        """D2280.1-34b: the template's Tmpfs (noexec included) run the app and a scan."""
        corpus = tmp_path / "corpus"
        corpus.mkdir()
        (corpus / "a.txt").write_text("CPF: 529.982.247-25\n", encoding="utf-8")
        cfg = tmp_path / "config.yaml"
        cfg.write_text(
            "targets:\n  - name: Corpus\n    type: filesystem\n    path: /corpus\n"
            "sqlite_path: /data/audit_results.db\nreport:\n  output_dir: /data\n"
            "scan:\n  max_workers: 1\n",
            encoding="utf-8",
        )
        for p in (tmp_path, corpus, corpus / "a.txt", cfg):
            p.chmod(0o755 if p.is_dir() else 0o644)
        tmpfs = []
        for t in _values(_unit(), "Container", "Tmpfs"):
            tmpfs += ["--tmpfs", t]
        driver = (
            "import os,subprocess,sys\n"
            "r=subprocess.run([sys.executable,'-m','core.licensing.gil_container_gate',"
            "'main.py','--config','/cfg/config.yaml'],capture_output=True,text=True)\n"
            "print('RC',r.returncode)\n"
            "print('DATA',sorted(os.listdir('/data')))\n"
        )
        r = subprocess.run(
            ["podman", "run", "--rm", "--read-only", "--cap-drop", "all",
             "--security-opt=no-new-privileges", "--network", "none", *tmpfs,
             "-e", "DATA_BOAR_LICENSE_MODE=open",
             "-v", f"{cfg}:/cfg/config.yaml:ro", "-v", f"{corpus}:/corpus:ro",
             "--entrypoint", "/usr/local/bin/python3.14t", _D34B_IMAGE, "-c", driver],
            capture_output=True,
            text=True,
            check=False,
            timeout=600,
        )  # fmt: skip
        assert "RC 0" in r.stdout, (r.stdout[-500:], r.stderr[-500:])
        assert "audit_results.db" in r.stdout
        assert all("noexec" in t for t in tmpfs[1::2])
