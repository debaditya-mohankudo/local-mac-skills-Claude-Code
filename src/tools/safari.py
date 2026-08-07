"""
safari.py
---------
MCP tool handlers for Safari control via AppleScript, ported from
local-mac-tool/Sources/LocalMacMCP/SafariTool.swift — which already just
shelled out to osascript itself, so this is a direct 1:1 port.

Allowlist: reads ~/workspace/claude_for_mac_local/safari_config.sh for a
DISABLE_ALLOWLIST flag and an ALLOWED_URLS array, same as Swift did. That
file does not currently exist in this repo, so — matching Swift's exact
fallback behavior — the allowlist is effectively a no-op until it's created.
"""
from __future__ import annotations

import re
import subprocess
import time
from pathlib import Path
from urllib.parse import urlparse

from local_process import run_osascript, LocalProcessError

_CONFIG_PATH = Path.home() / "workspace" / "claude_for_mac_local" / "safari_config.sh"


def _check_allowed(url: str) -> bool:
    try:
        content = _CONFIG_PATH.read_text()
    except OSError:
        return True

    if re.search(r"(?m)^DISABLE_ALLOWLIST\s*=\s*true", content):
        return True

    list_match = re.search(r"ALLOWED_URLS=\(([^)]+)\)", content)
    if not list_match:
        return False

    allowed = re.findall(r'"([^"]+)"', list_match.group(1))
    if not allowed:
        return True

    host = urlparse(url).hostname
    if not host:
        return False
    bare = host[4:] if host.startswith("www.") else host
    return any(bare == a or bare.endswith("." + a) for a in allowed)


def _escape_js(js: str) -> str:
    return (
        js.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
    )


def handle_open(url: str) -> str:
    """Open a URL in Safari (allowlist enforced)."""
    if not _check_allowed(url):
        raise LocalProcessError(f"BLOCKED: '{url}' is not in the Safari allowlist.")
    out = run_osascript(f'tell application "Safari" to open location "{url}"')
    return out if out else f"Opened: {url}"


def handle_navigate(url: str) -> str:
    """Navigate the current Safari tab to a URL (allowlist enforced)."""
    if not _check_allowed(url):
        raise LocalProcessError(f"BLOCKED: '{url}' is not in the Safari allowlist.")
    out = run_osascript(f'tell application "Safari" to set URL of current tab of front window to "{url}"')
    return out if out else f"Navigated: {url}"


def handle_current_url() -> str:
    """Get the URL of Safari's current tab."""
    return run_osascript('tell application "Safari" to return URL of current tab of front window')


def handle_current_title() -> str:
    """Get the title of Safari's current tab."""
    return run_osascript('tell application "Safari" to return name of current tab of front window')


def handle_list_tabs() -> str:
    """List all open Safari tabs."""
    script = '''
        tell application "Safari"
            set output to ""
            set winIdx to 0
            repeat with w in windows
                set winIdx to winIdx + 1
                set tabIdx to 0
                repeat with t in tabs of w
                    set tabIdx to tabIdx + 1
                    set output to output & "Window " & winIdx & " Tab " & tabIdx & ": " & name of t & " — " & URL of t & "\\n"
                end repeat
            end repeat
            return output
        end tell
        '''
    out = run_osascript(script)
    return out if out else "No tabs open."


def handle_close_tab() -> str:
    """Close Safari's current tab."""
    run_osascript('tell application "Safari" to close current tab of front window')
    return "Closed current tab."


def handle_close_all_tabs() -> str:
    """Close all Safari tabs."""
    run_osascript('tell application "Safari" to close every tab of every window')
    return "Closed all tabs."


def handle_reload() -> str:
    """Reload Safari's current tab."""
    run_osascript('tell application "Safari" to do JavaScript "location.reload()" in current tab of front window')
    return "Reloaded."


def handle_back() -> str:
    """Navigate back in Safari."""
    run_osascript('tell application "Safari" to do JavaScript "history.back()" in current tab of front window')
    return "Went back."


def handle_forward() -> str:
    """Navigate forward in Safari."""
    run_osascript('tell application "Safari" to do JavaScript "history.forward()" in current tab of front window')
    return "Went forward."


def handle_screenshot(outfile: str = None) -> str:
    """Take a screenshot of Safari's current tab."""
    outfile = outfile or str(Path.home() / "Desktop" / "safari_screenshot.png")
    run_osascript('tell application "Safari" to activate')
    time.sleep(0.4)
    result = subprocess.run(["/usr/sbin/screencapture", "-x", "-o", outfile], capture_output=True, timeout=15)
    if result.returncode != 0:
        raise LocalProcessError(f"screencapture failed (exit {result.returncode})")
    return f"Screenshot saved: {outfile}"


def handle_js(js: str) -> str:
    """Execute JavaScript in Safari's current tab."""
    if not js:
        raise ValueError("Missing required argument: js")
    escaped = _escape_js(js)
    return run_osascript(f'tell application "Safari" to do JavaScript "{escaped}" in current tab of front window')


def handle_read(mode: str) -> str:
    """Read page content from Safari. mode: text|html|links|title|selected"""
    modes = {
        "text": "document.body.innerText",
        "html": "document.documentElement.outerHTML",
        "links": "Array.from(document.querySelectorAll('a[href]')).map(a => a.href + ' | ' + a.innerText.trim()).join('\\n')",
        "title": "document.title",
        "selected": "window.getSelection().toString()",
    }
    js = modes.get(mode)
    if js is None:
        raise ValueError(f"Unknown mode: {mode}. Use: text|html|links|title|selected")
    escaped = _escape_js(js)
    return run_osascript(f'tell application "Safari" to do JavaScript "{escaped}" in current tab of front window')
