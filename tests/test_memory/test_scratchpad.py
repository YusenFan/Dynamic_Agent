"""Tests for Scratchpad."""

from pathlib import Path

from unifiedcli.memory.scratchpad import Scratchpad


class TestScratchpad:
    def test_in_memory(self) -> None:
        sp = Scratchpad()
        sp.set("key1", "value1")
        assert sp.get("key1") == "value1"
        assert sp.get("missing", "default") == "default"

    def test_persistence(self, tmp_path: Path) -> None:
        sp = Scratchpad(tmp_path / "scratch")
        sp.set("key1", "value1")
        sp.set("key2", "value2")

        sp2 = Scratchpad(tmp_path / "scratch")
        sp2.load()
        assert sp2.get("key1") == "value1"
        assert sp2.get("key2") == "value2"

    def test_clear(self) -> None:
        sp = Scratchpad()
        sp.set("a", "1")
        sp.clear()
        assert sp.keys() == []
