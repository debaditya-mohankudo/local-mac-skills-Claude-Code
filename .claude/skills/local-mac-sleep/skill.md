---
name: local-mac-sleep
description: Sleep the Mac now, on a timer, or via a wind-down sequence. Use for end-of-day and timed sleep.
user-invocable: true
---

Put the Mac to sleep.

## Tools
`system__sleep_now` `system__sleep_in` `system__sleep_cancel` `system__sleep_status`
`system__sleep_winddown`

## Rules
- Confirm before `system__sleep_now` — unsaved work is lost without warning.
- After scheduling, state the time it will fire and how to cancel.
- Check `system__sleep_status` before scheduling a second timer.
