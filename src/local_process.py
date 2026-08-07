"""
local_process.py
-----------------
Subprocess bridge for domain implementations that no longer shell out to the
Swift CLI binary — replaces src/swift_bridge.py's call_swift() contract.

Deliberately not AppleScript-specific: some domains (vpn, podcasts, sound)
don't use AppleScript at all in their best implementation (scutil, sqlite3,
CoreAudio respectively) — this module is a generic "run a subprocess, raise
on failure" helper that osascript-based and non-osascript-based tools/*.py
modules both call.
"""
from __future__ import annotations

import re
import subprocess


class LocalProcessError(RuntimeError):
    pass


#: AppleScript's "Application isn't running."
_APP_NOT_RUNNING = "-600"

#: The app a script drives, e.g. `tell application "Contacts"`.
_TELL_APP_RE = re.compile(r'tell application "([^"]+)"')


def run_osascript(script: str, timeout: int = 30) -> str:
    """Run an inline AppleScript snippet via osascript, return stdout stripped.

    Translates the one AppleScript failure that is both common and entirely
    actionable — error -600, the target app is not running — into a message
    that names the app and the fix. Raw, that error reaches the caller as a
    bare number explaining neither (task:ad9cae1c).

    Done here rather than in each tool because every osascript-backed domain
    drives an app that can be closed; nine modules would otherwise carry nine
    copies of the same translation, and seven of them carried none at all.
    """
    try:
        return run_shell(["osascript", "-e", script], timeout=timeout)
    except LocalProcessError as exc:
        if _APP_NOT_RUNNING not in str(exc):
            raise
        match = _TELL_APP_RE.search(script)
        app = match.group(1) if match else "The target application"
        raise LocalProcessError(
            f"{app} is not running, so this command cannot run. "
            f"Open {app} and retry. (osascript error -600)"
        ) from exc


def run_shell(args: list[str], timeout: int = 30) -> str:
    """Run a shell command, return stdout stripped. Raises LocalProcessError on failure."""
    result = subprocess.run(args, capture_output=True, timeout=timeout)
    if result.returncode != 0:
        stderr = result.stderr.decode(errors="replace").strip()
        raise LocalProcessError(stderr or f"{args[0]} exited {result.returncode}")
    return result.stdout.decode(errors="replace").strip()
