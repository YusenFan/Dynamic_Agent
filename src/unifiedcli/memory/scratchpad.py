"""Ephemeral session scratchpad — key-value store for temporary reasoning."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json


class Scratchpad:
    """Ephemeral key-value scratchpad for in-session reasoning.

    Optionally backed by a file for crash recovery, but not intended
    for long-term persistence.
    """

    def __init__(self, scratchpad_dir: Path | None = None) -> None:
        self._store: dict[str, str] = {}
        self._dir = scratchpad_dir

    def set(self, key: str, value: str) -> None:
        self._store[key] = value
        self._persist()

    def get(self, key: str, default: str = "") -> str:
        return self._store.get(key, default)

    def delete(self, key: str) -> None:
        self._store.pop(key, None)
        self._persist()

    def keys(self) -> list[str]:
        return list(self._store.keys())

    def clear(self) -> None:
        self._store.clear()
        self._persist()

    def _persist(self) -> None:
        if self._dir is None:
            return
        self._dir.mkdir(parents=True, exist_ok=True)
        path = self._dir / "scratchpad.json"
        path.write_text(json.dumps(self._store, indent=2))

    def load(self) -> None:
        """Load from disk if available."""
        if self._dir is None:
            return
        path = self._dir / "scratchpad.json"
        if path.exists():
            self._store = json.loads(path.read_text())
