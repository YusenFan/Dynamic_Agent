"""Tests for WorkspaceManager and ProjectManager."""

from pathlib import Path

from unifiedcli.workspace.workspace import WorkspaceManager
from unifiedcli.workspace.project import ProjectManager
from unifiedcli.models.memory import MemorySlot


class TestWorkspace:
    def test_initialize(self, tmp_workspace: Path) -> None:
        wm = WorkspaceManager(tmp_workspace)
        config = wm.initialize()
        assert (tmp_workspace / "projects").is_dir()
        assert (tmp_workspace / "vault").is_dir()
        assert (tmp_workspace / "configs" / "workspace.json").exists()
        assert config.workspace_id == "default"

    def test_load(self, tmp_workspace: Path) -> None:
        wm = WorkspaceManager(tmp_workspace)
        wm.initialize("test_ws")
        wm2 = WorkspaceManager(tmp_workspace)
        config = wm2.load()
        assert config.workspace_id == "test_ws"

    def test_list_projects(self, tmp_workspace: Path) -> None:
        wm = WorkspaceManager(tmp_workspace)
        wm.initialize()
        assert wm.list_projects() == []

        # Create a project
        pm = ProjectManager(wm.project_path("proj1"))
        pm.create("proj1", goal="Test goal")
        assert "proj1" in wm.list_projects()


class TestProject:
    def test_create(self, tmp_workspace: Path) -> None:
        proj_path = tmp_workspace / "projects" / "test"
        pm = ProjectManager(proj_path)
        config = pm.create("test", goal="Deploy a demo")
        assert config.project_id == "test"
        assert (proj_path / "config.yaml").exists()
        assert (proj_path / "memory" / "goals.md").exists()

    def test_load(self, tmp_workspace: Path) -> None:
        proj_path = tmp_workspace / "projects" / "test"
        pm = ProjectManager(proj_path)
        pm.create("test", goal="A goal")
        pm2 = ProjectManager(proj_path)
        config = pm2.load()
        assert config.project_id == "test"

    def test_graph_lifecycle(self, tmp_workspace: Path) -> None:
        from unifiedcli.models.task import TaskNode, TaskType

        proj_path = tmp_workspace / "projects" / "test"
        pm = ProjectManager(proj_path)
        pm.create("test")

        pm.graph.add_node(TaskNode(
            task_id="t1", project_id="test", name="Task 1", task_type=TaskType.BUILD
        ))
        pm.save_graph()

        pm2 = ProjectManager(proj_path)
        pm2.load()
        assert "t1" in pm2.graph.nodes
