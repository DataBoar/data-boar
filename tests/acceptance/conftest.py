"""Collection guard of the prospect acceptance suite (epic #2280).

``test_demo_prospect_acceptance.py`` needs a Data Boar test image (``PROSPECT_TEST_IMAGE``),
Podman and ``systemd-run --user``. Without the image its 18 tests would each count as a skip
and push the ``test-extras`` job over the skip ceiling, so the file is not collected at all.
Passing the file explicitly on the command line still collects it (pytest never applies this
hook to an explicit argument), and its fixture keeps the skips for a missing Podman.
"""

from __future__ import annotations

import os
from pathlib import Path

_GUARDED = "test_demo_prospect_acceptance.py"


def pytest_ignore_collect(collection_path: Path, config):
    if collection_path.name == _GUARDED and not os.environ.get("PROSPECT_TEST_IMAGE"):
        return True
    return None
