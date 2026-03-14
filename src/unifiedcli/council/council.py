"""Council orchestrator — high-level API for multi-model deliberation."""

from __future__ import annotations

from unifiedcli.council.protocol import DeliberationProtocol
from unifiedcli.council.providers import LLMProvider
from unifiedcli.memory.shared import SharedMemoryManager
from unifiedcli.models.council import ConsensusResult, DeliberationRound
from unifiedcli.models.memory import MemorySlot


class Council:
    """Orchestrates 3-model deliberation for planning, evaluation, and recovery."""

    def __init__(
        self,
        planner: LLMProvider,
        critic: LLMProvider,
        balancer: LLMProvider,
    ) -> None:
        self.protocol = DeliberationProtocol(planner, critic, balancer)

    async def deliberate(
        self,
        topic: str,
        context: str = "",
        memory: SharedMemoryManager | None = None,
    ) -> DeliberationRound:
        """Run a deliberation round, optionally reading shared memory for context."""
        if memory:
            mem_context = self._build_memory_context(memory)
            context = f"{context}\n\n{mem_context}" if context else mem_context

        dround = await self.protocol.run(topic, context)

        # Update memory with the decision if available
        if memory and dround.consensus:
            memory.append(
                MemorySlot.DECISIONS,
                f"## {topic}\n\n{dround.consensus.chosen_plan}\n\n"
                f"Confidence: {dround.consensus.confidence}\n",
            )

        return dround

    async def plan_task_graph(
        self,
        goal: str,
        memory: SharedMemoryManager | None = None,
    ) -> DeliberationRound:
        """Deliberate specifically on task graph generation for a user goal."""
        topic = f"Generate task graph for goal: {goal}"
        context = (
            "Generate a task graph (DAG) with task nodes. Each node should have:\n"
            "- task_id, name, task_type, dependencies, priority\n"
            "- executor_requirement with agent_type and capability_tags\n"
            "- decision_gate flag where appropriate\n"
            "Output the task graph as a JSON array of task node objects."
        )
        return await self.deliberate(topic, context, memory)

    async def evaluate_failure(
        self,
        task_id: str,
        error: str,
        memory: SharedMemoryManager | None = None,
    ) -> DeliberationRound:
        """Deliberate on how to handle a task failure."""
        topic = f"Evaluate failure for task {task_id}"
        context = f"Task {task_id} failed with error:\n{error}\n\nDetermine recovery strategy."
        return await self.deliberate(topic, context, memory)

    def _build_memory_context(self, memory: SharedMemoryManager) -> str:
        all_memory = memory.read_all()
        parts = []
        for slot, content in all_memory.items():
            if content.strip():
                parts.append(f"[{slot.value}]\n{content.strip()}")
        return "\n\n".join(parts)
