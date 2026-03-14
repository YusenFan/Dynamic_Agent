"""Tests for SharedMemoryManager."""

from pathlib import Path

from unifiedcli.memory.shared import SharedMemoryManager
from unifiedcli.models.memory import MemorySlot


class TestSharedMemory:
    def test_initialize_creates_files(self, tmp_path: Path) -> None:
        mem = SharedMemoryManager(tmp_path / "memory")
        mem.initialize()
        for slot in MemorySlot:
            assert (tmp_path / "memory" / f"{slot.value}.md").exists()

    def test_read_write(self, tmp_path: Path) -> None:
        mem = SharedMemoryManager(tmp_path / "memory")
        mem.initialize()
        mem.write(MemorySlot.GOALS, "# Goals\n\nDeploy a demo.\n")
        content = mem.read(MemorySlot.GOALS)
        assert "Deploy a demo" in content

    def test_append(self, tmp_path: Path) -> None:
        mem = SharedMemoryManager(tmp_path / "memory")
        mem.initialize()
        mem.append(MemorySlot.DECISIONS, "Chose Vercel for hosting.")
        mem.append(MemorySlot.DECISIONS, "Chose Supabase for database.")
        content = mem.read(MemorySlot.DECISIONS)
        assert "Vercel" in content
        assert "Supabase" in content

    def test_read_all(self, tmp_path: Path) -> None:
        mem = SharedMemoryManager(tmp_path / "memory")
        mem.initialize()
        all_mem = mem.read_all()
        assert len(all_mem) == 6
        assert MemorySlot.GOALS in all_mem
