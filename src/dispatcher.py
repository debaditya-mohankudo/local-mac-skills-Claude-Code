import importlib
import inspect
from mcp.server.fastmcp import FastMCP

from tool_hooks import tool_called


def _wrap(domain: str, action: str, handler):
    is_async = inspect.iscoroutinefunction(handler)

    if is_async:
        async def wrapped(**kwargs):
            with tool_called(domain, action, kwargs) as call:
                result = await handler(**kwargs)
                call["result"] = result
                return result
    else:
        def wrapped(**kwargs):
            with tool_called(domain, action, kwargs) as call:
                result = handler(**kwargs)
                call["result"] = result
                return result

    wrapped.__name__ = handler.__name__
    wrapped.__doc__ = handler.__doc__
    wrapped.__wrapped__ = handler
    return wrapped


DOMAIN_MAP = {
    "mail":      ("tools.mail",       ["read", "get", "list_drafts", "search", "list_mailboxes", "compose", "delete", "move", "add_local_mailbox"]),
    "imessage":  ("tools.imessage",   ["send", "read"]),
    "contacts":  ("tools.contacts",   ["search"]),
    "calendar":  ("tools.calendar",   ["list_events", "add_event", "delete_event",
                                       "get_events_by_date", "get_upcoming_events",
                                       "get_noise_summary"]),
    "reminders": ("tools.reminders",  ["list", "create", "complete", "delete"]),
    "notes":     ("tools.notes",      ["list", "read", "folders", "add", "delete"]),
    "music":     ("tools.music",      ["play", "pause", "next", "previous", "now_playing",
                                       "volume", "search_play", "list_playlists",
                                       "play_playlist", "play_track", "list_tracks"]),
    "safari":    ("tools.safari",     ["open", "navigate", "current_url", "current_title",
                                       "list_tabs", "close_tab", "close_all_tabs",
                                       "reload", "back", "forward", "screenshot", "js", "read"]),
    "system":    ("tools.system",     ["sleep_now", "sleep_in", "sleep_cancel", "sleep_status",
                                       "sleep_winddown", "notify", "clipboard_read",
                                       "clipboard_write", "process_list", "process_kill",
                                       "spotlight_search", "icloud_list", "foundation_models_query",
                                       "battery_status", "cpu_status", "memory_status"]),
    "podcasts":  ("tools.podcasts",   ["list", "episodes", "recent", "in_progress"]),
    "vpn":       ("tools.vpn",        ["status", "connect", "disconnect", "pause"]),
    "vault":     ("tools.vault",      ["read", "write", "append", "delete", "move", "list",
                                       "links", "backlinks", "daily_read",
                                       "outline", "tags", "tasks", "stats", "section_search",
                                       "folder_search", "tags_search", "filename_search",
                                       "vault_keyword_hints"]),
    "time":      ("tools.time_tools", ["now", "alarm", "wait", "play_sound"]),
    # The astrology domains (panchang, planets, astrology, aq, gochar) moved to
    # a separate private repository. They read birth data for identifiable
    # people, which cannot live in a repository intended to be public.
    "sound":     ("tools.sound",      ["list_devices", "get_output", "set_output",
                                       "get_volume", "set_volume", "mute", "unmute"]),
    "vault_rag": ("tools.vault_rag",  ["index_vault", "query_vault", "fts_vault", "smart_search",
                                       "index_status", "contains_section", "remove_section", "index_file",
                                       "unindexed_files"]),
    "code_rag":  ("tools.code_rag",   ["query", "smart_search", "index_files"]),
    "market":    ("tools.market_intel_tools", ["gold_regime_history", "gold_regime_projection"]),
    "ollama_agent": ("tools.ollama_agent", ["run", "chat"]),
    # "git" removed — the agent already has git through its own shell, and a
    # second path to it here duplicated that surface without adding anything.
    # "portfolio" removed — it held financial holdings, which this repo's own
    # privacy rules keep out of the codebase entirely.
    "connector":    ("tools.connector",    ["health", "list_actions", "execute_action"]),
    # memory, hooks, session, tasks migrated to claude-hooks MCP server
}


def build_dispatcher(mcp: FastMCP) -> None:
    for domain, (module_path, actions) in DOMAIN_MAP.items():
        module = importlib.import_module(module_path)
        for action in actions:
            handler = getattr(module, f"handle_{action}")
            mcp.tool(name=f"{domain}__{action}")(_wrap(domain, action, handler))
