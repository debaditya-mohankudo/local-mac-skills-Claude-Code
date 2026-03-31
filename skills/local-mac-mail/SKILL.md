---
name: local-mac-mail
description: Read emails from macOS Mail app by account email address. Use when user asks to check, read, show, or list emails/mail from a specific email account or inbox.
user-invocable: true
---

Read emails from macOS Mail app via AppleScript.

## How to use this skill

Arguments: `<email> <last_n_emails>`

- `<email>` — the account email address (e.g. `user@gmail.com`) or account name (e.g. `Google`, `iCloud`). If omitted, ask the user.
- `<last_n_emails>` — number of recent emails to fetch. If omitted, default to **5**.

## Step 1: Resolve account name from email

First, list all accounts to find the one matching the provided email or name:

```bash
~/workspace/claude_for_mac_local/tools/mail_list_accounts.sh
```

Match the user's input (case-insensitive) against account names or email addresses.

## Step 2: Fetch emails from matched account's INBOX

```bash
~/workspace/claude_for_mac_local/tools/mail_fetch_inbox.sh "ACCOUNT_NAME" N
```

Replace `ACCOUNT_NAME` with the matched account name and `N` with the number of emails.

## Display format

Present results as a table:

```
| # | Sender | Subject | Received |
|---|--------|---------|----------|
| 1 | HDFC MF | Weekend Bytes | Sat 21 Mar, 17:06 🔵 |
| 2 | DataCamp | Privacy Policy update | Sat 21 Mar, 13:00 |
```

- Mark unread emails with 🔵
- If account not found, list available accounts and ask the user to pick one
- If mailbox "INBOX" errors, try mailbox name variations: `Inbox`, `INBOX`

## Reading full email content

If the user asks to read/open a specific email (by number or subject):

```bash
~/workspace/claude_for_mac_local/tools/mail_read_email.sh "ACCOUNT_NAME" INDEX
```

Replace `INDEX` with the email number the user specified.

Truncate content to first 2000 characters if very long, and note: `[truncated — ask to see more]`
