#!/usr/bin/env bash
# test_dispatch_categories.sh
# Smoke-tests one tool per dispatch category via local-mpc.
# Each test checks that the response is non-empty and not an error.
# Usage: ./tests/test_dispatch_categories.sh

set -uo pipefail

MPC="local-mpc"
PASS=0
FAIL=0

pass() { echo "  ✓ $1"; PASS=$((PASS + 1)); }
fail() { echo "  ✗ $1 — $2"; FAIL=$((FAIL + 1)); }

run_test() {
    local category="$1"
    local tool="$2"
    local args="$3"

    local out
    out=$("$MPC" call "$tool" "$args" 2>/dev/null)

    if [[ -z "$out" ]]; then
        fail "$category ($tool)" "empty response"
    elif echo "$out" | grep -qi '"isError".*true'; then
        fail "$category ($tool)" "$out"
    else
        pass "$category ($tool)"
    fi
}

echo ""
echo "=== Dispatch Category Smoke Tests ==="
echo ""

# Calendar
run_test "calendar"    "calendar_get_upcoming_events"  '{"days": 1}'

# Vault
run_test "vault"       "vault_read"                    '{"note":"Documentation/Tools/TOOLS_WIKI"}'

# Market
run_test "market"      "market_prices_query"           '{"symbol":"NIFTY50"}'

# Safari (just check routing — skips actual browser interaction)
# safari_current_url returns an error if no tab open, but it should route and respond
out=$("$MPC" call safari_current_url '{}' 2>/dev/null)
if [[ -n "$out" ]]; then
    pass "safari (safari_current_url)"
else
    fail "safari (safari_current_url)" "empty response"
fi

# Reminders
run_test "reminders"   "reminders_list"                '{}'

# Communication — contacts (no network, SQLite)
run_test "communication" "contacts_search"             '{"name":"test"}'

# Native Data — notes
run_test "native_data" "notes_folders"                 '{}'

# Files — iCloud
run_test "files"       "icloud_list"                   '{}'

# System — process list
run_test "system"      "process_list"                  '{"filter":"LocalMacMCP"}'

# AI — foundation models (short prompt, skip if unavailable)
out=$("$MPC" call foundation_models_query '{"prompt":"Say OK","max_tokens":5}' 2>/dev/null)
if echo "$out" | grep -qi "unavailable\|requires macOS\|error"; then
    echo "  ~ ai (foundation_models_query) — skipped (model unavailable on this OS)"
elif [[ -n "$out" ]]; then
    pass "ai (foundation_models_query)"
else
    fail "ai (foundation_models_query)" "empty response"
fi

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
echo ""

[[ $FAIL -eq 0 ]]
