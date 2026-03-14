"""Adapter plugin data models."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ChannelType(str, Enum):
    CLI = "cli"
    API = "api"
    MCP = "mcp"
    SKILL = "skill"


class PluginStatus(str, Enum):
    REGISTERED = "registered"
    VALIDATED = "validated"
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    DEPRECATED = "deprecated"


class AuthRequirement(BaseModel):
    required: bool = False
    variables: list[str] = Field(default_factory=list)


class PluginManifest(BaseModel):
    plugin_id: str
    platform: str
    channel_type: ChannelType
    capability_tags: list[str] = Field(default_factory=list)
    auth: AuthRequirement = Field(default_factory=AuthRequirement)
    actions: list[str] = Field(default_factory=list)
    requires_user_secret_input: bool = False
    ai_secret_visibility: bool = False


class AdapterResult(BaseModel):
    status: str = "success"
    artifacts: list[dict[str, Any]] = Field(default_factory=list)
    logs_ref: str = ""


class AdapterError(BaseModel):
    status: str = "error"
    error_category: str = ""
    recoverable: bool = True
    message: str = ""
    suggested_action: str = ""
