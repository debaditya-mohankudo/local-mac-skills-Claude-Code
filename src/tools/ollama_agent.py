"""Tool-calling agent loop using qwen2.5:3b via Ollama."""
from __future__ import annotations

import ast
import datetime
import operator
from typing import Any

import ollama

MODEL = "qwen2.5:3b"
MAX_ITERATIONS = 10

# ---------------------------------------------------------------------------
# Built-in tools exposed to the model
# ---------------------------------------------------------------------------

_TOOL_SCHEMAS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Returns the current date and time in IST.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": (
                "Evaluates a safe arithmetic expression and returns the result. "
                "Supports +, -, *, /, **, //, %, and parentheses."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Arithmetic expression to evaluate, e.g. '2 ** 10 + 5'",
                    }
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_available_tools",
            "description": "Lists all built-in tools available in this agent.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]

_ALLOWED_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}


def _safe_eval(expr: str) -> float | int:
    """Evaluate arithmetic-only AST — no builtins, no names."""
    def _eval(node: ast.AST) -> Any:
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPS:
            return _ALLOWED_OPS[type(node.op)](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPS:
            return _ALLOWED_OPS[type(node.op)](_eval(node.operand))
        raise ValueError(f"Unsupported expression: {ast.dump(node)}")

    return _eval(ast.parse(expr, mode="eval"))


def _dispatch_tool(name: str, args: dict) -> str:
    if name == "get_current_time":
        now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5, minutes=30)))
        return now.strftime("%Y-%m-%d %H:%M:%S IST")
    if name == "calculate":
        expr = args.get("expression", "")
        try:
            result = _safe_eval(expr)
            return str(result)
        except Exception as e:
            return f"Error: {e}"
    if name == "list_available_tools":
        names = [t["function"]["name"] for t in _TOOL_SCHEMAS]
        return ", ".join(names)
    return f"Unknown tool: {name}"


# ---------------------------------------------------------------------------
# Agent loop
# ---------------------------------------------------------------------------

def handle_run(prompt: str, system: str = "", max_iterations: int = MAX_ITERATIONS) -> dict:
    """
    Run a tool-calling agent loop using qwen2.5:3b via Ollama.

    The agent can call built-in tools (get_current_time, calculate,
    list_available_tools) and loops until it produces a final text response
    or reaches max_iterations.

    Args:
        prompt:         User message to send to the agent.
        system:         Optional system prompt override.
        max_iterations: Max tool-call rounds before forcing a final answer.

    Returns:
        dict with keys:
            response   — final text answer from the model
            iterations — number of tool-call rounds used
            tool_calls — list of {tool, args, result} dicts
    """
    messages: list[dict] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    iterations = 0
    tool_call_log: list[dict] = []

    while iterations < max_iterations:
        reply = ollama.chat(model=MODEL, messages=messages, tools=_TOOL_SCHEMAS)
        msg = reply.message

        if not msg.tool_calls:
            return {
                "response": msg.content or "",
                "iterations": iterations,
                "tool_calls": tool_call_log,
            }

        # Append assistant turn with tool calls
        messages.append({"role": "assistant", "content": msg.content or "", "tool_calls": msg.tool_calls})

        # Execute each tool call and append results
        for tc in msg.tool_calls:
            name = tc.function.name
            args = dict(tc.function.arguments) if tc.function.arguments else {}
            result = _dispatch_tool(name, args)
            tool_call_log.append({"tool": name, "args": args, "result": result})
            messages.append({"role": "tool", "content": result})

        iterations += 1

    # Force a final answer after hitting max_iterations
    messages.append({
        "role": "user",
        "content": "Please provide your final answer based on the tool results so far.",
    })
    final = ollama.chat(model=MODEL, messages=messages)
    return {
        "response": final.message.content or "",
        "iterations": iterations,
        "tool_calls": tool_call_log,
    }


def handle_chat(prompt: str) -> str:
    """
    Simple single-turn chat with qwen2.5:3b (no tools).

    Returns the model's text response.
    """
    reply = ollama.chat(model=MODEL, messages=[{"role": "user", "content": prompt}])
    return reply.message.content or ""
