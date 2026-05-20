"""Hub index link guard (docs/hubs + PRIMERS_HUB)."""

from scripts.check_hubs import main


def test_check_hubs_passes_on_repo_tree():
    assert main() == 0
