---
name: market-intel-watchlist-check
description: Live price check for all 9 watchlist stocks vs entry zones. Auto-patches WIKI_WATCHLIST.md prices if last-updated date differs from today.
user-invocable: true
---

Run a live watchlist check for all 9 post-war recovery stocks.

## Step 1 — Fetch live prices (Safari-first, get_live_ticker fallback)

**Primary method: Safari** — open one tab, navigate sequentially through all 9 tickers, close when done.

Yahoo Finance URLs for NSE stocks:

| Name | URL |
|------|-----|
| IndiGo | `https://finance.yahoo.com/quote/INDIGO.NS/` |
| BPCL | `https://finance.yahoo.com/quote/BPCL.NS/` |
| Federal Bank | `https://finance.yahoo.com/quote/FEDERALBNK.NS/` |
| Adani Ports | `https://finance.yahoo.com/quote/ADANIPORTS.NS/` |
| GE Shipping | `https://finance.yahoo.com/quote/GESHIP.NS/` |
| L&T | `https://finance.yahoo.com/quote/LT.NS/` |
| Sobha | `https://finance.yahoo.com/quote/SOBHA.NS/` |
| Bosch | `https://finance.yahoo.com/quote/BOSCHLTD.NS/` |
| Pidilite | `https://finance.yahoo.com/quote/PIDILITIND.NS/` |

Open the first URL with `open`, use `navigate` for all subsequent ones (reuses same tab):

```bash
# First ticker
~/workspace/claude_for_mac_local/tools/safari_control.sh open "https://finance.yahoo.com/quote/INDIGO.NS/"
sleep 4
~/workspace/claude_for_mac_local/tools/safari_js.sh "var p = document.querySelector('[data-testid=qsp-price]'); var c = document.querySelector('[data-testid=qsp-price-change-percent]'); (p ? p.innerText : 'N/A') + ' | ' + (c ? c.innerText : 'N/A')"

# Subsequent tickers — navigate in same tab
~/workspace/claude_for_mac_local/tools/safari_control.sh navigate "https://finance.yahoo.com/quote/BPCL.NS/"
sleep 4
~/workspace/claude_for_mac_local/tools/safari_js.sh "var p = document.querySelector('[data-testid=qsp-price]'); var c = document.querySelector('[data-testid=qsp-price-change-percent]'); (p ? p.innerText : 'N/A') + ' | ' + (c ? c.innerText : 'N/A')"
# ... repeat for remaining tickers

# Close tab when done
~/workspace/claude_for_mac_local/tools/safari_control.sh close-tab
```

If JS returns `N/A | N/A`, wait 2–3 more seconds and retry once before giving up.

**Fallback (only if Safari fails entirely):** use `get_live_ticker` via MCP for any ticker that Safari couldn't read.

## Step 2 — Load entry zones from portfolio_state.py

Read entry zones from `src/portfolio_state.py` — the `WATCHLIST` list of `WatchlistEntry` objects. Each has: `name`, `ticker`, `wave`, `zone_low`, `zone_high`, `note`.

```bash
uv run python -c "
import sys
sys.path.insert(0, 'src')
from portfolio_state import WATCHLIST
for s in WATCHLIST:
    print(f'{s.name}: zone {s.zone_low}–{s.zone_high} wave={s.wave} ({s.note})')
"
```

## Step 3 — Compare live prices to entry zones

For each stock, compute:
- **Gap to zone top** = (live price − zone_high) / zone_high × 100
- Status rules:
  - Live price < zone_low → `🟢 BELOW ZONE — deep discount`
  - Live price ≥ zone_low and ≤ zone_high → `🟢 IN ZONE`
  - Live price within 10% above zone_high → `⚠️ NEAR ZONE`
  - Live price > 10% above zone_high → `Watch`
  - GESHIP always → `⛔ POST-CEASEFIRE ONLY` (regardless of price)

## Step 4 — Check signal status

```bash
uv run python -c "
import sys
sys.path.insert(0, 'src')
from tools import check_ceasefire_signals
print(check_ceasefire_signals())
"
```

Use the signal status to determine which waves are actionable:

| Signal status | Actionable waves |
|--------------|-----------------|
| `active` (0 signals) | None — hold; accumulate only on extreme Zone 2 dips |
| `watch` (1 signal) | Pre-position Wave 1 stocks if IN ZONE |
| `confirmed` (2+ signals) | Execute Wave 1 immediately; start Wave 2 |

## Step 5 — Auto-patch WIKI_WATCHLIST.md

Read `$VAULT_PATH/Documentation/market-intel/WIKI_WATCHLIST.md`. Check the `Last updated:` date in line 3 (format: `**Last updated:** YYYY-MM-DD`).

**If today's date differs from the last-updated date:**

1. Use the Edit tool to update each stock's price in the Master Table — the `Current` column (format: `₹X,XXX` or `₹X,XXX (Mon DD)` for partial data).
2. Update the `Last updated:` date on line 3 to today's date.
3. Update the `War status:` text if signal status has changed.

**If today's date matches the last-updated date:** skip the wiki edit — prices already current.

## Step 6 — Report

Output in this format:

```
## Watchlist Check — [DATE]
Signal status: [ACTIVE / WATCH / CONFIRMED] (X/4 signals)

| Stock         | Live ₹  | Entry Zone ₹     | Gap to Zone | Status               |
|---------------|---------|------------------|-------------|----------------------|
| IndiGo        | X,XXX   | 3,500–3,700      | +X.X%       | Watch / ⚠️ NEAR / 🟢 IN / 🟢 BELOW |
| BPCL          | XXX     | 270–285          | +X.X%       | Watch / ⚠️ NEAR / 🟢 IN / 🟢 BELOW |
| Federal Bank  | XXX     | 235–245          | +X.X%       | Watch / ⚠️ NEAR / 🟢 IN / 🟢 BELOW |
| Adani Ports   | X,XXX   | 1,250–1,290      | +X.X%       | Watch / ⚠️ NEAR / 🟢 IN / 🟢 BELOW |
| GE Shipping   | X,XXX   | 1,050–1,100      | —           | ⛔ POST-CEASEFIRE ONLY |
| L&T           | X,XXX   | 3,000–3,100      | +X.X%       | Watch / ⚠️ NEAR / 🟢 IN / 🟢 BELOW |
| Sobha         | X,XXX   | 1,050–1,100      | +X.X%       | Watch / ⚠️ NEAR / 🟢 IN / 🟢 BELOW |
| Bosch         | XX,XXX  | 27,000–28,000    | +X.X%       | Watch / ⚠️ NEAR / 🟢 IN / 🟢 BELOW |
| Pidilite      | X,XXX   | 1,250–1,280      | +X.X%       | Watch / ⚠️ NEAR / 🟢 IN / 🟢 BELOW |

### Stocks at or near entry zones
[List only BELOW ZONE / IN ZONE / NEAR ZONE stocks with specific action]

### Action
[Based on signal status — what to do now]

Wiki: [Updated ✓ / Already current — no edit needed]
```

Hard rules — always enforce:
- GESHIP: never buy during active war, regardless of price
- No position from dry powder — dry powder is reserved for Nifty tranche deployment
- Wave 1 sizing: small — mean-reversion trade, not a hold
- Single spike cap: max 50% of available savings in one event
