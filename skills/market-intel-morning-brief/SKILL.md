---
name: market-intel-morning-brief
description: Full morning intelligence brief — news digest, latest market data, ceasefire signals, and deployment triggers. Use this at the start of each trading day.
user-invocable: true
wiki: "[[MARKET_INTEL_MORNING_BRIEF]]"
---

Run the full morning intelligence brief for the Iran-Gulf War 2026 portfolio.

> **Architecture:** All vault ops use `obsidian_*` tools via the `local-mac` MCP server. All market/macOS ops use Python MCP server tools. `local-mpc` is retired. See vault: `Projects/SWIFT_CLI_MCP_MIGRATION.md`

## Step 0 — Time guard

Before doing anything else, get current IST time via `mcp__local-mac__time_now`:

```bash
mcp__local-mac__time_now
```

If the time is **before 6:00 AM** or **after 9:15 AM IST**, stop and respond:

> ⏰ Morning brief is only available between **6:00 AM – 9:15 AM IST** (pre-market window).
> Current time: [HH:MM IST]. Come back during the pre-market window.

---

## Step 0b — Clean Tmp/

Delete stale notes from any previous run via Obsidian MCP:

```
obsidian_delete: Tmp/brief_news
obsidian_delete: Tmp/brief_market
obsidian_delete: Tmp/brief_ceasefire
obsidian_delete: Tmp/brief_live_prices
obsidian_delete: Tmp/brief_triggers
obsidian_delete: Tmp/brief_risk
obsidian_delete: Tmp/brief_fii_dii
```

Errors expected if notes don't exist — ignore all.

---

> [!NOTE] Always persist tool output to vault Tmp/ — never hold in context memory.
> Write each tool result to `Tmp/` immediately via Obsidian MCP (`obsidian_create`). Read from vault when composing the report. Delete Tmp/ notes after report is saved.

**Step 1 (parallel):** Call these MCP tools simultaneously, write each result to Tmp/:

- `market_get_daily_news_digest` → `obsidian_create path="Tmp/brief_news"`
- `market_get_latest_data` → `obsidian_create path="Tmp/brief_market"`
- `market_check_ceasefire_signals` → `obsidian_create path="Tmp/brief_ceasefire"`
- `/market-intel-live-prices` skill → `obsidian_create path="Tmp/brief_live_prices"` (live real-time prices: Brent, Gold, DXY, Nifty, USD/INR, VIX, USD/JPY, Nasdaq, US 10Y)

> [!NOTE] `market_get_latest_data` returns yesterday's EOD cache — often stale pre-market. Always prefer live prices from the live-prices skill for the Markets section and signal flag check.

**Step 1b — Web search (run after Step 1, parallel with Step 2):**

Use the `/local-mac-safari` skill to run two targeted Google searches (sequentially in same tab, no new tabs):

- `"Iran oil gas infrastructure attack [TODAY'S DATE]"`
- `"Gulf energy attack Saudi UAE Qatar [TODAY'S DATE]"`

Scan for strikes on Iranian/Gulf energy infrastructure, Hormuz disruption. If web search reveals something the news digest missed, add a **⚠️ Web Search — Breaking** section. If nothing new, skip silently.

**Step 2 (parallel):** Call simultaneously, write each result to Tmp/:

- `market_check_deployment_triggers` → `obsidian_create path="Tmp/brief_triggers"`
- `market_get_signal_risk_level` → `obsidian_create path="Tmp/brief_risk"`

**Step 3:** Call `market_get_fii_dii_activity` → `obsidian_create path="Tmp/brief_fii_dii"`. Report net FII/DII and consecutive streak.

**Step 4:** Call `market_get_portfolio_status` to get `deployment_log` entries for last deployment context.

**Step 5:** Read all Tmp/ notes via `obsidian_read`. Compose brief in this format:

```
## Morning Brief — [DATE]

### Geopolitical
[2-3 key headlines from news digest]

### Markets *(live — Yahoo Finance)*
| Asset | Price | Day Change | Trend |
|-------|-------|------------|-------|
| Brent | $X | +X% | ▲/▼ |
| Gold  | $X | +X% | ▲/▼ |
| Nifty | X  | +X% | ▲/▼ or pre-mkt |
| DXY   | X  | +X% | ▲/▼ |
| USDINR| ₹X | +X% | ▲/▼ |
| VIX   | X  | +X% | ▲/▼ |
| Nasdaq| X  | +X% | ▲/▼ |
| US 10Y| X% | +X% | ▲/▼ |

### FII/DII
FII: [net] | DII: [net] | Streak: [X consecutive sell/buy sessions]

### Signal Status: [ACTIVE / WATCH / CONFIRMED]
Signals fired: X/4 — [list which ones]

### Portfolio Action
[HOLD / DEPLOY / REVIEW — with specific reasoning]
Dry powder: ₹XL | Next trigger: Nifty XXXXX → ₹XL
Single spike cap: ₹XL (50% of dry powder)
Last deployment: [date, amount, asset — from deployment log]

### Risk Level: [LOW / MEDIUM / HIGH / CRITICAL]
Ceasefire probability: X%
```

Keep brief factual and actionable. Deb makes the final decision — do not recommend actions outside the deployment triggers in portfolio_state.yaml.

**If any tool call fails:** report error inline and continue. Do not abort for one failure.

**Step 6 — Save to vault and cleanup:**

```
obsidian_create: path="Daily/MORNING_BRIEF_[YYYY-MM-DD]" content=[full brief text]
```

Then delete all Tmp/ notes via `obsidian_delete`:

```
obsidian_delete: Tmp/brief_news
obsidian_delete: Tmp/brief_market
obsidian_delete: Tmp/brief_ceasefire
obsidian_delete: Tmp/brief_live_prices
obsidian_delete: Tmp/brief_triggers
obsidian_delete: Tmp/brief_risk
obsidian_delete: Tmp/brief_fii_dii
```

Done silently — no mention to user.

**Step 7 — Foundation Models summary (on-device AI):**

Call MCP tool `foundation_models_query` with prompt:

> "Summarise this morning brief in exactly 5 bullet points. Be concise and factual. Focus on: key geopolitical event, market direction, FII/DII stance, signal status, and portfolio action.\n\nBrief:\n[BRIEF_CONTENT]"

Append result to vault via `obsidian_append path="Daily/MORNING_BRIEF_[DATE]"`:

```markdown

---

## TL;DR *(Foundation Models — on-device)*

[SUMMARY]
```

If Foundation Models call fails, append: `*Summary unavailable — requires macOS 15.0+ with Foundation Models framework*`
