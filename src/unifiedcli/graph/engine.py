"""Task Graph Engine — DAG-based task management."""

from __future__ import annotations

from datetime import datetime

from unifiedcli.models.task import DependencyType, TaskNode, TaskStatus
from unifiedcli.graph.validators import validate_no_cycles


class TaskGraphEngine:
    """DAG-based task graph with state transitions and runtime expansion."""

    def __init__(self) -> None:
        self._nodes: dict[str, TaskNode] = {}

    @property
    def nodes(self) -> dict[str, TaskNode]:
        return dict(self._nodes)

    def add_node(self, node: TaskNode) -> None:
        """Add a task node. Raises if it would create a cycle."""
        if node.task_id in self._nodes:
            raise ValueError(f"Node {node.task_id} already exists")
        self._nodes[node.task_id] = node
        try:
            validate_no_cycles(self._nodes)
        except ValueError:
            del self._nodes[node.task_id]
            raise

    def remove_node(self, task_id: str) -> TaskNode:
        """Remove a node and clean up references to it in other nodes."""
        node = self._nodes.pop(task_id, None)
        if node is None:
            raise KeyError(f"Node {task_id} not found")
        for n in self._nodes.values():
            if task_id in n.dependencies:
                n.dependencies.remove(task_id)
        return node

    def add_edge(self, from_id: str, to_id: str) -> None:
        """Add a dependency edge: to_id depends on from_id."""
        if from_id not in self._nodes:
            raise KeyError(f"Node {from_id} not found")
        if to_id not in self._nodes:
            raise KeyError(f"Node {to_id} not found")
        to_node = self._nodes[to_id]
        if from_id not in to_node.dependencies:
            to_node.dependencies.append(from_id)
        validate_no_cycles(self._nodes)

    def remove_edge(self, from_id: str, to_id: str) -> None:
        """Remove a dependency edge."""
        if to_id in self._nodes and from_id in self._nodes[to_id].dependencies:
            self._nodes[to_id].dependencies.remove(from_id)

    def get_ready_tasks(self) -> list[TaskNode]:
        """Return all tasks whose hard/decision dependencies are met."""
        ready = []
        for node in self._nodes.values():
            if node.status != TaskStatus.PENDING:
                continue
            if self._dependencies_met(node):
                ready.append(node)
        return ready

    def transition(self, task_id: str, new_status: TaskStatus) -> None:
        """Transition a task to a new status with basic validation."""
        node = self._nodes.get(task_id)
        if node is None:
            raise KeyError(f"Node {task_id} not found")
        valid = _VALID_TRANSITIONS.get(node.status, set())
        if new_status not in valid:
            raise ValueError(
                f"Invalid transition: {node.status.value} -> {new_status.value}"
            )
        node.status = new_status
        if new_status == TaskStatus.COMPLETED:
            node.completed_at = datetime.now()

    def archive_node(self, task_id: str) -> None:
        """Archive a task node."""
        self.transition(task_id, TaskStatus.ARCHIVED)

    def retry_node(self, task_id: str) -> None:
        """Reset a failed node back to pending for retry."""
        node = self._nodes.get(task_id)
        if node is None:
            raise KeyError(f"Node {task_id} not found")
        if node.status != TaskStatus.FAILED:
            raise ValueError(f"Can only retry failed tasks, got {node.status.value}")
        if node.retry_policy and node.retry_policy.retries_used >= node.retry_policy.max_retries:
            raise ValueError(f"Max retries ({node.retry_policy.max_retries}) exceeded")
        if node.retry_policy:
            node.retry_policy.retries_used += 1
        node.status = TaskStatus.PENDING
        node.error = None

    def expand(self, new_nodes: list[TaskNode]) -> None:
        """Add multiple nodes for runtime graph expansion (e.g. recovery path)."""
        for node in new_nodes:
            self.add_node(node)

    def get_node(self, task_id: str) -> TaskNode:
        node = self._nodes.get(task_id)
        if node is None:
            raise KeyError(f"Node {task_id} not found")
        return node

    def _dependencies_met(self, node: TaskNode) -> bool:
        for dep_id in node.dependencies:
            dep = self._nodes.get(dep_id)
            if dep is None:
                return False
            if node.dependency_type == DependencyType.SOFT:
                continue  # soft deps don't block
            if dep.status != TaskStatus.COMPLETED:
                return False
        return True


_VALID_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.PENDING: {TaskStatus.READY, TaskStatus.ARCHIVED},
    TaskStatus.READY: {TaskStatus.RUNNING, TaskStatus.ARCHIVED},
    TaskStatus.RUNNING: {
        TaskStatus.COMPLETED,
        TaskStatus.FAILED,
        TaskStatus.BLOCKED,
        TaskStatus.WAITING_USER,
    },
    TaskStatus.BLOCKED: {TaskStatus.READY, TaskStatus.ARCHIVED},
    TaskStatus.WAITING_USER: {TaskStatus.READY, TaskStatus.ARCHIVED},
    TaskStatus.FAILED: {TaskStatus.PENDING, TaskStatus.ARCHIVED},
    TaskStatus.COMPLETED: {TaskStatus.ARCHIVED},
    TaskStatus.ARCHIVED: set(),
}
