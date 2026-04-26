#!/bin/bash
# Read-only smoke tests for the local-mac-tool Swift binary.
# Skips any command that writes, sends, or deletes data.

BINARY="$HOME/bin/local-mac-tool"
EMPTY="{}"
PASS=0
FAIL=0

pass() { echo "  PASS  $1"; ((PASS++)); }
fail() { echo "  FAIL  $1 — $2"; ((FAIL++)); }

# run_ok <label> <command> [stdin_json]
run_ok() {
  local label="$1" cmd="$2" stdin="${3:-$EMPTY}"
  local output
  output=$(echo "$stdin" | "$BINARY" "$cmd" 2>&1)
  local exit_code=$?
  if [[ $exit_code -ne 0 ]]; then
    fail "$label" "exit code $exit_code: $output"
  elif ! echo "$output" | grep -q '"status".*"ok"'; then
    fail "$label" "missing status:ok — $output"
  else
    pass "$label"
  fi
}

# run_err <label> <command> [stdin_json]
run_err() {
  local label="$1" cmd="$2" stdin="${3:-$EMPTY}"
  local output
  output=$(echo "$stdin" | "$BINARY" "$cmd" 2>&1)
  local exit_code=$?
  if [[ $exit_code -eq 0 ]]; then
    fail "$label" "expected error but got exit 0"
  elif ! echo "$output" | grep -q '"status".*"error"'; then
    fail "$label" "expected status:error — $output"
  else
    pass "$label"
  fi
}

# run_contains <label> <command> <pattern> [stdin_json]
run_contains() {
  local label="$1" cmd="$2" pattern="$3" stdin="${4:-$EMPTY}"
  local output
  output=$(echo "$stdin" | "$BINARY" "$cmd" 2>&1)
  local exit_code=$?
  if [[ $exit_code -ne 0 ]]; then
    fail "$label" "exit code $exit_code: $output"
  elif ! echo "$output" | grep -qi "$pattern"; then
    fail "$label" "missing pattern '$pattern'"
  else
    pass "$label"
  fi
}

echo ""
echo "Binary"
echo "------"
if [[ ! -x "$BINARY" ]]; then
  echo "  FAIL  binary not found or not executable: $BINARY"
  exit 1
fi
pass "binary exists and is executable"

echo ""
echo "Time"
echo "----"
run_contains "time-now: returns date string" "time-now" "2026\|2025\|IST" "{}"

echo ""
echo "Contacts"
echo "--------"
run_ok       "contacts-search: no match returns ok"   "contacts-search" '{"name":"nobody999xyz"}'
run_contains "contacts-search: no match message"      "contacts-search" "No contacts" '{"name":"nobody999xyz"}'
run_err      "contacts-search: missing name arg"      "contacts-search" "{}"

echo ""
echo "Reminders"
echo "---------"
run_ok "reminders-list: limit 1 returns ok"   "reminders-list" '{"limit":1}'
run_ok "reminders-list: no args returns ok"   "reminders-list" '{}'

echo ""
echo "Mail"
echo "----"
run_ok "mail-list-mailboxes: returns ok"          "mail-list-mailboxes" '{}'
run_ok "mail-read: inbox limit 1 returns ok"      "mail-read"           '{"limit":1,"folder":"INBOX"}'
run_ok "mail-search: query returns ok"            "mail-search"         '{"query":"test","limit":1,"folder":"INBOX"}'

echo ""
echo "Notes"
echo "-----"
run_ok       "notes-folders: returns ok"                  "notes-folders"  '{}'
run_contains "notes-folders: contains folder name"        "notes-folders"  "ZTITLE2\|name\|Claude" '{}'
run_ok       "notes-list: default limit returns ok"       "notes-list"     '{}'
run_contains "notes-list: contains identifier field"      "notes-list"     "identifier" '{}'
run_ok       "notes-list: with limit 1 returns ok"        "notes-list"     '{"limit":1}'
run_err      "notes-read: missing id returns error"       "notes-read"     '{}'
run_err      "notes-read: unknown id returns error"       "notes-read"     '{"id":"nonexistent-id-xyz-000"}'

echo ""
echo "Error handling"
echo "--------------"
run_err "unknown command returns error" "unknown-command-xyz" "{}"

echo ""
echo "================================"
echo "  Passed: $PASS  Failed: $FAIL"
echo "================================"
[[ $FAIL -eq 0 ]]
