# claude_for_mac_local

> **Public repo notice:** No personal contact details, financial details, or email addresses shall be part of this code or any committed files.

macOS automation skills and tools for Claude Code — calendar, contacts, iMessage, mail, reminders, notes, Safari, music, sound, podcasts, VPN, vault, session memory, processes, screen recording, Finder, network, storage, Wi-Fi, and market intelligence.

The astrology tools (panchang, planets, Vimshottari dasha, gochar, chart queries) were moved to a separate private repository. They read birth data for identifiable people, and that cannot live in a repository meant to be public.

**Timezone:** IST (India Standard Time / Kolkata)
**Memory domains:** `macos` (CWD default), `vault` (CWD: the vault directory)

**Vault path:** set via `VAULT_PATH` in `.env` (see `.env.example`)
**Full docs:** Vault → `Documentation/Tools/WIKI_HOME.md`
**Vault MCP tools:** Vault → `Documentation/Tools/VAULT_SECTION_INDEX.md`

---

## Architecture

Single **Python MCP server** (`mcp_server.py`). Native macOS access is AppleScript via `osascript`, with direct SQLite reads where an app exposes a database. Vault operations are plain filesystem reads and writes over markdown at `VAULT_PATH`.

A **Swift CLI binary** (`~/bin/local-mac-tool`) remains for the two things AppleScript cannot do:

* **Sound** — selecting an audio output device is CoreAudio. AppleScript can set the system volume but cannot enumerate or switch devices.
* **Foundation Models** — Apple's on-device framework has no Python or PyObjC binding. The Python tool implements only the HTTP fallback.

Everything else that once lived in Swift has been ported. When adding a tool, reach for AppleScript first; Swift is the exception that has to justify itself.

`tools/` contains ~40 shell scripts — do not delete or move; skills reference them via absolute paths.

**Skills layout:** `skills/` holds the older non-personal skills (`gc-gp`, `memory-load-relevant`, `session-*`). The `local-mac-*` family lives in `.claude/skills/` and IS committed — the README documents it, so a reader who clones this must be able to obtain it.

Everything else under `.claude/` stays ignored: settings carrying absolute paths and permission allowlists, a scheduled-task lock, and a git worktree. The ignore is written as `.claude/*` plus `!.claude/skills/` so that admitting the skills cannot accidentally admit the rest.

Skills are logic only. Vault note paths are fine; phone numbers, addresses, account identifiers and machine-specific paths are not — those belong in `.env`.

**FastAPI memory server** (`server/`) runs on `127.0.0.1:8765` — auto-started by `mcp_server.py` at launch. Handles memory scoring, session keyword tracking, and tool-hint lookup. Self-contained: all config in `server/config.py`, docs in `server/README.md`. Stopword filtering shared via `server/stopwords.py` + `server/stopwords.json` (edit JSON to add words; takes effect on next server restart).

`hooks/` contains 6 Python hooks fired by Claude Code events — `memory_loader.py` (UserPromptSubmit), `pre_tool_use.py` (PreToolUse), `stop_hook.py` + `tool_usage_logger.py` (Stop/PostToolUse). `~/.claude/hooks` is a symlink to this directory.

**`sessions.db`** (`~/.claude/sessions.db`) — SQLite DB for live session state and persisted summaries. Two tables: `sessions` (per-session keywords, domains, injected memory names, state machine, turn counter, tasks) and `session_summaries` (compact snapshots saved by `session-compact-persist`, with tags).

---

## Databases

| DB | Path | Purpose |
| --- | --- | --- |
| `MEMORY.sqlite` | `~/.claude/MEMORY.sqlite` | Persistent memories (feedback, user, project, reference) — injected by `memory_loader.py` hook on every prompt |
| `tool_hints.sqlite` | `~/Library/Mobile Documents/com~apple~CloudDocs/Databases/tool_hints.sqlite` | MCP tool usage history for hint scoring; also holds `bash_audit` table |
| `vault_index.sqlite` | `~/Library/Mobile Documents/com~apple~CloudDocs/Databases/vault_index.sqlite` | Vault FTS index + TurboVec semantic embeddings used by `vault_rag__smart_search` |
| `sessions.db` | `~/.claude/sessions.db` | Live session state (`sessions`) and compact summary snapshots (`session_summaries`, `prompt_tool_calls`) |

All iCloud-hosted DBs (`tool_hints.sqlite`, `vault_index.sqlite`) sync across devices automatically.

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

## Memory Usage

- **Always check injected memories before asking the user for any information** in these domains: personal data (health, profile), stock markets, portfolio, contacts
- Global memories (priority=1) are always injected via `additionalSystemPrompt` — no tool call needed
- Order: injected memories → vault search → only then ask the user
- **Search tools:** use `memory__search` for SQLite memories (auto-retries individual keywords on zero results), `vault_rag__smart_search` for vault notes (hybrid FTS + semantic, one shot)

---

## Commands

```bash
# Start MCP server (Claude Code does this automatically on launch)
uv run python mcp_server.py

# Restart FastAPI memory server manually
./server/run.sh

# Run tests
uv run pytest tests/
```

Package manager: `uv` — use `uv run` not `python` directly.

---

## Development Workflow

- Always develop on a feature branch — never commit to `main` directly
- Always use `/gc-gp` for commits (runs personal data guardrail)
- Always sync `~/.claude/skills/<name>/` changes back to `skills/<name>/` in this repo for non-`local-mac-*` skills only
- Work milestones → `claude` calendar on Mac
- Before writing any Python code: search vault docs via RAG (`vault_rag__smart_search "<topic>"` in folder `Documentation/passive_learning_coding`) for established patterns — centralized logging, try/except/else, generator pipelines, stability patterns, etc.
