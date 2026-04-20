---
name: market-intel-live-prices
description: Live real-time prices for all 9 monitored tickers via realtime_quotes_agent.py (yfinance primary, Google fallback). Fast and focused — no analysis, no MCP calls, just live prices.
user-invocable: true
---

Fetch live prices for all 9 tickers by calling src/realtime_quotes_agent.py.

## Steps

**1. Execute the realtime quote agent:**

```bash
uv run python src/realtime_quotes_agent.py
```

The script returns JSON with:
- `quotes`: map of asset key to latest numeric price (see key mapping below)
- `errors`: any per-asset fetch errors
- `source`: data source summary
- `timestamp`: ISO timestamp
- `yfinance_success`, `google_success`, `fallback_success`: fetch counts
- `intraday_file`: path to the intraday snapshot JSON written to cache
- `snapshots_today`: number of snapshots written today

**2. Retry once on transient failures:**

```bash
uv run python src/realtime_quotes_agent.py
```

Retry only if the first run fails entirely (for example, network timeout). Do not loop.

**3. Output a clean table:**

The `quotes` dict uses these keys — map to display names when building the table:

| Display name | quotes key |
|---|---|
| Brent | `Brent` |
| Gold | `Gold` |
| DXY | `DXY` |
| Nifty 50 | `Nifty50` |
| USD/INR | `USDINR` |
| India VIX | `IndiaVIX` |
| USD/JPY | `USDJPY` |
| Nasdaq | `Nasdaq` |
| US 10Y | `US10Y` |

```
## Live Prices — [DATE TIME]

| Asset       | Price     |
|-------------|-----------|
| Brent       | ...       |
| Gold        | ...       |
| DXY         | ...       |
| Nifty 50    | ...       |
| USD/INR     | ...       |
| India VIX   | ...       |
| USD/JPY     | ...       |
| Nasdaq      | ...       |
| US 10Y      | ...       |
```

Append metadata lines below the table:
- `Source: ...`
- `Fetch counts: yfinance=X, google=Y, fallback=Z`

If any symbols fail, add:
- `Errors:` followed by one line per asset from `errors`

That's it. No web searches, no portfolio checks, no news.
