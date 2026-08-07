"""Central configuration — immutable singleton via pydantic-settings.

Reads from environment variables and .env file automatically.
All paths and table names live here — no scattered constants across files.

Pattern doc: vault → Documentation/Python_Best_Practices/Config_Pattern.md
"""
import os
from pathlib import Path

from pydantic import Field, computed_field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        frozen=True,
    )

    # --- Vault ---
    # The vault root is the iCloud Obsidian Documents directory itself. A
    # `claude_documents` subfolder exists there and is also a valid Obsidian
    # vault, but it holds none of the content the tools read — Documentation/
    # and LIFE_OS/ live at the root — so pointing here at the subfolder made
    # every vault lookup silently miss.
    vault_name: str = Field(default="Documents", description="Vault folder name")
    vault_path: Path = Field(
        default=Path.home() / "Library" / "Mobile Documents" / "iCloud~md~obsidian" / "Documents",
        description="Absolute path to the Obsidian vault root",
    )

    # Vault SQLite table names
    table_keyword_hints: str = Field(
        default="vault_keyword_hints",
        description="SQLite table name for the keyword hint index",
    )

    # --- Swift CLI binary ---
    swift_binary: str = Field(
        default=str(Path.home() / "bin" / "local-mac-tool"),
        description="Path to the local-mac-tool Swift CLI binary",
    )

    # --- Memory ---
    memory_db: Path = Field(
        default=Path.home() / ".claude" / "MEMORY.sqlite",
        description="Path to the memory SQLite database",
    )
    memory_valid_types: list[str] = Field(
        default=["user", "feedback", "project", "reference"],
        description="Allowed type values for memory entries",
    )

    @computed_field
    @property
    def vault_index_db(self) -> Path:
        return Path.home() / "Library/Mobile Documents/com~apple~CloudDocs/Databases/vault_index.sqlite"

    @computed_field
    @property
    def vault_rag_db(self) -> Path:
        return Path.home() / "Library/Mobile Documents/com~apple~CloudDocs/Databases/vault_rag"

    @computed_field
    @property
    def vault_rag_tvim(self) -> Path:
        return Path.home() / "Library/Mobile Documents/com~apple~CloudDocs/Databases/vault_rag.tvim"

    @computed_field
    @property
    def tool_hints_db(self) -> Path:
        return Path.home() / "Library/Mobile Documents/com~apple~CloudDocs/Databases/tool_hints.sqlite"

    # --- OpenConnector (Gmail/Calendar/Drive gateway) ---
    openconnector_base_url: str = Field(
        default="http://localhost:3000",
        description="Base URL of the locally-running OpenConnector container",
    )
    openconnector_runtime_token: str = Field(
        default="",
        description="Persistent runtime token (oct_...) for OpenConnector /v1 and /mcp calls — set via .env, never commit it",
    )

    @computed_field
    @property
    def openconnector_data_dir(self) -> Path:
        return Path.home() / "Library/Mobile Documents/com~apple~CloudDocs/Databases/openconnector"


# Module-level singleton — import and use directly
config = Settings()
