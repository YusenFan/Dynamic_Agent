"""Tests for TaskGraphEngine."""

import pytest

from unifiedcli.graph.engine import TaskGraphEngine
from unifiedcli.models.task import TaskNode, TaskStatus, TaskType


class TestTaskGraphEngine:
    def test_add_and_get_node(self, sample_graph: TaskGraphEngine) -> None:
        assert len(sample_graph.nodes) == 5
        node = sample_graph.get_node("intake")
        assert node.name == "User Goal Intake"

    def test_get_ready_tasks_initial(self, sample_graph: TaskGraphEngine) -> None:
        ready = sample_graph.get_ready_tasks()
        assert len(ready) == 1
        assert ready[0].task_id == "intake"

    def test_get_ready_after_completion(self, sample_graph: TaskGraphEngine) -> None:
        sample_graph.transition("intake", TaskStatus.READY)
        sample_graph.transition("intake", TaskStatus.RUNNING)
        sample_graph.transition("intake", TaskStatus.COMPLETED)
        ready = sample_graph.get_ready_tasks()
        assert len(ready) == 1
        assert ready[0].task_id == "research"

    def test_cycle_detection(self) -> None:
        engine = TaskGraphEngine()
        engine.add_node(TaskNode(task_id="a", project_id="t", name="A", task_type=TaskType.BUILD))
        engine.add_node(TaskNode(task_id="b", project_id="t", name="B", task_type=TaskType.BUILD, dependencies=["a"]))
        with pytest.raises(ValueError, match="cycle"):
            engine.add_node(TaskNode(task_id="c", project_id="t", name="C", task_type=TaskType.BUILD, dependencies=["b"]))
            engine.add_edge("c", "a")

    def test_remove_node(self, sample_graph: TaskGraphEngine) -> None:
        sample_graph.remove_node("verify")
        assert "verify" not in sample_graph.nodes

    def test_invalid_transition(self, sample_graph: TaskGraphEngine) -> None:
        with pytest.raises(ValueError, match="Invalid transition"):
            sample_graph.transition("intake", TaskStatus.COMPLETED)

    def test_retry_node(self, sample_graph: TaskGraphEngine) -> None:
        sample_graph.transition("intake", TaskStatus.READY)
        sample_graph.transition("intake", TaskStatus.RUNNING)
        sample_graph.transition("intake", TaskStatus.FAILED)
        sample_graph.retry_node("intake")
        assert sample_graph.get_node("intake").status == TaskStatus.PENDING

    def test_expand_graph(self, sample_graph: TaskGraphEngine) -> None:
        new_node = TaskNode(
            task_id="recovery_1",
            project_id="test",
            name="Recovery Task",
            task_type=TaskType.RECOVER,
            dependencies=["build"],
        )
        sample_graph.expand([new_node])
        assert "recovery_1" in sample_graph.nodes
