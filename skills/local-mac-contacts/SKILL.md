---
name: local-mac-contacts
description: Search macOS Contacts app by name and return phone numbers and details. Use when user asks to find a contact, look up a phone number, or search for someone's details.
user-invocable: true
---

Search macOS Contacts via AppleScript and return matching contacts with phone numbers.

## How to use this skill

When invoked, extract the search name from the user's message. If no name is provided, ask for one.

## Search for a contact

```bash
~/workspace/claude_for_mac_local/tools/contacts_search.sh "SEARCH_NAME"
```

Replace `SEARCH_NAME` with the name to search (case-insensitive partial match).

## Display format

Present results as a table:

```
| Name | Label | Number |
|------|-------|--------|
| Simran | Mobile | +91XXXXXXXXXX |
```

- Clean up label formatting: `_$!<Mobile>!$_` → `Mobile`, `_$!<Main>!$_` → `Main`, `_$!<Home>!$_` → `Home`, `_$!<Work>!$_` → `Work`
- If no contacts found: `No contacts found matching "[name]".`
- If multiple contacts match, show all of them

## Get email addresses

To also fetch emails, pass the `--with-email` flag:

```bash
~/workspace/claude_for_mac_local/tools/contacts_search.sh "SEARCH_NAME" --with-email
```

Use this variant if the user asks for email or "all details".

## Contacts Cache Manager

Use `contacts_cache_update.sh` to manage a fast, local contacts cache with **cache-first search**.

### Cache-First Search

The search command checks the cache first for instant results, then falls back to system contacts:

```bash
~/workspace/claude_for_mac_local/tools/contacts_cache_update.sh search "John"
```

Results show:
- **📦 Found in cache** — instant results from cached contacts
- **📱 Searching system contacts** — if not in cache, searches system Contacts app

### Cache Management

```bash
# Add contact to cache
~/workspace/claude_for_mac_local/tools/contacts_cache_update.sh add "John" "+1XXXXXXXXXX" mobile

# Add quick-access favorite (alias)
~/workspace/claude_for_mac_local/tools/contacts_cache_update.sh favorite "John" "+1XXXXXXXXXX" "J"

# List all cached contacts
~/workspace/claude_for_mac_local/tools/contacts_cache_update.sh list

# View recent iMessage contacts
~/workspace/claude_for_mac_local/tools/contacts_cache_update.sh recent

# Backup/restore cache
~/workspace/claude_for_mac_local/tools/contacts_cache_update.sh backup
~/workspace/claude_for_mac_local/tools/contacts_cache_update.sh restore

# Clear cache
~/workspace/claude_for_mac_local/tools/contacts_cache_update.sh reset
```

**Cache Location:** `~/.contacts_cache` (git-ignored, local only)
