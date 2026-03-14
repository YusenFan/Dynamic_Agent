"""Graph validation — cycle detection and topological sort."""

from __future__ import annotations

from collections import deque

from unifiedcli.models.task import TaskNode


def validate_no_cycles(nodes: dict[str, TaskNode]) -> None:
    """Raise ValueError if the graph contains a cycle (Kahn's algorithm)."""
    topological_sort(nodes)  # raises on cycle


def topological_sort(nodes: dict[str, TaskNode]) -> list[str]:
    """Return a topological ordering. Raises ValueError if cycle detected."""
    in_degree: dict[str, int] = {tid: 0 for tid in nodes}
    for node in nodes.values():
        for dep_id in node.dependencies:
            if dep_id in in_degree:
                in_degree[node.task_id] = in_degree.get(node.task_id, 0)
                # dep_id -> node.task_id edge
                pass

    # Build adjacency list: adj[a] = [b] means a -> b (b depends on a)
    adj: dict[str, list[str]] = {tid: [] for tid in nodes}
    in_degree = {tid: 0 for tid in nodes}
    for node in nodes.values():
        for dep_id in node.dependencies:
            if dep_id in nodes:
                adj[dep_id].append(node.task_id)
                in_degree[node.task_id] += 1

    queue: deque[str] = deque()
    for tid, deg in in_degree.items():
        if deg == 0:
            queue.append(tid)

    order: list[str] = []
    while queue:
        tid = queue.popleft()
        order.append(tid)
        for successor in adj[tid]:
            in_degree[successor] -= 1
            if in_degree[successor] == 0:
                queue.append(successor)

    if len(order) != len(nodes):
        raise ValueError("Task graph contains a cycle")

    return order
