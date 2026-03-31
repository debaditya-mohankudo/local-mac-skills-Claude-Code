---
name: local-mac-edit-env
description: Safely edit .env configuration file with user consent and guardrails
user-invocable: true
---

Edit the `.env` configuration file with built-in safety checks and automatic permission handling.

## How to use this skill

When editing `.env`:
1. **Check permissions** — if read-only, automatically unlock it
2. **Show the change** — display what will be modified
3. **Ask for consent** — get explicit user approval before proceeding
4. **Edit safely** — make the change after approval
5. **Restore protection** — automatically set back to read-only

## Edit .env variable

**Step 1: Check current permissions**

```bash
ls -l /Users/debaditya/workspace/claude_for_mac_local/.env | awk '{print $1}'
```

If read-only (`-r--r--r--`), unlock it:
```bash
chmod 644 /Users/debaditya/workspace/claude_for_mac_local/.env
```

**Step 2: Preview and request consent**

Display current value and proposed change:
```
Current:  ALLOWED_PHONE_NUMBERS=+1XXXXXXXXXX,+1YYYYYYYYYY,
Proposed: ALLOWED_PHONE_NUMBERS=+1XXXXXXXXXX,+1YYYYYYYYYY,+1ZZZZZZZZZZ,

Should I proceed? (yes/no)
```

**Step 3: Edit after approval**

Use the Edit tool to make the change:
```
OLD: ALLOWED_PHONE_NUMBERS=+1XXXXXXXXXX,+1YYYYYYYYYY,
NEW: ALLOWED_PHONE_NUMBERS=+1XXXXXXXXXX,+1YYYYYYYYYY,+1ZZZZZZZZZZ,
```

**Step 4: Restore read-only protection**

After editing, always set back to read-only:
```bash
chmod 444 /Users/debaditya/workspace/claude_for_mac_local/.env
```

**Step 5: Confirm result**

```
✓ Updated: ALLOWED_PHONE_NUMBERS
New value: +1XXXXXXXXXX,+1YYYYYYYYYY,+1ZZZZZZZZZZ,
✓ Restored: .env is now read-only (chmod 444)
```

## Important

- Never edit `.env` without explicit user consent
- Always unlock before editing, restore read-only after
- Always show the before/after values
- Variables affect iMessage sending, contact handling, and security settings
- File remains protected as read-only after each edit
