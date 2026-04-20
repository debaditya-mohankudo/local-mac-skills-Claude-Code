# claude_for_mac_local

macOS automation skills and tools for Claude Code — calendar, contacts, iMessage, mail, reminders, notes, processes, screen recording, Safari, music, Finder, network, storage, Docker, SSH, Wi-Fi, and market intelligence.

**Timezone:** IST (India Standard Time / Kolkata)

**Vault path:** `/Users/debaditya/workspace/claude_documents/`
**Full docs:** Vault → `Documentation/Tools/WIKI_HOME.md`
**Architecture:** Vault → `Projects/SWIFT_CLI_MCP_MIGRATION.md`

---

## Architecture

Single **Python MCP server** (`mcp_server.py`) wraps a **Swift CLI binary** (`~/bin/local-mac-tool`) for all native macOS tool calls. Vault operations use direct filesystem reads/writes via Python (markdown files at `VAULT_PATH`). `local-mpc` and the separate `obsidian` MCP server are retired.

`tools/` contains 50+ shell scripts — do not delete or move; skills reference them via absolute paths.

---

## Vault Rules

- All vault ops via direct filesystem (Read/Write/Edit tools) using Python markdown handling
- Vault scratchpad: `Tmp/` only — never `/tmp/`, never in-context memory
- Every skill that persists data: clean Tmp/ → write Tmp/ → compose report → save Daily/ → clean Tmp/
- Delete via `os.remove()` or `Path.unlink()` — never `rm` shell command
- Obsidian MCP tools are retired for vault ops (too slow/unreliable)

**Note naming:** `ALL_CAPS.md` for wiki/reference, `YYYY-MM-DD_summary.md` for daily captures, `Project_Name.md` for projects, `skill-name.md` in `Skills/`

---

## Privacy Rules

- No personal data in code or docs — use placeholders only
- No financial/portfolio data anywhere outside the vault
- Skills contain logic only — vault note paths are fine, hardcoded values are not
- Before committing: `./tools/scan_personal_data.sh`

---

## Output Rules

- Never show raw tool output — compose and display the final report only
- Intermediate steps run silently; surface errors inline in the report

---

## Development Workflow

- Always develop on a feature branch — never commit to `main` directly
- Always use `/gc-gp` for commits (runs personal data guardrail)
- Always sync `~/.claude/skills/<name>/` changes back to `skills/<name>/` in this repo
- Work milestones → `claude` calendar on Mac
