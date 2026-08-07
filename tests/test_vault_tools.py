"""Tests for src/tools/vault.py — pure string helpers and filesystem ops."""
import pytest
from pathlib import Path
from unittest.mock import patch

import tools.vault as vault


class TestVaultPath:
    def test_adds_md_extension(self):
        result = vault._vault_path("Notes/MyNote")
        assert str(result).endswith("MyNote.md")

    def test_keeps_existing_md(self):
        result = vault._vault_path("Notes/MyNote.md")
        assert str(result).endswith("MyNote.md")
        assert not str(result).endswith("MyNote.md.md")


class TestStripCodeBlocks:
    def test_removes_fenced_block(self):
        text = "before\n```python\ncode here\n```\nafter"
        result = vault._strip_code_blocks(text)
        assert "code here" not in result
        assert "before" in result
        assert "after" in result

    def test_no_code_blocks_unchanged(self):
        text = "plain text only"
        assert vault._strip_code_blocks(text) == text

    def test_multiple_blocks_removed(self):
        text = "```a```mid```b```"
        result = vault._strip_code_blocks(text)
        assert "a" not in result
        assert "b" not in result


class TestParseFrontmatter:
    def test_parses_key_value(self):
        text = "---\ntitle: My Note\ntags: python\n---\nbody here"
        meta, body = vault._parse_frontmatter(text)
        assert meta["title"] == "My Note"
        assert "body here" in body

    def test_no_frontmatter_returns_empty_dict(self):
        text = "# Just a heading\nbody"
        meta, body = vault._parse_frontmatter(text)
        assert meta == {}
        assert body == text

    def test_unclosed_frontmatter_returns_empty(self):
        text = "---\ntitle: Test\n# no closing delimiter"
        meta, body = vault._parse_frontmatter(text)
        assert meta == {}


class TestHandleReadWrite:
    def test_write_then_read(self, tmp_path):
        with patch.object(vault, "VAULT_PATH", tmp_path):
            vault.handle_write("TestNote", "hello world")
            content = vault.handle_read("TestNote")
        assert content == "hello world"

    def test_read_missing_raises(self, tmp_path):
        with patch.object(vault, "VAULT_PATH", tmp_path):
            with pytest.raises(FileNotFoundError):
                vault.handle_read("DoesNotExist")

    def test_write_creates_parent_dirs(self, tmp_path):
        with patch.object(vault, "VAULT_PATH", tmp_path):
            vault.handle_write("Sub/Folder/Note", "content")
            assert (tmp_path / "Sub" / "Folder" / "Note.md").exists()

    def test_append_adds_to_existing(self, tmp_path):
        with patch.object(vault, "VAULT_PATH", tmp_path):
            vault.handle_write("Note", "line1\n")
            vault.handle_append("Note", "line2\n")
            content = vault.handle_read("Note")
        assert "line1" in content
        assert "line2" in content

    def test_delete_removes_file(self, tmp_path):
        with patch.object(vault, "VAULT_PATH", tmp_path):
            vault.handle_write("Note", "content")
            vault.handle_delete("Note")
            assert not (tmp_path / "Note.md").exists()
