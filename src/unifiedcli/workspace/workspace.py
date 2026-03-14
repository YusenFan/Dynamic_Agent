"""WorkspaceManager — top-level execution environment."""

from __future__ import annotations

import json
from pathlib import Path

from unifiedcli.adapters.registry import AdapterRegistry
from unifiedcli.adapters.vault import VaultManager
from unifiedcli.models.workspace import WorkspaceConfig
from unifiedcli.workspace.initializer import bootstrap_workspace


class WorkspaceManager:
    """Manages the workspace: projects, adapter registry, vault."""

    def __init__(self, workspace_path: Path) -> None:
        self.path = workspace_path
        self.config: WorkspaceConfig | None = None
        self.adapter_registry = AdapterRegistry()
        self.vault = VaultManager(workspace_path / "vault")

    def initialize(self, workspace_id: str = "default") -> WorkspaceConfig:
        """Bootstrap workspace directories and save config."""
        bootstrap_workspace(self.path)
        self.vault.initialize()
        self.config = WorkspaceConfig(
            workspace_id=workspace_id,
            workspace_path=str(self.path),
            adapter_registry_path=str(self.path / "adapters"),
            vault_path=str(self.path / "vault"),
        )
        self._save_config()
        return self.config

    def load(self) -> WorkspaceConfig:
        """Load existing workspace config."""
        config_path = self.path / "configs" / "workspace.json"
        if not config_path.exists():
            raise FileNotFoundError(f"No workspace config at {config_path}")
        data = json.loads(config_path.read_text())
        self.config = WorkspaceConfig.model_validate(data)
        return self.config

    def list_projects(self) -> list[str]:
        """List project IDs in this workspace."""
        projects_dir = self.path / "projects"
        if not projects_dir.exists():
            return []
        return [d.name for d in projects_dir.iterdir() if d.is_dir()]

    def project_path(self, project_id: str) -> Path:
        return self.path / "projects" / project_id

    def _save_config(self) -> None:
        if self.config is None:
            return
        config_path = self.path / "configs" / "workspace.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(self.config.model_dump_json(indent=2))
