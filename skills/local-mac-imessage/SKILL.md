---

name: local-mac-imessage
description: Send and read iMessages on macOS using the native Messages app. Supports contact lookup, confirmation, delayed sending, and reading recent messages.
user-invocable: true
--------------------

# 📱 Local Mac iMessage Skill (Hybrid)

Send iMessages via the Messages app and read recent iMessages using structured workflows + natural language reasoning.

---

## 🧠 When to use this skill

Use this skill when the user wants to:

* Send a message via iMessage (name, phone, or email)
* Schedule/delay a message
* Read recent iMessages

---

## 🏗️ Architecture (Current)

All iMessage operations go through the **Python MCP server** (`mcp_server.py`) which calls the **Swift CLI binary** (`~/bin/local-mac-tool`) via subprocess.

> Migration complete: `local-mpc` client and old Swift MCP server are retired. See vault: `Projects/SWIFT_CLI_MCP_MIGRATION.md`

MCP tools available:
- `imessage-read` — read recent messages (SQLite on `chat.db`)
- `imessage-send` — send via AppleScript

---

## ⚙️ Execution Modes

---

### 📤 1. Send iMessage (Safe Workflow)

Use when:

* A **contact name** is provided
* There is **ambiguity**
* The action is **sensitive (default path)**

```yaml
type: workflow
intent: send_imessage

inputs:
  recipient_name: string | optional
  recipient_phone: string | optional
  message: string

steps:

  - id: resolve_contact
    tool: contacts-search          # MCP tool via Python MCP server
    when: "{{recipient_name}} != null AND {{recipient_phone}} == null"

  - id: select_contact
    type: ai_select
    from: "{{resolve_contact}}"

  - id: confirm
    type: user_confirm
    message: "Send '{{message}}' to {{recipient_phone || select_contact.phone}}?"

  - id: send
    tool: imessage-send            # MCP tool via Python MCP server
    if: "{{confirm}} == true"
```

#### ✅ Behavior

* Resolves contact automatically
* Handles multiple matches intelligently
* **Never sends without confirmation**

---

### ⚡ 2. Quick Send (Direct Command)

Use when:

* User provides **explicit phone/email**
* No ambiguity exists

```yaml
type: workflow
intent: send_quick_message

inputs:
  recipient: string
  message: string

steps:

  - id: confirm
    type: user_confirm
    message: "Send '{{message}}' to {{recipient}}?"

  - id: send
    tool: imessage-send            # MCP tool via Python MCP server
    if: "{{confirm}} == true"
```

#### ✅ Behavior

* Confirms before sending even when recipient is explicit
* Immediate execution after confirmation

---

### 📥 3. Read Recent iMessages

Use MCP tool `imessage-read` directly:

```yaml
type: command
intent: read_imessages
tool: imessage-read               # MCP tool via Python MCP server
inputs:
  limit: number | optional        # default: 10
```

#### ✅ Behavior

* Default limit = 10
* Returns structured data → must be formatted as table

---

## 📊 Output Formatting

### For reading messages

Always present results as:

```
| Time | Sender | Message |
|------|--------|---------|
| 2026-03-21 10:42:15 | +919876543210 | Hello! |
```

* If no messages found: `No iMessages found.`

---

## ⚠️ Error Handling

### Sending failures

If sending fails:

* Show clear error message
* Suggest:

  * Verify recipient supports iMessage
  * Ensure Messages app is signed in
  * Use international format (`+91...`)

---

### Reading failures (permissions)

If sqlite access fails:

* Ask user to grant:
  **System Settings → Privacy & Security → Full Disk Access**

---

## 🧠 Decision Rules (Critical)

* If **recipient name provided** → use *Safe Workflow*
* If **explicit phone/email provided** → use *Quick Send*
* If **reading requested** → use *Read Messages*

---

## 🧩 Design Principles

* YAML blocks = **execution layer (deterministic)**
* Natural language = **reasoning + interaction layer**
* Never bypass confirmation in safe workflow
* Prefer structured execution over ad-hoc tool calls

---

## 🚀 Notes

* All workflows composable via MCP tool use — no shell bridge needed
* Designed for hybrid AI + deterministic execution

---
