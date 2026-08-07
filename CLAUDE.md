# claude_for_mac_local

> **Public repo notice:** No personal contact details, financial details, or email addresses shall be part of this code or any committed files.

macOS automation skills and tools for Claude Code — calendar, contacts, iMessage, mail, reminders, notes, Safari, music, sound, podcasts, VPN, vault, session memory, processes, screen recording, Finder, network, storage, Wi-Fi, and market intelligence.

The astrology tools (panchang, planets, Vimshottari dasha, gochar, chart queries) were moved to a separate private repository. They read birth data for identifiable people, and that cannot live in a repository meant to be public.

## Why this repo exists

This is a personal Mac turned into a place Claude can act, not just answer. The point isn't any single skill — it's removing the gap between "Claude knows what to do" and "Claude did it": send the message, add the event, read the mail, check the portfolio, without the user relaying every detail by hand.

Two things are held in tension on purpose. First, it's built to be shared — the README, the committed `local-mac-*` skills, the public-repo notice at the top of this file all exist so a stranger can clone this and get real macOS automation, not a stub. Second, it runs against one person's actual life — their mail, their contacts, their finances, their vault of private notes — so nothing here can leak who they are. Every architectural choice downstream (what's gitignored, what gets redacted before logging, what the gates block) is that tension resolved in one direction or the other. When in doubt, privacy wins over convenience, and reversible/logged wins over silent.

The gates (see below) and the concept store exist for the same underlying reason: this system is meant to keep working correctly as it grows, without a human re-deriving "wait, why does it do it that way" from scratch each time. A gate encodes a rule in code so it can't be silently skipped; a concept encodes the reasoning behind a design so future changes don't undo it by accident.

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

`hooks/` contains 6 Python hooks fired by Claude Code events — `memory_loader.py` (UserPromptSubmit), `pre_tool_use.py` (PreToolUse), `stop_hook.py` + `tool_usage_logger.py` (Stop/PostToolUse). `~/.claude/hooks` is a symlink to this directory.

**`sessions.db`** (`~/.claude/sessions.db`) — SQLite DB for live session state and persisted summaries. Two tables: `sessions` (per-session keywords, domains, injected memory names, state machine, turn counter, tasks) and `session_summaries` (compact snapshots saved by `session-compact-persist`, with tags).

---

## Concept Store

`concept_store/concepts.json` holds the non-obvious design reasoning behind this repo — why something is built the way it is, not what the code does (the code already says that). Same schema as task-framework's concept stores: `name`, `module`, `description`, `contracts`, `invariants`, `evidence`, `confidence`. Update it (via `mcp__taskfw__concept__upsert` or by hand) when a design decision would otherwise have to be re-discovered by reading code and guessing intent — e.g. the MCP tool-call gates in `src/tool_hooks.py`.

## SysML Model

`models/*.sysml` is a SysML v2 structural model of the foundational call path and gate mechanism (`foundation.sysml`, `system.sysml`, `gates.sysml`, `requirements.sysml`) — `part def`s for `MCPServer`/`Dispatcher`/`ToolCallGates` and its guards, plus `requirement def`s citing the exact source lines they're satisfied by. Each package carries an `@ModelProvenance` stamp (commit + modelled paths); `tests/test_model_provenance.py` fails the moment a stamped path's code changes without the model being re-read, so the model can't silently go stale. Use `/generate-sysml` to extend it as new areas warrant modelling; re-validate with the `sysml-mcp` tools after any edit.

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
