"""Tests for the core scheduler."""

import pytest
from pathlib import Path

from unifiedcli.agents.base import BaseAgent
from unifiedcli.agents.runtime import AgentLifecycleManager
from unifiedcli.graph.engine import TaskGraphEngine
from unifiedcli.models.agent import DispatchContract, ReturnContract, FailureResult
from unifiedcli.models.task import (
    TaskNode, TaskType, TaskStatus, ExecutorRequirement, SpawnPolicy,
)
from unifiedcli.scheduler.scheduler import Scheduler


class MockAgent(BaseAgent):
    async def execute_task(self, contract: DispatchContract) -> ReturnContract:
        return ReturnContract(
            task_id=contract.task_id,
            agent_id=contract.agent_id,
            status="completed",
            confidence=0.9,
        )

    async def on_blocked(self, reason: str) -> None:
        pass

    async def on_terminate(self) -> dict[str, str]:
        return {"summary": "terminated"}


@pytest.mark.asyncio
async def test_scheduler_tick(tmp_path: Path) -> None:
    engine = TaskGraphEngine()
    engine.add_node(TaskNode(
        task_id="t1", project_id="p", name="Task 1",
        task_type=TaskType.ANALYSIS,
    ))
    engine.add_node(TaskNode(
        task_id="t2", project_id="p", name="Task 2",
        task_type=TaskType.BUILD,
        dependencies=["t1"],
    ))

    lifecycle = AgentLifecycleManager(tmp_path / "agents")
    scheduler = Scheduler(engine, lifecycle)

    # First tick: t1 should become ready and get dispatched
    dispatched = await scheduler.tick()
    assert len(dispatched) == 1
    assert dispatched[0].task_id == "t1"
    assert engine.get_node("t1").status == TaskStatus.RUNNING


@pytest.mark.asyncio
async def test_scheduler_collect_result(tmp_path: Path) -> None:
    engine = TaskGraphEngine()
    engine.add_node(TaskNode(
        task_id="t1", project_id="p", name="Task 1",
        task_type=TaskType.ANALYSIS, status=TaskStatus.RUNNING,
    ))

    lifecycle = AgentLifecycleManager(tmp_path / "agents")
    scheduler = Scheduler(engine, lifecycle)

    result = ReturnContract(
        task_id="t1", agent_id="main_agent", status="completed", confidence=0.9,
    )
    await scheduler.collect_result("t1", result)
    assert engine.get_node("t1").status == TaskStatus.COMPLETED


@pytest.mark.asyncio
async def test_scheduler_dynamic_spawn(tmp_path: Path) -> None:
    """Scheduler should dynamically create a subagent when no matching agent exists."""
    engine = TaskGraphEngine()
    engine.add_node(TaskNode(
        task_id="deploy",
        project_id="p",
        name="Deploy Demo",
        task_type=TaskType.DEPLOY,
        executor_requirement=ExecutorRequirement(
            agent_type="hosting_agent",
            capability_tags=["hosting", "deployment"],
        ),
        spawn_policy=SpawnPolicy(spawn_if_missing=True, reuse_existing_if_match=True),
    ))

    lifecycle = AgentLifecycleManager(tmp_path / "agents")
    scheduler = Scheduler(engine, lifecycle)

    # No agents exist yet
    assert lifecycle.list_active(project_id="p") == []

    # Tick should spawn an agent and dispatch the task
    dispatched = await scheduler.tick()
    assert len(dispatched) == 1
    assert dispatched[0].task_id == "deploy"

    # A new agent should have been created
    active = lifecycle.list_active(project_id="p")
    assert len(active) == 1
    agent = active[0]
    assert agent.spec.agent_type == "hosting_agent"
    assert set(agent.spec.capabilities) == {"hosting", "deployment"}
    assert "deploy" in agent.spec.spawn_reason

    # The task should be assigned to the new agent
    assert dispatched[0].agent_id == agent.spec.agent_id
    assert engine.get_node("deploy").assigned_agent_id == agent.spec.agent_id

    # Private memory directory should have been initialized
    assert agent.private_memory is not None
    assert "knowledge.md" in agent.private_memory.list_files()


@pytest.mark.asyncio
async def test_scheduler_reuse_existing_agent(tmp_path: Path) -> None:
    """Scheduler should reuse an existing agent when capabilities match."""
    engine = TaskGraphEngine()
    engine.add_node(TaskNode(
        task_id="deploy_1",
        project_id="p",
        name="First Deploy",
        task_type=TaskType.DEPLOY,
        status=TaskStatus.COMPLETED,
        executor_requirement=ExecutorRequirement(
            agent_type="hosting_agent",
            capability_tags=["hosting"],
        ),
        spawn_policy=SpawnPolicy(),
    ))
    engine.add_node(TaskNode(
        task_id="deploy_2",
        project_id="p",
        name="Second Deploy",
        task_type=TaskType.DEPLOY,
        dependencies=["deploy_1"],
        executor_requirement=ExecutorRequirement(
            agent_type="hosting_agent",
            capability_tags=["hosting"],
        ),
        spawn_policy=SpawnPolicy(spawn_if_missing=True, reuse_existing_if_match=True),
    ))

    lifecycle = AgentLifecycleManager(tmp_path / "agents")

    # Pre-create an agent from the first deploy
    from unifiedcli.models.agent import AgentSpec
    lifecycle.create(AgentSpec(
        agent_id="agent_hosting_existing",
        project_id="p",
        agent_type="hosting_agent",
        capabilities=["hosting"],
    ))

    scheduler = Scheduler(engine, lifecycle)
    dispatched = await scheduler.tick()

    assert len(dispatched) == 1
    # Should reuse the existing agent, not spawn a new one
    assert dispatched[0].agent_id == "agent_hosting_existing"
    assert len(lifecycle.list_active(project_id="p")) == 1
