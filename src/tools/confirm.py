"""confirm__send MCP tool — records explicit user confirmation before imessage__send."""
from __future__ import annotations


def handle_send(session_id: str, prompt_id: str, recipient: str, message: str) -> dict:
    """Record that the user has explicitly confirmed sending a message.

    Call this ONLY after showing the user the recipient name + number and
    receiving explicit confirmation (e.g. "yes", "go ahead"). Do NOT call
    this proactively — the gate will block imessage__send until this runs.

    Args:
        session_id: Current Claude Code session ID.
        prompt_id:  Current prompt_id from state (ties confirmation to this turn).
        recipient:  Phone number that will be passed to imessage__send.
        message:    Message text that will be sent.

    Returns a confirmation receipt that the gate checks before allowing imessage__send.
    """
    return {
        "confirmed": True,
        "recipient": recipient,
        "message": message,
        "token": prompt_id,
    }
