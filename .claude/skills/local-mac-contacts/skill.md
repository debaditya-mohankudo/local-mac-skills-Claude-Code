---
name: local-mac-contacts
description: Search contacts and return phone or email details. Use when a name needs resolving to a number or address.
user-invocable: true
---

Find a contact's details.

## Tools
- `contacts__search` — substring match over the contact store

## Rules
- This is the resolution step for messaging and calling skills — run it before `imessage__send` or a FaceTime URL.
- If several people match, show the options and ask; never pick one silently.
- Return only the field that was asked for. Do not volunteer other personal details.
