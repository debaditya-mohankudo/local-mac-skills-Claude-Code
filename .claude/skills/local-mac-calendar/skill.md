---
name: local-mac-calendar
description: Read, create, and delete Apple Calendar events. Use for scheduling questions or calendar changes.
user-invocable: true
---

Manage Apple Calendar.

## Tools
`calendar__list_events` `calendar__get_events_by_date` `calendar__get_upcoming_events`
`calendar__add_event` `calendar__delete_event` `calendar__get_noise_summary`

## Rules
- Confirm before `calendar__delete_event` — deletions are not recoverable from here.
- Resolve relative dates ("next Tuesday") to absolute dates before calling, and state the resolved date back.
- Timezone is IST unless the user says otherwise.
