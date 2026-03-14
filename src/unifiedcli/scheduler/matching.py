"""Agent matching — match tasks to agents: reuse > spawn > main agent direct."""

from __future__ import annotations

from unifiedcli.agents.runtime import AgentLifecycleManager, ManagedAgent
from unifiedcli.models.task import TaskNode


class MatchResult:
    """Result of matching a task to an agent."""

    def __init__(
        self,
        task: TaskNode,
        agent: ManagedAgent | None = None,
        action: str = "direct",  # "reuse", "spawn", "direct"
    ) -> None:
        self.task = task
        self.agent = agent
        self.action = action


def match_task_to_agent(
    task: TaskNode,
    lifecycle: AgentLifecycleManager,
) -> MatchResult:
    """Determine how to execute a task: reuse existing agent, spawn new, or direct.

    Priority:
    1. Reuse existing agent with matching capabilities in same project
    2. Spawn new agent if spawn_policy allows
    3. Main agent executes directly (no agent needed)
    """
    req = task.executor_requirement
    if req is None:
        return MatchResult(task, action="direct")

    # Try to reuse
    if task.spawn_policy is None or task.spawn_policy.reuse_existing_if_match:
        existing = lifecycle.find_matching(
            project_id=task.project_id,
            capability_tags=req.capability_tags,
        )
        if existing is not None:
            return MatchResult(task, agent=existing, action="reuse")

    # Try to spawn
    if task.spawn_policy is None or task.spawn_policy.spawn_if_missing:
        return MatchResult(task, action="spawn")

    # Fallback: direct execution
    return MatchResult(task, action="direct")
