"""
now/alarm/wait ported from local-mac-tool/Sources/LocalMacMCP/TimeTool.swift.
`now` is pure Python (no AppleScript needed, matches Swift's own approach).
`alarm`/`wait` fire an osascript notification from a detached shell that
waits until the target time. They used to go through `at`, as Swift did, but
macOS ships atrun disabled, so those jobs queued and never ran. The shell
compares wall-clock time every few seconds instead of one long `sleep`,
because sleep's clock stops while the Mac sleeps and the alert would come late.
A pending alert does not survive a reboot or logout.
"""
import subprocess
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


def handle_now() -> str:
    """Get the current time in IST."""
    now = datetime.now(ZoneInfo("Asia/Kolkata"))
    return now.strftime("%A, %d %b %Y  %H:%M:%S %Z")


def _spawn_detached(script: str) -> int:
    """Run a shell script in its own session so it outlives this process; returns its pid."""
    return subprocess.Popen(
        ["sh", "-c", script],
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        start_new_session=True,
    ).pid


def _schedule(notify_cmd: str, target: datetime) -> int:
    """Run notify_cmd at target in a detached shell; returns its pid."""
    epoch = int(target.timestamp())
    return _spawn_detached(f"while [ $(date +%s) -lt {epoch} ]; do sleep 5; done; {notify_cmd}")


# How every _schedule timer reads in `ps -o command=`. A timer leads its own
# process group, so pgid == pid is checked alongside this prefix.
_TIMER_COMMAND = "sh -c while [ $(date +%s) -lt "


def handle_cancel(pid: int) -> str:
    """Cancel a wait/alarm timer by the pid it reported. Stops its whole process group."""
    if pid <= 1:
        raise ValueError(f"Not a timer: pid {pid}")
    ps = subprocess.run(["/bin/ps", "-o", "pgid=,command=", "-p", str(pid)],
                        capture_output=True, text=True, timeout=10)
    fields = ps.stdout.split(None, 1)
    if ps.returncode != 0 or len(fields) < 2:
        return f"Timer {pid} already finished"
    pgid, command = fields
    if pgid != str(pid) or not command.startswith(_TIMER_COMMAND):
        raise ValueError(f"Not a timer: pid {pid} is {command.strip()[:80]!r}")
    import os
    import signal
    try:
        os.killpg(pid, signal.SIGTERM)
    except ProcessLookupError:
        return f"Timer {pid} already finished"
    return f"Timer {pid} cancelled"


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

    notify_cmd = (
        f'osascript -e \'display notification "Alarm: {human_time}" with title "⏰ {label}" sound name "Glass"\'; '
        f'osascript -e \'display alert "⏰ {label}" message "It is now {human_time}"\''
    )
    pid = _schedule(notify_cmd, target)

    msg = f'Alarm set: "{label}" at {human_date} (pid {pid})'

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

    finish = datetime.now() + timedelta(minutes=minutes)
    finish_str = finish.strftime("%H:%M")

    notify_cmd = (
        f'osascript -e \'display notification "{minutes} min elapsed" with title "⏱ {label}" sound name "Glass"\'; '
        f'for i in 1 2 3 4 5; do afplay /System/Library/Sounds/Glass.aiff; done; '
        f'osascript -e \'display alert "⏱ {label}" message "{minutes} minute(s) are up!"\''
    )
    pid = _schedule(notify_cmd, finish)

    msg = f'Timer started: "{label}" — {minutes} min, finishes ~{finish_str} (pid {pid})'
    return msg


def handle_play_sound(seconds: float, sound: str = "Glass") -> str:
    """Play a macOS system sound repeatedly for N seconds.

    Args:
        seconds: Duration in seconds to keep playing the sound.
        sound:   System sound name (default: Glass). Options: Glass, Ping, Purr, Basso,
                 Blow, Bottle, Frog, Funk, Hero, Morse, Pop, Sosumi, Submarine, Tink.
    """
    sound_path = f"/System/Library/Sounds/{sound}.aiff"
    dur = int(round(seconds))
    cmd = f"end=$(($(date +%s)+{dur})); while [ $(date +%s) -lt $end ]; do afplay {sound_path}; done"
    _spawn_detached(cmd)
    return f"Playing {sound} for {seconds}s"
