"""Contract for the public demo deployment files in ``deploy/demo/`` (#1447).

Parses the Quadlet units and configs without Podman: images pinned, memory
limits, capabilities dropped, nothing published on a public address, the reset
never runs a container from a oneshot unit, and no secret is tracked.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DEMO = REPO / "deploy" / "demo"
QUADLET = DEMO / "quadlet"
RESTORE = DEMO / "bin" / "demo-restore-baseline.sh"

_DIGEST = re.compile(r"@sha256:[0-9a-f]{64}$")
_VERSION_TAG = re.compile(r":\d+(\.\d+)+$")


def _parse_unit(path: Path) -> list[tuple[str, str, str]]:
    """Return (section, key, value) triples; systemd allows repeated keys."""
    section = ""
    out: list[tuple[str, str, str]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith(("#", ";")):
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1]
            continue
        key, _, value = line.partition("=")
        out.append((section, key.strip(), value.strip()))
    return out


def _values(unit: list[tuple[str, str, str]], section: str, key: str) -> list[str]:
    return [v for s, k, v in unit if s == section and k == key]


def _containers() -> dict[str, list[tuple[str, str, str]]]:
    units = {p.stem: _parse_unit(p) for p in sorted(QUADLET.glob("*.container"))}
    assert {"dashboard", "apresentacao", "samba"} <= set(units)  # no vacuous pass
    return units


def test_expected_units_exist():
    names = {p.name for p in QUADLET.iterdir()}
    assert {
        "dashboard.container",
        "apresentacao.container",
        "samba.container",
        "demo-reset.service",
        "demo-reset.timer",
    } <= names


def test_images_pinned_by_digest_or_version_tag():
    for name, unit in _containers().items():
        images = _values(unit, "Container", "Image")
        assert len(images) == 1, name
        image = images[0]
        assert "latest" not in image, name
        assert _DIGEST.search(image) or _VERSION_TAG.search(image), (name, image)


def test_every_container_has_memory_limit_and_hardening():
    for name, unit in _containers().items():
        args = " ".join(_values(unit, "Container", "PodmanArgs"))
        assert re.search(r"--memory[ =]\d+[mg]\b", args), name
        assert "all" in _values(unit, "Container", "DropCapability"), name
        assert _values(unit, "Container", "NoNewPrivileges") == ["true"], name


def test_nothing_published_on_a_public_address():
    for name, unit in _containers().items():
        for port in _values(unit, "Container", "PublishPort"):
            assert port.startswith("127.0.0.1:"), (name, port)
        if _values(unit, "Container", "Network") == ["host"]:
            exec_line = " ".join(_values(unit, "Container", "Exec"))
            assert "--host 127.0.0.1" in exec_line, name


def test_samba_is_loopback_high_port_and_small():
    unit = _containers()["samba"]
    ports = _values(unit, "Container", "PublishPort")
    assert ports and all(int(p.split(":")[1]) >= 1024 for p in ports), (
        "rootless cannot bind < 1024 on the host"
    )
    args = " ".join(_values(unit, "Container", "PodmanArgs"))
    assert "--memory 96m" in args
    assert any(":/share:ro" in v for v in _values(unit, "Container", "Volume"))


def test_reset_restarts_the_service_and_runs_no_container_itself():
    """The oneshot must not start Podman: a conmon left in its cgroup was
    SIGKILLed at the stop timeout, leaving the dashboard without a monitor."""
    reset = _parse_unit(QUADLET / "demo-reset.service")
    assert _values(reset, "Service", "Type") == ["oneshot"]
    execs = _values(reset, "Service", "ExecStart")
    assert execs == ["/usr/bin/systemctl --user restart dashboard.service"]
    assert not any("podman" in v for _s, _k, v in reset)
    timer = _parse_unit(QUADLET / "demo-reset.timer")
    assert _values(timer, "Timer", "OnCalendar") == ["*:00/30"]
    assert _values(timer, "Timer", "Unit") == ["demo-reset.service"]


def test_dashboard_restores_baseline_before_start_and_presentation_never_resets():
    dash = _containers()["dashboard"]
    pre = _values(dash, "Service", "ExecStartPre")
    assert pre and "demo-restore-baseline.sh" in pre[0]
    pres = _containers()["apresentacao"]
    assert not _values(pres, "Service", "ExecStartPre")
    assert not any("restore" in v for _s, _k, v in pres)


def test_no_secret_is_tracked():
    assert not (DEMO / "samba" / "users.json").exists()
    example = json.loads((DEMO / "samba" / "users.example.json").read_text())
    for entry in example["users"]["all_entries"]:
        assert entry["password"].startswith("CHANGE-ME")
    for path in DEMO.rglob("*"):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        assert not re.search(r"\$2[aby]\$\d\d\$", text), path  # bcrypt hash
        assert not re.search(r"-----BEGIN [A-Z ]*PRIVATE KEY-----", text), path
        for ip in re.findall(r"\b\d{1,3}(?:\.\d{1,3}){3}\b", text):
            assert ip in ("127.0.0.1", "0.0.0.0"), (path, ip)


def test_restore_script_is_executable_in_git_and_parses():
    # The mode on disk says nothing on Windows (no execute bit, st_mode 0o100666);
    # what reaches the demo host is the mode committed in the git index, and that
    # one is the same on every platform. No platform branch, so no skip is counted.
    listed = subprocess.run(
        ["git", "ls-files", "-s", "--", RESTORE.relative_to(REPO).as_posix()],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert listed.startswith("100755 "), listed
    subprocess.run(["bash", "-n", str(RESTORE)], check=True)


if os.name != "nt":  # bash + POSIX fake podman; defined only where it runs (#2233)

    def _fake_podman(tmp_path: Path) -> dict[str, str]:
        bindir = tmp_path / "fakebin"
        bindir.mkdir()
        fake = bindir / "podman"
        fake.write_text('#!/bin/sh\n[ "$1" = unshare ] && shift\nexec "$@"\n')
        fake.chmod(0o755)
        return {**os.environ, "PATH": f"{bindir}:{os.environ['PATH']}"}

    def test_restore_script_resets_data_to_baseline(tmp_path):
        data = tmp_path / "demo" / "data"
        base = tmp_path / "demo" / "baseline"
        (data / "reports").mkdir(parents=True)
        base.mkdir()
        (data / "audit_results.db").write_text("dirty")
        (data / "reports" / "r.xlsx").write_text("dirty")
        (data / "config.yaml").write_text("edited: true\n")
        (base / "config.yaml").write_text("baseline: true\n")
        subprocess.run(
            [str(RESTORE), str(data), str(base)], check=True, env=_fake_podman(tmp_path)
        )
        assert sorted(p.name for p in data.iterdir()) == ["config.yaml"]
        assert (data / "config.yaml").read_text() == "baseline: true\n"

    def test_restore_script_refuses_unexpected_paths(tmp_path):
        data = tmp_path / "somewhere"
        base = tmp_path / "demo" / "baseline"
        data.mkdir()
        base.mkdir(parents=True)
        (base / "config.yaml").write_text("baseline: true\n")
        (data / "keep.txt").write_text("keep")
        proc = subprocess.run(
            [str(RESTORE), str(data), str(base)],
            env=_fake_podman(tmp_path),
            capture_output=True,
            text=True,
        )
        assert proc.returncode != 0
        assert (data / "keep.txt").exists()

    def test_restore_script_refuses_baseline_without_config(tmp_path):
        data = tmp_path / "demo" / "data"
        base = tmp_path / "demo" / "baseline"
        data.mkdir(parents=True)
        base.mkdir()
        (data / "keep.txt").write_text("keep")
        proc = subprocess.run(
            [str(RESTORE), str(data), str(base)],
            env=_fake_podman(tmp_path),
            capture_output=True,
            text=True,
        )
        assert proc.returncode != 0
        assert (data / "keep.txt").exists()
