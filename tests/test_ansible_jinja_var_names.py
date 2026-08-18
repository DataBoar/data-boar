"""Guard Ansible variable / role prefixes stay valid Jinja2 identifiers (#1631).

Hyphenated prefixes such as ``lab-node-01_`` parse as subtraction in Jinja2 and
break every playbook that references them. Canonical role/var prefix is
``lab_node_01_`` (underscores only).
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
ANSIBLE_ROOT = REPO_ROOT / "ops" / "automation" / "ansible"
ROLES_DIR = ANSIBLE_ROOT / "roles"
PLAYBOOKS_DIR = ANSIBLE_ROOT / "playbooks"

# Broken pattern that shipped once via blind sed (issue #1631).
_HYPHENATED_VAR_PREFIX = re.compile(r"lab-node-01_")
_ROLE_LINE = re.compile(r"^\s*-\s*role:\s*([^\s#]+)", re.M)


def _iter_ansible_text_files() -> list[Path]:
    if not ANSIBLE_ROOT.is_dir():
        return []
    out: list[Path] = []
    for path in ANSIBLE_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".yml", ".yaml", ".j2", ".ini", ".md"}:
            continue
        out.append(path)
    return sorted(out)


def test_ansible_tree_has_no_hyphenated_lab_node_var_prefix() -> None:
    """Reject ``lab-node-01_`` anywhere under ops/automation/ansible (Jinja-invalid)."""
    hits: list[str] = []
    for path in _iter_ansible_text_files():
        text = path.read_text(encoding="utf-8")
        if _HYPHENATED_VAR_PREFIX.search(text):
            hits.append(str(path.relative_to(REPO_ROOT)))
    assert not hits, (
        "Invalid Jinja2 variable prefix lab-node-01_ (use lab_node_01_). Files: "
        + ", ".join(hits[:40])
    )


def test_playbook_role_names_match_role_directories() -> None:
    """Every ``role:`` in lab playbooks must have a matching directory under roles/."""
    if not PLAYBOOKS_DIR.is_dir() or not ROLES_DIR.is_dir():
        pytest.skip("ansible tree missing")
    role_dirs = {p.name for p in ROLES_DIR.iterdir() if p.is_dir()}
    missing: list[str] = []
    for playbook in sorted(PLAYBOOKS_DIR.glob("lab-node-01-*.yml")):
        text = playbook.read_text(encoding="utf-8")
        for name in _ROLE_LINE.findall(text):
            if name not in role_dirs:
                missing.append(f"{playbook.name}: role {name!r} (no roles/{name}/)")
    assert not missing, "Playbook role refs must match directories:\n" + "\n".join(
        missing
    )


def test_lab_node_01_role_dirs_use_underscore_prefix() -> None:
    """Role directories must use lab_node_01_* (never lab-node-01_* or leftover t14_*)."""
    if not ROLES_DIR.is_dir():
        pytest.skip("roles dir missing")
    bad: list[str] = []
    for path in ROLES_DIR.iterdir():
        if not path.is_dir():
            continue
        name = path.name
        if name.startswith("t14_") or name.startswith("lab-node-01_"):
            bad.append(name)
        elif name.startswith("lab_node_01_"):
            continue
        # Other roles (e.g. share-clients) are allowed without the prefix.
    assert not bad, f"Rename role dirs to lab_node_01_*: {bad}"


def test_ansible_playbook_syntax_check_when_ansible_available() -> None:
    """Delegate to ``scripts/ansible-syntax-check.sh`` when ansible-core is installed."""
    script = REPO_ROOT / "scripts" / "ansible-syntax-check.sh"
    if not script.is_file():
        pytest.skip("ansible-syntax-check.sh missing")
    try:
        probe = subprocess.run(
            ["ansible-playbook", "--version"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except FileNotFoundError:
        pytest.skip("ansible-playbook not on PATH (CI ansible-syntax job covers this)")
    if probe.returncode != 0:
        pytest.skip("ansible-playbook not usable")

    proc = subprocess.run(
        ["bash", str(script)],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    assert proc.returncode == 0, (
        f"ansible-syntax-check.sh failed:\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
    )


def test_jinja2_rejects_hyphenated_prefix_and_accepts_underscore() -> None:
    """Unit proof for #1631 (no Ansible filter required)."""
    from jinja2 import Environment
    from jinja2.exceptions import TemplateSyntaxError

    Environment().from_string("{{ lab_node_01_install_bitwarden_cli }}")
    with pytest.raises(TemplateSyntaxError):
        Environment().from_string("{{ lab-node-01_install_bitwarden_cli }}")


def test_group_vars_operator_key_uses_underscore_prefix() -> None:
    path = ANSIBLE_ROOT / "group_vars" / "all.yml"
    if not path.is_file():
        pytest.skip("group_vars missing")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    assert "lab_node_01_operator_target_user" in data
    assert "lab-node-01_operator_target_user" not in data
