---
name: local-mac-vault
description: Unified Obsidian vault interface — read, write, search, tasks, links, tags, sessions. Use for all vault work.
user-invocable: true
---

Unified vault interface. Supersedes the older session-summarise skill.

## Tools
Read/write: `vault__read` `vault__write` `vault__append` `vault__move` `vault__delete`
Discover:   `vault__list` `vault__outline` `vault__stats` `vault__tags` `vault__tasks`
Links:      `vault__links` `vault__backlinks`
Search:     `vault__section_search` `vault__folder_search` `vault__tags_search`
            `vault__filename_search` `vault_rag__smart_search` (hybrid FTS + semantic)
Daily:      `vault__daily_read`

## Rules
- `vault_rag__smart_search` is the one-shot search — prefer it over chaining narrower searches.
- Scratch work goes in `Tmp/` only, never `/tmp/`, and is cleaned up after.
- Delete via the tool, never a shell `rm`.
- Confirm before `vault__delete`.

## Naming
`ALL_CAPS.md` for reference, `YYYY-MM-DD_summary.md` for daily captures,
`Project_Name.md` for projects, `skill-name.md` under `Skills/`.
