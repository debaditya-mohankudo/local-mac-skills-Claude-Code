---
name: local-mac-time
description: Get the current time, set an alarm at HH:MM, or start a wait-N-minutes timer with a macOS notification + alert when done. Use when the user asks what time it is, wants to set an alarm, or wants to wait/timer for N minutes.
user-invocable: true
---

Get the current time, set a future alarm, or start a countdown timer — all backed by macOS notifications and alerts.

---

## Determine the operation

| Intent | Examples |
|--------|---------|
| **now** | "what time is it", "current time", "time now" |
| **alarm** | "set alarm for 9:30", "wake me at 14:00", "alarm at 7am" |
| **wait** | "wait 5 min", "timer for 20 minutes", "remind me in 10 min" |

---

## NOW — get current time

Call `mcp__local-mac__time_now` and output the result directly.

---

## ALARM — set alarm at HH:MM

**Step 1 — Extract time and optional label:**
- Parse target time from user message (convert "7am" → "07:00", "2:30pm" → "14:30")
- Optional label defaults to "Alarm" if none given

**Step 2 — Set the alarm:**

Call `mcp__local-mac__time_alarm` with:
- `time`: HH:MM (24-hour)
- `label`: optional label string
- `reminder`: set `true` when the alarm must survive a reboot or sync to iPhone/iPad

- If the time has already passed today, the binary automatically schedules it for tomorrow
- `at` job fires a macOS notification + modal alert at the exact time
- `reminder=true` additionally creates an Apple Reminder with a due date

**Step 3 — Confirm:**

Report the result string, e.g.:
`Alarm set: "Wake up" at 07:00 on Thu 26 Mar (scheduled via at + Apple Reminder)`

---

## WAIT — countdown timer for N minutes

**Step 1 — Extract duration and optional label:**
- Parse number of minutes (integers or decimals, e.g. 1.5 = 90 seconds)
- Optional label defaults to "Timer"

**Step 2 — Start the timer:**

Call `mcp__local-mac__time_wait` with:
- `minutes`: number (int or float)
- `label`: optional label string

Runs entirely in the background — fires a macOS notification + modal alert when the timer expires.

**Step 3 — Confirm:**

Report the result string, e.g.:
`Timer started: "Tea" — 5 min, finishes ~18:35 (scheduled via at)`
