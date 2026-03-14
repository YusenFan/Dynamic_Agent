"""Tests for VaultManager."""

from pathlib import Path

import pytest

from unifiedcli.adapters.vault import VaultManager


class TestVaultManager:
    def test_store_and_resolve(self, tmp_path: Path) -> None:
        vault = VaultManager(tmp_path / "vault")
        vault.initialize()
        ref = vault.store("vercel", "token", "sk-secret-123")
        assert ref == "vault://vercel/token"
        assert vault.resolve(ref) == "sk-secret-123"

    def test_has_secret(self, tmp_path: Path) -> None:
        vault = VaultManager(tmp_path / "vault")
        vault.initialize()
        vault.store("vercel", "token", "value")
        assert vault.has_secret("vault://vercel/token")
        assert not vault.has_secret("vault://vercel/missing")

    def test_list_refs(self, tmp_path: Path) -> None:
        vault = VaultManager(tmp_path / "vault")
        vault.initialize()
        vault.store("vercel", "token", "v1")
        vault.store("supabase", "key", "v2")
        refs = vault.list_refs()
        assert "vault://vercel/token" in refs
        assert "vault://supabase/key" in refs

    def test_delete(self, tmp_path: Path) -> None:
        vault = VaultManager(tmp_path / "vault")
        vault.initialize()
        vault.store("vercel", "token", "value")
        vault.delete("vault://vercel/token")
        assert not vault.has_secret("vault://vercel/token")

    def test_resolve_missing_raises(self, tmp_path: Path) -> None:
        vault = VaultManager(tmp_path / "vault")
        vault.initialize()
        with pytest.raises(FileNotFoundError):
            vault.resolve("vault://missing/key")
