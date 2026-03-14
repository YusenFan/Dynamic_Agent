"""Bootstrap workspace and project directory structures."""

from __future__ import annotations

from pathlib import Path


def bootstrap_workspace(workspace_path: Path) -> None:
    """Create the workspace directory layout."""
    dirs = ["projects", "memory", "adapters", "vault", "configs"]
    for d in dirs:
        (workspace_path / d).mkdir(parents=True, exist_ok=True)


def bootstrap_project(project_path: Path) -> None:
    """Create the project directory layout within a workspace."""
    dirs = [
        "memory",
        "agents",
        "artifacts",
        "logs",
    ]
    for d in dirs:
        (project_path / d).mkdir(parents=True, exist_ok=True)
