"""Task ranking — critical-path-aware prioritization."""

from __future__ import annotations

from unifiedcli.models.task import TaskNode, TaskType

_PRIORITY_WEIGHTS = {
    "critical": 4,
    "high": 3,
    "medium": 2,
    "low": 1,
}

_TYPE_BONUS = {
    TaskType.RECOVER: 3,
    TaskType.VERIFY: 2,
    TaskType.DECISION: 2,
    TaskType.DEPLOY: 1,
}


def rank_tasks(tasks: list[TaskNode], all_nodes: dict[str, TaskNode] | None = None) -> list[TaskNode]:
    """Rank ready tasks by priority, type bonus, and downstream impact.

    Ordering:
    1. High priority first
    2. Recovery tasks boosted
    3. Decision gate prereqs boosted
    4. Verify tasks boosted (to close the loop)
    5. Tasks with more downstream dependents rank higher
    """
    downstream_counts: dict[str, int] = {}
    if all_nodes:
        for node in all_nodes.values():
            for dep_id in node.dependencies:
                downstream_counts[dep_id] = downstream_counts.get(dep_id, 0) + 1

    def score(task: TaskNode) -> float:
        s = _PRIORITY_WEIGHTS.get(task.priority, 2)
        s += _TYPE_BONUS.get(task.task_type, 0)
        # Boost tasks that block many others
        s += downstream_counts.get(task.task_id, 0) * 0.5
        # Boost decision gate prereqs
        if task.decision_gate:
            s += 1
        return s

    return sorted(tasks, key=score, reverse=True)
