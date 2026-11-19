"""Contract of the ``demo_prospect`` Ansible role (task 2280.3, epic #2280, issue #2284).

Source of truth: ``docs/desenho/2280.1.md``, sections 14 and 16, items D2280.1-36 and
D2280.1-37 and DEC-19. The static checks need no Ansible. The role runs (against localhost,
in a temporary home, with the ``prereqs`` and ``systemd`` tags skipped because they touch the
real host) are *defined* only where ``ansible-playbook`` exists, so no skip is counted (#2233).
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
ANSIBLE = REPO / "deploy" / "ansible"
PLAYBOOK = ANSIBLE / "site-demo-prospect.yml"
ROLE = ANSIBLE / "roles" / "demo_prospect"
INVENTORY_EXAMPLE = ANSIBLE / "inventory" / "hosts.ini.example"
CHECK_SCRIPT = REPO / "scripts" / "ansible-syntax-check.sh"
CLI = REPO / "deploy" / "demo" / "prospect" / "prospect.py"
QUADLET = REPO / "deploy" / "demo" / "quadlet"

HOST_VARS = (
    "prospect_image",
    "prospect_license_hostname",
    "prospect_license_file",
    "prospect_profile_file",
    "prospect_base_env",
)
SHORTCUTS = ("prospect-up", "prospect-down", "prospect-list")


def _load_cli():
    spec = importlib.util.spec_from_file_location("prospect_cli_ansible", CLI)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    keep, sys.dont_write_bytecode = (
        sys.dont_write_bytecode,
        True,
    )  # no .pyc under deploy/
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.dont_write_bytecode = keep
    return mod


def _need(path: Path) -> Path:
    assert path.exists(), f"não implementado: {path.relative_to(REPO)}"
    return path


def _role_files() -> list[Path]:
    _need(ROLE)
    return sorted(p for p in ROLE.rglob("*") if p.is_file())


# ----------------------------------------------------------------------------- D-36
def test_D2280_1_36_playbook_shape() -> None:
    """D2280.1-36: hosts demo_prospect, become false, unattended-apt environment, the role."""
    plays = yaml.safe_load(_need(PLAYBOOK).read_text(encoding="utf-8"))
    assert isinstance(plays, list) and len(plays) == 1
    play = plays[0]
    assert play["hosts"] == "demo_prospect"
    assert play["become"] is False
    assert "labop_debian_unattended_apt_environment" in str(play["environment"])
    assert "demo_prospect" in play["roles"]


def test_D2280_1_36_host_vars_have_no_default_in_the_repo() -> None:
    """D2280.1-36: the host variables have no default in the role, nor in group_vars."""
    defaults = _need(ROLE / "defaults" / "main.yml")
    for path in (defaults, ANSIBLE / "group_vars" / "all.yml"):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for name in HOST_VARS:
            assert name not in data, f"{path.relative_to(REPO)} dá padrão a {name}"


def test_D2280_1_36_role_asserts_the_host_vars() -> None:
    """D2280.1-36 / section 14: the role fails with a clear message when a var is missing."""
    tasks = "\n".join(
        p.read_text(encoding="utf-8") for p in _role_files() if p.parent.name == "tasks"
    )
    assert "ansible.builtin.assert" in tasks
    for name in HOST_VARS:
        assert name in tasks, f"a role não confere {name}"


def test_D2280_1_36_syntax_check_script_covers_the_playbook() -> None:
    """D2280.1-36: scripts/ansible-syntax-check.sh checks site-demo-prospect.yml too."""
    text = CHECK_SCRIPT.read_text(encoding="utf-8")
    assert "site-demo-prospect.yml" in text
    assert "lab-node-01-baseline.yml" in text  # the old checks stay


def test_D2280_1_36_inventory_example_documents_the_group_and_vars() -> None:
    """D2280.1-36 / section 16: the example shows the group and the var names, no real host."""
    text = _need(INVENTORY_EXAMPLE).read_text(encoding="utf-8")
    assert "[demo_prospect]" in text
    for name in HOST_VARS:
        assert name in text
    assert "[data_boar]" in text  # the existing group stays


# ----------------------------------------------------------------------------- D-37
_FORBIDDEN = re.compile(r"supabase|m365|/demo/env", re.I)
_IPV4 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
_HOST = re.compile(
    r"\b[a-z0-9][a-z0-9-]*(?:\.[a-z0-9-]+)*\.(?:net\.br|com\.br|com|net|org|io|br|dev)\b",
    re.I,
)
_HOST_OK = {"dashboard.net.br", "docker.io"}
# 0.0.0.0 is only allowed as in-pod web bind (Exec + config), not elsewhere in the tree.
_POD_BIND_0_ALLOWLIST: dict[Path, re.Pattern[str]] = {
    QUADLET / "demo-prospect@.container": re.compile(r"--host\s+0\.0\.0\.0"),
    REPO / "deploy/demo/prospect/config.prospect.yaml": re.compile(
        r"^\s*host:\s+0\.0\.0\.0\s*$", re.M
    ),
}


def _d37_scan_text(rel: str, text: str) -> list[str]:
    bad: list[str] = []
    if _FORBIDDEN.search(text):
        bad.append(f"{rel}: segredo ou env da demo pública")
    path = REPO / rel
    allow = _POD_BIND_0_ALLOWLIST.get(path.resolve())
    for ip in _IPV4.findall(text):
        if ip.startswith("127."):
            continue
        if ip == "0.0.0.0":
            if allow and allow.search(text):
                continue
            bad.append(f"{rel}: 0.0.0.0 fora do bind interno permitido do pod")
            continue
        bad.append(f"{rel}: IP {ip}")
    for host in _HOST.findall(text):
        if host.lower() not in _HOST_OK:
            bad.append(f"{rel}: hostname {host}")
    return bad


def _d37_files() -> list[Path]:
    files = [p for p in (REPO / "deploy/demo/prospect").iterdir() if p.is_file()]
    files += _role_files()
    files += [p for p in QUADLET.glob("demo-prospect*") if p.is_file()]
    files += [QUADLET / "demo-slot-restore.service"]
    files += [PLAYBOOK]
    return files


def test_D2280_1_37_no_public_demo_secret_ip_or_hostname() -> None:
    """D2280.1-37: prospect/, the role and the units name no supabase, m365, /demo/env,
    IP beyond loopback or hostname beyond dashboard.net.br."""
    bad: list[str] = []
    for path in _d37_files():
        rel = str(path.relative_to(REPO))
        bad.extend(_d37_scan_text(rel, path.read_text(encoding="utf-8")))
    assert not bad, bad


def test_D2280_1_37_rejects_non_loopback_ip_outside_pod_bind() -> None:
    """D2280.1-37: 0.0.0.0 in Ansible/templates is forbidden; only pod Exec/config bind."""
    bad = _d37_scan_text(
        "deploy/ansible/roles/demo_prospect/templates/example.j2",
        "reverse_proxy 0.0.0.0:443\n",
    )
    assert bad and "0.0.0.0" in bad[0]
    bad2 = _d37_scan_text(
        "deploy/ansible/roles/demo_prospect/templates/example.j2",
        "reverse_proxy 192.0.2.1:443\n",
    )
    assert bad2 and "192.0.2.1" in bad2[0]
    ok = _d37_scan_text(
        str((QUADLET / "demo-prospect@.container").relative_to(REPO)),
        (QUADLET / "demo-prospect@.container").read_text(encoding="utf-8"),
    )
    assert ok == []


# ------------------------------------------------------------------- the role, for real
if shutil.which("ansible-playbook"):
    import pytest

    def _vars(tmp: Path, **over: object) -> dict[str, object]:
        for d in ("corpus", "extras", "caddy"):
            (tmp / d).mkdir(exist_ok=True)
        for f in ("profile.yaml", "recs.yaml", "base.env", "license.lic", "Caddyfile"):
            (tmp / f).write_text("x\n", encoding="utf-8")
        (tmp / "admin.sock").write_text("", encoding="utf-8")
        base: dict[str, object] = {
            "demo_prospect_home": str(tmp / "home"),
            "prospect_domain": "dashboard.net.br",
            "prospect_proxy_container": "proxy",
            "prospect_tls_line": "tls internal",
            "prospect_caddy_dir": str(tmp / "caddy"),
            "prospect_caddy_admin_socket": str(tmp / "admin.sock"),
            "prospect_caddyfile": str(tmp / "Caddyfile"),
            "prospect_corpus_dir": str(tmp / "corpus"),
            "prospect_profile_file": str(tmp / "profile.yaml"),
            "prospect_recommendations_file": str(tmp / "recs.yaml"),
            "prospect_base_env": str(tmp / "base.env"),
            "prospect_license_file": str(tmp / "license.lic"),
            "prospect_image": "localhost/data_boar:test-signed",
            "prospect_license_hostname": "demo-host",
            "prospect_port": 18101,
            "prospect_protected_containers": ["apresentacao"],
        }
        base.update(over)
        return {k: v for k, v in base.items() if v is not None}

    def _run(tmp: Path, extra_vars: dict[str, object], *flags: str):
        (tmp / "hosts.ini").write_text(
            "[demo_prospect]\nlocalhost ansible_connection=local "
            f"ansible_python_interpreter={sys.executable}\n",
            encoding="utf-8",
        )
        (tmp / "vars.json").write_text(json.dumps(extra_vars), encoding="utf-8")
        env = {
            **os.environ,
            "ANSIBLE_STDOUT_CALLBACK": "default",
            "ANSIBLE_HOME": str(tmp / "ansible-home"),
            "ANSIBLE_LOCAL_TEMP": str(tmp / "ansible-tmp"),
            "ANSIBLE_NOCOLOR": "1",
        }
        return subprocess.run(
            [
                "ansible-playbook",
                "-i",
                str(tmp / "hosts.ini"),
                str(PLAYBOOK),
                "-e",
                f"@{tmp / 'vars.json'}",
                "--skip-tags",
                "prereqs,systemd",
                *flags,
            ],
            cwd=ANSIBLE,
            env=env,
            capture_output=True,
            text=True,
            check=False,
            timeout=300,
        )

    def _changed(out: str) -> int:
        m = re.search(r"changed=(\d+)", out)
        assert m, out[-2000:]
        return int(m.group(1))

    @pytest.fixture(scope="module")
    def applied(tmp_path_factory):
        tmp = tmp_path_factory.mktemp("role")
        extra = _vars(tmp)
        res = _run(tmp, extra)
        return tmp, extra, res

    def test_D2280_1_14_role_installs_everything(applied) -> None:
        """Section 14: CLI and both templates in bin/, units, shortcuts, drop-in, fragment dir."""
        tmp, extra, res = applied
        assert res.returncode == 0, res.stdout[-3000:] + res.stderr[-1500:]
        home = tmp / "home"
        bin_dir = home / "demo" / "prospect" / "bin"
        for name in ("prospect.py", "config.prospect.yaml", "site.caddy.tmpl"):
            src = REPO / "deploy" / "demo" / "prospect" / name
            assert (bin_dir / name).read_bytes() == src.read_bytes(), name
        assert (bin_dir / "prospect.py").stat().st_mode & stat.S_IXUSR
        sysd = home / ".config" / "systemd" / "user"
        for name in (
            "demo-prospect.slice",
            "demo-slot-restore.service",
            "demo-prospect-reap.service",
            "demo-prospect-reap.timer",
        ):
            assert (sysd / name).read_bytes() == (QUADLET / name).read_bytes(), name
        quad = home / ".config" / "containers" / "systemd"
        tpl = "demo-prospect@.container"
        assert (quad / tpl).read_bytes() == (QUADLET / tpl).read_bytes()
        drop = (quad / f"{tpl}.d" / "10-host.conf").read_text(encoding="utf-8")
        assert "[Container]" in drop.splitlines()
        assert "Image=localhost/data_boar:test-signed" in drop
        assert "HostName=demo-host" in drop
        assert "PROSPECT_INVENTORY" not in drop
        for sc in SHORTCUTS:
            path = home / ".local" / "bin" / sc
            assert path.stat().st_mode & stat.S_IXUSR, sc
            body = path.read_text(encoding="utf-8")
            sub = sc.removeprefix("prospect-")
            assert f'exec "{home}/demo/prospect/bin/prospect.py" {sub} "$@"' in body
        assert (tmp / "caddy").is_dir()

    def test_D2280_1_16_inventory_json_is_closed_0600_and_loadable(applied) -> None:
        """Section 16 / DEC-19: 0600, only schema keys, license mode enforced, CLI accepts."""
        tmp, extra, res = applied
        assert res.returncode == 0, res.stdout[-3000:]
        path = tmp / "home" / "demo" / "prospect" / "inventory.json"
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
        data = json.loads(path.read_text(encoding="utf-8"))
        cli = _load_cli()
        assert set(data) <= set(cli._INV_SCHEMA)
        assert data["prospect_license_mode"] == "enforced"
        assert data["prospect_port"] == 18101 and isinstance(data["prospect_port"], int)
        assert data["prospect_protected_containers"] == ["apresentacao"]
        assert (
            "prospect_reserve" not in data
        )  # unset optional keys keep the CLI default
        assert "demo_prospect_home" not in data
        inv = cli.load_inventory(path)
        assert inv["prospect_image"] == "localhost/data_boar:test-signed"
        assert inv["prospect_reserve"] == 128

    def test_D2280_1_14_second_run_changes_nothing(applied) -> None:
        """Section 14: idempotent."""
        tmp, extra, _ = applied
        res = _run(tmp, extra)
        assert res.returncode == 0, res.stdout[-3000:]
        assert _changed(res.stdout) == 0, res.stdout[-3000:]

    def test_D2280_1_14_check_mode_changes_nothing(tmp_path) -> None:
        """Section 14: --check writes nothing."""
        res = _run(tmp_path, _vars(tmp_path), "--check")
        assert res.returncode == 0, res.stdout[-3000:] + res.stderr[-1500:]
        assert not (tmp_path / "home").exists()

    def test_D2280_1_36_missing_host_var_fails_clear_and_writes_nothing(
        tmp_path,
    ) -> None:
        """D2280.1-36: without prospect_image the role asserts, naming the variable."""
        res = _run(tmp_path, _vars(tmp_path, prospect_image=None))
        assert res.returncode != 0
        assert "prospect_image" in res.stdout + res.stderr
        assert not (tmp_path / "home" / "demo" / "prospect" / "inventory.json").exists()

    def test_D2280_1_14_license_mode_is_fixed_enforced(tmp_path) -> None:
        """Revision 1: the role never writes prospect_license_mode other than enforced."""
        res = _run(tmp_path, _vars(tmp_path, prospect_license_mode="open"))
        assert res.returncode != 0
        assert "prospect_license_mode" in res.stdout + res.stderr

    def test_D2280_1_36_playbook_syntax_check() -> None:
        """D2280.1-36: ansible-playbook --syntax-check passes on the example inventory."""
        res = subprocess.run(
            [
                "ansible-playbook",
                "--syntax-check",
                "-i",
                str(INVENTORY_EXAMPLE),
                str(PLAYBOOK),
            ],
            cwd=ANSIBLE,
            env={**os.environ, "ANSIBLE_STDOUT_CALLBACK": "default"},
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )
        assert res.returncode == 0, res.stdout + res.stderr
