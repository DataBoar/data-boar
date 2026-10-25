"""Talent playbooks content (private data -- loaded from docs/private/)."""

from __future__ import annotations

import importlib.util
import os

PLAYBOOKS: dict[str, str] = {}
_private = os.path.join(
    os.path.dirname(__file__),
    "..",
    "docs",
    "private",
    "commercial",
    "_talent_playbooks_content_private.py",
)
if os.path.isfile(_private):
    _spec = importlib.util.spec_from_file_location("_priv", _private)
    if _spec and _spec.loader:
        _mod = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(_mod)
        PLAYBOOKS = getattr(_mod, "PLAYBOOKS", {})
