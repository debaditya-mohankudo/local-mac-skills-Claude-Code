"""Tests for the qwen2.5:3b tool-calling agent loop."""
import pytest
from tools.ollama_agent import _safe_eval, _dispatch_tool, handle_run, handle_chat


# ---------------------------------------------------------------------------
# Unit tests — no network calls
# ---------------------------------------------------------------------------

class TestSafeEval:
    def test_basic_arithmetic(self):
        assert _safe_eval("2 + 3") == 5
        assert _safe_eval("10 - 4") == 6
        assert _safe_eval("3 * 4") == 12
        assert _safe_eval("10 / 4") == 2.5
        assert _safe_eval("10 // 3") == 3
        assert _safe_eval("10 % 3") == 1
        assert _safe_eval("2 ** 10") == 1024

    def test_parentheses(self):
        assert _safe_eval("(2 + 3) * 4") == 20

    def test_unary_neg(self):
        assert _safe_eval("-5 + 10") == 5

    def test_rejects_names(self):
        with pytest.raises((ValueError, KeyError, AttributeError)):
            _safe_eval("__import__('os')")

    def test_rejects_string(self):
        with pytest.raises(Exception):
            _safe_eval("'hello'")


class TestDispatchTool:
    def test_get_current_time_returns_ist(self):
        result = _dispatch_tool("get_current_time", {})
        assert "IST" in result
        assert len(result) > 10

    def test_calculate_basic(self):
        assert _dispatch_tool("calculate", {"expression": "2 ** 10"}) == "1024"

    def test_calculate_bad_expr(self):
        result = _dispatch_tool("calculate", {"expression": "import os"})
        assert "Error" in result

    def test_list_tools(self):
        result = _dispatch_tool("list_available_tools", {})
        assert "get_current_time" in result
        assert "calculate" in result

    def test_unknown_tool(self):
        result = _dispatch_tool("nonexistent", {})
        assert "Unknown tool" in result


# ---------------------------------------------------------------------------
# Integration tests — hit real Ollama (qwen2.5:3b must be running)
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestAgentLoop:
    def test_simple_no_tools(self):
        # qwen2.5:3b may still call tools on simple prompts; just verify structure
        result = handle_run("Say exactly: HELLO")
        assert isinstance(result["response"], str)
        assert len(result["response"]) > 0
        assert isinstance(result["iterations"], int)
        assert isinstance(result["tool_calls"], list)

    def test_time_tool_called(self):
        result = handle_run("What is the current time? Use the get_current_time tool.")
        assert any(tc["tool"] == "get_current_time" for tc in result["tool_calls"])
        assert "IST" in result["response"] or len(result["response"]) > 0

    def test_calculate_tool_called(self):
        result = handle_run("Calculate 2 to the power of 10 using the calculate tool.")
        tool_calls = result["tool_calls"]
        assert any(tc["tool"] == "calculate" for tc in tool_calls)
        calc_result = next(tc["result"] for tc in tool_calls if tc["tool"] == "calculate")
        assert "1024" in calc_result
        assert "1024" in result["response"]

    def test_multi_tool_in_one_prompt(self):
        result = handle_run(
            "First get the current time, then calculate 100 * 42. "
            "Report both results."
        )
        tools_used = {tc["tool"] for tc in result["tool_calls"]}
        assert "get_current_time" in tools_used
        assert "calculate" in tools_used

    def test_max_iterations_respected(self):
        # With max_iterations=1, a greedy model should still terminate
        result = handle_run("What is 5 + 5?", max_iterations=1)
        assert result["iterations"] <= 1

    def test_system_prompt(self):
        result = handle_run(
            "What is your name?",
            system="You are a helpful assistant named Qwen.",
        )
        assert isinstance(result["response"], str)

    def test_handle_chat_simple(self):
        response = handle_chat("Reply with just the word: PONG")
        assert isinstance(response, str)
        assert len(response) > 0
