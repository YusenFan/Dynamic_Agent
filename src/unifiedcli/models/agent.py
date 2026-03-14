"""Agent data models."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    CREATED = "created"
    READY = "ready"
    RUNNING = "running"
    BLOCKED = "blocked"
    IDLE = "idle"
    RECOVERING = "recovering"
    TERMINATED = "terminated"
    ARCHIVED = "archived"


class AgentCategory(str, Enum):
    PERSISTENT_DOMAIN = "persistent_domain"
    EPISODIC_EXECUTION = "episodic_execution"
    RECOVERY = "recovery"


class AgentSpec(BaseModel):
    agent_id: str
    project_id: str
    agent_type: str
    role_description: str = ""
    category: AgentCategory = AgentCategory.EPISODIC_EXECUTION
    status: AgentStatus = AgentStatus.CREATED
    capabilities: list[str] = Field(default_factory=list)
    knowledge_scope: list[str] = Field(default_factory=list)
    private_memory_path: str = ""
    auth_variable_refs: list[str] = Field(default_factory=list)
    active_tasks: list[str] = Field(default_factory=list)
    installed_skills: list[str] = Field(default_factory=list)
    spawn_reason: str = ""
    created_by: str = "main_agent"
    created_at: datetime = Field(default_factory=datetime.now)
    terminated_at: datetime | None = None


class SpawnPolicy(BaseModel):
    spawn_if_missing: bool = True
    reuse_existing_if_match: bool = True


class ExecutorRequirement(BaseModel):
    agent_type: str
    capability_tags: list[str] = Field(default_factory=list)


class DispatchContract(BaseModel):
    dispatch_id: str
    task_id: str
    project_id: str
    agent_id: str
    task_summary: str = ""
    input_refs: list[str] = Field(default_factory=list)
    expected_outputs: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)


class ReturnContract(BaseModel):
    task_id: str
    agent_id: str
    status: str
    facts_discovered: list[str] = Field(default_factory=list)
    artifacts_produced: list[str] = Field(default_factory=list)
    risks_detected: list[str] = Field(default_factory=list)
    followup_task_suggestions: list[str] = Field(default_factory=list)
    requires_decision_gate: bool = False
    confidence: float = 0.0


class FailureResult(BaseModel):
    task_id: str
    agent_id: str
    status: str = "failed"
    error_category: str = ""
    recoverable: bool = True
    suggested_recovery_task: str = ""
