"""BaseAgent ABC — interface all agents must implement."""

from __future__ import annotations

from abc import ABC, abstractmethod

from unifiedcli.models.agent import DispatchContract, ReturnContract, FailureResult


class BaseAgent(ABC):
    """Abstract base for all agents (subagents)."""

    @abstractmethod
    async def execute_task(self, contract: DispatchContract) -> ReturnContract | FailureResult:
        """Execute a dispatched task and return a structured result."""
        ...

    @abstractmethod
    async def on_blocked(self, reason: str) -> None:
        """Called when the agent is blocked by an external condition."""
        ...

    @abstractmethod
    async def on_terminate(self) -> dict[str, str]:
        """Called when the agent is being terminated. Return summary for archival."""
        ...
