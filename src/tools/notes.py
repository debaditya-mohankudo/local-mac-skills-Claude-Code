"""Notes tools — AppleScript bridge for Apple Notes."""
import subprocess


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


def handle_list(folder: str = "", limit: int = 20) -> list:
    """List Apple Notes. folder: folder name to filter (default: all). limit: max results."""
    escaped_folder = folder.replace('"', '\\"')
    if folder:
        source = f'notes of folder "{escaped_folder}"'
    else:
        source = "notes"
    script = f"""
tell application "Notes"
    set output to ""
    set cnt to 0
    repeat with n in {source}
        if cnt >= {limit} then exit repeat
        set nid to id of n
        set ntitle to name of n
        set nmod to (modification date of n) as string
        set ncreated to (creation date of n) as string
        set nbody to body of n
        set snippet to ""
        if length of nbody > 100 then
            set snippet to (text 1 thru 100 of nbody) & "..."
        else
            set snippet to nbody
        end if
        set output to output & nid & "|||" & ntitle & "|||" & nmod & "|||" & ncreated & "|||" & snippet & "\\n"
        set cnt to cnt + 1
    end repeat
    return output
end tell
"""
    raw = _run_applescript(script)
    results = []
    for line in raw.splitlines():
        cols = line.split("|||")
        if len(cols) >= 4:
            results.append({
                "id": cols[0],
                "title": cols[1],
                "modified": cols[2],
                "created": cols[3],
                "snippet": cols[4] if len(cols) > 4 else "",
            })
    return results or "No notes found."


def handle_read(id: str) -> dict:
    """Read full content of a note by its AppleScript id or title."""
    escaped = id.replace('"', '\\"')
    # Try by id first, fall back to name search
    script = f"""
tell application "Notes"
    set found to missing value
    try
        set found to note id "{escaped}"
    end try
    if found is missing value then
        repeat with n in notes
            if name of n is "{escaped}" then
                set found to n
                exit repeat
            end if
        end repeat
    end if
    if found is missing value then return ""
    set ntitle to name of found
    set nmod to (modification date of found) as string
    set ncreated to (creation date of found) as string
    set nbody to body of found
    set nid to id of found
    return nid & "|||" & ntitle & "|||" & nmod & "|||" & ncreated & "|||" & nbody
end tell
"""
    raw = _run_applescript(script)
    if not raw:
        return {"error": f"Note not found: {id}"}
    cols = raw.split("|||", 4)
    if len(cols) < 5:
        return {"error": "Unexpected response format"}
    return {
        "id": cols[0],
        "title": cols[1],
        "modified": cols[2],
        "created": cols[3],
        "body": cols[4],
    }


def handle_folders() -> list:
    """List all Apple Notes folders with note counts."""
    script = """
tell application "Notes"
    set output to ""
    repeat with f in folders
        set fname to name of f
        set fcnt to count of notes of f
        set output to output & fname & "|||" & (fcnt as string) & "\\n"
    end repeat
    return output
end tell
"""
    raw = _run_applescript(script)
    results = []
    for line in raw.splitlines():
        cols = line.split("|||")
        if cols:
            results.append({
                "name": cols[0],
                "noteCount": cols[1] if len(cols) > 1 else "0",
            })
    return results or "No folders found."


def handle_add(title: str, body: str = "", folder: str = "Notes") -> dict:
    """Create a new Apple Note. folder: target folder name (default: Notes)."""
    escaped_title = title.replace('"', '\\"').replace("\\n", "\n")
    escaped_body = body.replace("\\", "\\\\").replace('"', '\\"')
    escaped_folder = folder.replace('"', '\\"')
    script = f"""
tell application "Notes"
    set targetFolder to missing value
    repeat with f in folders
        if name of f is "{escaped_folder}" then
            set targetFolder to f
            exit repeat
        end if
    end repeat
    if targetFolder is missing value then
        set targetFolder to make new folder with properties {{name:"{escaped_folder}"}}
    end if
    set n to make new note at targetFolder with properties {{name:"{escaped_title}", body:"{escaped_body}"}}
    return (id of n) & "|||" & (name of n)
end tell
"""
    raw = _run_applescript(script)
    cols = raw.split("|||", 1)
    return {
        "status": "created",
        "id": cols[0] if cols else "",
        "title": cols[1] if len(cols) > 1 else title,
        "folder": folder,
    }


def handle_delete(title: str, folder: str = "Notes") -> dict:
    """Delete an Apple Note by title. folder: folder to search in (default: Notes)."""
    escaped_title = title.replace('"', '\\"')
    escaped_folder = folder.replace('"', '\\"')
    script = f"""
tell application "Notes"
    set deleted to 0
    set targetFolder to missing value
    repeat with f in folders
        if name of f is "{escaped_folder}" then
            set targetFolder to f
            exit repeat
        end if
    end repeat
    if targetFolder is missing value then return "0"
    set toDelete to (notes of targetFolder whose name is "{escaped_title}")
    set deleted to count of toDelete
    repeat with n in toDelete
        delete n
    end repeat
    return deleted as string
end tell
"""
    raw = _run_applescript(script)
    count = int(raw.strip()) if raw.strip().isdigit() else 0
    if count == 0:
        return {"status": "not_found", "title": title, "folder": folder}
    return {"status": "deleted", "count": count, "title": title, "folder": folder}
