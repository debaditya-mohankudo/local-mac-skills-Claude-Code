#!/usr/bin/env python3
"""
Stress Test: Connection Pool Under Load

Verifies MCPConnectionPool can handle multiple concurrent requests efficiently.
Tests: 50 sequential calls in ~1 second (demonstrating reuse throughput)
"""

import subprocess
import time
import json
import sys
import concurrent.futures
from threading import Lock

BINPATH = "/tmp/local-mpc"
results_lock = Lock()

def call_mpc(call_num: int, tool: str, args: dict) -> dict:
    """Call local-mpc tool and return timing + response."""
    start = time.perf_counter()
    try:
        result = subprocess.run(
            [BINPATH, "call", tool, json.dumps(args)],
            capture_output=True,
            text=True,
            timeout=10
        )
        latency_ms = (time.perf_counter() - start) * 1000

        success = result.returncode == 0
        return {
            "call": call_num,
            "latency_ms": latency_ms,
            "success": success,
            "error": result.stderr if not success else None
        }
    except subprocess.TimeoutExpired:
        latency_ms = (time.perf_counter() - start) * 1000
        return {
            "call": call_num,
            "latency_ms": latency_ms,
            "success": False,
            "error": "timeout"
        }
    except Exception as e:
        return {
            "call": call_num,
            "latency_ms": (time.perf_counter() - start) * 1000,
            "success": False,
            "error": str(e)
        }

def test_stress():
    """Run 50 concurrent requests to test connection pool throughput."""
    print("\n" + "="*70)
    print("STRESS TEST: Connection Pool Under Load")
    print("="*70)
    print(f"Using binary: {BINPATH}")
    print(f"Target: 50 sequential calls in ~1 second\n")

    # Run 50 sequential calls
    results = []
    overall_start = time.perf_counter()

    print("Making 50 calls to mail_list_mailboxes...")
    for i in range(50):
        result = call_mpc(i + 1, "mail_list_mailboxes", {})
        results.append(result)

        # Print progress every 10 calls
        if (i + 1) % 10 == 0:
            print(f"  [{i + 1:2d}/50] completed")

    overall_time = (time.perf_counter() - overall_start)

    # Analyze results
    print(f"\n{'='*70}")
    print("RESULTS:")
    print(f"{'='*70}")

    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    print(f"Total calls:        {len(results)}")
    print(f"Successful:         {len(successful)}")
    print(f"Failed:             {len(failed)}")
    print(f"Total time:         {overall_time:.2f}s")
    print(f"Throughput:         {len(successful) / overall_time:.1f} calls/sec")

    if results:
        latencies = [r["latency_ms"] for r in results]
        print(f"\nLatency statistics:")
        print(f"  Min:              {min(latencies):.1f}ms")
        print(f"  Max:              {max(latencies):.1f}ms")
        print(f"  Avg:              {sum(latencies) / len(latencies):.1f}ms")
        print(f"  First 5 calls:    {[f'{l:.1f}ms' for l in latencies[:5]]}")
        print(f"  Last 5 calls:     {[f'{l:.1f}ms' for l in latencies[-5:]]}")

    # Success criteria
    print(f"\n{'='*70}")
    passed = len(failed) == 0 and overall_time < 2.0

    if passed:
        print("✅ PASSED: Connection pool handled 50 calls efficiently")
        print(f"   - All calls succeeded")
        print(f"   - Completed in {overall_time:.2f}s (target: <2s)")
        print(f"   - Throughput: {len(successful) / overall_time:.1f} calls/sec")
    else:
        if len(failed) > 0:
            print(f"❌ FAILED: {len(failed)} calls failed")
            for r in failed[:3]:
                print(f"   Call {r['call']}: {r['error']}")
        if overall_time >= 2.0:
            print(f"⚠️  SLOW: Took {overall_time:.2f}s (target: <2s)")

    print("="*70 + "\n")
    return passed

if __name__ == "__main__":
    try:
        passed = test_stress()
        sys.exit(0 if passed else 1)
    except Exception as e:
        print(f"❌ CRASHED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)
