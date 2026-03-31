---
name: run-tests
description: Run all shell script tests in tests/test_tools.sh for the claude_for_mac_local project. Use when the user wants to run tests, check test results, or verify tool scripts are working.
user-invocable: true
---

Run all shell script tests for the claude_for_mac_local project.

---

## Run the tests

```bash
bash ~/workspace/claude_for_mac_local/tests/test_tools.sh
```

- Capture the full output
- Report the final `Passed: N  Failed: N` summary to the user
- If any tests failed, list each `FAIL` line so the user can see what broke
- If all tests passed, confirm with the pass count

## Notes

- SSH sandbox tests are automatically skipped if the Docker container is not running — that is expected and not a failure
- Local Docker tests are skipped if Docker Desktop is not running — also expected
- To start the SSH sandbox before running tests: `bash ~/workspace/claude_for_mac_local/tests/test_setup.sh`
- To stop it after: `bash ~/workspace/claude_for_mac_local/tests/test_setup.sh --stop`
