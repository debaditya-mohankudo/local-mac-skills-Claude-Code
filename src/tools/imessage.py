"""
imessage.py
-----------
MCP tool handlers for iMessage, ported from
local-mac-tool/Sources/LocalMacMCP/iMessageTool.swift.

send: AppleScript via `tell application "Messages"` — the Swift tool already
just shelled out to osascript itself for this, direct 1:1 port.

read: direct sqlite3 read against ~/Library/Messages/chat.db (same pattern
as portfolio.py) — Swift used the same DB, not AppleScript, since
Messages.app's AppleScript dictionary doesn't expose message history at all.
attributedBody (used when message.text is empty, e.g. tapbacks/rich text)
is decoded via the same length-prefixed-UTF8 byte-scan heuristic Swift's
NSUnarchiver fallback used — Python has no lightweight NSUnarchiver
equivalent, and this heuristic is what Swift actually falls back to for a
lot of real messages anyway (legacy typedstream archives NSUnarchiver often
can't decode on modern macOS).
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from local_process import run_osascript

_CHAT_DB = Path.home() / "Library" / "Messages" / "chat.db"

# Apple's Core Data / NSDate epoch offset (seconds from Unix epoch to 2001-01-01)
_APPLE_EPOCH_OFFSET = 978307200


def handle_send(recipient: str, message: str, delay_seconds: int = 0) -> str:
    """Send an iMessage to a recipient (phone number or email). Usually called after contacts__search."""
    if not recipient:
        raise ValueError("Missing required argument: recipient (phone number or email)")
    if not message:
        raise ValueError("Missing required argument: message")

    escaped_recipient = recipient.replace('"', '\\"')
    escaped_message = message.replace('"', '\\"').replace("\n", "\\n")

    delay_clause = f"delay {delay_seconds}\n" if delay_seconds > 0 else ""
    script = f'''
        {delay_clause}tell application "Messages"
            activate
            set targetBuddy to "{escaped_recipient}"
            set targetService to 1st service whose service type = iMessage
            send "{escaped_message}" to buddy targetBuddy of targetService
        end tell
        '''
    # osascript itself blocks for `delay_seconds` before sending — the
    # subprocess timeout must exceed that, or run_shell kills it prematurely.
    run_osascript(script, timeout=max(30, delay_seconds + 15))
    suffix = f" (scheduled for {delay_seconds}s from now)" if delay_seconds > 0 else ""
    return f"Message sent to {recipient}{suffix}"


def _extract_text_from_attributed_body(data: bytes) -> str:
    """Scan a legacy NSAttributedString typedstream archive for a
    length-prefixed UTF-8 string at the 0x01 0x2b marker.

    NSArchiver's packed-integer length encoding: a length byte < 0x81 is the
    literal length; 0x81 signals an extended length in the next 2 bytes
    (little-endian uint16) — needed for any text over 127 bytes, which is
    most real SMS/iMessage content."""
    for i in range(len(data) - 2):
        if data[i] == 0x01 and data[i + 1] == 0x2B:
            length_byte = data[i + 2]
            if length_byte == 0x81:
                if i + 4 >= len(data):
                    continue
                length = data[i + 3] | (data[i + 4] << 8)
                start = i + 5
            else:
                length = length_byte
                start = i + 3
            end = start + length
            if end <= len(data):
                try:
                    return data[start:end].decode("utf-8")
                except UnicodeDecodeError:
                    return ""
    return ""


def handle_read(limit: int = 10, direction: str = "received") -> dict | str:
    """Read recent iMessages. direction: received | sent | all"""
    if direction == "sent":
        direction_clause = "AND message.is_from_me = 1"
    elif direction == "all":
        direction_clause = ""
    else:
        direction_clause = "AND message.is_from_me = 0"

    sql = f"""
        SELECT datetime(message.date/1000000000 + {_APPLE_EPOCH_OFFSET}, 'unixepoch', 'localtime') as date,
               CASE WHEN message.is_from_me = 1 THEN 'me' ELSE COALESCE(handle.id, '') END as sender,
               message.is_from_me,
               COALESCE(message.text, '') as text,
               message.attributedBody
        FROM message
        LEFT JOIN handle ON message.handle_id = handle.ROWID
        WHERE (handle.id IS NOT NULL OR message.is_from_me = 1)
          {direction_clause}
        ORDER BY message.date DESC
        LIMIT ?
        """

    con = sqlite3.connect(f"file:{_CHAT_DB}?mode=ro", uri=True)
    try:
        rows = con.execute(sql, (limit,)).fetchall()
    finally:
        con.close()

    if not rows:
        return "No messages found."

    messages = []
    for date, sender, is_from_me, text, attributed_body in rows:
        if not text and attributed_body:
            text = _extract_text_from_attributed_body(attributed_body)
        messages.append({
            "date": date,
            "from": sender,
            "text": text,
            "direction": "sent" if is_from_me == 1 else "received",
        })
    return messages
