"""AdapterPlugin ABC — unified interface for all external system integrations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from unifiedcli.models.adapter import AdapterResult, AdapterError


class AdapterPlugin(ABC):
    """Base class for all adapter plugins.

    Adapters wrap CLI/API/MCP/Skill integrations behind a uniform interface.
    Agents never interact with external systems directly — always through adapters.
    """

    @abstractmethod
    def discover_capabilities(self) -> list[str]:
        """Return capability tags this adapter provides."""
        ...

    @abstractmethod
    def validate_environment(self) -> bool:
        """Check if required tools/CLIs are available."""
        ...

    @abstractmethod
    def authenticate(self, auth_ref: str) -> bool:
        """Authenticate using a vault:// reference. Never receives raw secrets."""
        ...

    @abstractmethod
    def execute(self, action: str, params: dict[str, Any]) -> AdapterResult | AdapterError:
        """Execute a named action with parameters."""
        ...

    @abstractmethod
    def get_status(self, resource_ref: str) -> dict[str, Any]:
        """Get the status of a resource managed by this adapter."""
        ...

    @abstractmethod
    def recover(self, error_context: dict[str, Any]) -> AdapterResult | AdapterError:
        """Attempt to recover from an error."""
        ...
