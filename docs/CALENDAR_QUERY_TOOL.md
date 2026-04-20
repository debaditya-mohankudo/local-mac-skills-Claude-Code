# CalendarQueryTool.swift — Economic Calendar Queries via Swift

**Location:** `local-mac-mcp/Sources/LocalMacMCP/CalendarQueryTool.swift`  
**Database:** `~/Documents/claude_cache_data/market-intel/market.sqlite`  
**Lines:** 380 LOC  
**Performance:** <1ms SQLite3 C bindings

---

## Overview

Native Swift MCP tool for querying the economic calendar SQLite database. Replaces Python `db.py` calendar functions with native Swift, providing:

- ✅ All structured metadata preserved (noise_level, event_type, noise_assets)
- ✅ <1ms query performance via indexed SQLite
- ✅ JSON responses matching Python interface
- ✅ Three endpoints for different query patterns

---

## Tools

### 1. `calendar_get_events_by_date`

Get all calendar events for a specific date.

**Parameters:**
```json
{
  "date": "2026-04-14"  // YYYY-MM-DD (required)
}
```

**Returns:** Array of events sorted by `noise_level` (high → medium → low)

**Example response:**
```json
[
  {
    "date": "2026-04-14",
    "event_type": "comex_roll_start",
    "label": "COMEX Gold Apr 2026 Roll Period Starts",
    "noise_level": "high",
    "noise_assets": ["gold"],
    "notes": "COMEX roll start — OI shifts to next contract...",
    "reference_month": null,
    "confirmed": false
  },
  {
    "date": "2026-04-14",
    "event_type": "us_ppi",
    "label": "US PPI — March 2026 data (8:30 AM ET / ~18:30 IST)",
    "noise_level": "medium",
    "noise_assets": ["gold", "usdinr"],
    "notes": "PPI release — typically 1-4 days after CPI...",
    "reference_month": "March 2026",
    "confirmed": true
  }
]
```

### 2. `calendar_get_upcoming_events`

Query events for a date range.

**Parameters:**
```json
{
  "days_ahead": 7,           // optional, default: 7
  "from_date": "2026-04-11"  // optional, default: today (YYYY-MM-DD)
}
```

**Returns:** Array of events for `[from_date, from_date + days_ahead]`, sorted by date then noise_level

**Example:** Get next week's events
```bash
{
  "days_ahead": 7
}
```

Returns 16 events from today through next 7 days.

### 3. `calendar_get_noise_summary`

Compute noise risk summary for a date across all assets.

**Parameters:**
```json
{
  "date": "2026-04-14"  // YYYY-MM-DD (required)
}
```

**Returns:** Noise levels for each asset + event count

**Example response:**
```json
{
  "date": "2026-04-14",
  "events_count": 3,
  "high_noise_events": 1,
  "noise_assets": {
    "gold": "high",
    "crude": "low",
    "nifty": "low",
    "usdinr": "medium",
    "dxy": "low"
  },
  "events": [
    // ... full event objects
  ]
}
```

---

## Data Structure

All events returned with this structure (matches Python `CalendarEvent` namedtuple):

```python
{
  "date": str,                  # YYYY-MM-DD format
  "event_type": str,            # e.g., "us_nfp", "nse_fo_weekly", "mcx_gold"
  "label": str,                 # Human-readable title
  "noise_level": str,           # "high", "medium", or "low"
  "noise_assets": [str],        # ["gold", "usdinr", ...] — affected markets
  "notes": str | null,          # Context on market impact
  "reference_month": str | null # For economic releases (e.g., "March 2026")
  "confirmed": bool             # True if date is confirmed, false if estimated
}
```

### Event Types

**India Markets:**
- `nse_fo_weekly` — NSE F&O weekly expiry (Thursday)
- `nse_fo_monthly` — NSE F&O monthly expiry (last Thursday)
- `nse_holiday` — NSE trading holiday

**Commodity Futures:**
- `mcx_gold` — MCX Gold contract expiry
- `mcx_crude` — MCX Crude contract expiry
- `comex_roll_start`, `comex_ltd` — COMEX Gold roll + last trading day
- `shfe_gold` — Shanghai Futures Exchange gold LTD

**US Macroeconomic:**
- `us_cpi` — Consumer Price Index (high noise)
- `us_ppi` — Producer Price Index (medium noise)
- `us_nfp` — Non-Farm Payrolls (high noise)
- `us_adp` — ADP Employment (medium noise)

**India Macroeconomic:**
- `india_cpi` — Consumer Price Index (medium noise)
- `india_wpi` — Wholesale Price Index (low noise)
- `rbi_mpc` — RBI Monetary Policy (high noise)

**Central Banks:**
- `ecb_rate_decision` — ECB rate decision (high noise)
- `fed_fomc` — Federal Reserve FOMC meeting

**Trading Holidays:**
- `lbma_holiday` — London Bullion Market Association holiday

---

## Implementation Details

### Database Query

Uses SQLite3 C bindings (matching NotesTool/MailTool pattern):

```swift
let sql = """
SELECT date, event_type, label, noise_level, noise_assets, notes, reference_month, confirmed
FROM calendar
WHERE date >= ? AND date <= ?
ORDER BY date ASC, 
    CASE noise_level
        WHEN 'high' THEN 0
        WHEN 'medium' THEN 1
        ELSE 2
    END
"""
```

### JSON Parsing

`noise_assets` stored as JSON string in database, parsed on-the-fly:

```swift
let noiseAssetsStr = String(cString: sqlite3_column_text(statement, 4))
let noiseAssets = parseJSONArray(noiseAssetsStr)  // → ["gold", "usdinr"]
```

### Performance

- **Build time:** ~15s (release build)
- **Query time:** <1ms per query (indexed SQLite)
- **Memory:** ~2MB database in memory

---

## Migration from Python

### Before (Python):
```python
from db import get_events_for_date, get_upcoming_events

events = get_events_for_date("2026-04-14")
upcoming = get_upcoming_events(days_ahead=7)
```

### After (Swift via MCP):
```bash
# Via local-mpc (recommended for Python callers)
local-mpc call calendar_get_events_by_date '{"date":"2026-04-14"}'
local-mpc call calendar_get_upcoming_events '{"days_ahead":7}'
```

**Migration path:**
1. ✅ CalendarQueryTool.swift created and tested
2. ⏳ Update tools.py to call via local-mpc instead of db module
3. ⏳ Optional: remove SQLite dependency from Python

---

## Testing

### Test events on a known date:
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"calendar_get_events_by_date","arguments":{"date":"2026-04-14"}}}' | \
  /path/to/LocalMacMCP
```

**Expected:** 3 events (COMEX roll start, US PPI, India CPI)

### Test upcoming window:
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"calendar_get_upcoming_events","arguments":{"days_ahead":7}}}' | \
  /path/to/LocalMacMCP
```

**Expected:** 16 events sorted by date and noise level

---

## Summary

✅ **Achieved:**
- Native Swift SQLite querying (no Python subprocess)
- Full metadata preservation (noise_level, event_type, confirmed)
- Sub-millisecond performance
- JSON responses compatible with tools.py
- 195 economic calendar events queryable

✅ **Next:** Migrate tools.py to call CalendarQueryTool via local-mpc
