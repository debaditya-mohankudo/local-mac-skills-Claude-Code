#!/usr/bin/env bash
# Save a summarized context snapshot to vault before autocompact (PreCompact hook)
# Hook passes JSON via stdin: { session_id, transcript_path, cwd, hook_event_name }

set -euo pipefail

DATE=$(date +"%Y-%m-%d")
TIME=$(date +"%H:%M:%S")
VAULT="${VAULT_PATH:-$HOME/workspace/claude_documents}"

mkdir -p "$VAULT/Context"

# Parse hook JSON from stdin
HOOK_JSON=$(cat)
SESSION_ID=$(echo "$HOOK_JSON" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('session_id','unknown'))" 2>/dev/null || echo "unknown")
TRANSCRIPT=$(echo "$HOOK_JSON" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('transcript_path','unknown'))" 2>/dev/null || echo "unknown")
CWD=$(echo "$HOOK_JSON" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('cwd','unknown'))" 2>/dev/null || echo "unknown")

DAILY_NOTE="$VAULT/Daily/Context_${DATE}.md"
TIMESTAMP_NOTE="$VAULT/Context/${DATE}_${TIME}.md"

# --- Summarize transcript with apfel (on-device, no API call) ---
SUMMARY=""
if [ -f "$TRANSCRIPT" ] && command -v apfel &>/dev/null; then
    SUMMARY=$(apfel -f "$TRANSCRIPT" \
        --quiet \
        --no-color \
        --max-tokens 600 \
        "Summarize this Claude Code session transcript concisely. Output plain markdown only — no preamble. Include: 1) What was worked on (bullet points), 2) Key decisions made, 3) Files changed, 4) Any open issues or next steps. Be specific, not generic." \
        2>/dev/null || echo "")
fi

if [ -z "$SUMMARY" ]; then
    SUMMARY="> apfel summary unavailable — transcript missing or apfel not reachable."
fi

# --- Write to Daily/Context_DATE.md (append if exists) ---
if [ -f "$DAILY_NOTE" ]; then
    # Append new session block
    cat >> "$DAILY_NOTE" << MARKDOWN


---

## Snapshot — ${TIME}

| Field | Value |
|---|---|
| Session ID | ${SESSION_ID} |
| Working dir | ${CWD} |

${SUMMARY}
MARKDOWN
else
    # First snapshot of the day
    cat > "$DAILY_NOTE" << MARKDOWN
---
date: ${DATE}
tags: [context, session-summary]
---

[[claude_for_mac_local|context]]
# Context Snapshots — ${DATE}

## Snapshot — ${TIME}

| Field | Value |
|---|---|
| Session ID | ${SESSION_ID} |
| Working dir | ${CWD} |

${SUMMARY}

[[claude_for_mac_local|context]]
MARKDOWN
fi

# --- Also write raw metadata to Context/ for reference ---
cat > "$TIMESTAMP_NOTE" << MARKDOWN
---
date: ${DATE}
time: ${TIME}
session_id: ${SESSION_ID}
tags: [context, autocompact]
---

# Context Snapshot — ${DATE} ${TIME}

| Field | Value |
|---|---|
| Session ID | ${SESSION_ID} |
| Working dir | ${CWD} |
| Transcript | ${TRANSCRIPT} |

See [[Context_${DATE}]] for the summarized daily log.
MARKDOWN

echo "Saved: Daily/Context_${DATE}.md (summary) + Context/${DATE}_${TIME}.md (metadata)"
