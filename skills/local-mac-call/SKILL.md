---
name: local-mac-call
description: Call a contact on macOS using tel:// URL scheme. Use when user asks to call someone, place a phone call, or dial a number.
user-invocable: true
---

Place phone calls on macOS by opening the `tel://` URL scheme (handled by iPhone Mirroring, FaceTime, or the default calling app).

## How to use this skill

When invoked (e.g. `/local-mac-call`), ask the user for:
1. **Recipient** — name, phone number, or short code (e.g. `121`)

If the user has already provided the recipient in the same request, skip asking.

## Step 1 — Look up contact (if a name is given)

If the user provides a name, resolve the phone number first via `mcp__local-mac__contacts_search` with the name as the query.

Display the resolved number and confirm with the user before calling.

If the user provides a phone number or short code directly, skip the lookup and call immediately.

## Step 2 — Place the call

```bash
open "tel://PHONE_OR_CODE"
```

Replace `PHONE_OR_CODE` with the phone number or short code (e.g. `121`, `+91XXXXXXXXXX`).

### Examples

```bash
open "tel://121"
open "tel://+91XXXXXXXXXX"
```

## Workflow summary

1. If a name was given, look up via `mcp__local-mac__contacts_search` and confirm the number
2. Call using `open "tel://NUMBER"`
3. Confirm: `Calling NUMBER — your calling app should open now.`

## After initiating

Confirm: `Calling NUMBER — your calling app should open now.`

## Error handling

If the call doesn't connect:
- Ensure iPhone Mirroring or FaceTime is set up and signed in
- Try the full international format for phone numbers (e.g. `+919876543210`)
