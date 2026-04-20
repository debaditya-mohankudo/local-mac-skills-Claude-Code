---
name: local-mac-vault
description: Unified vault operations — read, write, list, delete, move, links, backlinks, search, tasks, tags, outline, and session capture. Uses direct filesystem + mistletoe markdown. Supersedes local-mac-summarize-claude-session and claude-mac-obsidian.
user-invocable: true
---

# local-mac-vault

Unified interface for all vault operations.

**Architecture:** All vault ops use direct filesystem reads/writes via Python (`pathlib` + `mistletoe`). Vault path configured via `.env` (`VAULT_NAME`, `VAULT_PATH`). No Obsidian CLI dependency.

**Vault conventions:** Read `Documentation/CLAUDE.md` in the vault before writing notes or capturing sessions — defines folder structure, naming conventions, and link patterns.

---

## MCP Tool Reference

| Operation | MCP Tool | Key params |
|-----------|----------|------------|
| Read a note | `vault_read` | `path` |
| Create/overwrite | `vault_write` | `path`, `content` |
| Append | `vault_append` | `path`, `content` |
| Delete | `vault_delete` | `path` |
| Move/rename | `vault_move` | `path`, `to` |
| List files | `vault_list` | `path` (optional folder) |
| Search | `vault_search` | `query`, `project_folder`, `max_results` |
| Outgoing links | `vault_links` | `path` |
| Backlinks | `vault_backlinks` | `path` |
| Today's daily | `vault_daily_read` | — |
| Heading outline | `vault_outline` | `path` |
| Tags | `vault_tags` | `path` (optional) |
| Tasks | `vault_tasks` | `scope` (`all`/`daily`/note path) |
| Vault stats | `vault_stats` | — |

All `path` values are vault-relative (e.g. `Documentation/Tools/SKILLS_WIKI`). `.md` extension is optional.

---

## Subcommands

### read
```
vault_read(path="Projects/MyProject")
```

### write
```
vault_write(path="Projects/MyProject", content="...")
```

### append
```
vault_append(path="Daily/2026-04-19_summary", content="...")
```

### delete
Confirm with user first.
```
vault_delete(path="Daily/2026-01-01")
```

### edit (atomic)
Never overwrite directly. Stage in `Tmp/`, then move:
1. `vault_write(path="Tmp/NOTE", content=<updated>)`
2. `vault_move(path="Tmp/NOTE", to="Target/NOTE")`

If move fails, delete Tmp note — original untouched.

### list
```
vault_list(path="Projects")   # folder
vault_list()                  # all files
```

### search
```
vault_search(query="cache strategy", project_folder="Projects", max_results=5)
```

### move
```
vault_move(path="Old/Path", to="New/Path")
```

### links / backlinks
```
vault_links(path="Projects/MyProject")
vault_backlinks(path="Key Concepts/Cache Strategy")
```

### tasks
```
vault_tasks(scope="all")     # vault-wide incomplete
vault_tasks(scope="daily")   # today's daily note
vault_tasks(scope="Projects/MyProject")  # specific note
```

### tags
```
vault_tags()                          # all vault tags with counts
vault_tags(path="Projects/MyProject") # tags for one note
```

### outline
```
vault_outline(path="Documentation/Tools/SKILLS_WIKI")
```

---

## capture-session / summary session

Capture this Claude session's thinking, decisions, and learnings to today's daily summary note.

**Steps:**
1. Read vault conventions: `vault_read(path="CLAUDE")`
2. Check today's summary: `vault_daily_read()`
3. Compose session summary with `[[ProjectName]]` wikilinks at start and end.
4. If first session today: write via filesystem `Write` tool to `VAULT_PATH/Daily/YYYY-MM-DD_summary.md`
5. If subsequent: append via filesystem `Edit` tool

**Naming:** `Daily/YYYY-MM-DD_summary.md` — separate from Obsidian's built-in `Daily/YYYY-MM-DD.md`.

**Format — first session:**
```markdown
---
project: ProjectName
date: YYYY-MM-DD
tags: [tag1, tag2]
---

[[ProjectName|capture1]]
# Session 1 — Title

... session content ...

[[ProjectName|capture1]]
```

**Format — subsequent sessions** (append only, no frontmatter):
```markdown

---

[[ProjectName|captureN]]
# Session N — Title

... session content ...

[[ProjectName|captureN]]
```

---

## Notes

- Vault name/path in `.env`: `VAULT_NAME`, `VAULT_PATH`
- Bidirectional links: `[[Note Name]]` syntax — preserve when writing
- `Tmp/` is the scratchpad — always clean before and after skill runs
- Markdown parsing (tables, headings, frontmatter): use `mistletoe` library
- This skill supersedes `/local-mac-summarize-claude-session` and `/claude-mac-obsidian`
