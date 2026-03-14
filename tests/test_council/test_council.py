"""Tests for council deliberation."""

import pytest
from pathlib import Path

from unifiedcli.council.council import Council
from unifiedcli.council.providers import MockLLMProvider
from unifiedcli.memory.shared import SharedMemoryManager
from unifiedcli.models.memory import MemorySlot


@pytest.mark.asyncio
async def test_deliberation_round() -> None:
    planner = MockLLMProvider(["Plan: Build scaffold, then deploy."])
    critic = MockLLMProvider(["Missing: dependency on research phase."])
    balancer = MockLLMProvider(['{"chosen_plan": "Build with research first", "confidence": 0.8, "risks": [], "rejected_plans": [], "reasoning_summary": "Added research", "agents_to_spawn": [], "decision_gate_required": false}'])

    council = Council(planner, critic, balancer)
    dround = await council.deliberate("Plan the project")

    assert dround.consensus is not None
    assert dround.consensus.confidence == 0.8
    assert len(dround.steps) == 5  # plan, critique, respond, balance, update_memory


@pytest.mark.asyncio
async def test_deliberation_with_memory(tmp_path: Path) -> None:
    memory = SharedMemoryManager(tmp_path / "memory")
    memory.initialize()
    memory.write(MemorySlot.GOALS, "# Goals\n\nDeploy a demo.\n")

    planner = MockLLMProvider(["Plan response"])
    critic = MockLLMProvider(["Critique response"])
    balancer = MockLLMProvider(["Balance response — no JSON"])

    council = Council(planner, critic, balancer)
    dround = await council.deliberate("Evaluate goals", memory=memory)

    assert dround.consensus is not None
    # Fallback parsing should still work
    assert dround.consensus.confidence == 0.5
    # Decision should be written to memory
    decisions = memory.read(MemorySlot.DECISIONS)
    assert "Evaluate goals" in decisions
