"""
contacts.py
-----------
MCP tool handler for contact search via Contacts.app (AppleScript), ported
from local-mac-tool/Sources/LocalMacMCP/ContactsTool.swift — vault-markdown
lookup dropped per user request; Contacts.app is now the sole source.
"""
from __future__ import annotations

import subprocess

from local_process import LocalProcessError, run_osascript

#: AppleScript's "Application isn't running." Raw, it says nothing about which
#: application or what to do; the caller only sees a number (task:ad9cae1c).
_APP_NOT_RUNNING = "-600"


def _launch_contacts() -> None:
    """Start Contacts.app in the background, without bringing it to the front."""
    subprocess.run(["open", "-ga", "Contacts"], capture_output=True, timeout=10, check=False)


def handle_search(name: str, include_email: bool = False) -> str:
    """Search contacts by name via Contacts.app."""
    if not name:
        raise ValueError("Missing required argument: name")

    escaped = name.replace('"', '\\"')
    script = f'''
        tell application "Contacts"
            set results to every person whose name contains "{escaped}"
            set output to ""
            repeat with p in results
                set pName to name of p
                repeat with ph in phones of p
                    set output to output & pName & " | " & (label of ph) & ": " & (value of ph) & "\\n"
                end repeat
            end repeat
            return output
        end tell
        '''
    try:
        result = run_osascript(script)
    except LocalProcessError as exc:
        if _APP_NOT_RUNNING not in str(exc):
            raise
        # Contacts.app was closed. Launching it is the entire fix, so do it and
        # retry once rather than handing back a bare -600 the caller has to
        # decode. Only this one error is retried — anything else is a real
        # failure and must surface unchanged.
        _launch_contacts()
        try:
            result = run_osascript(script)
        except LocalProcessError as retry_exc:
            raise LocalProcessError(
                "Contacts.app is not running and could not be started, so contacts "
                f"cannot be searched. Open Contacts.app and retry. ({retry_exc})"
            ) from retry_exc

    return result if result else f"No contacts found matching '{name}'."
