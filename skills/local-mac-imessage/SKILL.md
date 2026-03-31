---
name: local-mac-imessage
description: Send iMessages on macOS using osascript (immediate or delayed), and read recent iMessages from chat.db. Use when user asks to send an iMessage, text, or message via iMessage to a contact, phone number, or Apple ID email, OR when user asks to check/read/show recent iMessages received in the last N minutes.
user-invocable: true
---

Send iMessages on macOS via AppleScript (osascript).

## How to use this skill

When invoked directly (e.g. `/local-mac-imessage`), ask the user for:
1. **Recipient** — phone number (e.g. `1XXXXXXXXXX`) or Apple ID email
2. **Message** — the text to send

If the user has already provided the recipient and/or message in the same request, skip asking for what was already provided.

## Sending a message

```bash
~/workspace/claude_for_mac_local/tools/imessage_send.sh -y "RECIPIENT" "MESSAGE_TEXT"
```

Replace `RECIPIENT` with the phone number or Apple ID, and `MESSAGE_TEXT` with the message.

> The `-y` flag confirms the send. Without it the script runs as a dry-run and prints a preview without sending.

## Sending a message later (delayed send)

To schedule a message to be sent after a delay:

```bash
~/workspace/claude_for_mac_local/tools/imessage_send.sh -y --delay MINUTES "RECIPIENT" "MESSAGE_TEXT"
```

- `--delay MINUTES` — wait N minutes before sending (integer or decimal, e.g. 5, 1.5)
- The send runs entirely in the background — the script returns immediately
- After the delay expires, the message is sent automatically

Example: Send "hi" to `1XXXXXXXXXX` after 5 minutes:
```bash
~/workspace/claude_for_mac_local/tools/imessage_send.sh -y --delay 5 "1XXXXXXXXXX" "hi"
```

**After starting a delayed send**, confirm to the user: `Scheduled: "MESSAGE_TEXT" → RECIPIENT (in N minutes)`

## Sending to multiple recipients

Run the tool once per recipient — they are independent calls.

## After sending

Confirm to the user: `Sent: "MESSAGE_TEXT" → RECIPIENT`

If the script errors (e.g. buddy not found, Messages not signed in), report the error clearly and suggest the user:
- Verify the recipient is reachable via iMessage (not just SMS)
- Ensure the Messages app is open and signed into iMessage
- Try using the full international format for phone numbers (e.g. `+911XXXXXXXXXX`)

## Checking recent iMessages

When the user asks to check/read/show iMessages received in the last N minutes (e.g. "check messages since last 30 minutes"), use the tool below. If no duration is specified, default to 30 minutes:

```bash
~/workspace/claude_for_mac_local/tools/imessage_check.sh [MINUTES]
```

Replace `MINUTES` with the number of minutes the user specified (default: 30).

Present results as a table:

```
| Time | Sender | Message |
|------|--------|---------|
| 2026-03-21 10:42:15 | +1YYYYYYYYYY | Hello! |
| 2026-03-21 10:43:02 | Me | Hi there |
```

- If no messages found: `No iMessages in the last N minutes.`
- Sent messages show sender as **Me**
- If sqlite3 errors with permissions, tell the user to grant Terminal (or the app running Claude) Full Disk Access in System Settings → Privacy & Security → Full Disk Access
