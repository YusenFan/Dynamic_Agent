"""Memory data models."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class MemorySlot(str, Enum):
    GOALS = "goals"
    CONSTRAINTS = "constraints"
    DECISIONS = "decisions"
    RESOURCES = "resources"
    PROGRESS = "progress"
    RISKS = "risks"


class MemoryRef(BaseModel):
    """Reference to a memory location (e.g. memory://goals.md)."""
    slot: MemorySlot | None = None
    agent_id: str | None = None
    file_name: str = ""

    @classmethod
    def parse_ref(cls, ref: str) -> MemoryRef:
        """Parse a memory:// URI into a MemoryRef."""
        if not ref.startswith("memory://"):
            raise ValueError(f"Invalid memory ref: {ref}")
        path = ref[len("memory://"):]
        file_name = path.rstrip(".md")
        try:
            slot = MemorySlot(file_name)
            return cls(slot=slot, file_name=f"{file_name}.md")
        except ValueError:
            return cls(file_name=path)
