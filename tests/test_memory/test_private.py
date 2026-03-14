"""Tests for PrivateMemoryManager."""

from pathlib import Path

from unifiedcli.memory.private import PrivateMemoryManager


class TestPrivateMemory:
    def test_initialize(self, tmp_path: Path) -> None:
        mem = PrivateMemoryManager(tmp_path / "agent_mem")
        mem.initialize()
        files = mem.list_files()
        assert "knowledge.md" in files
        assert "failures.md" in files

    def test_read_write(self, tmp_path: Path) -> None:
        mem = PrivateMemoryManager(tmp_path / "agent_mem")
        mem.initialize()
        mem.write("knowledge.md", "# Knowledge\n\nVercel CLI basics.\n")
        content = mem.read("knowledge.md")
        assert "Vercel CLI basics" in content

    def test_append(self, tmp_path: Path) -> None:
        mem = PrivateMemoryManager(tmp_path / "agent_mem")
        mem.initialize()
        mem.append("sessions.md", "Session 1: deployed successfully.")
        content = mem.read("sessions.md")
        assert "Session 1" in content
