package ToolCallGatesPackage {
    private import Foundation::ModelProvenance;
    private import LocalMacSystem::Dispatcher;

    doc
    /*
     * The pre-check "gate" mechanism that runs inside Dispatcher's invoke
     * choke point before a domain handler executes, plus the call-outcome
     * logging that runs after. Source: src/tool_hooks.py.
     */

    part def ToolCallGates {
        doc
        /*
         * Owns the ordered precheck list; every guard reads the persisted
         * SessionCallLog. Invoked once per domain__action call via
         * tool_called(domain, action, kwargs) as a context manager; a
         * failed precheck raises Refused (a PermissionError subclass)
         * before the wrapped handler ever runs.
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
         * or _vault_dir, which raise Refused unless the resolved
         * path (absolute, `..` and symlinked folders included) stays under
         * the resolved VAULT_PATH. tool_called logs that refusal as
         * blocked=1 like a precheck refusal. Nothing enforces that a new
         * handler uses the helpers instead of joining onto VAULT_PATH itself.
         * Source: src/tools/vault.py:_inside_vault, _vault_path, _vault_dir;
         * src/tool_hooks.py:tool_called, Refused.
         */
    }

    part def IMessageRecipientGuard {
        doc
        /*
         * Blocks imessage__send unless contacts__search ran within the
         * last gateWindowSeconds AND that search's own recorded "found"
         * flag (from SessionCallLog) is True — a stale or empty-result
         * search (contacts__search returned []) still blocks the send.
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
         * The mcp_tool_calls table in tool_hints.sqlite, read by the guards
         * via _recent_call (through _called_recently / _last_found): the
         * most recent row for the prerequisite with ok=1 and blocked=0
         * whose ts is within gateWindowSeconds. Its nullable `found`
         * column holds the result-quality flag from _FOUND_CHECKS. Being
         * persisted, it is shared by every process that logs calls — the
         * MCP server and each `mac` CLI invocation — so a prerequisite met
         * in one process satisfies a gate in another. A failed read counts
         * as no prerequisite, so the guards fail closed.
         * Source: src/tool_hooks.py:_recent_call, _ensure_schema, _FOUND_CHECKS.
         */
    }

    requirement def GateBlocksBeforeHandlerRuns {
        doc
        /*
         * A precheck failure must raise Refused before the wrapped handler
         * executes, and must be logged with blocked=1 — the handler must
         * never run on a blocked call. A Refused the handler raises itself
         * (VaultPathContainment) is also logged with blocked=1. A plain
         * PermissionError from the OS is logged as an ordinary error.
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
         * ok/error/blocked/reason/duration_ms/found. That same table is the
         * SessionCallLog the guards read, which consider only successful,
         * unblocked rows.
         * Source: src/tool_hooks.py:_log_call, tool_called (finally block).
         */
    }
    satisfy requirement EveryCallIsLogged by ToolCallGates;

    @ModelProvenance {
        derivedFromCommit = "babd2f8ee9da3d7c751de3702d56b089db8a58ae";
        derivedAt = "2026-10-26";
        modelledPaths = (
            "src/tool_hooks.py",
            "src/tools/vault.py"
        );
    }
}
