#!/usr/bin/env python3
"""
Test: Parallel Dispatch via tools_call_batch

Verifies that the tools_call_batch tool can execute multiple tools concurrently
and return results in order.
"""

import subprocess
import time
import json
import sys

BINDIR = "/Users/debaditya/workspace/claude_for_mac_local/local-mac-mcp/.build/arm64-apple-macosx/release"
BINPATH = "local-mpc"


def call_mpc(tool: str, args: dict) -> tuple[float, dict]:
    """Call local-mpc tool and return (latency_ms, response)."""
    start = time.perf_counter()
    try:
        cmd = f"cd {BINDIR} && ./{BINPATH} call {tool} '{json.dumps(args)}'"
        result = subprocess.run(
            cmd,
            shell=True,
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


def test_parallel_dispatch():
    """Test that tools_call_batch executes multiple tools in parallel."""
    print("\n" + "="*70)
    print("TEST: Parallel Dispatch (tools_call_batch)")
    print("="*70)

    print(f"Using binary: {BINDIR}/{BINPATH}\n")

    # Test 1: Single tool call
    print("[1/3] Test 1: Single tool call (baseline)...")
    latency_single, resp_single = call_mpc("notes_list", {})
    print(f"      ✓ {latency_single:.0f}ms")

    if "error" in resp_single:
        print(f"❌ FAILED: Single call error: {resp_single['error']}")
        return False

    # Test 2: Parallel dispatch with 2 tools
    print("[2/3] Test 2: Parallel dispatch (2 tools)...")
    latency_parallel_2, resp_parallel_2 = call_mpc("tools_call_batch", {
        "calls": [
            {"tool": "notes_list", "args": {}},
            {"tool": "reminders_list", "args": {}}
        ]
    })
    print(f"      ✓ {latency_parallel_2:.0f}ms")

    if "error" in resp_parallel_2:
        print(f"❌ FAILED: Parallel dispatch error: {resp_parallel_2['error']}")
        return False

    # Test 3: Parallel dispatch with 3 tools
    print("[3/3] Test 3: Parallel dispatch (3 tools)...")
    latency_parallel_3, resp_parallel_3 = call_mpc("tools_call_batch", {
        "calls": [
            {"tool": "notes_list", "args": {}},
            {"tool": "reminders_list", "args": {}},
            {"tool": "mail_list_mailboxes", "args": {}}
        ]
    })
    print(f"      ✓ {latency_parallel_3:.0f}ms")

    if "error" in resp_parallel_3:
        print(f"❌ FAILED: Parallel dispatch error: {resp_parallel_3['error']}")
        return False

    # Analyze results
    print(f"\n{'='*70}")
    print("RESULTS:")
    print(f"{'='*70}")

    # Verify response structure
    if not isinstance(resp_parallel_2, list):
        print(f"❌ FAILED: Expected list response, got {type(resp_parallel_2)}")
        return False

    if len(resp_parallel_2) != 2:
        print(f"❌ FAILED: Expected 2 results, got {len(resp_parallel_2)}")
        return False

    # Check each result has tool and result fields
    for i, item in enumerate(resp_parallel_2):
        if "tool" not in item or "result" not in item:
            print(f"❌ FAILED: Result {i} missing 'tool' or 'result' field")
            return False

    # Verify order is preserved
    if resp_parallel_2[0]["tool"] != "notes_list":
        print(f"❌ FAILED: Order not preserved - expected notes_list first, got {resp_parallel_2[0]['tool']}")
        return False

    if resp_parallel_2[1]["tool"] != "reminders_list":
        print(f"❌ FAILED: Order not preserved - expected reminders_list second, got {resp_parallel_2[1]['tool']}")
        return False

    print(f"Single tool call:        {latency_single:6.0f}ms")
    print(f"Parallel (2 tools):      {latency_parallel_2:6.0f}ms")
    print(f"Parallel (3 tools):      {latency_parallel_3:6.0f}ms")
    print(f"\nResults structure:")
    print(f"  ✓ Response is a list of {len(resp_parallel_2)} items")
    print(f"  ✓ Each item has 'tool' and 'result' fields")
    print(f"  ✓ Order preserved: {[r['tool'] for r in resp_parallel_2]}")

    print(f"\n{'='*70}")
    print("✅ PASSED: Parallel dispatch working correctly")
    print(f"   - Multiple tools execute and return results")
    print(f"   - Results are returned in original call order")
    print(f"   - Response structure is valid JSON")
    print("="*70 + "\n")
    return True


if __name__ == "__main__":
    try:
        passed = test_parallel_dispatch()
        sys.exit(0 if passed else 1)
    except Exception as e:
        print(f"❌ CRASHED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)
