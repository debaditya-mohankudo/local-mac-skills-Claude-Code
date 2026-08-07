"""Tests for src/config.py — Settings computed fields and path resolution."""
import pytest
from config import Settings


class TestSettings:
    def test_singleton_is_settings(self):
        from config import config
        assert isinstance(config, Settings)

    def test_vault_path_is_absolute(self):
        from config import config
        assert config.vault_path.is_absolute()

    def test_memory_db_path_ends_with_sqlite(self):
        from config import config
        assert str(config.memory_db).endswith(".sqlite") or str(config.memory_db).endswith(".db")

    def test_valid_memory_types_contains_expected(self):
        from config import config
        for t in ("user", "feedback", "project", "reference"):
            assert t in config.memory_valid_types

    def test_swift_binary_is_path(self):
        from config import config
        assert config.swift_binary is not None
