"""Generated RULES_AND_SKILLS_HUB must match .cursor tree."""

import sys

from scripts.build_rules_skills_hub import main


def test_rules_skills_hub_check_mode():
    old = sys.argv
    try:
        sys.argv = ["build_rules_skills_hub.py", "--check"]
        assert main() == 0
    finally:
        sys.argv = old
