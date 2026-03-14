"""Tests for AdapterRegistry."""

from unifiedcli.adapters.registry import AdapterRegistry
from unifiedcli.models.adapter import PluginManifest, ChannelType, PluginStatus


class TestAdapterRegistry:
    def test_register_and_get(self) -> None:
        registry = AdapterRegistry()
        manifest = PluginManifest(
            plugin_id="vercel_adapter",
            platform="vercel",
            channel_type=ChannelType.CLI,
            capability_tags=["hosting", "deployment"],
            actions=["deploy", "get_status"],
        )
        registry.register(manifest)
        result = registry.get("vercel_adapter")
        assert result is not None
        assert result.manifest.platform == "vercel"

    def test_match_by_capabilities(self) -> None:
        registry = AdapterRegistry()
        registry.register(PluginManifest(
            plugin_id="vercel",
            platform="vercel",
            channel_type=ChannelType.CLI,
            capability_tags=["hosting", "deployment"],
        ))
        registry.register(PluginManifest(
            plugin_id="supabase",
            platform="supabase",
            channel_type=ChannelType.API,
            capability_tags=["database", "auth"],
        ))
        matches = registry.match_by_capabilities(["hosting"])
        assert len(matches) == 1
        assert matches[0].manifest.plugin_id == "vercel"

    def test_unavailable_excluded_from_match(self) -> None:
        registry = AdapterRegistry()
        registry.register(PluginManifest(
            plugin_id="vercel",
            platform="vercel",
            channel_type=ChannelType.CLI,
            capability_tags=["hosting"],
        ))
        registry.set_status("vercel", PluginStatus.UNAVAILABLE)
        matches = registry.match_by_capabilities(["hosting"])
        assert len(matches) == 0
