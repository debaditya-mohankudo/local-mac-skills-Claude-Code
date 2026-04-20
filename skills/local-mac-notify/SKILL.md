---
name: local-mac-notify
description: Create macOS notifications that appear in Notification Center and menu bar, and list recent notifications. Use when you need to show alerts, delivery updates, reminders, or view notification history.
user-invocable: true
---

Create and manage macOS notifications in Notification Center and menu bar.

## How to use this skill

When invoked directly (e.g. `/local-mac-notify`), check if the user is asking to:
1. **Create a notification** — ask for title, message, and optional sound (yes/no, default: Ping)
2. **List recent notifications** — show notifications from the last N hours (default: 24)
3. **Clear notification history** — remove all logged notifications

If the user has already provided the title and/or message in the same request, skip asking for those.

## Creating a notification

Basic notification with default sound (Ping):

```bash
~/workspace/claude_for_mac_local/tools/notify.sh "Swiggy Delivery" "Delivery in 22 minutes"
```

The notification is logged locally to `~/.claude/notifications.jsonl` for history.

## Notification with custom sound

Available sounds: Ping, Basso, Blow, Bottle, Frog, Funk, Glass, Hero, Morse, Pop, Submarine, Tink

```bash
~/workspace/claude_for_mac_local/tools/notify.sh "Swiggy Delivery" "Delivery in 22 minutes" --sound Pop
```

## Notification without sound

```bash
~/workspace/claude_for_mac_local/tools/notify.sh "Swiggy Delivery" "Delivery in 22 minutes" --sound none
```

## Listing recent notifications

Show notifications from the last N hours (default: 24):

```bash
~/workspace/claude_for_mac_local/tools/notify.sh --list-notifications
~/workspace/claude_for_mac_local/tools/notify.sh --list-notifications 12
~/workspace/claude_for_mac_local/tools/notify.sh --list-notifications 1
```

Output format:
```
Time                | Title                           | Message
====================================================================
[2026-03-29 10:22:15] | Swiggy Delivery                 | Delivery in 12 minutes
[2026-03-29 10:18:42] | Zomato                          | Order arrived
```

## Clearing notification history

Remove all logged notifications:

```bash
~/workspace/claude_for_mac_local/tools/notify.sh --clear
```

## After operations

**After creating a notification:**
Confirm to the user: `✓ Notification sent: "TITLE"`

**After listing:**
Display the formatted table of recent notifications.

**After clearing:**
Confirm to the user: `✓ Notification log cleared`

If the script errors:
- Check that the macOS Notification Center is enabled
- Verify the title and message are provided
- Try a different sound if the default doesn't work
- For listing, check that `~/.claude/notifications.jsonl` exists

## Examples

**Create delivery notification:**
```bash
~/workspace/claude_for_mac_local/tools/notify.sh "Zomato" "Order arriving in 18 minutes"
```

**Create reminder with custom sound:**
```bash
~/workspace/claude_for_mac_local/tools/notify.sh "Meeting" "Team standup in 5 minutes" --sound Glass
```

**Create silent status notification:**
```bash
~/workspace/claude_for_mac_local/tools/notify.sh "Build Complete" "Deployment ready" --sound none
```

**List notifications from last 24 hours:**
```bash
~/workspace/claude_for_mac_local/tools/notify.sh --list-notifications
```

**List notifications from last 6 hours:**
```bash
~/workspace/claude_for_mac_local/tools/notify.sh --list-notifications 6
```
