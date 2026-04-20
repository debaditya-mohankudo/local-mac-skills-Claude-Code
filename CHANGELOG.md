# Changelog — claude_for_mac_local

All notable changes to this project are documented here.

**→ Full changelog with implementation details:** Vault → `Documentation/market-intel/WIKI_CHANGELOG.md`

---

## 2026-04-13

### Morning Brief Tools Migrated to Native Swift MCP
- **All 8 market-intel tools now available:** 6 native Swift (instant), 2 Python fallback
- Created `MarketIntelNativeTool.swift` with all core tools: market data, ceasefire signals, deployment triggers, risk level, FII/DII, portfolio status
- Parquet → SQLite migration complete (`market_intel.sqlite`, `market.sqlite`)
- **Zero Python overhead** for cached operations; instant reads
- All tools tested and operational ✅
- **See vault:** `Documentation/market-intel/WIKI_CHANGELOG.md` for full details

### Build Identifier
- Git commit hash + timestamp embedded in binary
- CLI: `local-mpc --version`

---

## 2026-04-12

### Gold Regime & Market Prices SQLite Migration
- Migrated market price data from parquet to `market_intel.sqlite`
- Gold regime tools (`GoldRegimeTool.swift`) now native Swift
- SQLite3 C API integration (no polars subprocess overhead)
- See vault: `Documentation/market-intel/WIKI_CHANGELOG.md` § 2026-04-12

---

## 2026-04-05

### Native Swift MCP Tools (8 tools)
- CalendarTool, ContactsTool, iMessageTool, MailTool, RemindersManager, NotesTool, ProcessTool, ScreenTool
- See vault: `Documentation/Tools/WIKI_HOME.md` for details

---

## 2026-03-24

### MCP Connection Pool & local-mpc CLI
- Persistent connection pooling (1.6x–3.7x speedup)
- local-mpc Swift CLI bridge for shell-based tool invocation

---

**For detailed changelog:** See vault → `Documentation/market-intel/WIKI_CHANGELOG.md`

See `CLAUDE.md` for development workflow and privacy rules.
