# Wiki Home — local-mac-skills

This is the navigation hub for this project's documentation. Read this first, then go to the specific wiki that matches your task.

**Last updated:** 2026-03-22

---

## What is this project?

A set of Claude Code skills and shell tools that give Claude direct control over macOS apps (Calendar, Notes, Reminders, Mail, iMessage, Contacts, Music, Spotify, Safari, Finder) and remote workstations over SSH. Skills are installed globally at `~/.claude/skills/`. Shell tools live in `~/workspace/claude_for_mac_local/tools/`.

---

## Where to go

| If you want to… | Go to |
| --------------- | ----- |
| Use a skill or understand what it can do | [SKILLS_WIKI.md](SKILLS_WIKI.md) |
| Call a specific `tools/*.sh` script directly | [TOOLS_WIKI.md](TOOLS_WIKI.md) |
| Understand what guardrails are enforced and why | [GUARDRAILS_WIKI.md](GUARDRAILS_WIKI.md) |
| Run tests or add tests for a new script | [QUALITY_WIKI.md](QUALITY_WIKI.md) |
| See what skills are planned or pending | [FUTURE_SKILLS.md](FUTURE_SKILLS.md) |
| Understand how Claude runs commands (subprocess vs Terminal, SSH performance) | [EXECUTION_MODEL_WIKI.md](EXECUTION_MODEL_WIKI.md) |

---

## Quick orientation

### Skills (agent-facing)

Each skill is a slash command (`/local-mac-*`) that Claude invokes when the user asks for a macOS or SSH action. Skills call the `tools/*.sh` scripts under the hood.

→ See [SKILLS_WIKI.md](SKILLS_WIKI.md) for full usage, options, and setup notes per skill.

### Tools (script-facing)

Standalone bash scripts in `tools/`. Each has a clear argument signature and can be called directly from the terminal. Grouped by domain: iMessage, Mail, Calendar, Notes, Reminders, Contacts, SSH, Storage, Safari, Finder.

→ See [TOOLS_WIKI.md](TOOLS_WIKI.md) for argument signatures and example calls.

### Guardrails

Every skill has restrictions. Some are instruction-level (in `SKILL.md`). Others are script-level (in the shell scripts themselves, enforced regardless of what Claude decides). Script-level guardrails are stronger.

Key guardrails at a glance:
- **Notes** — Claude folder only
- **Calendar** — Work calendar by default; system calendars skipped
- **Mail** — read-only, inbox only, 2000-char truncation
- **SSH DB queries** — `--read-only` MySQL flag + 7-keyword block list
- **SSH git** — large block list enforced before SSH connects
- **Safari** — URL domain allowlist in `safari_config.sh`
- **Finder** — `mkdir` restricted to `$HOME`; `trash` requires y/N confirmation
- **File transfer** — remote paths restricted to `REMOTE_DIRS` in `ssh_config.sh`

→ See [GUARDRAILS_WIKI.md](GUARDRAILS_WIKI.md) for the full list with reasoning.

### Tests

All tests live in `tests/test_tools.sh`. Run with:

```bash
bash ~/workspace/claude_for_mac_local/tests/test_tools.sh
```

Tests cover: local happy-path checks, SSH sandbox tests (Docker, skipped if container not running), guardrail block tests for SQL keywords and git subcommands, and file transfer allowlist enforcement.

→ See [QUALITY_WIKI.md](QUALITY_WIKI.md) for what is tested, what is not, and how to add tests.

---

## Config files

| File | Purpose |
| ---- | ------- |
| `ssh_config.sh` | Workstation nicknames, `REMOTE_DIRS`, DB defaults, cache retention |
| `music_config.sh` | iMusic playlist nicknames → exact Music.app playlist names |
| `spotify_config.sh` | Spotify playlist nicknames → Spotify URIs |
| `safari_config.sh` | URL allowlist, `DISABLE_ALLOWLIST` flag |

---

## Adding a new skill

1. Create the skill at `~/.claude/skills/<skill-name>/SKILL.md`
2. Add any shell tools to `tools/`
3. Add the tool to the table in `CLAUDE.md`
4. Add guardrails — check [GUARDRAILS_WIKI.md](GUARDRAILS_WIKI.md) for the design checklist
5. Add the skill to [SKILLS_WIKI.md](SKILLS_WIKI.md) and tools to [TOOLS_WIKI.md](TOOLS_WIKI.md)
6. Add tests — check [QUALITY_WIKI.md](QUALITY_WIKI.md) for conventions
7. Mark the skill as done in [FUTURE_SKILLS.md](FUTURE_SKILLS.md)
