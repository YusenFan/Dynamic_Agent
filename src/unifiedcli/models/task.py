"""Task graph data models."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    BLOCKED = "blocked"
    WAITING_USER = "waiting_user"
    FAILED = "failed"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class TaskType(str, Enum):
    ANALYSIS = "analysis"
    RESEARCH = "research"
    DECISION = "decision"
    BUILD = "build"
    CONFIGURE = "configure"
    DEPLOY = "deploy"
    VERIFY = "verify"
    RECOVER = "recover"


class DependencyType(str, Enum):
    HARD = "hard"
    SOFT = "soft"
    DECISION = "decision"


class TaskLayer(str, Enum):
    DISCOVERY = "discovery"
    DESIGN = "design"
    BUILD = "build"
    INFRA = "infra"
    VALIDATION = "validation"


class TaskNode(BaseModel):
    task_id: str
    project_id: str
    name: str
    task_type: TaskType
    status: TaskStatus = TaskStatus.PENDING
    priority: str = "medium"
    description: str = ""
    layer: TaskLayer | None = None
    dependencies: list[str] = Field(default_factory=list)
    dependency_type: DependencyType = DependencyType.HARD
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    executor_requirement: ExecutorRequirement | None = None
    spawn_policy: SpawnPolicy | None = None
    decision_gate: bool = False
    reversible: bool = True
    retry_policy: RetryPolicy | None = None
    artifact_contract: ArtifactContract | None = None
    created_by: str = "main_agent_council"
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: datetime | None = None
    error: str | None = None
    assigned_agent_id: str | None = None


class ExecutorRequirement(BaseModel):
    agent_type: str
    capability_tags: list[str] = Field(default_factory=list)


class SpawnPolicy(BaseModel):
    spawn_if_missing: bool = True
    reuse_existing_if_match: bool = True


class RetryPolicy(BaseModel):
    max_retries: int = 2
    retries_used: int = 0


class ArtifactContract(BaseModel):
    expected_outputs: list[str] = Field(default_factory=list)


# Rebuild to resolve forward refs
TaskNode.model_rebuild()
