---
name: local-mac-imessage
description: Send iMessages on macOS using osascript (immediate or delayed), and read recent iMessages from chat.db. Use when user asks to send an iMessage, text, or message via iMessage to a contact, phone number, or Apple ID email, OR when user asks to check/read/show recent iMessages received in the last N minutes.
user-invocable: true
---

Send iMessages on macOS via AppleScript (osascript).

## How to use this skill

When invoked directly (e.g. `/local-mac-imessage`), ask the user for:
1. **Recipient** — phone number (e.g. `+919988776655`) or Apple ID email
2. **Message** — the text to send

If the user has already provided the recipient and/or message in the same request, skip asking for what was already provided.

## Guardrails

**Recipient allowlist (optional but recommended):**

If `ALLOWED_PHONE_NUMBERS` is configured in `.env`, the script will **only allow sending to recipients in that list**. This prevents accidental messages to wrong contacts.

Configure in `.env`:
```bash
ALLOWED_PHONE_NUMBERS=+91XXXXXXXXXX,+91XXXXXXXXXX,user@example.com
```

- Comma-separated list of phone numbers and/or Apple ID emails
- Phone numbers should be in E.164 format (e.g. `+91XXXXXXXXXX`)
- Whitespace is automatically trimmed
- If not set or empty, all recipients are allowed

**Example:** If `ALLOWED_PHONE_NUMBERS=+91XXXXXXXXXX`, attempting to send to any other number will fail with:
```
Error: Recipient '+919988776655' is not in ALLOWED_PHONE_NUMBERS
```

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

Example: Send "hi" to `+919988776655` after 5 minutes:
```bash
~/workspace/claude_for_mac_local/tools/imessage_send.sh -y --delay 5 "+919988776655" "hi"
```

**After starting a delayed send**, confirm to the user: `Scheduled: "MESSAGE_TEXT" → RECIPIENT (in N minutes)`

## Sending to multiple recipients

Run the tool once per recipient — they are independent calls.

## After sending

Confirm to the user: `Sent: "MESSAGE_TEXT" → RECIPIENT`

If the script errors (e.g. buddy not found, Messages not signed in), report the error clearly and suggest the user:
- Verify the recipient is reachable via iMessage (not just SMS)
- Ensure the Messages app is open and signed into iMessage
- Try using the full international format for phone numbers (e.g. `+91+919988776655`)

## Checking recent iMessages

When the user asks to check/read/show iMessages received in the last N minutes (e.g. "check messages since last 30 minutes"), use the tool below. If no duration is specified, default to 30 minutes:

```bash
~/workspace/claude_for_mac_local/tools/imessage_check.sh [MINUTES] [CONTACT]
```

`CONTACT` can be a phone number (e.g. `+919988776655`) or contact name (e.g. `Simraan`).

### Check all messages (last 30 minutes by default):
```bash
~/workspace/claude_for_mac_local/tools/imessage_check.sh
```

### Check all messages from a specific time period:
```bash
~/workspace/claude_for_mac_local/tools/imessage_check.sh 120  # last 2 hours
```

### Check messages from a specific contact (optional):
```bash
~/workspace/claude_for_mac_local/tools/imessage_check.sh 120 +919988776655
~/workspace/claude_for_mac_local/tools/imessage_check.sh 120 Simraan
```

### Using .env for default phone number:
Create or copy `.env` from `.env.example` and set `IMESSAGE_PHONE_NUMBER`:

```bash
cp .env.example .env
# Edit .env and set your default phone number
# IMESSAGE_PHONE_NUMBER=+919988776655
```

Then check messages from the default contact:
```bash
~/workspace/claude_for_mac_local/tools/imessage_check.sh 120  # uses IMESSAGE_PHONE_NUMBER from .env
```

### Preview messages with redaction (ask before showing content):

Show redacted preview (time and sender only), then ask user if ready to see full messages:

```bash
~/workspace/claude_for_mac_local/tools/imessage_check.sh --preview 120
~/workspace/claude_for_mac_local/tools/imessage_check.sh --preview 120 +917766554433
```

**Output with redaction:**

```
📋 Message Preview (Redacted):

2026-03-21 10:42:15|+917766554433|[REDACTED]
2026-03-21 10:43:02|Me|[REDACTED]
2026-03-29 10:15:40|SBICRD-S|[REDACTED]

Ready to see full message content? (y/n) y

📬 Full Messages:

2026-03-21 10:42:15|+917766554433|Hello!
2026-03-21 10:43:02|Me|Hi there
2026-03-29 10:15:40|SBICRD-S|[Media/Attachment]
```

**Output format:**

```
| Time | Sender | Message |
|------|--------|---------|
| 2026-03-21 10:42:15 | +917766554433 | Hello! |
| 2026-03-21 10:43:02 | Me | Hi there |
| 2026-03-29 10:15:40 | SBICRD-S(smsft) | [Media/Attachment] |
```

- If no messages found: `No iMessages in the last N minutes.`
- Sent messages show sender as **Me**
- Messages without text (photos, videos, etc.) show as `[Media/Attachment]`
- If sqlite3 errors with permissions, tell the user to grant Terminal (or the app running Claude) Full Disk Access in System Settings → Privacy & Security → Full Disk Access
