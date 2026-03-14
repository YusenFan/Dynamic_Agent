"""VaultManager — secure secret boundary.

AI agents never see secret values. They only work with vault:// references.
The VaultManager resolves these references at execution time in a controlled runtime.
"""

from __future__ import annotations

import json
from pathlib import Path


class VaultManager:
    """Manage secrets stored in the workspace vault directory.

    Secrets are stored as JSON files: vault/{platform}/{key}.json
    AI only sees references like vault://vercel/token.
    """

    def __init__(self, vault_dir: Path) -> None:
        self.vault_dir = vault_dir

    def initialize(self) -> None:
        self.vault_dir.mkdir(parents=True, exist_ok=True)

    def store(self, platform: str, key: str, value: str) -> str:
        """Store a secret and return a vault:// reference."""
        platform_dir = self.vault_dir / platform
        platform_dir.mkdir(parents=True, exist_ok=True)
        secret_file = platform_dir / f"{key}.json"
        secret_file.write_text(json.dumps({"value": value}))
        return f"vault://{platform}/{key}"

    def resolve(self, ref: str) -> str:
        """Resolve a vault:// reference to the actual secret value.

        This should ONLY be called by the controlled adapter runtime,
        never by AI agent code.
        """
        if not ref.startswith("vault://"):
            raise ValueError(f"Invalid vault reference: {ref}")
        path = ref[len("vault://"):]
        parts = path.split("/", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid vault reference format: {ref}")
        platform, key = parts
        secret_file = self.vault_dir / platform / f"{key}.json"
        if not secret_file.exists():
            raise FileNotFoundError(f"Secret not found: {ref}")
        data = json.loads(secret_file.read_text())
        return data["value"]

    def has_secret(self, ref: str) -> bool:
        """Check if a vault reference exists without revealing the value."""
        try:
            self.resolve(ref)
            return True
        except (ValueError, FileNotFoundError):
            return False

    def list_refs(self, platform: str | None = None) -> list[str]:
        """List available vault references (not values)."""
        refs: list[str] = []
        if not self.vault_dir.exists():
            return refs
        dirs = [self.vault_dir / platform] if platform else self.vault_dir.iterdir()
        for d in dirs:
            if not d.is_dir():
                continue
            for f in d.glob("*.json"):
                refs.append(f"vault://{d.name}/{f.stem}")
        return refs

    def delete(self, ref: str) -> None:
        """Delete a secret by its vault reference."""
        if not ref.startswith("vault://"):
            raise ValueError(f"Invalid vault reference: {ref}")
        path = ref[len("vault://"):]
        parts = path.split("/", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid vault reference format: {ref}")
        platform, key = parts
        secret_file = self.vault_dir / platform / f"{key}.json"
        if secret_file.exists():
            secret_file.unlink()
