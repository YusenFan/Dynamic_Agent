"""Private memory manager — per-agent memory files."""

from __future__ import annotations

from pathlib import Path

_PRIVATE_FILES = ["knowledge.md", "execution_patterns.md", "failures.md", "sessions.md"]


class PrivateMemoryManager:
    """Manage per-agent private memory (knowledge, patterns, failures, sessions)."""

    def __init__(self, agent_memory_dir: Path) -> None:
        self.memory_dir = agent_memory_dir

    def initialize(self) -> None:
        """Create default private memory files."""
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        for fname in _PRIVATE_FILES:
            path = self.memory_dir / fname
            if not path.exists():
                header = f"# {fname.replace('.md', '').replace('_', ' ').title()}\n\n"
                path.write_text(header)

    def read(self, file_name: str) -> str:
        path = self.memory_dir / file_name
        if not path.exists():
            return ""
        return path.read_text()

    def write(self, file_name: str, content: str) -> None:
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        (self.memory_dir / file_name).write_text(content)

    def append(self, file_name: str, entry: str) -> None:
        current = self.read(file_name)
        updated = current.rstrip("\n") + "\n\n" + entry.strip() + "\n"
        self.write(file_name, updated)

    def list_files(self) -> list[str]:
        if not self.memory_dir.exists():
            return []
        return [f.name for f in self.memory_dir.iterdir() if f.suffix == ".md"]
