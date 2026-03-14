"""ProjectManager — per-project config, memory, graph, agents access."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from unifiedcli.graph.engine import TaskGraphEngine
from unifiedcli.graph.serialization import load_graph, save_graph
from unifiedcli.memory.shared import SharedMemoryManager
from unifiedcli.models.project import ProjectConfig
from unifiedcli.workspace.initializer import bootstrap_project


class ProjectManager:
    """Manages a single project's lifecycle within a workspace."""

    def __init__(self, project_path: Path) -> None:
        self.path = project_path
        self.config: ProjectConfig | None = None
        self.memory = SharedMemoryManager(project_path / "memory")
        self._graph: TaskGraphEngine | None = None

    def create(self, project_id: str, goal: str = "", name: str = "") -> ProjectConfig:
        """Create a new project with directory structure and initial config."""
        bootstrap_project(self.path)
        self.config = ProjectConfig(
            project_id=project_id,
            name=name or project_id,
            goal=goal,
        )
        self._save_config()
        self.memory.initialize()
        if goal:
            self.memory.write(
                __import__("unifiedcli.models.memory", fromlist=["MemorySlot"]).MemorySlot.GOALS,
                f"# Goals\n\nPrimary Goal:\n{goal}\n",
            )
        return self.config

    def load(self) -> ProjectConfig:
        """Load existing project config."""
        config_path = self.path / "config.yaml"
        if not config_path.exists():
            raise FileNotFoundError(f"No project config at {config_path}")
        data = yaml.safe_load(config_path.read_text())
        self.config = ProjectConfig.model_validate(data)
        return self.config

    @property
    def graph(self) -> TaskGraphEngine:
        if self._graph is None:
            graph_path = self.path / "task_graph.json"
            if graph_path.exists():
                self._graph = load_graph(graph_path)
            else:
                self._graph = TaskGraphEngine()
        return self._graph

    def save_graph(self) -> None:
        if self._graph is not None:
            save_graph(self._graph, self.path / "task_graph.json")

    def _save_config(self) -> None:
        if self.config is None:
            return
        config_path = self.path / "config.yaml"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        data = self.config.model_dump(mode="json")
        config_path.write_text(yaml.dump(data, default_flow_style=False))
