"""Council deliberation data models."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class CouncilRole(str, Enum):
    PLANNER = "planner"
    CRITIC = "critic"
    BALANCER = "balancer"


class DeliberationStep(str, Enum):
    PLAN = "plan"
    CRITIQUE = "critique"
    RESPOND = "respond"
    BALANCE = "balance"
    UPDATE_MEMORY = "update_memory"


class DeliberationRound(BaseModel):
    round_id: str
    topic: str
    steps: list[StepResult] = Field(default_factory=list)
    consensus: ConsensusResult | None = None


class StepResult(BaseModel):
    step: DeliberationStep
    role: CouncilRole
    content: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConsensusResult(BaseModel):
    chosen_plan: str = ""
    rejected_plans: list[str] = Field(default_factory=list)
    reasoning_summary: str = ""
    risks: list[str] = Field(default_factory=list)
    agents_to_spawn: list[dict[str, Any]] = Field(default_factory=list)
    decision_gate_required: bool = False
    confidence: float = 0.0


# Rebuild for forward refs
DeliberationRound.model_rebuild()
