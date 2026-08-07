---
name: local-mac-imessage
description: Send iMessages and read recent conversations from macOS Messages. Use when the user wants to message someone or check what was said.
user-invocable: true
---

Send and read iMessages through the native Messages app.

## Tools
- `imessage__send` — send to a phone number or handle
- `imessage__read` — read recent messages

## Rules
- Confirm the recipient before sending. A message to the wrong person cannot be recalled.
- Resolve names to numbers with `contacts__search` first — never guess a number.
- Read is scoped to recent messages; do not attempt to dump whole conversation history.
- Never echo message content into a report unless the user asked to see it.
