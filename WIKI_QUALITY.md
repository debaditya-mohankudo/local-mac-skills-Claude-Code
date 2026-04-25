# Quality & Tests Wiki

**Full documentation:** Vault → `Documentation/Tools/QUALITY_WIKI.md`

## Quick Start

```bash
# Swift binary smoke tests (read-only, no Docker needed)
bash ~/workspace/claude_for_mac_local/tests/test_swift_binary.sh

# Shell/Docker tests (requires Docker running)
bash ~/workspace/claude_for_mac_local/tests/test_tools.sh
```

## Latest Run — 2026-04-25

| Suite                               | Result  |
|-------------------------------------|---------|
| Swift binary smoke tests (11 tests) | ✓ 11/11 |

See the vault wiki for comprehensive test coverage, guardrails, and how to add new tests.
