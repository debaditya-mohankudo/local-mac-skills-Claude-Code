---
name: local-mac-call
description: Place a FaceTime audio or video call to a contact or number. Use when the user asks to call someone.
user-invocable: true
---

Start a FaceTime call.

## Approach
Open a `facetime://` (video) or `facetime-audio://` URL with the resolved handle.

## Rules
- Resolve the person with `contacts__search` first, and confirm the number before dialling.
  A call placed to the wrong person cannot be taken back.
- State clearly which number and which mode (audio or video) before starting.
