"""AgentLifecycleManager — create, find, match, terminate, archive agents."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from unifiedcli.agents.base import BaseAgent
from unifiedcli.memory.private import PrivateMemoryManager
from unifiedcli.models.agent import AgentSpec, AgentStatus


class ManagedAgent:
    """An agent spec paired with its runtime instance."""

    def __init__(self, spec: AgentSpec, instance: BaseAgent | None = None) -> None:
        self.spec = spec
        self.instance = instance
        self.private_memory: PrivateMemoryManager | None = None


class AgentLifecycleManager:
    """Manages agent creation, matching, lifecycle transitions, and archival."""

    def __init__(self, agents_dir: Path) -> None:
        self.agents_dir = agents_dir
        self._agents: dict[str, ManagedAgent] = {}

    def create(
        self,
        spec: AgentSpec,
        instance: BaseAgent | None = None,
    ) -> ManagedAgent:
        """Create and register a new agent."""
        if spec.agent_id in self._agents:
            raise ValueError(f"Agent {spec.agent_id} already exists")
        managed = ManagedAgent(spec, instance)
        # Set up private memory
        agent_dir = self.agents_dir / spec.agent_id / "memory"
        managed.private_memory = PrivateMemoryManager(agent_dir)
        managed.private_memory.initialize()
        spec.private_memory_path = str(agent_dir)
        spec.status = AgentStatus.READY
        self._agents[spec.agent_id] = managed
        return managed

    def find_matching(
        self,
        project_id: str,
        capability_tags: list[str],
    ) -> ManagedAgent | None:
        """Find an existing agent that matches the required capabilities."""
        tag_set = set(capability_tags)
        for managed in self._agents.values():
            spec = managed.spec
            if spec.project_id != project_id:
                continue
            if spec.status in (AgentStatus.TERMINATED, AgentStatus.ARCHIVED):
                continue
            if tag_set & set(spec.capabilities):
                return managed
        return None

    def get(self, agent_id: str) -> ManagedAgent | None:
        return self._agents.get(agent_id)

    def transition(self, agent_id: str, new_status: AgentStatus) -> None:
        managed = self._agents.get(agent_id)
        if managed is None:
            raise KeyError(f"Agent {agent_id} not found")
        managed.spec.status = new_status
        if new_status == AgentStatus.TERMINATED:
            managed.spec.terminated_at = datetime.now()

    def terminate(self, agent_id: str) -> None:
        self.transition(agent_id, AgentStatus.TERMINATED)

    def archive(self, agent_id: str) -> None:
        self.transition(agent_id, AgentStatus.ARCHIVED)

    def list_active(self, project_id: str | None = None) -> list[ManagedAgent]:
        """List agents that are not terminated or archived."""
        result = []
        for managed in self._agents.values():
            if managed.spec.status in (AgentStatus.TERMINATED, AgentStatus.ARCHIVED):
                continue
            if project_id and managed.spec.project_id != project_id:
                continue
            result.append(managed)
        return result

    def list_all(self) -> list[ManagedAgent]:
        return list(self._agents.values())
