"""
Allowlisted inventory metadata builders for connector probes.

The goal is to avoid dumping full vendor payloads (which can include excessive
runtime internals) while keeping useful operator diagnostics.
"""

from __future__ import annotations

from typing import Any


def _text(value: Any, *, limit: int = 120) -> str:
    if value is None:
        return ""
    out = str(value).strip()
    if not out:
        return ""
    return out[:limit]


def build_redis_inventory_details(info: dict[str, Any]) -> dict[str, dict[str, str]]:
    executive = {
        "engine": "redis",
        "version": _text(info.get("redis_version"), limit=48),
        "mode": _text(info.get("redis_mode"), limit=48),
    }
    technical = {
        "os": _text(info.get("os"), limit=120),
        "arch_bits": _text(info.get("arch_bits"), limit=16),
        "tcp_port": _text(info.get("tcp_port"), limit=16),
    }
    return {
        "executive": {k: v for k, v in executive.items() if v},
        "technical": {k: v for k, v in technical.items() if v},
    }


def build_mongodb_inventory_details(info: dict[str, Any]) -> dict[str, dict[str, str]]:
    executive = {
        "engine": "mongodb",
        "version": _text(info.get("version"), limit=64),
        "wire_version": _text(info.get("maxWireVersion"), limit=16),
    }
    technical = {
        "allocator": _text(info.get("allocator"), limit=48),
        "javascript_engine": _text(info.get("javascriptEngine"), limit=48),
        "openssl": _text(
            (info.get("openssl") or {}).get("running")
            if isinstance(info.get("openssl"), dict)
            else None,
            limit=48,
        ),
    }
    return {
        "executive": {k: v for k, v in executive.items() if v},
        "technical": {k: v for k, v in technical.items() if v},
    }
