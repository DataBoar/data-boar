"""Public plugin host surface (#606 / ADR-0059)."""

from core.plugins.base import PluginError, RemediationPlugin
from core.plugins.loader import load_remediation_plugin

__all__ = ["RemediationPlugin", "PluginError", "load_remediation_plugin"]
