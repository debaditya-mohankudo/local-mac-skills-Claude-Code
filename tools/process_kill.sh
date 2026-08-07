#!/bin/bash
# Usage: process_kill.sh PID [SIGNAL]
# Kills a process by PID. Requires y/N confirmation.
# SIGNAL defaults to TERM (graceful). Use 9 for force kill.
# Guardrail: blocks PIDs < 100 and known critical process names.

PID="$1"
SIGNAL="${2:-TERM}"

if [[ -z "$PID" ]]; then
  echo "Usage: process_kill.sh PID [SIGNAL]"
  exit 1
fi

if ! [[ "$PID" =~ ^[0-9]+$ ]]; then
  echo "ERROR: PID must be a number, got: $PID"
  exit 1
fi

# Block system PIDs
if (( PID < 100 )); then
  echo "BLOCKED: refusing to kill PID $PID — system process range (PID < 100)"
  exit 1
fi

# Get process info before asking
INFO=$(ps -p "$PID" -o pid,user,comm,args 2>/dev/null | tail -1)
if [[ -z "$INFO" ]]; then
  echo "ERROR: no process with PID $PID"
  exit 1
fi

# Block critical system processes by name
PROC_NAME=$(ps -p "$PID" -o comm= 2>/dev/null)
BLOCKED_NAMES="launchd kernel_task WindowServer loginwindow systemd init"
for BLOCKED in $BLOCKED_NAMES; do
  if [[ "$PROC_NAME" == "$BLOCKED" ]]; then
    echo "BLOCKED: refusing to kill '$PROC_NAME' (critical system process)"
    exit 1
  fi
done

echo "Process found:"
echo "$INFO"
echo ""
printf "Kill PID %s with SIG%s? [y/N] " "$PID" "$SIGNAL"
read -r CONFIRM

if [[ "$CONFIRM" != "y" && "$CONFIRM" != "Y" ]]; then
  echo "Aborted."
  exit 0
fi

kill -"$SIGNAL" "$PID" 2>&1
if [[ $? -eq 0 ]]; then
  echo "Sent SIG$SIGNAL to PID $PID"
else
  echo "ERROR: failed to kill PID $PID (permission denied or process gone)"
  exit 1
fi
