"""Mail tools — AppleScript bridge, multi-account via UUID dispatch.

Account identities are configuration, not code. Each account needs an Apple
Mail account UUID and the address it belongs to, both of which are personal to
whoever runs this, so they are read from the environment rather than committed.

Set MAIL_ACCOUNTS to a comma-separated list of `key:uuid:address` triples:

    MAIL_ACCOUNTS=gmail:1AC8B81B-...:you@example.com,icloud:5DEB1E45-...:you2@example.com

Find a UUID in Mail.app under Settings → Accounts, or in
~/Library/Mail/V*/MailData. Optionally set MAIL_DEFAULT_ACCOUNT (defaults to
the first key listed) and MAIL_LOCAL_MAILBOXES.
"""
import os
import subprocess


def _parse_accounts(raw: str) -> dict[str, tuple[str, str]]:
    """Parse MAIL_ACCOUNTS into {key: (uuid, address)}.

    Malformed entries are skipped rather than raising: a typo in one account
    should not take out the tools for every other account.
    """
    accounts: dict[str, tuple[str, str]] = {}
    for entry in raw.split(","):
        entry = entry.strip()
        if not entry:
            continue
        parts = entry.split(":")
        if len(parts) != 3:
            continue
        key, uuid, address = (p.strip() for p in parts)
        if key and uuid and address:
            accounts[key] = (uuid, address)
    return accounts


# Apple Mail account UUIDs — stable identifiers independent of display name
ACCOUNTS = _parse_accounts(os.environ.get("MAIL_ACCOUNTS", ""))
# "local" = On My Mac mailboxes — no UUID, accessed directly by mailbox name

DEFAULT_ACCOUNT = os.environ.get("MAIL_DEFAULT_ACCOUNT") or next(iter(ACCOUNTS), "")
LOCAL_ACCOUNT = "local"
LOCAL_LABEL = "On My Mac"

# On My Mac mailboxes — set MAIL_LOCAL_MAILBOXES to a comma-separated list.
LOCAL_MAILBOXES = [
    m.strip()
    for m in os.environ.get("MAIL_LOCAL_MAILBOXES", "").split(",")
    if m.strip()
]


def _resolve(account: str) -> tuple[str, str]:
    """Return (uuid, email) for the given account key.

    Falls back to DEFAULT_ACCOUNT for an unknown key. Returns ('', 'On My Mac')
    for account='local' — caller must use local mailbox AppleScript.
    """
    key = account.lower().strip()
    if key == LOCAL_ACCOUNT:
        return ("", LOCAL_LABEL)
    if key not in ACCOUNTS:
        key = DEFAULT_ACCOUNT
    if key not in ACCOUNTS:
        raise RuntimeError(
            "No mail accounts configured. Set MAIL_ACCOUNTS to a comma-separated "
            "list of key:uuid:address triples — see this module's docstring and "
            ".env.example."
        )
    return ACCOUNTS[key]


def _run_applescript(script: str) -> str:
    result = subprocess.run(
        ["/usr/bin/osascript", "-e", script],
        capture_output=True,
        timeout=60,
    )
    if result.returncode != 0:
        err = result.stderr.decode(errors="replace").strip()
        raise RuntimeError(err)
    return result.stdout.decode(errors="replace").strip()


def _parse_lines(raw: str, email: str) -> list[dict]:
    results = []
    for line in raw.splitlines():
        cols = line.split("|||")
        if len(cols) >= 4:
            results.append({
                "message_id": cols[0],
                "date": cols[1],
                "sender": cols[2],
                "subject": cols[3],
                "account": email,
            })
    return results


def handle_read(limit: int = 20, folder: str = "INBOX", account: str = DEFAULT_ACCOUNT) -> dict:
    """Read recent emails from Apple Mail. account: 'gmail' (default), 'icloud', 'exchange', 'local' (On My Mac)."""
    uuid, email = _resolve(account)
    if uuid:
        mb_ref = f'mailbox "{folder}" of account id "{uuid}"'
    else:
        mb_ref = f'mailbox "{folder}"'
    script = f"""
tell application "Mail"
    set output to ""
    set cnt to 0
    set mb to {mb_ref}
    repeat with m in (messages of mb)
        if cnt >= {limit} then exit repeat
        set output to output & (id of m) & "|||" & ((date received of m) as string) & "|||" & (sender of m) & "|||" & (subject of m) & "\\n"
        set cnt to cnt + 1
    end repeat
    return output
end tell
"""
    raw = _run_applescript(script)
    return _parse_lines(raw, email) or "No emails found."


def handle_search(query: str, folder: str = "", limit: int = 50, account: str = DEFAULT_ACCOUNT) -> dict:
    """Search emails by subject or sender. account: 'gmail' (default), 'icloud', 'exchange'."""
    uuid, email = _resolve(account)
    escaped_query = query.replace('"', '\\"')
    mailbox_block = "every mailbox of acc" if not folder else f'{{mailbox "{folder}" of acc}}'
    script = f"""
tell application "Mail"
    set output to ""
    set cnt to 0
    set acc to account id "{uuid}"
    repeat with mb in {mailbox_block}
        try
            repeat with m in (messages of mb)
                if cnt >= {limit} then exit repeat
                set msgSubject to subject of m
                set msgSender to sender of m
                if msgSubject contains "{escaped_query}" or msgSender contains "{escaped_query}" then
                    set output to output & (id of m) & "|||" & ((date received of m) as string) & "|||" & msgSender & "|||" & msgSubject & "\\n"
                    set cnt to cnt + 1
                end if
            end repeat
        end try
        if cnt >= {limit} then exit repeat
    end repeat
    return output
end tell
"""
    raw = _run_applescript(script)
    return _parse_lines(raw, email) or f"No emails found matching '{query}'."


def handle_delete(message_ids: list[int], folder: str = "INBOX", account: str = DEFAULT_ACCOUNT) -> dict:
    """Delete emails by message_id. Moves to Trash. account: 'gmail' (default), 'icloud', 'exchange', 'local' (On My Mac)."""
    if not message_ids:
        raise ValueError("message_ids must be a non-empty list")
    uuid, email = _resolve(account)
    id_list = ", ".join(str(i) for i in message_ids)
    escaped_folder = folder.replace('"', '\\"')
    mb_ref = f'mailbox "{escaped_folder}" of account id "{uuid}"' if uuid else f'mailbox "{escaped_folder}"'
    # Report the OUTCOME PER ID, not a bare count. The previous version wrapped
    # each deletion in a bare `try ... end try`, so failures were swallowed and
    # the count reflected successes only — while the response echoed back every
    # id it was given. A caller handed 22 ids and told "18" had no way to learn
    # which 4 survived except by re-reading the mailbox (task:ad9cae1c).
    script = f"""
tell application "Mail"
    set targetIds to {{{id_list}}}
    set mbox to {mb_ref}
    set outcomes to ""
    repeat with tid in targetIds
        set deletedThis to 0
        try
            set toDelete to (messages of mbox whose id is tid)
            repeat with m in toDelete
                delete m
                set deletedThis to deletedThis + 1
            end repeat
            if deletedThis is 0 then
                set outcomes to outcomes & tid & "=notfound" & linefeed
            else
                set outcomes to outcomes & tid & "=deleted" & linefeed
            end if
        on error errMsg
            set outcomes to outcomes & tid & "=error:" & errMsg & linefeed
        end try
    end repeat
    return outcomes
end tell
"""
    output = _run_applescript(script)

    deleted: list[int] = []
    failed: list[dict] = []
    seen: set[int] = set()
    for line in output.splitlines():
        if "=" not in line:
            continue
        raw_id, _, outcome = line.partition("=")
        try:
            mid = int(raw_id.strip())
        except ValueError:
            continue
        seen.add(mid)
        if outcome == "deleted":
            deleted.append(mid)
        else:
            failed.append({"message_id": mid, "reason": outcome})

    # An id AppleScript never reported on is a failure too — silence is not
    # success, and it is exactly what made the original defect invisible.
    for mid in message_ids:
        if mid not in seen:
            failed.append({"message_id": mid, "reason": "no result returned"})

    if not failed:
        status = "deleted"
    elif deleted:
        status = "partial"
    else:
        status = "failed"

    return {
        "status": status,
        "requested": len(message_ids),
        "deleted_count": len(deleted),
        "deleted": deleted,
        "failed": failed,
        "account": email,
    }


def handle_list_mailboxes(account: str = DEFAULT_ACCOUNT) -> dict:
    """List mailboxes for an account. account: 'gmail' (default), 'icloud', 'exchange', 'local' (On My Mac)."""
    uuid, email = _resolve(account)
    if uuid:
        container = f'every mailbox of account id "{uuid}"'
    else:
        container = "every mailbox"
    script = f"""
tell application "Mail"
    set output to ""
    repeat with mb in {container}
        set output to output & (name of mb) & "\\n"
    end repeat
    return output
end tell
"""
    raw = _run_applescript(script)
    return [{"mailbox": line, "account": email} for line in raw.splitlines() if line] or "No mailboxes found."


def handle_list_drafts(limit: int = 20, account: str = DEFAULT_ACCOUNT) -> dict:
    """List draft emails from Apple Mail. account: 'gmail' (default), 'icloud', 'exchange', 'local' (On My Mac)."""
    uuid, email = _resolve(account)
    if uuid:
        acc_ref = f'account id "{uuid}"'
        mb_lookup = f"every mailbox of acc"
        acc_block = f"set acc to {acc_ref}\n    "
    else:
        acc_block = ""
        mb_lookup = "every mailbox"
    script = f"""
tell application "Mail"
    set output to ""
    set cnt to 0
    {acc_block}set draftBox to missing value
    repeat with mb in {mb_lookup}
        if name of mb is "Drafts" then
            set draftBox to mb
            exit repeat
        end if
    end repeat
    if draftBox is missing value then return ""
    repeat with m in (messages of draftBox)
        if cnt >= {limit} then exit repeat
        set msgSubject to subject of m
        if msgSubject is missing value then set msgSubject to "(no subject)"
        set output to output & (id of m) & "|||" & ((date received of m) as string) & "|||" & (sender of m) & "|||" & msgSubject & "\\n"
        set cnt to cnt + 1
    end repeat
    return output
end tell
"""
    raw = _run_applescript(script)
    return _parse_lines(raw, email) or "No drafts found."


def handle_get(message_id: int, account: str = DEFAULT_ACCOUNT) -> dict:
    """Read full content of a specific email by message_id. account: 'gmail' (default), 'icloud', 'exchange'."""
    uuid, email = _resolve(account)
    script = f"""
tell application "Mail"
    set acc to account id "{uuid}"
    repeat with mb in every mailbox of acc
        try
            set msgs to (messages of mb whose id is {message_id})
            if length of msgs > 0 then
                set m to item 1 of msgs
                set msgContent to content of m
                if msgContent is missing value then set msgContent to ""
                return (id of m) & "|||" & ((date received of m) as string) & "|||" & (sender of m) & "|||" & (subject of m) & "|||" & msgContent
            end if
        end try
    end repeat
    return ""
end tell
"""
    raw = _run_applescript(script)
    if not raw:
        return {"error": f"Message {message_id} not found"}
    cols = raw.split("|||", 4)
    if len(cols) < 5:
        return {"error": "Unexpected response format"}
    return {
        "message_id": cols[0],
        "date": cols[1],
        "sender": cols[2],
        "subject": cols[3],
        "body": cols[4].strip(),
        "account": email,
    }


def handle_add_local_mailbox(name: str) -> dict:
    """Create a new On My Mac mailbox in Mail.app and register it in LOCAL_MAILBOXES.

    name: mailbox name to create (e.g. 'Finance', 'Newsletters')
    """
    escaped = name.replace('"', '\\"')
    script = f"""
tell application "Mail"
    set existing to every mailbox whose name is "{escaped}"
    if length of existing > 0 then
        return "exists"
    end if
    make new mailbox with properties {{name:"{escaped}"}}
    return "created"
end tell
"""
    result = _run_applescript(script)
    status = "already_exists" if result.strip() == "exists" else "created"

    if status == "created" and name not in LOCAL_MAILBOXES:
        LOCAL_MAILBOXES.append(name)

    return {"status": status, "mailbox": name, "local_mailboxes": LOCAL_MAILBOXES}


def handle_move(
    message_ids: list[int],
    dest_mailbox: str,
    src_account: str = DEFAULT_ACCOUNT,
    src_folder: str = "INBOX",
) -> dict:
    """Move emails from any internet account mailbox to an On My Mac local mailbox.

    src_account: 'gmail' (default), 'icloud', 'exchange'
    src_folder:  source mailbox name, default 'INBOX'
    dest_mailbox: name of the On My Mac target mailbox (e.g. 'Useful', 'Jiras')
    message_ids: list of integer message ids to move
    """
    if not message_ids:
        raise ValueError("message_ids must be a non-empty list")
    uuid, email = _resolve(src_account)
    if not uuid:
        raise ValueError("src_account must be an internet account (gmail/icloud/exchange), not local")
    escaped_src = src_folder.replace('"', '\\"')
    escaped_dest = dest_mailbox.replace('"', '\\"')
    id_list = ", ".join(str(i) for i in message_ids)
    script = f"""
tell application "Mail"
    set srcMB to mailbox "{escaped_src}" of account id "{uuid}"
    set dstMB to mailbox "{escaped_dest}"
    set targetIds to {{{id_list}}}
    set movedCount to 0
    set failCount to 0
    repeat with tid in targetIds
        try
            set msgs to (messages of srcMB whose id is tid)
            repeat with m in msgs
                move m to dstMB
                set movedCount to movedCount + 1
            end repeat
        on error
            set failCount to failCount + 1
        end try
    end repeat
    return (movedCount as string) & "," & (failCount as string)
end tell
"""
    raw = _run_applescript(script)
    parts = raw.split(",")
    moved = int(parts[0].strip()) if parts else 0
    failed = int(parts[1].strip()) if len(parts) > 1 else 0
    return {
        "status": "done",
        "moved": moved,
        "failed": failed,
        "src_account": email,
        "src_folder": src_folder,
        "dest_mailbox": dest_mailbox,
    }


def handle_compose(to: str, subject: str = "", body: str = "") -> dict:
    """Open a pre-filled compose window in Mail.app. Does not send — user reviews and sends manually."""
    escaped_to = to.replace('"', '\\"')
    escaped_subject = subject.replace('"', '\\"')
    escaped_body = body.replace("\\", "\\\\").replace('"', '\\"')
    script = f"""
tell application "Mail"
    activate
    set newMsg to make new outgoing message with properties {{subject:"{escaped_subject}", content:"{escaped_body}", visible:true}}
    tell newMsg
        make new to recipient with properties {{address:"{escaped_to}"}}
    end tell
end tell
"""
    _run_applescript(script)
    return {"status": "composed", "to": to, "subject": subject}

