"""Project configuration model."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ProjectStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"


class ProjectConfig(BaseModel):
    project_id: str
    name: str = ""
    goal: str = ""
    status: ProjectStatus = ProjectStatus.ACTIVE
    created_at: datetime = Field(default_factory=datetime.now)
    supported_platforms: list[str] = Field(default_factory=list)
    default_models: dict[str, str] = Field(default_factory=lambda: {
        "planner": "claude_opus",
        "critic": "gemini_5_1_pro",
        "balancer": "chatgpt_5_4",
    })
