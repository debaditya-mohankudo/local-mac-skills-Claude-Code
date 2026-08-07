---
name: kaise
description: Break a plain-language task into the right skills and execution order. Use when a request spans several tools.
user-invocable: true
---

Route a request to the right skills, in the right order.

## Approach
1. Name the concrete outcome the user wants.
2. Identify which skills own each part of it.
3. Order them by dependency — resolution before action (`contacts__search` before
   `imessage__send`), read before write, check before change.
4. State the plan, then execute. Do not narrate every step as it runs.

## Rules
- Prefer one skill that covers the task over three that overlap.
- If a step is destructive, surface it in the plan rather than at the moment it runs.
- If no skill fits, say so instead of forcing the closest match.
