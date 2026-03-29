#!/bin/bash

set -e

# iMessage Command Executor
# Polls for commands from a trusted contact (phone or email), asks for confirmation, and executes them
# State is tracked in ~/.imessage-commands-state to handle multi-step confirmation flow

STATE_FILE="$HOME/.imessage-commands-state"
TOOLS_DIR="$HOME/workspace/claude_for_mac_local/tools"
CONFIRMATION_TIMEOUT=300  # 5 minutes
LOG_FILE="$HOME/.imessage-commands.log"

# Determine contact from argument or .env
TRUSTED_CONTACT="$1"

if [[ -z "$TRUSTED_CONTACT" ]]; then
    # No argument provided, load from .env
    if [[ ! -f .env ]]; then
        echo "$(date) [ERROR] .env not found in current directory" >> "$LOG_FILE"
        exit 1
    fi

    source .env
    if [[ -z "$PHONE_NUMBER" ]]; then
        echo "$(date) [ERROR] PHONE_NUMBER not set in .env and no contact argument provided" >> "$LOG_FILE"
        exit 1
    fi
    TRUSTED_CONTACT="$PHONE_NUMBER"
fi

# Initialize state file if needed
if [[ ! -f "$STATE_FILE" ]]; then
    echo "{\"last_checked\": 0, \"pending\": {}}" > "$STATE_FILE"
fi

# Helper: log with timestamp
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $1" >> "$LOG_FILE"
}

# Helper: read state JSON
read_state() {
    cat "$STATE_FILE"
}

# Helper: write state JSON
write_state() {
    echo "$1" > "$STATE_FILE"
}

# Helper: send message with word wrapping for iMessage (160 char chunks)
send_message_wrapped() {
    local msg="$1"
    local recipient="$TRUSTED_CONTACT"

    # Split by 150 char chunks to be safe with iMessage
    while [[ ${#msg} -gt 150 ]]; do
        local chunk="${msg:0:150}"
        # Try to break at last space
        local last_space=${chunk%% *}
        if [[ ${#last_space} -gt 50 ]]; then
            chunk="$last_space"
        fi

        bash "$TOOLS_DIR/imessage_send.sh" "$recipient" "$chunk" 2>/dev/null || log "[WARN] Failed to send message chunk"
        msg="${msg:${#chunk}}"
        sleep 1
    done

    # Send remainder
    if [[ -n "$msg" ]]; then
        bash "$TOOLS_DIR/imessage_send.sh" "$recipient" "$msg" 2>/dev/null || log "[WARN] Failed to send final message"
    fi
}

# Step 1: Check for new messages from TRUSTED_CONTACT
log "[INFO] Checking for messages from $TRUSTED_CONTACT"

# Get recent messages (last 100 lines from imessage_check.sh output)
messages=$(bash "$TOOLS_DIR/imessage_check.sh" 2>/dev/null | tail -100 || echo "")

if [[ -z "$messages" ]]; then
    log "[INFO] No messages found"
    exit 0
fi

# Parse messages for commands from PHONE_NUMBER (format: "PHONE | MSG | TIMESTAMP")
# Filter to messages from our trusted number only
new_commands=$(echo "$messages" | grep "| " | while IFS='|' read -r phone msg timestamp; do
    phone=$(echo "$phone" | xargs)  # trim
    msg=$(echo "$msg" | xargs)       # trim
    timestamp=$(echo "$timestamp" | xargs)

    if [[ "$phone" == "$TRUSTED_CONTACT" ]]; then
        echo "$timestamp|$msg"
    fi
done)

if [[ -z "$new_commands" ]]; then
    log "[INFO] No new messages from $TRUSTED_CONTACT"
    exit 0
fi

# Step 2: Check pending confirmations and new commands
state=$(read_state)
now=$(date +%s)

# Process each new command
while IFS='|' read -r timestamp cmd; do
    cmd_id="${timestamp}_${cmd:0:20}"  # Simple unique ID

    # Check if this command is already in pending state
    if echo "$state" | grep -q "\"$cmd_id\""; then
        # This command is being tracked—check for confirmation
        pending_entry=$(echo "$state" | grep -o "\"$cmd_id\":[^}]*}")
        confirmed=$(echo "$pending_entry" | grep -o '"confirmed":"[^"]*"' | cut -d'"' -f4)
        asked_at=$(echo "$pending_entry" | grep -o '"asked_at":[0-9]*' | cut -d':' -f2)

        if [[ "$confirmed" == "yes" ]]; then
            # Execute the command
            log "[INFO] Executing confirmed command: $cmd"
            output=$(eval "$cmd" 2>&1 || echo "[ERROR] Command failed: $?")

            if [[ ${#output} -gt 0 ]]; then
                send_message_wrapped "✓ Command executed:\n\n$output"
            else
                send_message_wrapped "✓ Command executed (no output)"
            fi

            # Mark as done (remove from pending)
            state=$(echo "$state" | sed "s/\"$cmd_id\":[^,}]*[,}]//g")
        elif [[ $((now - asked_at)) -gt $CONFIRMATION_TIMEOUT ]]; then
            # Confirmation timeout
            log "[WARN] Confirmation timeout for: $cmd"
            send_message_wrapped "✗ Command timed out (no confirmation): $cmd"
            state=$(echo "$state" | sed "s/\"$cmd_id\":[^,}]*[,}]//g")
        fi
        # else: still waiting for confirmation
    else
        # New command—ask for confirmation
        log "[INFO] New command from $TRUSTED_CONTACT: $cmd"
        send_message_wrapped "Command request:\n\n$cmd\n\nReply 'YES' to confirm"

        # Add to pending state
        new_entry="\"$cmd_id\": {\"cmd\": \"$cmd\", \"asked_at\": $now, \"confirmed\": \"no\"}"
        # Simple JSON merge (assumes well-formed state)
        state=$(echo "$state" | sed "s/\"pending\": {/\"pending\": { $new_entry,/")
    fi
done <<< "$new_commands"

# Step 3: Check for YES/OK/CONFIRM replies
if [[ -n "$messages" ]]; then
    confirmations=$(echo "$messages" | grep -iE "(\byes\b|\bok\b|\bconfirm\b|\bcontinue\b)" | grep "| " | while IFS='|' read -r phone msg timestamp; do
        phone=$(echo "$phone" | xargs)
        msg=$(echo "$msg" | xargs)

        if [[ "$phone" == "$TRUSTED_CONTACT" ]]; then
            echo "$timestamp|$msg"
        fi
    done)

    if [[ -n "$confirmations" ]]; then
        log "[INFO] Confirmation message(s) received"
        # Mark the most recent pending command as confirmed
        most_recent_cmd=$(echo "$new_commands" | tail -1 | cut -d'|' -f2)
        cmd_id="${timestamp}_${most_recent_cmd:0:20}"

        # Update state: mark as confirmed
        state=$(echo "$state" | sed "s/\"$cmd_id\": {/\"$cmd_id\": {\"confirmed\": \"yes\",/")
    fi
fi

write_state "$state"
log "[INFO] Check complete"
