# Quality & Tests Wiki

This document covers how code quality and correctness are maintained in this project — what is tested, how to run it, and the conventions that keep scripts sane.

**Last updated:** 2026-03-22

---

## Test Suite

All tests live in `tests/test_tools.sh`. Run it any time you add or change a script.

```bash
bash ~/workspace/claude_for_mac_local/tests/test_tools.sh
```

Output:

```text
  PASS  ssh_db_query: blocks DROP
  PASS  ssh_git: blocks commit
  ...
  ===============================
    Passed: 35  Failed: 0
  ===============================
```

Exit code `0` = all passed. Non-zero = at least one failure.

---

## Test Helpers

Three helpers cover all cases:

| Helper | When to use |
| ------ | ----------- |
| `run label cmd...` | Command must exit 0 |
| `run_contains label pattern cmd...` | Command must exit 0 AND output must contain `pattern` |
| `run_blocked label pattern cmd...` | Command must exit non-zero AND output must contain `pattern` |

`run_blocked` is the workhorse for guardrail tests — it verifies both that the command was rejected and that the rejection message is meaningful.

---

## What Is Tested

### Happy path — local tools

These verify the scripts can run against the local macOS environment without crashing:

| Test | Script | Check |
| ---- | ------ | ----- |
| Disk info present | `storage_overview.sh` | output contains `GB` / `used` / `avail` |
| Library dir present | `storage_detail.sh` | output contains `Library` |
| Notes list | `notes_list.sh` | exits 0 |
| Reminders list | `reminders_list.sh` | exits 0 |
| Calendar list (today) | `calendar_list_events.sh` | exits 0 |
| Mail accounts | `mail_list_accounts.sh` | output contains `@` or `account` |
| Contacts search | `contacts_search.sh "a"` | exits 0 |

### SSH sandbox tests (Docker, port 2222)

These tests perform **real SSH connections** against a local Docker container. They are skipped automatically if the container is not running — no failure, just `SKIP`.

**Requirement:** Docker container with sshd on port 2222, key-based auth. See the sandbox example in `ssh_config.sh`.

| Test | Command run remotely | Check |
| ---- | -------------------- | ----- |
| echo | `echo hello` | output contains `hello` |
| whoami | `whoami` | output contains `testuser` |
| uname | `uname` | output contains `Linux` |
| pwd | `pwd` | output contains `/` |
| env PATH | `env \| grep PATH` | output contains `PATH` |
| file round-trip | `ssh_copy.sh` up + `ssh_fetch.sh` back | fetched file content matches original |

The file round-trip test exercises the full scp path through `SCP_OPTS` (port-aware) in both directions.

### Guardrail tests — SSH database queries

`ssh_db_query.sh` blocks destructive SQL **before SSH connects** — tested for all seven blocked keywords:

| Test | Input | Expected |
| ---- | ----- | -------- |
| blocks DROP | `DROP TABLE users` | exit 1 + `BLOCKED` |
| blocks ALTER | `ALTER TABLE users ADD col INT` | exit 1 + `BLOCKED` |
| blocks TRUNCATE | `TRUNCATE TABLE logs` | exit 1 + `BLOCKED` |
| blocks DELETE | `DELETE FROM sessions` | exit 1 + `BLOCKED` |
| blocks RENAME | `RENAME TABLE a TO b` | exit 1 + `BLOCKED` |
| blocks CREATE | `CREATE TABLE test (id INT)` | exit 1 + `BLOCKED` |
| blocks REPLACE | `REPLACE INTO users VALUES (1,'x')` | exit 1 + `BLOCKED` |

### Guardrail tests — remote git

`ssh_git.sh` blocks all write git subcommands before SSH connects — tested for 12 variants:

`commit`, `push`, `pull`, `merge`, `rebase`, `reset`, `checkout`, `fetch`, `add`, `branch -D`, `stash pop`, `clean`

Each must exit non-zero and print `BLOCKED`.

### Guardrail tests — file transfer

`ssh_copy.sh` and `ssh_fetch.sh` enforce the `REMOTE_DIRS` allowlist:

| Test | Input | Expected |
| ---- | ----- | -------- |
| ssh_copy: unknown nickname | `secret:/etc` | exit 1 + `ERROR` |
| ssh_fetch: unknown nickname | `secret:/etc/passwd` | exit 1 + `ERROR` |
| ssh_copy: missing args | _(no args)_ | exit 1 + `Usage` |
| ssh_fetch: missing args | _(no args)_ | exit 1 + `Usage` |

### Cache cleanup

`ssh_cache_clean.sh` deletes cached files older than N days:

| Test | Setup | Expected |
| ---- | ----- | -------- |
| removes old file | creates file with mtime −10 days, runs with threshold 7 | exit 0 + `Deleted` |
| file is actually gone | checks `[[ ! -f ... ]]` after deletion | exit 0 |
| nothing to clean | runs with threshold 9999 | exit 0 + `No files` |

---

## What Is Not Tested (and Why)

| Script | Reason skipped |
| ------ | -------------- |
| `contacts_search.sh` | Requires Contacts.app to be open — too noisy for automated runs |
| Write/delete scripts (`reminders_add.sh`, `notes_add.sh`, etc.) | Would mutate live macOS data — not safe in automated runs |
| `imessage_send.sh` | Would send a real iMessage |
| `ssh_logs.sh`, `ssh_disk.sh`, `ssh_db_dump.sh`, `ssh_db_query.sh` (live) | Require a reachable SSH host |
| `safari_control.sh`, `safari_js.sh` | Require Safari open and a live URL |

Guardrail behaviour (block lists, keyword checks) is always tested even when the full script cannot be run — since guardrails fire before any external call is made.

---

## Adding Tests

When adding a new script:

1. **Add a happy-path test** if the script is read-only and safe to run locally.
2. **Add `run_blocked` tests for every guardrail** the script enforces — one test per blocked keyword or condition.
3. Keep the test self-contained — no setup files, no network, no passwords.

The bar is: **any guardrail that exists should have a test that confirms it fires**.

---

## Relationship to Guardrails

Tests and guardrails are co-designed. See [GUARDRAILS_WIKI.md](GUARDRAILS_WIKI.md) for the full list of guardrails. Every script-level guardrail documented there has a corresponding `run_blocked` test in `test_tools.sh`.

When you add a new guardrail to a script, add the test at the same time.

---

## Experimental: LLM Agent Response Tests

`tests/test_agent_responses.py` evaluates the **quality of Claude's answers** when it uses local-mac skills — not just whether scripts exit 0, but whether the agent's natural-language response is faithful, relevant, and hallucination-free.

### Setup

```bash
uv sync --extra test
deepeval login          # sets up the deepeval evaluator model
```

Requires the Claude Code CLI to be installed and authenticated (`claude` on PATH). No API key needed.

### Running

```bash
uv run pytest tests/test_agent_responses.py -v
```

The module skips gracefully if `deepeval` is not installed or the `claude` CLI is not on PATH — safe to keep in CI without breaking it.

### Test Coverage

| Test class | Skill context source | Metrics |
| ---------- | ------------------- | ------- |
| `TestCalendarAgentResponse` | `calendar_list_events.sh today` (live) | Faithfulness, AnswerRelevancy, Hallucination |
| `TestRemindersAgentResponse` | `reminders_list.sh` (live) + synthetic | Faithfulness, AnswerRelevancy |
| `TestNotesAgentResponse` | `notes_list.sh` (live) + synthetic | Faithfulness, Hallucination |
| `TestStorageAgentResponse` | `storage_overview.sh` (live) | AnswerRelevancy |
| `TestNetworkAgentResponse` | Synthetic port-status context | Faithfulness, Hallucination |

### Metric Thresholds

| Metric | Default threshold | Rationale |
| ------ | ----------------- | --------- |
| `FaithfulnessMetric` | 0.7–0.85 | Agent must not contradict provided context |
| `AnswerRelevancyMetric` | 0.7–0.8 | Response must directly address the question |
| `HallucinationMetric` | 0.2–0.5 | Agent must not invent facts not in context |

Thresholds are tighter (≥ 0.8) for tests with synthetic context, where the expected output is fully predictable.

### Retrieval Context Pattern

Each test:

1. Calls the relevant `tools/*.sh` script to get live data (or falls back to synthetic text if the script is unavailable).
2. Passes that output as both the Claude prompt context and deepeval's `retrieval_context`.
3. Evaluates the agent's response against that same context.

This mirrors the real skill execution path — tool output → agent response — making failures actionable.

### Adding New Agent Tests

1. Pick the tool script that supplies context for the skill.
2. Write a `LLMTestCase` with `input`, `actual_output=run_agent(...)`, and `retrieval_context`.
3. Choose metrics: use `HallucinationMetric` when the context fully defines the correct answer; use `AnswerRelevancyMetric` when the question is open-ended.
4. Keep thresholds ≥ 0.8 for synthetic context, ≥ 0.7 for live tool output (which may be noisy).

---

## Future: Real-Time Per-Response Quality Gate (local LLM judge)

> **Status: planned — deferred, judge model not yet chosen.**

The idea is to automatically evaluate every Claude response as it happens, using a **local, non-Anthropic LLM** as the judge, so evaluation adds zero token cost and no external API dependency.

### Judge model options

deepeval supports any `DeepEvalBaseLLM` subclass as a judge. Good local options:

| Option | How to run locally | Notes |
| ------ | ------------------ | ----- |
| **Ollama** (e.g. `llama3`, `mistral`, `gemma2`) | `ollama serve` + `ollama pull <model>` | Easiest setup; REST API on `localhost:11434` |
| **LM Studio** | GUI app, exposes OpenAI-compatible endpoint | Good for quick local testing |
| **vLLM** | `vllm serve <model>` | Higher throughput, needs a GPU |

Recommended starting point: **Ollama + `llama3.2:3b`** — small, fast, runs on Apple Silicon MPS, OpenAI-compatible API.

#### Model shortlist for 8GB RAM (Mac Air)

Tested RAM usage leaves ~3GB headroom for macOS. Avoid 7b+ models — they swap to disk and become too slow for a real-time hook.

| Model | Disk size | RAM usage | Strength |
| ----- | --------- | --------- | -------- |
| `gemma2:2b` | 1.6 GB | ~2 GB | Fast; good for short eval tasks |
| **`llama3.2:3b`** ⭐ | 2.0 GB | ~2.5 GB | Best balance — recommended |
| `phi3.5:mini` | 2.2 GB | ~3 GB | Strong reasoning for its size |
| `qwen2.5:3b` | 1.9 GB | ~2.5 GB | Good instruction following |

Pull the recommended model with:

```bash
ollama pull llama3.2:3b
```

### How it would work

1. **Claude Code `Stop` hook** — fires after every response. Receives the full conversation turn (prompt + response) as JSON on stdin.
2. **`tests/realtime_eval.py`** — the hook target. Parses the turn, runs deepeval metrics, prints a compact score line to stderr (e.g. `[eval] relevancy=0.92 faithfulness=0.88 ✓`).
3. **`tests/local_judge.py`** — a `DeepEvalBaseLLM` subclass that points deepeval at the local model's OpenAI-compatible endpoint (e.g. `http://localhost:11434/v1`). No API keys needed.
4. The hook is **non-blocking** — runs after Claude finishes, never delays the response. A low score prints a warning but does not interrupt the session.

### Files to create

| File | Purpose |
| ---- | ------- |
| `tests/local_judge.py` | Custom deepeval LLM wrapper targeting local model endpoint |
| `tests/realtime_eval.py` | Hook script — parses stdin, runs metrics, prints score |
| `.claude/settings.json` | Add `Stop` hook: `uv run python tests/realtime_eval.py` |

### Dependencies to add

```text
ollama          # Python client (pip: ollama) — or use openai SDK pointed at local endpoint
```

### Trade-offs to keep in mind

- Local model must be running before the hook fires — hook should bail out silently if the endpoint is unreachable.
- Smaller local models are less reliable judges than GPT-4 or Sonnet; expect more variance in scores.
- The hook should skip silently if `deepeval` is not installed or the turn has no retrievable context to judge against.
- First run will be slow if the model needs to load into memory; subsequent calls are fast.
