"""Serialize / deserialize task graph to JSON."""

from __future__ import annotations

import json
from pathlib import Path

from unifiedcli.models.task import TaskNode
from unifiedcli.graph.engine import TaskGraphEngine


def save_graph(engine: TaskGraphEngine, path: Path) -> None:
    """Save the task graph to a JSON file."""
    data = {
        "nodes": [node.model_dump(mode="json") for node in engine.nodes.values()]
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str))


def load_graph(path: Path) -> TaskGraphEngine:
    """Load a task graph from a JSON file."""
    data = json.loads(path.read_text())
    engine = TaskGraphEngine()
    for node_data in data["nodes"]:
        node = TaskNode.model_validate(node_data)
        engine._nodes[node.task_id] = node
    return engine
