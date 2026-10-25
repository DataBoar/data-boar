# Copyright (c) 2025-2026, FabioLeitao. All rights reserved.
# This file is part of the Pro tier and is proprietary — NOT covered by
# the repository's root BSD-3-Clause LICENSE. See pro/LICENSE.
"""
Atomic checkpoint tracker for resumable Pro+ scans.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


class BoarStateTracker:
    """Persist and restore scan progress using atomic replace writes."""

    def __init__(self, checkpoint_file: str = ".data_boar_state.json") -> None:
        self.file_path = Path(checkpoint_file)
        self.state = self._load_state()

    def _load_state(self) -> dict[str, Any]:
        if not self.file_path.exists():
            return {"assets": {}}
        with self.file_path.open("r", encoding="utf-8") as handle:
            loaded = json.load(handle)
        if not isinstance(loaded, dict):
            return {"assets": {}}
        loaded.setdefault("assets", {})
        return loaded

    def table_checkpoint(self, table_name: str) -> dict[str, Any]:
        assets = self.state.get("assets")
        if not isinstance(assets, dict):
            return {}
        row = assets.get(table_name, {})
        return row if isinstance(row, dict) else {}

    def save_checkpoint(
        self,
        table_name: str,
        *,
        last_id: int,
        risk_score_accumulated: int = 0,
        status: str = "IN_PROGRESS",
    ) -> None:
        assets = self.state.setdefault("assets", {})
        if not isinstance(assets, dict):
            self.state["assets"] = {}
            assets = self.state["assets"]
        assets[table_name] = {
            "last_processed_id": int(last_id),
            "risk_score_accumulated": int(risk_score_accumulated),
            "status": str(status),
            "timestamp": time.time(),
        }
        self._atomic_write()

    def mark_completed(
        self, table_name: str, *, last_id: int, risk_score_accumulated: int = 0
    ) -> None:
        self.save_checkpoint(
            table_name,
            last_id=last_id,
            risk_score_accumulated=risk_score_accumulated,
            status="COMPLETED",
        )

    def _atomic_write(self) -> None:
        temp_file = self.file_path.with_name(f"{self.file_path.name}.tmp")
        with temp_file.open("w", encoding="utf-8") as handle:
            json.dump(self.state, handle, indent=2, sort_keys=True)
        temp_file.replace(self.file_path)
