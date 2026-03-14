"""Tests for task priority ranking."""

from unifiedcli.models.task import TaskNode, TaskType
from unifiedcli.scheduler.priority import rank_tasks


class TestPriority:
    def test_high_priority_first(self) -> None:
        tasks = [
            TaskNode(task_id="low", project_id="p", name="Low", task_type=TaskType.BUILD, priority="low"),
            TaskNode(task_id="high", project_id="p", name="High", task_type=TaskType.BUILD, priority="high"),
        ]
        ranked = rank_tasks(tasks)
        assert ranked[0].task_id == "high"

    def test_recovery_boosted(self) -> None:
        tasks = [
            TaskNode(task_id="build", project_id="p", name="Build", task_type=TaskType.BUILD, priority="medium"),
            TaskNode(task_id="recover", project_id="p", name="Recover", task_type=TaskType.RECOVER, priority="medium"),
        ]
        ranked = rank_tasks(tasks)
        assert ranked[0].task_id == "recover"

    def test_decision_gate_boosted(self) -> None:
        tasks = [
            TaskNode(task_id="normal", project_id="p", name="Normal", task_type=TaskType.BUILD, priority="medium"),
            TaskNode(task_id="gate", project_id="p", name="Gate", task_type=TaskType.BUILD, priority="medium", decision_gate=True),
        ]
        ranked = rank_tasks(tasks)
        assert ranked[0].task_id == "gate"
