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
         * handle_<action> on it. Every registered tool is wrapped by _wrap.
         * Sync calls go through invoke(domain, action, handler, kwargs),
         * the single choke point every domain__action call passes through
         * before and after its handler runs — this is where ToolCallGates
         * is invoked, not inside individual handlers. The `mac` CLI
         * (cli-graph) uses resolve and invoke too, so a CLI call takes the
         * same path without the MCP server. On the MCP path only, _wrap
         * renders an empty-list result as the text "No results.", because
         * FastMCP sends [] as a result with no content.
         * Source: src/dispatcher.py:resolve, invoke, _wrap, _for_mcp.
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
         * directly, always through the invoke/_wrap gate boundary. A
         * handler returns [] when nothing matched.
         * Source: src/dispatcher.py:DOMAIN_MAP, src/tools/*.py.
         */
    }

    part def System {
        doc
        /*
         * Top-level composition: every part in this model is reachable
         * from here. ToolCallGates (see gates.sysml) sits structurally
         * inside Dispatcher's call path, not beside it — Dispatcher.invoke
         * IS the invocation of ToolCallGates around each handler call.
         */
        part server : MCPServer;
        part dispatcher : Dispatcher;
        part handlers : DomainToolHandlers;
    }

    @ModelProvenance {
        derivedFromCommit = "de1538d33683d3962b4dda67779e4068ba431ce3";
        derivedAt = "2026-10-26";
        modelledPaths = (
            "mcp_server.py",
            "src/dispatcher.py"
        );
    }
}
