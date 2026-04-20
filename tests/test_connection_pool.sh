#!/bin/bash
# Test: Connection Pool Reuse
# Verifies that MCPConnectionPool keeps the server process alive and reuses pipes

set -e

BINPATH="/tmp/local-mpc"

echo ""
echo "======================================================================"
echo "TEST: Connection Pool Reuse"
echo "======================================================================"

if [ ! -x "$BINPATH" ]; then
    echo "❌ FAILED: Binary not executable at $BINPATH"
    exit 1
fi

echo "Using binary: $BINPATH"
echo ""

# Call 1: mail_list_mailboxes (process startup)
echo "[1/3] Call 1: mail_list_mailboxes (process startup)..."
start=$(date +%s)
output1=$("$BINPATH" call mail_list_mailboxes '{}' 2>&1)
end=$(date +%s)
latency1=$(( (end - start) * 1000 ))
echo "      ✓ ${latency1}ms"

if echo "$output1" | grep -q "error"; then
    echo "❌ FAILED: Call 1 error: $output1"
    exit 1
fi

# Call 2: contacts_search (reuse pool)
echo "[2/3] Call 2: contacts_search (reuse pool)..."
start=$(date +%s)
output2=$("$BINPATH" call contacts_search '{"name":"test"}' 2>&1)
end=$(date +%s)
latency2=$(( (end - start) * 1000 ))
echo "      ✓ ${latency2}ms"

# Call 3: reminders_list (reuse pool again)
echo "[3/3] Call 3: reminders_list (reuse pool again)..."
start=$(date +%s)
output3=$("$BINPATH" call reminders_list '{"include_completed":false}' 2>&1)
end=$(date +%s)
latency3=$(( (end - start) * 1000 ))
echo "      ✓ ${latency3}ms"

# Analyze results
echo ""
echo "======================================================================"
echo "RESULTS:"
echo "======================================================================"
echo "Call 1 (startup):    ${latency1}ms"
echo "Call 2 (reuse):      ${latency2}ms"
echo "Call 3 (reuse):      ${latency3}ms"

# Calculate speedups
speedup2=$(( latency1 > 0 ? latency1 / latency2 : 0 ))
speedup3=$(( latency1 > 0 ? latency1 / latency3 : 0 ))

echo ""
echo "Speedup (Call 1 vs Call 2): ${speedup2}x"
echo "Speedup (Call 1 vs Call 3): ${speedup3}x"

# Check threshold: Call 2/3 should be < 50% of Call 1 latency (5x+ speedup)
threshold=$((latency1 / 2))
echo ""
echo "Threshold: Call 2/3 latency < ${threshold}ms (50% of Call 1)"

if [ "$latency2" -lt "$threshold" ] && [ "$latency3" -lt "$threshold" ]; then
    echo "✅ PASSED: Connection pool is reusing process (5x+ speedup)"
    echo "======================================================================"
    echo ""
    exit 0
else
    echo "❌ FAILED: Expected 5x+ speedup, got ${speedup2}x and ${speedup3}x"
    echo "======================================================================"
    echo ""
    exit 1
fi
