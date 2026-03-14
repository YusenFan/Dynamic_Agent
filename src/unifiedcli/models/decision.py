"""Decision gate data models."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class DecisionTrigger(str, Enum):
    IRREVERSIBLE_ACTION = "irreversible_action"
    COST_BEARING = "cost_bearing"
    EXTERNAL_AUTHORIZATION = "external_authorization"
    ARCHITECTURE_LOCK_IN = "architecture_lock_in"
    PUBLIC_EXPOSURE = "public_exposure"
    MULTIPLE_TRADEOFFS = "multiple_tradeoffs"
    LOW_CONFIDENCE = "low_confidence"


class DecisionOption(BaseModel):
    option_id: str
    label: str
    description: str = ""
    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)
    cost_impact: str = ""
    risk: str = ""


class DecisionPacket(BaseModel):
    decision_id: str
    task_id: str
    project_id: str
    decision_topic: str
    reason: str = ""
    trigger: DecisionTrigger
    options: list[DecisionOption] = Field(default_factory=list)
    recommended_option: str | None = None
    reversibility: str = ""


class UserDecision(BaseModel):
    decision_id: str
    chosen_option: str
    user_notes: str = ""
