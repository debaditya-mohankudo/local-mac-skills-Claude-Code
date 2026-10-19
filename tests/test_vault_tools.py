"""Tests for src/tools/vault.py — pure string helpers and filesystem ops."""
import pytest
from pathlib import Path
from unittest.mock import patch

import tools.vault as vault
import tools.vault_rag as vault_rag


class TestVaultPath:
    def test_adds_md_extension(self):
        result = vault._vault_path("Notes/MyNote")
        assert str(result).endswith("MyNote.md")

    def test_keeps_existing_md(self):
        result = vault._vault_path("Notes/MyNote.md")
        assert str(result).endswith("MyNote.md")
        assert not str(result).endswith("MyNote.md.md")


class TestVaultContainment:
    @pytest.fixture
    def vault_root(self, tmp_path):
        root = tmp_path / "vault"
        root.mkdir()
        (tmp_path / "secret.md").write_text("outside")
        (root / "Note.md").write_text("inside")
        (root / "link").symlink_to(tmp_path)
        with patch.object(vault, "VAULT_PATH", root):
            yield root

    # Each escape is built from the vault root, so the absolute case needs no placeholder.
    ESCAPES = [
        lambda root: str(root.parent / "secret.md"),  # absolute path outside the vault
        lambda root: "../secret",                     # walks out with ..
        lambda root: "Sub/../../secret",              # walks out from inside a subfolder
        lambda root: "link/secret",                   # walks out through a symlinked folder
    ]
    FOLDER_ESCAPES = [
        lambda root: str(root.parent),
        lambda root: "..",
        lambda root: "../vault/..",
    ]

    @pytest.mark.parametrize("escape", ESCAPES)
    @pytest.mark.parametrize("call", [
        vault.handle_read,
        lambda a: vault.handle_write(a, "x"),
        lambda a: vault.handle_append(a, "x"),
        vault.handle_delete,
        lambda a: vault.handle_move("Note", a),
        vault.handle_links,
        vault.handle_outline,
        vault.handle_tags,
        vault.handle_tasks,
        lambda a: vault_rag.handle_index_file(a),
    ])
    def test_escape_refused_and_outside_untouched(self, vault_root, escape, call):
        with pytest.raises(PermissionError):
            call(escape(vault_root))
        assert (vault_root.parent / "secret.md").read_text() == "outside"
        assert (vault_root / "Note.md").read_text() == "inside"

    @pytest.mark.parametrize("escape", FOLDER_ESCAPES)
    @pytest.mark.parametrize("call", [
        lambda f: vault.handle_filename_search("secret", f),
        lambda f: vault_rag.handle_unindexed_files(f),
    ])
    def test_folder_escape_refused(self, vault_root, escape, call):
        with pytest.raises(PermissionError):
            call(escape(vault_root))

    def test_in_vault_paths_unchanged(self, vault_root):
        vault.handle_write("Sub/Note", "body")
        assert (vault_root / "Sub" / "Note.md").read_text() == "body"
        assert vault.handle_read("Sub/../Sub/Note.md") == "body"
        vault.handle_move("Sub/Note", "Other/Note")
        assert (vault_root / "Other" / "Note.md").exists()
        assert "Other/Note.md" in vault.handle_filename_search("note", "Other")

    def test_refusal_logged_as_blocked(self, vault_root):
        import tool_hooks
        with patch.object(tool_hooks, "_log_call") as log:
            with pytest.raises(PermissionError):
                with tool_hooks.tool_called("vault", "read", {"path": "../secret"}):
                    vault.handle_read("../secret")
        assert log.call_args.kwargs["blocked"] is True


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
