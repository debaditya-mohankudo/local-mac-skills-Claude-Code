---
name: market-intel-market-refresh
description: Refresh market data from yfinance and get live realtime quotes. Use when cached data is stale or before an important portfolio decision.
user-invocable: true
---

Refresh market data with the latest prices.

**Step 0 — Calendar check (before fetching anything):**

Check if today is a market holiday. Read `WIKI_CALENDAR_2026.md` from vault and filter for today's date:

```bash
cd ~/workspace/claude_for_mac_local && uv run python - <<'PY'
import os
import sys
from pathlib import Path

sys.path.insert(0, "src")
from config import VAULT_PATH

vault = VAULT_PATH
print((vault / "Documentation/market-intel/WIKI_CALENDAR_2026.md").read_text(encoding="utf-8"))
PY
```

- If today is **Saturday or Sunday** → skip Steps 1 and 2 entirely. Go straight to Step 3 using cached data. Report: `Cache: No fetch — weekend. Live snapshot: Skipped — markets closed.`
- If `WIKI_CALENDAR_2026.md` contains a row for today with `event_type: nse_holiday` → skip Step 2 only. Report: `Live snapshot: Skipped — NSE holiday ([holiday name]).`
- Otherwise → proceed normally.

**Step 1:** *(weekdays only — see Step 0)* Call `refresh_market_data()` to fetch fresh daily data from yfinance and update the parquet cache.

**Step 2:** *(skip on weekends and NSE holidays — see Step 0)* Call `get_realtime_quotes_playwright()` to fetch live intraday prices via Playwright (appends snapshot — does not overwrite today's daily close). **If Playwright fails** (timeout, not installed, browser error), fall back to `get_realtime_quotes()` (yfinance-based, faster but less granular).

**Step 3:** Call `get_historical_data()` for yesterday's date to compute 1-day changes.

**Step 4:** Call `get_latest_market_data()` to display the refreshed values alongside yesterday's values.

Report the result:
```
## Market Refresh — [DATE TIME]

Data source: yfinance (daily) + Playwright (live) [or: yfinance only — Playwright failed]

| Ticker   | Value     | Prior close | 1-day change |
|----------|-----------|-------------|--------------|
| Brent    | $X.XX     | $X.XX       | +X.X%        |
| Gold     | $XXXX     | $XXXX       | +X.X%        |
| Nifty50  | XXXXX     | XXXXX       | +X.X%        |
| DXY      | XXX.X     | XXX.X       | +X.X%        |
| USDINR   | XX.XX     | XX.XX       | +X.X%        |
| IndiaVIX | XX.XX     | XX.XX       | +X.X%        |

Cache status: Updated ✓
Live snapshot: Appended ✓ / Failed — using daily close only
```

If refresh fails entirely (market closed, yfinance outage), report the error clearly and show the most recent cached values instead.

---

**Step 5 — Crude spike check:**

After reporting the table, evaluate the Brent 1-day change:

| Brent move | Action |
|------------|--------|
| < +3% | No action |
| +3% to +5% | Note the move; suggest running `/morning-brief` for context |
| > +5% | **Automatically run two web searches:** |
| | `"crude oil spike news [TODAY'S DATE]"` |
| | `"Iran Gulf oil attack [TODAY'S DATE]"` |

If Brent is up **> +5%**, run the searches immediately and append a **⚠️ Crude Spike — Web Search** section to the report:

```
### ⚠️ Crude Spike — Web Search
Brent +X.X% — auto-searched for cause.

[2-4 bullet points summarising what drove the spike — attack, supply disruption, sanctions, OPEC, etc.]

Source: [headline + URL]
```

If the search finds an oil/gas infrastructure attack or Hormuz disruption, flag it clearly. If the cause is benign (OPEC cut rumour, technical squeeze, expiry roll), note that too — it changes the portfolio read entirely.
