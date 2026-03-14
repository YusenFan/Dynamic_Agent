"""AdapterRegistry — register, discover, and match plugins by capability."""

from __future__ import annotations

from unifiedcli.adapters.interface import AdapterPlugin
from unifiedcli.models.adapter import PluginManifest, PluginStatus


class RegisteredPlugin:
    """A plugin with its manifest, instance, and lifecycle status."""

    def __init__(
        self,
        manifest: PluginManifest,
        instance: AdapterPlugin | None = None,
    ) -> None:
        self.manifest = manifest
        self.instance = instance
        self.status: PluginStatus = PluginStatus.REGISTERED


class AdapterRegistry:
    """Registry for adapter plugins. Supports capability-based matching."""

    def __init__(self) -> None:
        self._plugins: dict[str, RegisteredPlugin] = {}

    def register(
        self,
        manifest: PluginManifest,
        instance: AdapterPlugin | None = None,
    ) -> None:
        """Register a plugin manifest and optionally its instance."""
        entry = RegisteredPlugin(manifest, instance)
        if instance is not None and instance.validate_environment():
            entry.status = PluginStatus.VALIDATED
        self._plugins[manifest.plugin_id] = entry

    def get(self, plugin_id: str) -> RegisteredPlugin | None:
        return self._plugins.get(plugin_id)

    def match_by_capabilities(self, tags: list[str]) -> list[RegisteredPlugin]:
        """Find all plugins whose capability_tags intersect with the requested tags."""
        tag_set = set(tags)
        return [
            p for p in self._plugins.values()
            if tag_set & set(p.manifest.capability_tags)
            and p.status not in (PluginStatus.UNAVAILABLE, PluginStatus.DEPRECATED)
        ]

    def set_status(self, plugin_id: str, status: PluginStatus) -> None:
        plugin = self._plugins.get(plugin_id)
        if plugin is None:
            raise KeyError(f"Plugin {plugin_id} not found")
        plugin.status = status

    def list_plugins(self) -> list[RegisteredPlugin]:
        return list(self._plugins.values())
