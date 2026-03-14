"""Adapter plugin system."""

from unifiedcli.adapters.interface import AdapterPlugin
from unifiedcli.adapters.registry import AdapterRegistry
from unifiedcli.adapters.loader import load_plugin_manifest
from unifiedcli.adapters.vault import VaultManager

__all__ = ["AdapterPlugin", "AdapterRegistry", "load_plugin_manifest", "VaultManager"]
