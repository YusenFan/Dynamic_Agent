"""Shared memory manager — 6 markdown slot files per project."""

from __future__ import annotations

from pathlib import Path

from unifiedcli.models.memory import MemorySlot

_SLOT_HEADERS: dict[MemorySlot, str] = {
    MemorySlot.GOALS: "# Goals\n\n",
    MemorySlot.CONSTRAINTS: "# Constraints\n\n",
    MemorySlot.DECISIONS: "# Decisions\n\n",
    MemorySlot.RESOURCES: "# Resources\n\n",
    MemorySlot.PROGRESS: "# Progress\n\n",
    MemorySlot.RISKS: "# Risks\n\n",
}


class SharedMemoryManager:
    """Read/write the 6 shared memory markdown slots for a project."""

    def __init__(self, memory_dir: Path) -> None:
        self.memory_dir = memory_dir

    def initialize(self) -> None:
        """Create all 6 slot files with default headers."""
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        for slot, header in _SLOT_HEADERS.items():
            path = self._slot_path(slot)
            if not path.exists():
                path.write_text(header)

    def read(self, slot: MemorySlot) -> str:
        """Read the content of a memory slot."""
        path = self._slot_path(slot)
        if not path.exists():
            return ""
        return path.read_text()

    def write(self, slot: MemorySlot, content: str) -> None:
        """Overwrite a memory slot with new content."""
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self._slot_path(slot).write_text(content)

    def append(self, slot: MemorySlot, entry: str) -> None:
        """Append an entry to a memory slot."""
        current = self.read(slot)
        if not current:
            current = _SLOT_HEADERS.get(slot, "")
        updated = current.rstrip("\n") + "\n\n" + entry.strip() + "\n"
        self.write(slot, updated)

    def read_all(self) -> dict[MemorySlot, str]:
        """Read all 6 slots."""
        return {slot: self.read(slot) for slot in MemorySlot}

    def _slot_path(self, slot: MemorySlot) -> Path:
        return self.memory_dir / f"{slot.value}.md"
