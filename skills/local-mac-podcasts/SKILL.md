---
name: local-mac-podcasts
description: Browse Apple Podcasts on macOS — list subscribed shows, list episodes, recent episodes across all shows, and in-progress episodes. Use when user asks about podcasts, what's new in podcasts, unplayed episodes, or episodes in progress.
user-invocable: true
---

Read-only access to Apple Podcasts library via the Podcasts.app SQLite database. No playback control — browse only.

---

## Available MCP tools

| Tool | Purpose |
|------|---------|
| `mcp__local-mac__podcasts_list` | List all subscribed podcasts with episode counts |
| `mcp__local-mac__podcasts_recent` | Recent episodes across all shows (optional: `new_only=True`, `limit`) |
| `mcp__local-mac__podcasts_in_progress` | Episodes started but not finished (have a playhead position) |
| `mcp__local-mac__podcasts_episodes` | Episodes for a specific show (`podcast_title` or `podcast_uuid`, optional: `limit`, `unplayed=True`) |

---

## Intent → tool mapping

| User says | Tool |
|-----------|------|
| list my podcasts / what shows am I subscribed to | `podcasts_list` |
| what's new / recent episodes | `podcasts_recent` |
| what haven't I listened to / unplayed | `podcasts_recent` with `new_only=True` |
| what was I listening to / in progress | `podcasts_in_progress` |
| episodes for [show name] | `podcasts_episodes` with `podcast_title` |
| unplayed episodes for [show name] | `podcasts_episodes` with `podcast_title` + `unplayed=True` |

---

## Display format

**Podcast list** — one line per show:
```
• Bloomberg Intelligence (Bloomberg) — 2000 episodes
• Urgency of Change • The Krishnamurti Podcast — 292 episodes
```

**Episode list** — one line per episode:
```
• DOJ Drops Powell Probe... [19:50] — Bloomberg Intelligence — Apr 24
• Instant Reaction: Intel... [10:01] — Apr 23 ★ new
```

Show `★ new` for `is_new=true`. Show playhead as `(at 4:32)` for in-progress episodes. Format `published` dates as human-readable (Apr 24, 2026). Format duration as M:SS or H:MM:SS.

---

## Guardrails

- Read-only — no playback, no mark-as-played, no downloads via this tool.
- `podcast_title` does a partial match (LIKE %title%) — if no match, tell the user the exact show name from `podcasts_list`.
- Timestamps are ISO 8601 UTC — convert to IST for display.
