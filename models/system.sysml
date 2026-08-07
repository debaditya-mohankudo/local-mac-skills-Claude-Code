package LocalMacSystem {
    private import Foundation::ModelProvenance;

    doc
    /*
     * Foundational structure of the local-mac MCP server: how a tool call
     * enters the process, how it is routed to a domain handler, and where
     * the single choke point for cross-cutting concerns (gates, logging)
     * sits in that path. See mcp_server.py, src/dispatcher.py.
     */

    part def MCPServer {
        doc
        /*
         * Process entry point. Loads .env, puts src/ on sys.path, builds a
         * FastMCP instance named "local-mac", and hands it to Dispatcher to
         * populate with tools before serving. Owns no domain logic itself.
         * Source: mcp_server.py.
         */
    }

    part def Dispatcher {
        doc
        /*
         * Registers one MCP tool per (domain, action) pair declared in
         * DOMAIN_MAP by importing tools.<module> and resolving
         * handle_<action> on it. Every registered tool is wrapped by _wrap,
         * which is the single choke point every domain__action call passes
         * through before and after its handler runs — this is where
         * ToolCallGates is invoked, not inside individual handlers.
         * Source: src/dispatcher.py.
         */
    }

    part def DomainToolHandlers {
        doc
        /*
         * The domain packages listed in Dispatcher's DOMAIN_MAP (mail,
         * imessage, contacts, calendar, reminders, notes, music, safari,
         * system, podcasts, vpn, vault, time, sound, vault_rag, code_rag,
         * market, ollama_agent, connector). Each exposes handle_<action>
         * functions; Dispatcher is the only caller that invokes them
         * directly, always through the _wrap gate boundary.
         * Source: src/dispatcher.py:DOMAIN_MAP, src/tools/*.py.
         */
    }

    part def System {
        doc
        /*
         * Top-level composition: every part in this model is reachable
         * from here. ToolCallGates (see gates.sysml) sits structurally
         * inside Dispatcher's call path, not beside it — Dispatcher.wrap
         * IS the invocation of ToolCallGates around each handler call.
         */
        part server : MCPServer;
        part dispatcher : Dispatcher;
        part handlers : DomainToolHandlers;
    }

    @ModelProvenance {
        derivedFromCommit = "7c2da7ac34f89807624f0d5672c28235e58f8056";
        derivedAt = "2026-08-07";
        modelledPaths = (
            "mcp_server.py",
            "src/dispatcher.py"
        );
    }
}
