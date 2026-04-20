---
name: market-intel-gold
description: Gold regime check — current regime, 5-regime history, next-regime projection, and gold action recommendation (BUY / HOLD / TRIM_CANDIDATE / TRIM / DO_NOT_BUY).
user-invocable: true
---

Run a full gold intelligence check — regime classification, projection, and action.

> **Architecture:** All vault ops use `obsidian_*` tools via the `local-mac` MCP server. Market data via Python MCP server tools. `local-mpc` is retired. See vault: `Projects/SWIFT_CLI_MCP_MIGRATION.md`

---

## Reference Gold Wiki (Mandatory Context)

Before analyzing regime & trim decisions, read this wiki via `obsidian_read`:

- **Path:** `Documentation/market-intel/WIKI_GOLD`
- **Contains:** structural case, analyst targets, price floor veto ($4,800), 5-gate trim framework, liquidity crunch vs geopolitical regimes, fund selection, bond yield correlation

Reference it in the report (e.g., "Per WIKI_GOLD Gate 0...").

---

## Tmp/ Contract

All intermediate data lives in `Tmp/` during the skill run. Every Tmp/ note created must be deleted in Step 6.

Notes used:
- `Tmp/gold_history` — raw history JSON
- `Tmp/gold_projection` — raw projection JSON
- `Tmp/gold_live` — live Safari price
- `Tmp/gold_report` — composed report

---

## Step 0 — Clean Tmp/

```
obsidian_delete: Tmp/gold_history
obsidian_delete: Tmp/gold_projection
obsidian_delete: Tmp/gold_live
obsidian_delete: Tmp/gold_report
```

Errors expected if notes don't exist — ignore.

---

## Step 1 — Fetch data into Tmp/ (run in parallel)

**1a.** Call MCP tool `market_get_gold_regime_history` → `obsidian_create path="Tmp/gold_history" content=[result]`

**1b.** Call MCP tool `market_get_gold_regime_projection` → `obsidian_create path="Tmp/gold_projection" content=[result]`

**1c.** Live gold price via Safari — open `https://finance.yahoo.com/quote/GC=F/`, read page, extract price and day % change → `obsidian_create path="Tmp/gold_live" content="Price: $PRICE\nDay Change: CHANGE%\nDate: DATE"`

If today's date is missing from cache (stale):
- Live Gold change > +0.5% → regime is Secular Continuation
- Live Gold change <= -0.5% AND Nifty falling → likely Dollar-Neutral Crash or Liquidity Crunch
- Add stale cache callout to report

---

## Step 2 — Read wiki context

```
obsidian_read: Documentation/market-intel/WIKI_GOLD
```

Focus on: price floor veto ($4,800), Gate 0-4 framework, action labels.

---

## Step 3 — Compose report → Tmp/gold_report

Read `Tmp/gold_history`, `Tmp/gold_projection`, `Tmp/gold_live` via `obsidian_read`. Compose full report and write to `Tmp/gold_report` via `obsidian_create`. Do NOT output to conversation yet.

Report format:

```
---
date: YYYY-MM-DD
tags: [gold, market-intel, daily]
---

[[Documentation/market-intel/WIKI_GOLD]]

## Gold Check — [DATE]

### Gold Action: [BUY / HOLD / TRIM_CANDIDATE / TRIM / DO_NOT_BUY]
- [reason 1]
- [reason 2]
- [reason 3]

Gold allocation: [X.X]% | Target: [X.X]% | Ceiling: 25%
Ceasefire: [active / watch / confirmed]
Live gold: $X,XXX ([+/-X.XX%]) — cache last: YYYY-MM-DD [stale / current]

---

### Current Regime: [regime name] (streak: Xd)

5-day momentum:
  Gold  [+/-X.XX]%/day (rising/falling/flat)
  Nifty [+/-X.XX]%/day (rising/falling/flat)
  DXY   [+/-X.XX]%/day (rising/falling/flat)

### Next Regime Projection ([confidence] confidence)
Most likely: [regime name]

| Regime | Base prob | Adjusted |
|--------|-----------|----------|
| Liquidity Crunch   | X% | X% |
| War Premium Unwind | X% | X% |
| Macro Headwind     | X% | X% |
| Equity Rotation    | X% | X% |
| Secular Cont.      | X% | X% |

Watch for: [single actionable sentence]

### Trigger conditions for each regime
- **Liquidity Crunch:** [condition]
- **War Premium Unwind:** [condition]
- **Macro Headwind:** [condition]
- **Equity Rotation:** [condition]
- **Secular Continuation:** [condition]

---

### Regime History (all available data)
| Regime | Days | % of period |
|--------|------|-------------|
...

Gate 0 veto days: X
Trim candidate days: X

Recent 5 days (newest first):
| Date | Gold% | Nifty% | DXY% | Regime | Flag |
|------|-------|--------|------|--------|------|
...

[[Documentation/market-intel/WIKI_GOLD]]
```

Regime labels:
- 1. Liquidity Crunch — gold down + stocks down + DXY up → DO NOT TRIM
- 2. War Premium Unwind — gold down + stocks up + DXY flat/down → monitor
- 3. Macro Headwind — gold down + DXY up + stocks mixed → possible trim
- 4. Equity Rotation — gold flat/down + stocks up + DXY flat → trim signal
- 5. Secular Continuation — gold up → hold

Flags: X = Gate 0 veto fired | T = Trim candidate (regime 2 or 4, no veto) | blank = neutral

Action labels:
- TRIM — gold at/above 25% ceiling; trim immediately
- TRIM_CANDIDATE — ceasefire confirmed; war premium unwinding; prepare Tranche 1
- DO_NOT_BUY — gold within 2pp of ceiling; no new purchases
- BUY — gold >3pp below target; under-hedged during active war
- HOLD — allocation correct; no action

---

## Step 4 — Output report once

Read `Tmp/gold_report` via `obsidian_read` and output its content to the conversation exactly once. Do not summarise, paraphrase, or repeat.

---

## Step 5 — Save to Daily/ (silent)

```
obsidian_create: path="Daily/GOLD_CHECK_[YYYY-MM-DD]" content=[Tmp/gold_report content]
```

No output, no mention to user.

---

## Step 6 — Clean all Tmp/

```
obsidian_delete: Tmp/gold_history
obsidian_delete: Tmp/gold_projection
obsidian_delete: Tmp/gold_live
obsidian_delete: Tmp/gold_report
```
