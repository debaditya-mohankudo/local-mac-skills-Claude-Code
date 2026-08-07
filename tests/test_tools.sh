#!/bin/bash
# Happy path tests for read-only tool scripts.
# Skips write/delete operations and external dependencies (SSH, iMessage).

TOOLS=~/workspace/claude_for_mac_local/tools
PASS=0
FAIL=0

pass() { echo "  PASS  $1"; ((PASS++)); }
fail() { echo "  FAIL  $1 — $2"; ((FAIL++)); }

run() {
  local label="$1"; shift
  local output
  output=$("$@" 2>&1)
  local exit_code=$?
  echo "$output"
  if [[ $exit_code -ne 0 ]]; then
    fail "$label" "exit code $exit_code"
  else
    pass "$label"
  fi
}

run_contains() {
  local label="$1"; local pattern="$2"; shift 2
  local output
  output=$("$@" 2>&1)
  local exit_code=$?
  if [[ $exit_code -ne 0 ]]; then
    fail "$label" "exit code $exit_code"
  elif ! echo "$output" | grep -qi "$pattern"; then
    fail "$label" "output missing '$pattern'"
  else
    pass "$label"
  fi
}

# Expects non-zero exit AND output containing pattern
run_blocked() {
  local label="$1"; local pattern="$2"; shift 2
  local output
  output=$("$@" 2>&1)
  local exit_code=$?
  if [[ $exit_code -eq 0 ]]; then
    fail "$label" "expected block but command succeeded"
  elif ! echo "$output" | grep -qi "$pattern"; then
    fail "$label" "blocked but output missing '$pattern'"
  else
    pass "$label"
  fi
}

echo ""
echo "Storage"
echo "-------"
run_contains "storage_overview: has disk info"   "gigabytes\|GB\|GiB\|used\|avail"   "$TOOLS/storage_overview.sh"
run_contains "storage_detail: has Library"       "Library"                            "$TOOLS/storage_detail.sh"

echo ""
echo "Notes (Claude folder)"
echo "---------------------"
run          "notes_list: exits 0"               "$TOOLS/notes_list.sh"

echo ""
echo "Reminders"
echo "---------"
run          "reminders_list: exits 0"           "$TOOLS/reminders_list.sh"

echo ""
echo "Calendar"
echo "--------"
TODAY=$(date "+%m/%d/%Y")
run          "calendar_list: exits 0"            "$TOOLS/calendar_list_events.sh" "$TODAY 00:00:00" "$TODAY 23:59:59"

echo ""
echo "Mail"
echo "----"
run_contains "mail_list_accounts: has accounts"  "account\|mail\|@"   "$TOOLS/mail_list_accounts.sh"

echo ""
echo "Finder"
echo "------"

# finder_read: exits 0 for all subcommands (Finder always running on macOS)
run          "finder_read: front-path exits 0"    "$TOOLS/finder_read.sh" front-path
run          "finder_read: list-windows exits 0"  "$TOOLS/finder_read.sh" list-windows
run          "finder_read: selection exits 0"     "$TOOLS/finder_read.sh" selection

# finder_read: unknown subcommand is blocked
run_blocked  "finder_read: unknown subcommand"  "Usage"  "$TOOLS/finder_read.sh" bad-command

# finder_control: missing PATH argument → blocked with Usage
run_blocked  "finder_control: open missing path"    "Usage"  "$TOOLS/finder_control.sh" open
run_blocked  "finder_control: reveal missing path"  "Usage"  "$TOOLS/finder_control.sh" reveal
run_blocked  "finder_control: mkdir missing path"   "Usage"  "$TOOLS/finder_control.sh" mkdir
run_blocked  "finder_control: trash missing path"   "Usage"  "$TOOLS/finder_control.sh" trash

# finder_control: non-existent path → error
run_blocked  "finder_control: open bad path"    "ERROR"  "$TOOLS/finder_control.sh" open   "/nonexistent/path/xyz"
run_blocked  "finder_control: reveal bad path"  "ERROR"  "$TOOLS/finder_control.sh" reveal "/nonexistent/path/xyz"

# finder_control: mkdir outside HOME → blocked
run_blocked  "finder_control: mkdir outside HOME"  "ERROR"  "$TOOLS/finder_control.sh" mkdir "/tmp/should-be-blocked"

# finder_control: mkdir inside HOME (round-trip: create + verify + remove)
FINDER_TESTDIR="$HOME/.claude_finder_test_$$"
run          "finder_control: mkdir in HOME"  "$TOOLS/finder_control.sh" mkdir "$FINDER_TESTDIR"
run          "finder_control: mkdir created"  bash -c "[[ -d '$FINDER_TESTDIR' ]]"
rmdir "$FINDER_TESTDIR" 2>/dev/null

echo ""
echo "Network"
echo "-------"
run_blocked  "network_port: invalid port (0)"     "ERROR"   "$TOOLS/network_port.sh" 0
run_blocked  "network_port: invalid port (99999)" "ERROR"   "$TOOLS/network_port.sh" 99999
run_blocked  "network_port: missing arg"          "Usage"   "$TOOLS/network_port.sh"
run_contains "network_port: valid port exits 0"   "listen\|Nothing" "$TOOLS/network_port.sh" 80
run_blocked  "network_curl: missing arg"          "Usage"   "$TOOLS/network_curl.sh"
run_blocked  "network_ping: count > 20 blocked"   "ERROR"   "$TOOLS/network_ping.sh" localhost 21
run_blocked  "network_ping: missing arg"          "Usage"   "$TOOLS/network_ping.sh"
run_blocked  "network_dns: bad record type"       "ERROR"   "$TOOLS/network_dns.sh" example.com AXFR
run_blocked  "network_dns: missing arg"           "Usage"   "$TOOLS/network_dns.sh"
run          "network_listen: exits 0"                      "$TOOLS/network_listen.sh"

echo ""
echo "Process"
echo "-------"
run_contains "process_list: no filter shows output"    "PID\|USER"   "$TOOLS/process_list.sh"
run_contains "process_list: filter by name"            "bash\|zsh\|sh\|PID"  "$TOOLS/process_list.sh" sh
run_blocked  "process_kill: blocks system PID (1)"     "BLOCKED"     "$TOOLS/process_kill.sh" 1
run_blocked  "process_kill: blocks PID 99"             "BLOCKED"     "$TOOLS/process_kill.sh" 99
run_blocked  "process_kill: missing arg"               "Usage"       "$TOOLS/process_kill.sh"
run_blocked  "process_kill: non-numeric PID"           "ERROR"       "$TOOLS/process_kill.sh" abc

echo ""
echo "Local Docker (skipped if Docker not running)"
echo "---------------------------------------------"
if ! docker info >/dev/null 2>&1; then
  echo "  SKIP  Docker not running — start Docker Desktop to run these tests"
else
  run          "docker_local_ps: exits 0"                            "$TOOLS/docker_local_ps.sh"
  run          "docker_local_stats: exits 0"                         "$TOOLS/docker_local_stats.sh"
  run_blocked  "docker_local_logs: missing arg"           "Usage"    "$TOOLS/docker_local_logs.sh"
  run_blocked  "docker_local_compose: missing arg"        "Usage"    "$TOOLS/docker_local_compose.sh"
  run_blocked  "docker_local_compose: unsupported action" "ERROR"    "$TOOLS/docker_local_compose.sh" destroy
fi


echo ""
echo "Screen Recording"
echo "----------------"
run_blocked  "screencapture_control: missing arg"        "Usage"    "$TOOLS/screencapture_control.sh"
run_blocked  "screencapture_control: unknown action"     "Usage"    "$TOOLS/screencapture_control.sh" badaction
run_contains "screencapture_control: status no recording" "No active recording" "$TOOLS/screencapture_control.sh" status
run_contains "screencapture_control: list no recordings"  "No recordings found\|Recordings in" "$TOOLS/screencapture_control.sh" list

echo ""
echo "==============================="
echo "  Passed: $PASS  Failed: $FAIL"
echo "==============================="
[[ $FAIL -eq 0 ]]
