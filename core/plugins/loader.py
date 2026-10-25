"""Load remediation plugins by dotted ``module.path:ClassName`` (#606)."""

from __future__ import annotations

import importlib

from core.plugins.base import PluginError, RemediationPlugin


def load_remediation_plugin(plugin_path: str) -> RemediationPlugin:
    """
    Loads a remediation plugin from a dotted module path in the format
    ``module.submodule:ClassName`` (e.g. ``myorg.stealthizer:StealthizerPlugin``).

    Uses importlib.import_module + getattr. Validates the loaded object
    against RemediationPlugin protocol before returning.
    Raises PluginError if module cannot be imported or object is non-conformant.
    """
    try:
        module_path, class_name = plugin_path.rsplit(":", 1)
    except ValueError as exc:
        raise PluginError(
            f"Invalid plugin_path format '{plugin_path}'. "
            "Expected 'module.path:ClassName'."
        ) from exc
    if not module_path or not class_name:
        raise PluginError(
            f"Invalid plugin_path format '{plugin_path}'. "
            "Expected 'module.path:ClassName'."
        )
    try:
        module = importlib.import_module(module_path)
    except ImportError as exc:
        raise PluginError(
            f"Cannot import plugin module '{module_path}': {exc}"
        ) from exc
    cls = getattr(module, class_name, None)
    if cls is None:
        raise PluginError(f"Class '{class_name}' not found in module '{module_path}'.")
    try:
        instance = cls()
    except Exception as exc:
        raise PluginError(f"Cannot instantiate plugin '{class_name}': {exc}") from exc
    if not isinstance(instance, RemediationPlugin):
        raise PluginError(
            f"'{plugin_path}' does not conform to RemediationPlugin protocol."
        )
    return instance
