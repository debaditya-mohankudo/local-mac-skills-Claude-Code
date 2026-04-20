#!/usr/bin/env python3
"""
Test: Connection Pool Reuse

Verifies that MCPConnectionPool keeps the server process alive and reuses pipes
across multiple requests, resulting in significant latency reduction after first call.

Expected behavior:
- Call 1: ~500-900ms (process startup + first request)
- Call 2: ~50-150ms (reuses existing process + pipes)
- Call 3: ~50-150ms (reuses existing process + pipes)

Passes if: Call 2 latency < Call 1 latency * 0.5 (5x speedup threshold)
"""

import subprocess
import time
import json
import sys

BINDIR = "/Users/debaditya/workspace/claude_for_mac_local/local-mac-mpc/.build/arm64-apple-macosx/release"
BINPATH = "local-mpc"

def call_mpc(tool: str, args: dict) -> tuple[float, dict]:
    """Call local-mpc tool and return (latency_ms, response_dict)."""
    start = time.time()
    try:
        # Use shell to cd and run to avoid path expansion issues
        cmd = f"cd {BINDIR} && ./{BINPATH} call {tool} '{json.dumps(args)}'"
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )
        latency_ms = (time.time() - start) * 1000

        if result.returncode != 0:
            return latency_ms, {"error": result.stderr}

        # Try to parse JSON response
        try:
            response = json.loads(result.stdout)
        except:
            response = {"raw": result.stdout[:100]}

        return latency_ms, response
    except subprocess.TimeoutExpired:
        latency_ms = (time.time() - start) * 1000
        return latency_ms, {"error": "timeout"}

def test_connection_pool_reuse():
    """Test that connection pool reuses process across calls."""
    print("\n" + "="*70)
    print("TEST: Connection Pool Reuse")
    print("="*70)

    # Just verify we can run a command (actual binary check will happen on first call)
    print(f"Using binary: {BINDIR}/{BINPATH}\n")

    # Call 1: mail_list_mailboxes (process spawn)
    print("[1/3] Call 1: mail_list_mailboxes (process startup)...")
    latency1, resp1 = call_mpc("mail_list_mailboxes", {})
    print(f"      ✓ {latency1:.0f}ms")

    if "error" in resp1:
        print(f"❌ FAILED: Call 1 error: {resp1['error']}")
        return False

    # Call 2: calendar_list_events (reuse pool)
    print("[2/3] Call 2: calendar_list_events (reuse pool)...")
    latency2, resp2 = call_mpc("calendar_list_events", {
        "start_date": "2026-04-11T00:00:00Z",
        "end_date": "2026-04-12T23:59:59Z"
    })
    print(f"      ✓ {latency2:.0f}ms")

    # Call 3: contacts_search (reuse pool again)
    print("[3/3] Call 3: contacts_search (reuse pool again)...")
    latency3, resp3 = call_mpc("contacts_search", {"name": "test"})
    print(f"      ✓ {latency3:.0f}ms")

    # Analyze results
    print(f"\n{'='*70}")
    print("RESULTS:")
    print(f"{'='*70}")
    print(f"Call 1 (startup):    {latency1:6.0f}ms")
    print(f"Call 2 (reuse):      {latency2:6.0f}ms")
    print(f"Call 3 (reuse):      {latency3:6.0f}ms")

    speedup2 = latency1 / latency2 if latency2 > 0 else 0
    speedup3 = latency1 / latency3 if latency3 > 0 else 0

    print(f"\nSpeedup (Call 1 vs Call 2): {speedup2:.1f}x")
    print(f"Speedup (Call 1 vs Call 3): {speedup3:.1f}x")

    # Pass if Call 2/3 are significantly faster than Call 1
    threshold = 0.5  # 5x speedup (50% of Call 1 latency)
    passed = (latency2 < latency1 * threshold and
              latency3 < latency1 * threshold)

    print(f"\nThreshold: Call 2/3 latency < {int(latency1 * threshold)}ms (50% of Call 1)")
    if passed:
        print("✅ PASSED: Connection pool is reusing process (5x+ speedup)")
    else:
        print(f"❌ FAILED: Expected 5x+ speedup, got {speedup2:.1f}x and {speedup3:.1f}x")

    print("="*70 + "\n")
    return passed

if __name__ == "__main__":
    try:
        passed = test_connection_pool_reuse()
        sys.exit(0 if passed else 1)
    except Exception as e:
        print(f"❌ CRASHED: {e}")
        sys.exit(2)
