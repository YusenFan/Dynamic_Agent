"""Shared test fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from unifiedcli.models.task import (
    TaskNode, TaskType, TaskStatus, DependencyType,
    ExecutorRequirement, SpawnPolicy, RetryPolicy, ArtifactContract,
)
from unifiedcli.models.agent import AgentSpec, AgentCategory
from unifiedcli.graph.engine import TaskGraphEngine


@pytest.fixture
def tmp_workspace(tmp_path: Path) -> Path:
    return tmp_path / "workspace"


@pytest.fixture
def tmp_project(tmp_workspace: Path) -> Path:
    return tmp_workspace / "projects" / "test_project"


@pytest.fixture
def sample_nodes() -> list[TaskNode]:
    """A small DAG: intake → research → build → deploy → verify."""
    return [
        TaskNode(
            task_id="intake",
            project_id="test",
            name="User Goal Intake",
            task_type=TaskType.ANALYSIS,
            priority="high",
        ),
        TaskNode(
            task_id="research",
            project_id="test",
            name="Product Research",
            task_type=TaskType.RESEARCH,
            dependencies=["intake"],
            executor_requirement=ExecutorRequirement(
                agent_type="research_agent",
                capability_tags=["research"],
            ),
            spawn_policy=SpawnPolicy(),
        ),
        TaskNode(
            task_id="build",
            project_id="test",
            name="Build Scaffold",
            task_type=TaskType.BUILD,
            dependencies=["research"],
            priority="high",
            executor_requirement=ExecutorRequirement(
                agent_type="build_agent",
                capability_tags=["build", "code_generation"],
            ),
            spawn_policy=SpawnPolicy(),
        ),
        TaskNode(
            task_id="deploy",
            project_id="test",
            name="Deploy Demo",
            task_type=TaskType.DEPLOY,
            dependencies=["build"],
            decision_gate=True,
            reversible=False,
            executor_requirement=ExecutorRequirement(
                agent_type="hosting_agent",
                capability_tags=["hosting", "deployment"],
            ),
            spawn_policy=SpawnPolicy(),
            artifact_contract=ArtifactContract(expected_outputs=["deployment_url"]),
        ),
        TaskNode(
            task_id="verify",
            project_id="test",
            name="Verify Deployment",
            task_type=TaskType.VERIFY,
            dependencies=["deploy"],
        ),
    ]


@pytest.fixture
def sample_graph(sample_nodes: list[TaskNode]) -> TaskGraphEngine:
    engine = TaskGraphEngine()
    for node in sample_nodes:
        engine.add_node(node)
    return engine
