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

```bash
~/workspace/claude_for_mac_local/tools/time_control.sh now
```

Output the result directly.

---

## ALARM — set alarm at HH:MM

**Step 1 — Extract time and optional label:**
- Parse target time from user message (convert "7am" → "07:00", "2:30pm" → "14:30")
- Optional label defaults to "Alarm" if none given

**Step 2 — Set the alarm:**

```bash
# basic — at job only
~/workspace/claude_for_mac_local/tools/time_control.sh alarm HH:MM [label]

# hardened — at job + Apple Reminder (survives reboot, syncs to iPhone)
~/workspace/claude_for_mac_local/tools/time_control.sh alarm --reminder HH:MM [label]
```

- Time must be 24-hour `HH:MM`
- If the time has already passed today, the script automatically schedules it for tomorrow
- `at` job fires a macOS notification + modal alert at the exact time
- `--reminder` additionally creates an Apple Reminder with a due date — use this when the alarm must survive a reboot or sync to iPhone/iPad

**Step 3 — Confirm:**

Report what the script prints, e.g.:
`Alarm set: "Wake up" at 07:00 on Thu 26 Mar (scheduled via at + Apple Reminder)`

---

## WAIT — countdown timer for N minutes

**Step 1 — Extract duration and optional label:**
- Parse number of minutes (integers or decimals, e.g. 1.5 = 90 seconds)
- Optional label defaults to "Timer"

**Step 2 — Start the timer:**

```bash
~/workspace/claude_for_mac_local/tools/time_control.sh wait <minutes> [label]
```

- Runs entirely in the background — no blocking
- Fires a macOS notification + modal alert when the timer expires

**Step 3 — Confirm:**

Report what the script prints, e.g.:
`Timer started: "Tea" — 5 min, finishes at 18:35:00`
