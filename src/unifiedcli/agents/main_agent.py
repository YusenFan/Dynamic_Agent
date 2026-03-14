"""MainAgent — central orchestrator that ties everything together."""

from __future__ import annotations

from enum import Enum
from pathlib import Path

from unifiedcli.agents.runtime import AgentLifecycleManager
from unifiedcli.council.council import Council
from unifiedcli.council.providers import LLMProvider
from unifiedcli.decisions.gate import DecisionGateEngine
from unifiedcli.graph.engine import TaskGraphEngine
from unifiedcli.memory.shared import SharedMemoryManager
from unifiedcli.models.memory import MemorySlot
from unifiedcli.models.task import TaskNode, TaskStatus, TaskType
from unifiedcli.scheduler.scheduler import Scheduler
from unifiedcli.workspace.project import ProjectManager


class MainAgentState(str, Enum):
    IDLE = "idle"
    INTAKE = "intake"
    PLANNING = "planning"
    ALLOCATING = "allocating"
    EXECUTING = "executing"
    WAITING_FOR_USER_DECISION = "waiting_for_user_decision"
    RECOVERY_COORDINATION = "recovery_coordination"
    VERIFYING = "verifying"
    TERMINAL = "terminal"


class MainAgent:
    """Central orchestrator for a project. Manages the full lifecycle.

    State machine:
    IDLE → INTAKE → PLANNING → ALLOCATING → EXECUTING
    → WAITING_FOR_USER_DECISION → EXECUTING
    → RECOVERY_COORDINATION → EXECUTING
    → VERIFYING → TERMINAL
    """

    def __init__(
        self,
        project: ProjectManager,
        council: Council,
        decision_engine: DecisionGateEngine | None = None,
    ) -> None:
        self.project = project
        self.council = council
        self.decision_engine = decision_engine or DecisionGateEngine()
        self.state = MainAgentState.IDLE
        self.lifecycle = AgentLifecycleManager(self.project.path / "agents")
        self.scheduler = Scheduler(self.project.graph, self.lifecycle)

    @property
    def memory(self) -> SharedMemoryManager:
        return self.project.memory

    @property
    def graph(self) -> TaskGraphEngine:
        return self.project.graph

    async def intake(self, goal: str) -> None:
        """Parse user goal and initialize shared memory."""
        self.state = MainAgentState.INTAKE

        self.memory.write(
            MemorySlot.GOALS,
            f"# Goals\n\nPrimary Goal:\n{goal}\n",
        )
        self.memory.write(
            MemorySlot.CONSTRAINTS,
            "# Constraints\n\nUser is non-technical.\nMinimal interaction preferred.\n",
        )
        self.memory.write(
            MemorySlot.PROGRESS,
            "# Progress\n\nStatus: Intake complete, planning next.\n",
        )

    async def plan(self) -> None:
        """Run council deliberation to generate the task graph."""
        self.state = MainAgentState.PLANNING

        goal = self.memory.read(MemorySlot.GOALS)
        dround = await self.council.plan_task_graph(goal, self.memory)

        # Store deliberation result
        if dround.consensus:
            self.memory.append(
                MemorySlot.PROGRESS,
                f"Planning complete. Confidence: {dround.consensus.confidence}\n",
            )

    async def execute_loop(self, max_ticks: int = 50) -> None:
        """Run the scheduler loop until completion or max ticks."""
        self.state = MainAgentState.EXECUTING

        for _ in range(max_ticks):
            # Check for decision gates
            for node in self.graph.nodes.values():
                if node.status == TaskStatus.WAITING_USER:
                    self.state = MainAgentState.WAITING_FOR_USER_DECISION
                    # Decision handling would happen here
                    break

            # Check for failures needing recovery
            failed = [
                n for n in self.graph.nodes.values()
                if n.status == TaskStatus.FAILED
            ]
            if failed:
                self.state = MainAgentState.RECOVERY_COORDINATION
                for node in failed:
                    await self._handle_failure(node)
                self.state = MainAgentState.EXECUTING

            # Run scheduler tick
            dispatched = await self.scheduler.tick()
            if not dispatched:
                # Check if all done
                all_done = all(
                    n.status in (TaskStatus.COMPLETED, TaskStatus.ARCHIVED)
                    for n in self.graph.nodes.values()
                )
                if all_done:
                    break

        # Final state
        all_completed = all(
            n.status in (TaskStatus.COMPLETED, TaskStatus.ARCHIVED)
            for n in self.graph.nodes.values()
        )
        self.state = MainAgentState.VERIFYING if all_completed else MainAgentState.EXECUTING

    async def verify_and_finish(self) -> bool:
        """Verify deployment and transition to terminal state."""
        self.state = MainAgentState.VERIFYING

        all_completed = all(
            n.status in (TaskStatus.COMPLETED, TaskStatus.ARCHIVED)
            for n in self.graph.nodes.values()
        )

        if all_completed:
            self.state = MainAgentState.TERMINAL
            self.memory.append(MemorySlot.PROGRESS, "Project completed successfully.\n")
            self.project.save_graph()
            return True

        return False

    async def _handle_failure(self, node: TaskNode) -> None:
        """Handle a failed task through council evaluation."""
        dround = await self.council.evaluate_failure(
            node.task_id,
            node.error or "Unknown error",
            self.memory,
        )

        # Try retry if possible
        try:
            self.graph.retry_node(node.task_id)
        except ValueError:
            # Max retries exceeded — archive the node
            self.graph.transition(node.task_id, TaskStatus.ARCHIVED)
            self.memory.append(
                MemorySlot.RISKS,
                f"Task {node.task_id} failed permanently: {node.error}\n",
            )
