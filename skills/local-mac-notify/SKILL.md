---
name: local-mac-notify
description: Create macOS notifications that appear in Notification Center and menu bar. Use when you need to show alerts, delivery updates, reminders, or status messages to the user.
user-invocable: true
---

Create macOS notifications that appear in the Notification Center and menu bar.

## How to use this skill

When invoked directly (e.g. `/local-mac-notify`), ask the user for:
1. **Title** — the main notification heading (e.g., "Swiggy Delivery")
2. **Message** — the notification body (e.g., "Delivery in 22 minutes")
3. **Sound** — optional sound to play (yes/no, default: Ping)

If the user has already provided the title and/or message in the same request, skip asking for those.

## Creating a notification

Basic notification with default sound (Ping):

```bash
~/workspace/claude_for_mac_local/tools/notify.sh "Swiggy Delivery" "Delivery in 22 minutes"
```

## Notification with custom sound

Available sounds: Ping, Basso, Blow, Bottle, Frog, Funk, Glass, Hero, Morse, Pop, Submarine, Tink

```bash
~/workspace/claude_for_mac_local/tools/notify.sh "Swiggy Delivery" "Delivery in 22 minutes" --sound Pop
```

## Notification without sound

```bash
~/workspace/claude_for_mac_local/tools/notify.sh "Swiggy Delivery" "Delivery in 22 minutes" --sound none
```

## After sending notification

Confirm to the user: `✓ Notification sent: "TITLE"`

If the script errors:
- Check that the macOS Notification Center is enabled
- Verify the title and message are provided
- Try a different sound if the default doesn't work

## Examples

**Delivery notification:**
```bash
~/workspace/claude_for_mac_local/tools/notify.sh "Zomato" "Order arriving in 18 minutes"
```

**Reminder notification:**
```bash
~/workspace/claude_for_mac_local/tools/notify.sh "Meeting" "Team standup in 5 minutes" --sound Glass
```

**Silent status notification:**
```bash
~/workspace/claude_for_mac_local/tools/notify.sh "Build Complete" "Deployment ready" --sound none
```
