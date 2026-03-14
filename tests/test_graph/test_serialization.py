"""Tests for graph serialization."""

from pathlib import Path

from unifiedcli.graph.engine import TaskGraphEngine
from unifiedcli.graph.serialization import save_graph, load_graph
from unifiedcli.models.task import TaskStatus


class TestSerialization:
    def test_round_trip(self, sample_graph: TaskGraphEngine, tmp_path: Path) -> None:
        path = tmp_path / "task_graph.json"
        save_graph(sample_graph, path)
        assert path.exists()

        loaded = load_graph(path)
        assert len(loaded.nodes) == len(sample_graph.nodes)
        for tid in sample_graph.nodes:
            assert tid in loaded.nodes
            assert loaded.nodes[tid].name == sample_graph.nodes[tid].name

    def test_preserves_status(self, sample_graph: TaskGraphEngine, tmp_path: Path) -> None:
        sample_graph.transition("intake", TaskStatus.READY)
        sample_graph.transition("intake", TaskStatus.RUNNING)
        sample_graph.transition("intake", TaskStatus.COMPLETED)

        path = tmp_path / "task_graph.json"
        save_graph(sample_graph, path)
        loaded = load_graph(path)
        assert loaded.nodes["intake"].status == TaskStatus.COMPLETED
