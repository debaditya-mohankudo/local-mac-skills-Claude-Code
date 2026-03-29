# Execution Model Wiki

How Claude actually runs commands on your Mac and on remote machines — what happens under the hood, why it's fast, and how it differs from opening a Terminal window yourself.

**Last updated:** 2026-03-22

---

## How Claude decides what to use

There are two ways to invoke a skill — explicit slash commands and natural language. They work very differently.

### Explicit slash commands — no routing, direct invoke

When you type `/local-mac-*`, Claude invokes that skill immediately. No description matching, no routing decision — the skill loads and Claude follows its instructions.

```text
/local-mac-network
    ↓
Skill loads directly — routing bypassed entirely
```

**This is the recommended way to use skills.** It is unambiguous, predictable, and faster — Claude does not spend any effort deciding what tool to use.

```text
/local-mac-network      → always network skill
/local-mac-process      → always process skill
/local-mac-docker       → always docker skill
/local-mac-ssh          → always ssh skill
/local-mac-finder       → always finder skill
/local-mac-safari       → always safari skill
/local-mac-calendar     → always calendar skill
/local-mac-notes        → always notes skill
/local-mac-reminders    → always reminders skill
/local-mac-mail         → always mail skill
/local-mac-imessage     → always imessage skill
/local-mac-contacts     → always contacts skill
/local-mac-music        → always music skill
/local-mac-spotify      → always spotify skill
/local-mac-storage      → always storage skill
/local-mac-screencapture → always screencapture skill
```

### Natural language — routing via description matching

When you use natural language, Claude reads all skill descriptions injected at session start and matches your intent against them.

```text
User sends a natural language message
    ↓
Claude reads all skill descriptions (injected at session start)
    ↓
Does any description match the intent?
    ├── Yes → invoke the matched skill
    └── No  → use built-in tools directly (Bash, Read, Grep, Glob, etc.)
```

This works well but introduces a routing step — and if the description isn't precise enough, Claude may pick the wrong skill or fall back to Bash when a skill would be better.

### Routing examples

| User says | Claude uses | Why |
| --------- | ----------- | --- |
| "what's on port 3000" | `local-mac-network` | description matches |
| "is nginx running" | `local-mac-process` | description matches |
| "run df -h on dev server" | `local-mac-ssh` | description matches |
| "search for TODO in src/" | Grep tool directly | no skill description matches |
| "read this file" | Read tool directly | no skill description matches |
| "list png files" | Bash tool directly | no skill description matches |

### Tags — human reference, not routing

All skills have a `tags` field in their frontmatter:

```yaml
tags: [network, port, curl, dns, ping, type:discipline]
```

Tags are **not used by Claude for routing** — only `description` is surfaced at session start. Tags exist purely for humans browsing the `skills/` directory on GitHub.

Two consistent tag types are used across all skills:

| Tag | Meaning |
| --- | ------- |
| `type:capability` | Skill uses AppleScript — adds capability Claude cannot do via Bash alone |
| `type:discipline` | Skill wraps Bash commands — adds guardrails Claude would not enforce ad-hoc |

Domain tags (`docker`, `git`, `ssh`, `applescript`, etc.) let you identify the skill's scope at a glance without reading the full description.

### The description field is the routing rule

The `description` field in a skill's SKILL.md frontmatter is the most important line in the file — it determines when the skill gets invoked:

```yaml
---
description: Check network status on the local Mac — what's on a port, curl an
  endpoint, ping a host, DNS lookup, list all listening ports. Use when the user
  asks what's using a port, whether a service is up, DNS resolution, or what
  ports are open.
---
```

- **Too vague** → skill is never invoked when it should be
- **Too broad** → skill is invoked in situations it wasn't designed for
- **Well-scoped** → Claude routes correctly every time

When writing a new skill, the description is what you tune first.

---

## The two execution models

Every action Claude takes runs in one of two ways:

| Model | How it works | Example skills |
| ----- | ------------ | -------------- |
| **Claude subprocess** | Claude calls a shell script directly as a child process. No UI. Output is captured and returned to Claude inline. | All `local-mac-*` skills, `local-mac-ssh` |
| **Terminal.app** | Claude tells Terminal.app to open a window/tab and run a command via AppleScript. The human watches the output live. Claude cannot read it. | `local-mac-terminal` *(planned)* |

---

## Claude subprocess — how it works

When you ask Claude to run a remote command, check logs, or query a database, this is what happens:

```text
User prompt
    ↓
Claude invokes skill (e.g. /local-mac-ssh)
    ↓
Skill calls tools/ssh_run.sh as a subprocess
    ↓
ssh_run.sh runs: ssh [SSH_OPTS] user@host "command"
    ↓
Output captured → returned to Claude inline
    ↓
Claude reads, summarizes, and replies
```

**Key points:**

- Terminal.app is never opened
- The SSH process runs silently in the background
- Claude sees the full output and can reason about it
- The process blocks until the remote command exits — no live streaming

---

## Terminal.app model — how it works

When a command is run via Terminal.app (the `local-mac-terminal` skill is planned):

```text
User prompt
    ↓
Claude calls AppleScript → Terminal.app opens a window/tab
    ↓
Terminal runs: ssh -t user@host "docker logs --follow"
    ↓
Output streams live in the Terminal window
    ↓
Human watches directly — Claude sees nothing
```

**Key points:**

- Terminal.app window opens (200–500ms startup if not already running)
- A fresh SSH connection is made every time — no socket reuse
- Output is live-streamed (supports `--follow`, interactive commands)
- Claude cannot read or analyze the output

---

## Performance comparison

### SSH connection speed

| Connection type | Claude subprocess | Terminal.app |
| --------------- | ----------------- | ------------ |
| App launch | None | ~200–500ms (if no window open) |
| SSH handshake (cold) | ~75ms | ~75ms |
| SSH handshake (warm) | **~10ms** (ControlMaster) | ~75ms (new connection every time) |
| Speedup on repeat calls | **~7.5×** | None |

### Why Claude subprocess is faster on repeat calls — ControlMaster

`ssh_common.sh` configures SSH with `ControlMaster=auto`:

```text
First SSH call to a host
    → full TLS handshake + key exchange (~75ms)
    → creates a socket at /tmp/ssh_mux_user@host:22

Every subsequent call to the same host
    → reuses the existing socket (~10ms)
    → skips handshake entirely
```

Terminal.app opens a fresh connection every time with no socket reuse — so it always pays the full ~75ms handshake cost.

Each `user@host:port` gets its own socket, so multiple remote machines are fully independent.

### Overall verdict

| Use case | Winner | Why |
| -------- | ------ | --- |
| Run a command and get output | **Claude subprocess** | Faster, Claude can read and act on output |
| Repeat calls to same host | **Claude subprocess** | ControlMaster saves ~65ms per call |
| Live log tailing (`--follow`) | **Terminal.app** | Subprocess waits for exit — can't stream |
| Interactive session | **Terminal.app** | Subprocess has no TTY |
| Claude analyzes the output | **Claude subprocess** | Terminal output is invisible to Claude |

---

## Why this matters for skill design

This distinction drives the responsibility boundary between `local-mac-ssh` and the planned `local-mac-terminal`:

- **Use `local-mac-ssh` when** Claude needs to read the result — logs analysis, DB queries, disk reports, git history
- **Use `local-mac-terminal` when** you want to watch something live — log tailing, interactive debugging, long-running processes

There is no overlap. The two skills serve different masters: one serves Claude, one serves the human watching the screen.

**In practice, Terminal.app is needed ~5% of the time.** The vast majority of DevOps work — running commands, fetching logs, querying DBs, checking disk, reading git history — is read-output-and-analyze, which the subprocess model handles faster and better. The only gap is live streaming (`--follow`, interactive sessions), which `ssh_logs.sh` already partially covers by fetching the last N lines on demand. `local-mac-terminal` is therefore low priority.

---

## Local macOS commands (non-SSH)

The same subprocess model applies to all local skills. When Claude reads your calendar, sends an iMessage, or opens a Finder window:

```text
Skill calls tools/calendar_list_events.sh
    ↓
Script runs osascript (AppleScript) or sqlite3 as subprocess
    ↓
Output captured → returned to Claude
```

No app is launched unless explicitly needed (e.g. `finder_control.sh open` opens a Finder window by design). Most read operations query system databases or AppleScript properties silently.

---

## How Claude runs ALL commands — the full picture

This applies not just to skills but to everything Claude does when it uses the Bash tool directly.

```text
You ask Claude something
    ↓
Claude decides to run a shell command (Bash tool)
    ↓
Claude's process forks a child subprocess via execve()
    ↓
Command runs silently — no Terminal.app, no window, no UI
    ↓
stdout/stderr captured → returned to Claude inline
    ↓
Claude reads the output and replies to you
```

This is why you never see a Terminal window flash open when Claude runs commands. It is not using Terminal at all — it is running commands the same way any program launches another program: as a direct child process.

### The full stack — subprocesses all the way down

Every action Claude takes follows this same pattern, just at different layers:

| What you ask | Claude calls | Which runs | Via |
| ------------ | ------------ | ---------- | --- |
| "run df -h on dev" | `ssh_run.sh` | `ssh user@host "df -h"` | subprocess → SSH → remote shell |
| "show my calendar" | `calendar_list_events.sh` | `osascript` | subprocess → AppleScript → Calendar.app |
| "send iMessage" | `imessage_send.sh` | `osascript` | subprocess → AppleScript → Messages.app |
| "open this folder" | `finder_control.sh open` | `osascript` | subprocess → AppleScript → Finder.app |
| "list png files" | Bash tool directly | `mdfind -name ".png"` | subprocess → Spotlight index |
| "what's my disk usage" | `storage_overview.sh` | `df -h`, `du -sh` | subprocess → kernel |

**The rule:** Claude never touches a UI unless the tool explicitly tells an app to do something visible (like `finder_control.sh open` or `safari_control.sh open`). Everything else — reading files, querying databases, running SSH commands, checking calendars — happens silently in the background.

### Why this matters

- **Fast** — no app launch overhead, no window rendering
- **Invisible** — nothing opens on your screen unless intended
- **Claude reads the output** — because it's captured inline, Claude can reason about it, summarize it, and act on it
- **Contrast with Terminal.app** — if Claude ran commands via Terminal, it would see nothing. The output would be in a window only you can see.
