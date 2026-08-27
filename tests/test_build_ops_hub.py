"""Generated OPS_HUB must match tracked docs/ops Markdown."""

import sys

from scripts.build_ops_hub import main


def test_ops_hub_check_mode():
    old = sys.argv
    try:
        sys.argv = ["build_ops_hub.py", "--check"]
        assert main() == 0
    finally:
        sys.argv = old
