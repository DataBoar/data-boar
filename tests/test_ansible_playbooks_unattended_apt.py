"""Guard: every Ansible play that targets hosts sets unattended-apt environment (apt-listbugs)."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]

# Playbooks that define one or more plays with `hosts:` must set `environment` on each play
# so Debian apt-listbugs does not abort non-interactive apt (see group_vars/all.yml in each tree).
_ANSIBLE_PLAYBOOK_GLOBS = [
    "ops/automation/ansible/playbooks/*.yml",
    "deploy/ansible/site*.yml",
]


def _iter_play_dicts(document: object):
    if isinstance(document, list):
        for item in document:
            if isinstance(item, dict) and "hosts" in item:
                yield item
    elif isinstance(document, dict) and "hosts" in document:
        yield document


def _playbook_files() -> list[Path]:
    out: list[Path] = []
    for pattern in _ANSIBLE_PLAYBOOK_GLOBS:
        out.extend(sorted(REPO_ROOT.glob(pattern)))
    return out


@pytest.mark.parametrize(
    "path",
    _playbook_files(),
    ids=lambda p: str(p.relative_to(REPO_ROOT)).replace("\\", "/"),
)
def test_each_play_sets_environment_for_unattended_apt(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    document = yaml.safe_load(text)
    plays = list(_iter_play_dicts(document))
    assert plays, f"{path}: expected at least one play with hosts"
    for play in plays:
        assert "environment" in play, (
            f"{path}: play {play.get('name', '?')!r} must set "
            f'environment: "{{{{ labop_debian_unattended_apt_environment }}}}" '
            f"(or combine with extras) so apt-listbugs does not abort unattended apt. "
            f"See ops/automation/ansible/group_vars/all.yml and README Troubleshooting."
        )


def test_group_vars_define_labop_debian_unattended_apt_environment() -> None:
    for rel in (
        "ops/automation/ansible/group_vars/all.yml",
        "deploy/ansible/group_vars/all.yml",
    ):
        p = REPO_ROOT / rel
        data = yaml.safe_load(p.read_text(encoding="utf-8"))
        assert isinstance(data, dict)
        env = data.get("labop_debian_unattended_apt_environment")
        assert isinstance(env, dict), rel
        assert env.get("APT_LISTBUGS_FRONTEND") == "none", rel
