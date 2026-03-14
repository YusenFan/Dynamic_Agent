"""Workspace configuration model."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class WorkspaceConfig(BaseModel):
    workspace_id: str
    workspace_path: str
    created_at: datetime = Field(default_factory=datetime.now)
    adapter_registry_path: str = ""
    vault_path: str = ""
