# Quality & Tests Wiki

**Full documentation:** Vault → `Documentation/Tools/QUALITY_WIKI.md`

## Quick Start

```bash
# Python tests
cd ~/workspace/claude_for_mac_local
uv run pytest tests/test_connection_pool.py tests/test_connection_pool_fast.py tests/test_parallel_dispatch.py tests/test_agent_responses.py -v

# MCP dispatch categories (Swift)
~/workspace/claude_for_mac_local/local-mac-mcp/Tests/test_dispatch_categories.sh

# Shell/Docker tests (requires Docker running)
bash ~/workspace/claude_for_mac_local/tests/test_tools.sh
```

## Latest Run — 2026-04-14

| Suite | Result |
|---|---|
| test_connection_pool | ✓ PASSED |
| test_connection_pool_fast | ✓ PASSED |
| test_parallel_dispatch | ✓ PASSED |
| test_agent_responses | ~ SKIPPED |
| MCP dispatch (10 categories) | ✓ 10/10 |
| Shell/Docker | ~ SKIPPED (Docker down) |

## Previous Run — 2026-04-12

### Shell Tests (test_tools.sh)

| Metric | Value |
| --- | --- |
| Total Runtime | 2m 34.56s |
| Tests Passed | 73 |
| Tests Failed | 0 |
| Success Rate | 100% |

**Breakdown:**

- Storage: 2/2 ✓
- Notes: 1/1 ✓
- Reminders: 1/1 ✓
- Calendar: 1/1 ✓
- Mail: 1/1 ✓
- SSH guardrails: 23/23 ✓
- Finder: 7/7 ✓
- Network: 5/5 ✓
- Process: 6/6 ✓
- Screen Recording: 4/4 ✓

### Parallel Dispatch Test

| Test | Latency | Status |
| --- | --- | --- |
| Single tool (baseline) | 77ms | ✓ |
| 2 concurrent tools | 285ms | ✓ |
| 3 concurrent tools | 196ms | ✓ |

See the vault wiki for comprehensive test coverage, guardrails, and how to add new tests.
