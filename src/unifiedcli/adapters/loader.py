"""Load plugin manifests from plugin.yaml files on disk."""

from __future__ import annotations

from pathlib import Path

import yaml

from unifiedcli.models.adapter import PluginManifest


def load_plugin_manifest(plugin_yaml_path: Path) -> PluginManifest:
    """Parse a plugin.yaml into a PluginManifest."""
    data = yaml.safe_load(plugin_yaml_path.read_text())
    return PluginManifest.model_validate(data)


def discover_plugins(adapters_dir: Path) -> list[PluginManifest]:
    """Scan an adapters directory for all plugin.yaml manifests."""
    manifests: list[PluginManifest] = []
    if not adapters_dir.exists():
        return manifests
    for plugin_dir in sorted(adapters_dir.iterdir()):
        if not plugin_dir.is_dir():
            continue
        yaml_path = plugin_dir / "plugin.yaml"
        if yaml_path.exists():
            manifests.append(load_plugin_manifest(yaml_path))
    return manifests
