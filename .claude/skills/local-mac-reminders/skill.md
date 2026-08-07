---
name: local-mac-reminders
description: Read and manage Apple Reminders with list and status filters. Use for task capture and completion.
user-invocable: true
---

Manage Apple Reminders.

## Tools
`reminders__list` `reminders__create` `reminders__complete` `reminders__delete`

## Rules
- Resolve due dates to absolute values before creating.
- Confirm before deleting; completing is preferred over deleting for finished work.
