"""Core scheduler — event-driven loop for task dispatch and collection."""

from __future__ import annotations

import json
import uuid
from pathlib import Path

from unifiedcli.agents.runtime import AgentLifecycleManager, ManagedAgent
from unifiedcli.graph.engine import TaskGraphEngine
from unifiedcli.models.agent import AgentSpec, AgentStatus, DispatchContract, ReturnContract, FailureResult
from unifiedcli.models.task import TaskNode, TaskStatus
from unifiedcli.scheduler.matching import MatchResult, match_task_to_agent
from unifiedcli.scheduler.priority import rank_tasks


class Scheduler:
    """Core scheduling loop: scan → rank → match → dispatch → collect → update."""

    def __init__(
        self,
        graph: TaskGraphEngine,
        lifecycle: AgentLifecycleManager,
    ) -> None:
        self.graph = graph
        self.lifecycle = lifecycle
        self._dispatches: dict[str, DispatchContract] = {}

    async def tick(self) -> list[DispatchContract]:
        """Run one scheduling tick. Returns dispatched contracts."""
        # 1. Get ready tasks
        ready = self.graph.get_ready_tasks()
        if not ready:
            return []

        # 2. Transition pending → ready
        for task in ready:
            self.graph.transition(task.task_id, TaskStatus.READY)

        # 3. Rank
        ranked = rank_tasks(ready, self.graph.nodes)

        # 4. Match and dispatch
        dispatched: list[DispatchContract] = []
        for task in ranked:
            match = match_task_to_agent(task, self.lifecycle)
            contract = await self._dispatch(task, match)
            if contract:
                dispatched.append(contract)

        return dispatched

    async def collect_result(
        self, task_id: str, result: ReturnContract | FailureResult
    ) -> None:
        """Process a completed or failed task result."""
        node = self.graph.get_node(task_id)
        if isinstance(result, FailureResult) or result.status == "failed":
            if isinstance(result, FailureResult):
                node.error = result.error_category
            self.graph.transition(task_id, TaskStatus.FAILED)
        else:
            self.graph.transition(task_id, TaskStatus.COMPLETED)

        # Clean up dispatch
        self._dispatches.pop(task_id, None)

    async def _dispatch(self, task: TaskNode, match: MatchResult) -> DispatchContract | None:
        """Dispatch a task based on matching result."""
        agent: ManagedAgent | None = match.agent

        if match.action == "spawn":
            # Create a new agent
            spec = AgentSpec(
                agent_id=f"agent_{uuid.uuid4().hex[:8]}",
                project_id=task.project_id,
                agent_type=task.executor_requirement.agent_type if task.executor_requirement else "generic",
                capabilities=(
                    task.executor_requirement.capability_tags
                    if task.executor_requirement
                    else []
                ),
                spawn_reason=f"Spawned for task {task.task_id}",
            )
            agent = self.lifecycle.create(spec)

        # Build dispatch contract
        contract = DispatchContract(
            dispatch_id=f"dispatch_{uuid.uuid4().hex[:8]}",
            task_id=task.task_id,
            project_id=task.project_id,
            agent_id=agent.spec.agent_id if agent else "main_agent",
            task_summary=task.description or task.name,
            input_refs=task.inputs,
            expected_outputs=(
                task.artifact_contract.expected_outputs
                if task.artifact_contract
                else []
            ),
        )

        self._dispatches[task.task_id] = contract
        self.graph.transition(task.task_id, TaskStatus.RUNNING)
        task.assigned_agent_id = contract.agent_id

        # If there's an agent instance, execute
        if agent and agent.instance:
            result = await agent.instance.execute_task(contract)
            await self.collect_result(task.task_id, result)

        return contract

    def save_state(self, path: Path) -> None:
        """Persist scheduler state for crash recovery."""
        state = {
            "dispatches": {
                k: v.model_dump(mode="json")
                for k, v in self._dispatches.items()
            },
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(state, indent=2))
