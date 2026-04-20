#!/usr/bin/env python3
"""
Test: Connection Pool Reuse (Mail-only test for speed)

Verifies that MCPConnectionPool keeps the server process alive and reuses pipes
across multiple requests. Uses mail_list_mailboxes which responds quickly.
"""

import subprocess
import time
import json
import sys

BINPATH = "/tmp/local-mpc"

def call_mpc(tool: str, args: dict) -> tuple[float, dict]:
    """Call local-mpc tool and return (latency_ms, response_dict)."""
    start = time.perf_counter()
    try:
        result = subprocess.run(
            [BINPATH, "call", tool, json.dumps(args)],
            capture_output=True,
            text=True,
            timeout=10
        )
        latency_ms = (time.perf_counter() - start) * 1000

        if result.returncode != 0:
            return latency_ms, {"error": result.stderr}

        try:
            response = json.loads(result.stdout)
        except:
            response = {"raw": result.stdout[:100]}

        return latency_ms, response
    except subprocess.TimeoutExpired:
        latency_ms = (time.perf_counter() - start) * 1000
        return latency_ms, {"error": "timeout"}
    except Exception as e:
        return (time.perf_counter() - start) * 1000, {"error": str(e)}

def test_connection_pool_reuse():
    """Test that connection pool reuses process across calls."""
    print("\n" + "="*70)
    print("TEST: Connection Pool Reuse (Mail Tool)")
    print("="*70)
    print(f"Using binary: {BINPATH}\n")

    # Call 1: mail_list_mailboxes (process startup)
    print("[1/3] Call 1: mail_list_mailboxes (process startup)...")
    latency1, resp1 = call_mpc("mail_list_mailboxes", {})
    print(f"      ✓ {latency1:.1f}ms")

    if "error" in resp1:
        print(f"❌ FAILED: Call 1 error: {resp1['error']}")
        return False

    # Call 2: mail_list_mailboxes again (reuse pool)
    print("[2/3] Call 2: mail_list_mailboxes (reuse pool)...")
    latency2, resp2 = call_mpc("mail_list_mailboxes", {})
    print(f"      ✓ {latency2:.1f}ms")

    # Call 3: mail_list_mailboxes again (reuse pool)
    print("[3/3] Call 3: mail_list_mailboxes (reuse pool again)...")
    latency3, resp3 = call_mpc("mail_list_mailboxes", {})
    print(f"      ✓ {latency3:.1f}ms")

    # Analyze results
    print(f"\n{'='*70}")
    print("RESULTS:")
    print(f"{'='*70}")
    print(f"Call 1 (startup):    {latency1:7.1f}ms")
    print(f"Call 2 (reuse):      {latency2:7.1f}ms")
    print(f"Call 3 (reuse):      {latency3:7.1f}ms")

    speedup2 = latency1 / latency2 if latency2 > 0 else 0
    speedup3 = latency1 / latency3 if latency3 > 0 else 0

    print(f"\nSpeedup (Call 1 vs Call 2): {speedup2:.1f}x")
    print(f"Speedup (Call 1 vs Call 3): {speedup3:.1f}x")

    # Pass if Call 2/3 are faster than Call 1 (indicating process reuse)
    # Threshold: Call 2 must be at least 10% faster than Call 1
    threshold_percent = 0.9
    passed = (latency2 < latency1 * threshold_percent and
              latency3 < latency1 * threshold_percent)

    print(f"\nThreshold: Call 2/3 latency < {latency1 * threshold_percent:.1f}ms (10% faster than Call 1)")
    if passed:
        print("✅ PASSED: Connection pool is reusing process")
        print("   Evidence: Call 2 and 3 are faster due to process startup being amortized")
    else:
        print(f"❌ FAILED: Call 2/3 not faster than Call 1")

    print("="*70 + "\n")
    return passed

if __name__ == "__main__":
    try:
        passed = test_connection_pool_reuse()
        sys.exit(0 if passed else 1)
    except Exception as e:
        print(f"❌ CRASHED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)
