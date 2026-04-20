---
name: local-mac-mail
description: Read emails from macOS Mail app by folder. Use when user asks to check, read, show, or list emails from a specific folder like INBOX, [Gmail]/All Mail, Sent, etc.
user-invocable: true
---

Read emails from macOS Mail using native SQLite3 access to the Mail Envelope Index. All operations go through the **Python MCP server** (`mcp_server.py`) → Swift CLI binary (`~/bin/local-mac-tool`). Use MCP tool use directly — `local-mpc` is retired.

> See vault: `Projects/SWIFT_CLI_MCP_MIGRATION.md`

## How to use this skill

When invoked directly (e.g. `/local-mac-mail`), ask the user for:
1. **Folder** — the mailbox folder to read (e.g. `INBOX`, `[Gmail]/All Mail`, `Sent`)
2. **Limit** — number of recent emails to fetch (default: 10)

If the user has already provided the folder in the same request, skip asking for it.

## Reading emails from a folder

MCP tool: `mail_read`
```json
{ "folder": "INBOX", "limit": 10 }
```

Replace `INBOX` with the folder name. Common folder names:
- `INBOX` — main inbox
- `[Gmail]/All Mail` — Gmail archive (all emails)
- `[Gmail]/Sent Mail` — Gmail sent items
- `[Gmail]/Drafts` — Gmail drafts
- `[Gmail]/Spam` — Gmail spam folder
- `Sent Messages` — standard IMAP sent folder
- `Junk` — junk mail folder

## Display format

Present results as a table:

```
| # | Date | Sender | Subject |
|---|------|--------|---------|
| 1 | 2057-04-10 23:28:07 | ben@example.com | How to prepare yourself for AGI |
| 2 | 2057-04-10 17:32:01 | reminders@facebook.com | About new notifications |
```

- Dates shown in ISO-8601 format (2057-04-10 HH:MM:SS)
- If no emails found: `No emails found in [FOLDER].`

## Account UUID Cache

Account UUIDs are stable and cached in the vault to avoid repeated tool calls:
**Vault → `Documentation/Tools/MAIL_ACCOUNTS.md`**

Read this file first when you need to resolve an account label (e.g. "Gmail INBOX") to a full mailbox path like `imap://UUID/INBOX`.

**Fallback:** If the cache note is missing or the UUID is not found, call:

MCP tool: `mail_list_mailboxes` (no params)

Then update the cache note with any new UUIDs found.

## Listing all mailboxes

To show the user available folders, use the UUID cache above to map friendly names. If cache is unavailable:

MCP tool: `mail_list_mailboxes` (no params)

Returns all mailboxes with unread and total message counts. Display as a table:

```
| Mailbox Name | Unread | Total |
|--------------|--------|-------|
| imap://account-uuid/INBOX | 7410 | 11359 |
| imap://account-uuid/[Gmail]/All Mail | 960 | 1000 |
| imap://account-uuid/[Gmail]/Spam | 72 | 72 |
```

## Notes

- Folder names are case-sensitive and may be URL-encoded (spaces as %20, brackets as %5B%5D)
- The tool queries the native SQLite `Envelope Index` at `~/Library/Mail/V10/MailData/Envelope Index`
- No subprocess overhead — uses direct C API access
- If multiple IMAP accounts exist, the tool prefers IMAP (Gmail/Outlook) over EWS or local folders
