"""Importable package name for ``python -m data_boar`` (native / embed channel).

The dist name remains ``data-boar`` (hyphen). This package exists so the embedded
interpreter can run ``-m data_boar`` without relying on PATH console scripts alone.
"""

from __future__ import annotations

__all__: list[str] = []
