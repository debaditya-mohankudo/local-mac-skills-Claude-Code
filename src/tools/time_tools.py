"""
now/alarm/wait ported from local-mac-tool/Sources/LocalMacMCP/TimeTool.swift.
`now` is pure Python (no AppleScript needed, matches Swift's own approach).
`alarm`/`wait` schedule via the `at` command + osascript notification, same
as Swift did — Swift itself wasn't pure AppleScript here either.
"""
import shlex
import subprocess
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


def handle_now() -> str:
    """Get the current time in IST."""
    now = datetime.now(ZoneInfo("Asia/Kolkata"))
    return now.strftime("%A, %d %b %Y  %H:%M:%S %Z")


def _at_schedule(notify_cmd: str, at_spec: str) -> str:
    quoted = shlex.quote(notify_cmd)
    result = subprocess.run(
        ["sh", "-c", f"echo {quoted} | at {at_spec}"],
        capture_output=True, text=True, timeout=15,
    )
    return (result.stdout + result.stderr).strip()


def handle_alarm(time: str, label: str = "Alarm", reminder: bool = False) -> str:
    """Set an alarm at HH:MM (24h). Optionally also creates an Apple Reminder."""
    if not time:
        raise ValueError("Missing required argument: time (HH:MM)")
    parts = time.split(":")
    if len(parts) != 2 or not (parts[0].isdigit() and parts[1].isdigit()):
        raise ValueError("Invalid time format. Use HH:MM (24-hour).")
    h, m = int(parts[0]), int(parts[1])
    if not (0 <= h <= 23 and 0 <= m <= 59):
        raise ValueError("Invalid time format. Use HH:MM (24-hour).")

    now = datetime.now()
    target = now.replace(hour=h, minute=m, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)

    human_time = f"{h:02d}:{m:02d}"
    human_date = target.strftime("%H:%M on %a %d %b")
    at_time = target.strftime("%H:%M")

    notify_cmd = (
        f'osascript -e \'display notification "Alarm: {human_time}" with title "⏰ {label}" sound name "Glass"\'; '
        f'osascript -e \'display alert "⏰ {label}" message "It is now {human_time}"\''
    )
    at_result = _at_schedule(notify_cmd, at_time)

    msg = f'Alarm set: "{label}" at {human_date} (scheduled via at)'
    if at_result:
        msg += f"\n{at_result}"

    if reminder:
        from tools.reminders import handle_create as reminders_create
        due_str = target.isoformat()
        reminders_create(title=f"⏰ {label}", due_date=due_str)
        msg += " + Apple Reminder"

    return msg


def handle_wait(minutes: float, label: str = "Timer") -> str:
    """Start a countdown timer for N minutes. Fires a macOS notification when done."""
    if minutes <= 0:
        raise ValueError("minutes must be positive.")

    at_mins = max(1, round(minutes))
    finish = datetime.now() + timedelta(minutes=at_mins)
    finish_str = finish.strftime("%H:%M")

    notify_cmd = (
        f'osascript -e \'display notification "{minutes} min elapsed" with title "⏱ {label}" sound name "Glass"\'; '
        f'for i in 1 2 3 4 5; do afplay /System/Library/Sounds/Glass.aiff; done; '
        f'osascript -e \'display alert "⏱ {label}" message "{minutes} minute(s) are up!"\''
    )
    at_result = _at_schedule(notify_cmd, f"now + {at_mins} minutes")

    msg = f'Timer started: "{label}" — {minutes} min, finishes ~{finish_str} (scheduled via at)'
    if at_result:
        msg += f"\n{at_result}"
    return msg


def handle_play_sound(seconds: float, sound: str = "Glass") -> str:
    """Play a macOS system sound repeatedly for N seconds.

    Args:
        seconds: Duration in seconds to keep playing the sound.
        sound:   System sound name (default: Glass). Options: Glass, Ping, Purr, Basso,
                 Blow, Bottle, Frog, Funk, Hero, Morse, Pop, Sosumi, Submarine, Tink.
    """
    import subprocess, os
    sound_path = f"/System/Library/Sounds/{sound}.aiff"
    dur = int(round(seconds))
    cmd = f"end=$(($(date +%s)+{dur})); while [ $(date +%s) -lt $end ]; do afplay {sound_path}; done"
    subprocess.Popen(
        ["sh", "-c", cmd],
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    return f"Playing {sound} for {seconds}s"
