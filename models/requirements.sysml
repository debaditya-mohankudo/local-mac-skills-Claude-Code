package LocalMacRequirements {
    private import Foundation::ModelProvenance;
    private import LocalMacSystem::Dispatcher;
    private import ToolCallGatesPackage::ToolCallGates;

    doc
    /*
     * Requirements that span the foundational call path (Dispatcher) and
     * cross-cutting concerns (ToolCallGates), rather than belonging to
     * either package alone.
     */

    requirement def AllToolCallsFunnelThroughOneChokePoint {
        doc
        /*
         * Every domain__action MCP tool, for every domain in DOMAIN_MAP,
         * is registered via _wrap — there is no direct mcp.tool()
         * registration path that bypasses it. This is what makes
         * ToolCallGates a true choke point rather than an opt-in check
         * some handlers happen to call.
         * Source: src/dispatcher.py:build_dispatcher, _wrap.
         */
    }
    satisfy requirement AllToolCallsFunnelThroughOneChokePoint by Dispatcher;

    requirement def HandlerResultVisibleToLaterGateLogic {
        doc
        /*
         * The wrapped handler's return value must be captured into the
         * tool_called() holder dict (call["result"] = result) before the
         * context manager exits, so gates that need to inspect the
         * previous call's result (e.g. IMessageRecipientGuard reading
         * whether contacts__search actually found someone) can do so via
         * SessionCallLog's "found" flag, not just whether the call
         * happened.
         * Source: src/dispatcher.py:_wrap, src/tool_hooks.py:_found.
         */
    }
    satisfy requirement HandlerResultVisibleToLaterGateLogic by Dispatcher;
    satisfy requirement HandlerResultVisibleToLaterGateLogic by ToolCallGates;

    requirement def NoDomainLogicOutsideToolsPackage {
        doc
        /*
         * Dispatcher only imports tools.<module> and resolves
         * handle_<action> by name — it contains no domain-specific
         * behavior itself, keeping the routing layer generic across all
         * 19 domains it currently serves.
         * Source: src/dispatcher.py:DOMAIN_MAP, build_dispatcher.
         */
    }
    satisfy requirement NoDomainLogicOutsideToolsPackage by Dispatcher;

    @ModelProvenance {
        derivedFromCommit = "a926de74408ce95dbe963cfdc13abd479bbf7c25";
        derivedAt = "2026-08-07";
        modelledPaths = (
            "src/dispatcher.py",
            "src/tool_hooks.py"
        );
    }
}
