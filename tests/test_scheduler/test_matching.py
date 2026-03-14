"""Tests for agent matching."""

from pathlib import Path

from unifiedcli.agents.runtime import AgentLifecycleManager
from unifiedcli.models.agent import AgentSpec
from unifiedcli.models.task import (
    TaskNode, TaskType, ExecutorRequirement, SpawnPolicy,
)
from unifiedcli.scheduler.matching import match_task_to_agent


class TestMatching:
    def test_direct_when_no_requirement(self, tmp_path: Path) -> None:
        lifecycle = AgentLifecycleManager(tmp_path / "agents")
        task = TaskNode(task_id="t1", project_id="p", name="T", task_type=TaskType.ANALYSIS)
        result = match_task_to_agent(task, lifecycle)
        assert result.action == "direct"

    def test_reuse_existing(self, tmp_path: Path) -> None:
        lifecycle = AgentLifecycleManager(tmp_path / "agents")
        spec = AgentSpec(
            agent_id="agent_1", project_id="p",
            agent_type="research_agent",
            capabilities=["research"],
        )
        lifecycle.create(spec)

        task = TaskNode(
            task_id="t1", project_id="p", name="Research",
            task_type=TaskType.RESEARCH,
            executor_requirement=ExecutorRequirement(
                agent_type="research_agent",
                capability_tags=["research"],
            ),
            spawn_policy=SpawnPolicy(),
        )
        result = match_task_to_agent(task, lifecycle)
        assert result.action == "reuse"
        assert result.agent is not None

    def test_spawn_when_no_match(self, tmp_path: Path) -> None:
        lifecycle = AgentLifecycleManager(tmp_path / "agents")
        task = TaskNode(
            task_id="t1", project_id="p", name="Deploy",
            task_type=TaskType.DEPLOY,
            executor_requirement=ExecutorRequirement(
                agent_type="hosting_agent",
                capability_tags=["hosting"],
            ),
            spawn_policy=SpawnPolicy(),
        )
        result = match_task_to_agent(task, lifecycle)
        assert result.action == "spawn"
