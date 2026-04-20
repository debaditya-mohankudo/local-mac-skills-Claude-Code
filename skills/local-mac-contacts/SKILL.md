---
name: local-mac-contacts
description: Search personal contacts by name and return phone numbers and details. Use when user asks to find a contact, look up a phone number, or search for someone's details.
user-invocable: true
---

Search personal contacts by name from macOS Contacts. All operations go through the **Python MCP server** (`mcp_server.py`) → Swift CLI binary (`~/bin/local-mac-tool`). Use MCP tool use directly — `local-mpc` is retired.

> See vault: `Projects/SWIFT_CLI_MCP_MIGRATION.md`

## How to use this skill

Extract the search name from the user's message. If no name is provided, ask for one.

### Searching contacts

MCP tool: `contacts_search`
```json
{ "name": "SEARCH_NAME", "include_email": false }
```

Returns JSON array of matching contacts with:
- `name` — full contact name
- `phoneNumbers` — array of phone entries with `label` and `value`
- `emailAddresses` — optional, included only if `include_email: true`

## Display format

Present results as a table:

```
| Name | Label | Phone |
|------|-------|-------|
| Simran | mobile | +919876543210 |
| Simran | home | +919876543210 |
```

- If no contacts found: `No contacts found matching "[name]".`
- If multiple contacts match, show all of them
- Include email addresses if user asks for "email" or "all details" by using `include_email: true`

## Getting email addresses

To include email addresses in the search, set `include_email: true`:

```bash
local-mpc call contacts_search '{
  "name": "SEARCH_NAME",
  "include_email": true
}'
```

The response will include an `emailAddresses` field with `label` and `value` pairs.
