---
name: apfel-vault-chat
description: On-device interactive chat with full Obsidian vault access via apfel + MCP. Fully private — no API calls. Ask questions about your notes, market data, session history, or anything in the vault.
user-invocable: true
---

# apfel-vault-chat

Start an on-device interactive chat session (via apfel) with live access to your Obsidian vault through the local MCP server. All reasoning happens on-device — nothing leaves the machine.

**Requires:**
- `apfel` installed (`brew install apfel` or equivalent)
- `obsidian` CLI available at `/opt/homebrew/bin/obsidian`
- Obsidian app running (vault must be open)

---

## Usage

```
/apfel-vault-chat
/apfel-vault-chat "ask about market data"
/apfel-vault-chat summarize
/apfel-vault-chat tasks
```

---

## What to run

When this skill is invoked, output the following instruction block to the user and then execute the command:

### Default — interactive chat with vault access

```bash
apfel --chat \
  --mcp ~/workspace/claude_for_mac_local/tools/obsidian_mcp_server.py \
  --context-strategy summarize \
  -s "You are a helpful assistant with access to an Obsidian vault called claude_documents. The vault contains: daily session summaries (Daily/YYYY-MM-DD_summary.md), market intelligence notes, Krishnamurti inquiry notes (Documentation/K-mirror/), project documentation (Documentation/Tools/), and skills wiki. Use the vault tools to search and read notes before answering. Be concise. When asked about recent activity, read today's daily summary first."
```

### Quick question (non-interactive, one-shot)

If the user provides a question as an argument:

```bash
apfel \
  --mcp ~/workspace/claude_for_mac_local/tools/obsidian_mcp_server.py \
  -s "You have access to an Obsidian vault called claude_documents. Use vault tools to find relevant notes before answering. Be concise." \
  "<user's question>"
```

### Summarize today's vault activity

```bash
apfel \
  --mcp ~/workspace/claude_for_mac_local/tools/obsidian_mcp_server.py \
  -s "You have access to an Obsidian vault. Read today's daily summary note and give a concise overview of what was worked on today." \
  "Summarize today's vault activity"
```

### List open tasks

```bash
apfel \
  --mcp ~/workspace/claude_for_mac_local/tools/obsidian_mcp_server.py \
  -s "You have access to an Obsidian vault. Use obsidian_tasks to list all open tasks." \
  "What are my open tasks?"
```

---

## Subcommands

| Trigger | Behaviour |
|---------|-----------|
| `/apfel-vault-chat` | Interactive chat (default) |
| `/apfel-vault-chat summarize` | One-shot: summarize today's daily note |
| `/apfel-vault-chat tasks` | One-shot: list open vault tasks |
| `/apfel-vault-chat "<question>"` | One-shot: answer a specific question |

---

## Notes

- `--context-strategy summarize` compresses old turns on-device as the session grows — suitable for long research sessions
- The MCP server is `tools/obsidian_mcp_server.py` — it wraps the `obsidian` CLI and exposes search, read, list, tasks, tags, and write tools
- Exit the chat with `Ctrl-C`
- All data stays on-device — vault contents never leave the machine
