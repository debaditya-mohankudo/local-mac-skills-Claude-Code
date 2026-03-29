"""
Experimental: LLM agent response quality tests using deepeval.

These tests evaluate whether Claude agent responses are faithful and relevant
when invoking local-mac skills. They require:
  - pip install deepeval pytest
  - Claude Code CLI installed and authenticated (`claude` on PATH)
  - deepeval configured (run `deepeval login` or set OPENAI_API_KEY for the
    default evaluator model, or configure a custom one via deepeval settings)

Run:
  pytest tests/test_agent_responses.py -v

The module skips gracefully if deepeval is not installed or the claude CLI
is not available — safe to keep in CI without breaking it.
"""

import os
import shutil
import subprocess
import pytest

# ---------------------------------------------------------------------------
# Optional imports — skip entire module if deepeval is not installed
# ---------------------------------------------------------------------------
try:
    from deepeval import assert_test
    from deepeval.test_case import LLMTestCase
    from deepeval.metrics import FaithfulnessMetric, AnswerRelevancyMetric, HallucinationMetric
except ImportError:
    pytest.skip("deepeval not installed — run: pip install deepeval", allow_module_level=True)


# ---------------------------------------------------------------------------
# Minimal Claude agent — delegates to the `claude` CLI (no API key needed)
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = (
    "You are a helpful local Mac assistant. "
    "Answer concisely and only based on the context provided."
)

def run_agent(prompt: str, context: str = "") -> str:
    """Run a single-turn query via the Claude Code CLI and return the response text."""
    claude_bin = shutil.which("claude")
    if not claude_bin:
        pytest.skip("claude CLI not found on PATH")

    full_prompt = f"Context:\n{context}\n\nQuestion: {prompt}" if context else prompt
    result = subprocess.run(
        [claude_bin, "-p", full_prompt, "--system-prompt", SYSTEM_PROMPT],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0:
        pytest.skip(f"claude CLI failed: {result.stderr.strip()[:200]}")
    return result.stdout.strip()


# ---------------------------------------------------------------------------
# Helper to call a tool script and capture its output as retrieval context
# ---------------------------------------------------------------------------
TOOLS = os.path.expanduser("~/workspace/claude_for_mac_local/tools")

def tool_output(script: str, *args: str, timeout: int = 10) -> str:
    """Run a tool script and return stdout, or empty string on failure."""
    path = os.path.join(TOOLS, script)
    if not os.path.isfile(path):
        return ""
    try:
        result = subprocess.run(
            [path, *args],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.stdout.strip()
    except (subprocess.TimeoutExpired, OSError):
        return ""


# ---------------------------------------------------------------------------
# Shared metric factories
# ---------------------------------------------------------------------------
def faithfulness(threshold: float = 0.7) -> FaithfulnessMetric:
    return FaithfulnessMetric(threshold=threshold)

def relevancy(threshold: float = 0.7) -> AnswerRelevancyMetric:
    return AnswerRelevancyMetric(threshold=threshold)

def hallucination(threshold: float = 0.5) -> HallucinationMetric:
    return HallucinationMetric(threshold=threshold)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestCalendarAgentResponse:
    """Agent responses about calendar events."""

    def test_list_todays_events(self):
        context = tool_output("calendar_list_events.sh", "today") or (
            "No calendar events found for today."
        )
        question = "What events do I have today?"
        test_case = LLMTestCase(
            input=question,
            actual_output=run_agent(question, context),
            retrieval_context=[context],
        )
        assert_test(test_case, [faithfulness(), relevancy()])

    def test_no_hallucination_on_empty_calendar(self):
        context = "No calendar events found for today."
        question = "Do I have any meetings today?"
        test_case = LLMTestCase(
            input=question,
            actual_output=run_agent(question, context),
            retrieval_context=[context],
            context=[context],
        )
        assert_test(test_case, [faithfulness(threshold=0.8), hallucination(threshold=0.3)])


class TestRemindersAgentResponse:
    """Agent responses about Apple Reminders."""

    def test_list_reminders(self):
        context = tool_output("reminders_list.sh") or "No reminders found."
        question = "What are my current reminders?"
        test_case = LLMTestCase(
            input=question,
            actual_output=run_agent(question, context),
            retrieval_context=[context],
        )
        assert_test(test_case, [faithfulness(), relevancy()])

    def test_specific_reminder_lookup(self):
        context = "Reminder: Buy groceries — due 2026-03-25. Reminder: Review PR — due 2026-03-24."
        question = "When is my grocery reminder due?"
        test_case = LLMTestCase(
            input=question,
            actual_output=run_agent(question, context),
            retrieval_context=[context],
        )
        assert_test(test_case, [faithfulness(threshold=0.8), relevancy(threshold=0.8)])


class TestNotesAgentResponse:
    """Agent responses about Apple Notes (Claude folder)."""

    def test_list_notes(self):
        context = tool_output("notes_list.sh") or "No notes found."
        question = "What notes do I have saved?"
        test_case = LLMTestCase(
            input=question,
            actual_output=run_agent(question, context),
            retrieval_context=[context],
        )
        assert_test(test_case, [faithfulness(), relevancy()])

    def test_note_content_faithfulness(self):
        # Synthetic note content — tests that agent does not add unsupported info
        context = (
            "Note title: 'Project Ideas'\n"
            "Content: 1. Build a CLI tool for Mac automation. 2. Add deepeval tests."
        )
        question = "What are my project ideas?"
        test_case = LLMTestCase(
            input=question,
            actual_output=run_agent(question, context),
            retrieval_context=[context],
            context=[context],
        )
        assert_test(test_case, [faithfulness(threshold=0.85), hallucination(threshold=0.3)])


class TestStorageAgentResponse:
    """Agent responses about disk storage."""

    def test_storage_overview_relevancy(self):
        context = tool_output("storage_overview.sh") or "Storage info unavailable."
        question = "How much disk space do I have left?"
        test_case = LLMTestCase(
            input=question,
            actual_output=run_agent(question, context),
            retrieval_context=[context],
        )
        assert_test(test_case, [relevancy(threshold=0.75)])


class TestNetworkAgentResponse:
    """Agent responses about network/port status."""

    def test_port_status_faithfulness(self):
        context = "Port 8080: process 'python3' (PID 12345) is listening."
        question = "What is running on port 8080?"
        test_case = LLMTestCase(
            input=question,
            actual_output=run_agent(question, context),
            retrieval_context=[context],
        )
        assert_test(test_case, [faithfulness(threshold=0.85), relevancy(threshold=0.8)])

    def test_port_not_in_use(self):
        context = "Nothing is listening on port 9999."
        question = "Is anything running on port 9999?"
        test_case = LLMTestCase(
            input=question,
            actual_output=run_agent(question, context),
            retrieval_context=[context],
            context=[context],
        )
        assert_test(test_case, [faithfulness(threshold=0.9), hallucination(threshold=0.2)])
