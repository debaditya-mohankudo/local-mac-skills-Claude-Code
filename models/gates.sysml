package ToolCallGatesPackage {
    private import Foundation::ModelProvenance;
    private import LocalMacSystem::Dispatcher;

    doc
    /*
     * The pre-check "gate" mechanism that runs inside Dispatcher's _wrap
     * choke point before a domain handler executes, plus the call-outcome
     * logging that runs after. Source: src/tool_hooks.py.
     */

    part def ToolCallGates {
        doc
        /*
         * Owns the ordered precheck list and the in-memory session-call
         * record every guard reads from. Invoked once per domain__action
         * call via tool_called(domain, action, kwargs) as a context
         * manager; a failed precheck raises PermissionError before the
         * wrapped handler ever runs.
         * Source: src/tool_hooks.py:tool_called, _PRECHECKS.
         */
        attribute gateWindowSeconds : Integer = 120;

        part imessageGuard : IMessageRecipientGuard;
        part mailGuard : MailDeleteGuard;
        part sessionLog : SessionCallLog;
    }

    part def VaultPathContainment {
        doc
        /*
         * Not a precheck: containment lives where vault paths are built, so
         * no vault or vault_rag handler can build one without it. Every
         * caller argument naming a note or folder goes through _vault_path
         * or _vault_dir, which raise PermissionError unless the resolved
         * path (absolute, `..` and symlinked folders included) stays under
         * the resolved VAULT_PATH. tool_called logs that refusal as
         * blocked=1 like a precheck refusal. Nothing enforces that a new
         * handler uses the helpers instead of joining onto VAULT_PATH itself.
         * Source: src/tools/vault.py:_inside_vault, _vault_path, _vault_dir;
         * src/tool_hooks.py:tool_called.
         */
    }

    part def IMessageRecipientGuard {
        doc
        /*
         * Blocks imessage__send unless contacts__search ran within the
         * last gateWindowSeconds AND that search's own recorded "found"
         * flag (from SessionCallLog) is True — a stale or empty-result
         * search still blocks the send.
         * Source: src/tool_hooks.py:_imessage_guard, _last_found.
         */
    }

    part def MailDeleteGuard {
        doc
        /*
         * Blocks mail__delete unless mail__read ran within the last
         * gateWindowSeconds. Presence of the call is sufficient — no
         * result-quality check is registered for mail__read.
         * Source: src/tool_hooks.py:_mail_guard, _called_recently.
         */
    }

    part def SessionCallLog {
        doc
        /*
         * In-memory, per-server-process FIFO (maxlen 100) of
         * (call_name, monotonic_ts, found) for every successful call this
         * process has made. Guards query it via _called_recently /
         * _last_found. Reset on MCP server restart — this is deliberately
         * NOT the same as mcp_tool_calls in tool_hints.sqlite, which
         * persists indefinitely and is written to regardless of outcome.
         * Source: src/tool_hooks.py:_SESSION_CALLS, _FOUND_CHECKS.
         */
    }

    requirement def GateBlocksBeforeHandlerRuns {
        doc
        /*
         * A precheck failure must raise PermissionError before the
         * wrapped handler executes, and must be logged with blocked=1 —
         * the handler must never run on a blocked call. A PermissionError
         * the handler raises itself (VaultPathContainment) is also logged
         * with blocked=1.
         * Source: src/tool_hooks.py:tool_called (for check in _PRECHECKS
         * loop, raised before `yield holder`).
         */
    }
    satisfy requirement GateBlocksBeforeHandlerRuns by ToolCallGates;

    requirement def GateWindowIsSelfContained {
        doc
        /*
         * The 120s gate window is defined and owned entirely within this
         * repo (_GATE_WINDOW_S in src/tool_hooks.py) — it is not derived
         * from or synchronized with any external repo's configuration.
         * Source: src/tool_hooks.py:_GATE_WINDOW_S.
         */
    }
    satisfy requirement GateWindowIsSelfContained by ToolCallGates;

    requirement def EveryCallIsLogged {
        doc
        /*
         * Every domain__action call — blocked, failed, or successful — is
         * recorded to tool_hints.sqlite's mcp_tool_calls table with
         * ok/error/blocked/reason/duration_ms, independent of the
         * in-memory SessionCallLog which only records successful calls.
         * Source: src/tool_hooks.py:_log_call, tool_called (finally block).
         */
    }
    satisfy requirement EveryCallIsLogged by ToolCallGates;

    @ModelProvenance {
        derivedFromCommit = "080409c1511708d98cabc569a64303356be84fe6";
        derivedAt = "2026-10-19";
        modelledPaths = (
            "src/tool_hooks.py",
            "src/tools/vault.py"
        );
    }
}
