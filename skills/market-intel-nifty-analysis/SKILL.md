---
name: market-intel-nifty-analysis
description: Nifty 50 analysis — recent price action, FII/DII flow correlation, VIX context, and upcoming F&O expiry schedule. Use post-market to understand what drove the day.
user-invocable: true
---

Run a Nifty 50 analysis — recent price action, live FII/DII flows, VIX context, F&O OI/PCR, and expiry schedule.

## Step 0 — Time guard

Before doing anything else, run:

```bash
mcp__local-mac__time_now
```

Parse the current IST hour and minute. The valid window is **7:30 PM – 11:59 PM IST** (post-market, after EOD data is available). If the time is outside this window, do NOT run the analysis. Instead respond:

> ⏰ Nifty analysis is only available between **7:30 PM – 11:59 PM IST** (post-market window).
> Current time: [HH:MM IST]. Come back after 7:30 PM IST.

Stop here — do not execute any further steps.

If the time is within 7:30 PM – 11:59 PM IST, proceed.

---

## Step 0b — Clean Tmp/

```bash
cd ~/workspace/claude_for_mac_local && uv run python - <<'PY'
import os
import sys
from pathlib import Path

sys.path.insert(0, "src")
from config import VAULT_PATH

vault = VAULT_PATH
for rel in ("Tmp/nifty_history.md", "Tmp/nifty_quotes.md", "Tmp/nifty_fii_dii.md"):
	fp = vault / rel
	if fp.exists():
		fp.unlink()
PY
```

## Step 1 — Fetch data (parallel)

> [!NOTE] Always persist tool output to vault Tmp/ — never hold in context memory.

Run all simultaneously, saving each to vault Tmp/ via direct file writes:

```bash
# historical data → Tmp/nifty_history
HIST=$(cd ~/workspace/claude_for_mac_local && uv run python -c "
import sys, json; sys.path.insert(0, 'src')
from tools import get_historical_data
from datetime import date, timedelta
end = date.today().isoformat()
start = (date.today() - timedelta(days=10)).isoformat()
print(json.dumps(get_historical_data(start, end), indent=2, default=str))
" 2>&1 | grep -v "Loaded cache\|Date range\|Last updated")

# realtime quotes → Tmp/nifty_quotes
QUOTES=$(cd ~/workspace/claude_for_mac_local && uv run python -c "
import sys, json; sys.path.insert(0, 'src')
from tools import get_realtime_quotes
print(json.dumps(get_realtime_quotes(), indent=2, default=str))
" 2>&1 | grep -v "Loaded cache\|Date range\|Last updated")

# FII/DII activity → Tmp/nifty_fii_dii
FIIDII=$(cd ~/workspace/claude_for_mac_local && uv run python -c "
import sys, json; sys.path.insert(0, 'src')
from tools import get_fii_dii_activity
print(json.dumps(get_fii_dii_activity(), indent=2, default=str))
" 2>&1 | grep -v "Loaded cache\|Date range\|Last updated")

cd ~/workspace/claude_for_mac_local && HIST="$HIST" QUOTES="$QUOTES" FIIDII="$FIIDII" uv run python - <<'PY'
import os
import sys
from pathlib import Path

sys.path.insert(0, "src")
from config import VAULT_PATH

vault = VAULT_PATH
tmp = vault / "Tmp"
tmp.mkdir(parents=True, exist_ok=True)
(tmp / "nifty_history.md").write_text(os.environ.get("HIST", ""), encoding="utf-8")
(tmp / "nifty_quotes.md").write_text(os.environ.get("QUOTES", ""), encoding="utf-8")
(tmp / "nifty_fii_dii.md").write_text(os.environ.get("FIIDII", ""), encoding="utf-8")
PY
```

Also read the calendar from vault (parallel):

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

Scan for rows matching today's date and the next 14 days for upcoming expiry schedule.

For historical FII/DII context (last 5 sessions), read the current month's vault note:

```bash
cd ~/workspace/claude_for_mac_local && uv run python - <<'PY'
import os
import sys
from pathlib import Path

sys.path.insert(0, "src")
from config import VAULT_PATH

vault = VAULT_PATH
print((vault / "Daily/FII_DII_2026-MM.md").read_text(encoding="utf-8"))
PY
```

## Step 2 — F&O Market Data (Safari)

Use the `/local-mac-safari` skill to fetch the NSE F&O market watch page. Open it in a **new tab**.

URL: `https://www.nseindia.com/market-data/equity-derivatives-watch`

Extract: PCR, Total OI (Nifty futures), Top OI strikes (max Call OI = resistance, max Put OI = support).

If the page fails, skip this section.

## Step 3 — Compute changes

For each of the last 5 sessions compute:
- Nifty daily change (points and %)
- VIX change
- FII net, DII net, net market flow

Use `get_fii_dii_activity()` result for today; for earlier sessions use `Monthly/FII_DII_2026-MM.md` vault note.

## Step 4 — Report

```
## Nifty 50 Analysis — [DATE]

### Recent Price Action
| Date | Nifty 50 | Change | VIX | FII Net (₹ Cr) | DII Net (₹ Cr) | Net Flow |
|------|----------|--------|-----|----------------|----------------|----------|

### FII/DII vs Nifty — What's Happening
[For each session with a notable move (>1%), explain the FII/DII dynamic]

### F&O Snapshot
| Metric | Value |
|--------|-------|
| PCR (Put-Call Ratio) | X.XX |
| Nifty Futures Total OI | X.XX Cr |
| Max Call OI Strike | XX,XXX (resistance) |
| Max Put OI Strike | XX,XXX (support) |

### F&O Expiry Context
[Upcoming expiries from WIKI_CALENDAR_2026.md — next 14 days]

### Next F&O Expiry Schedule
| Date | Event | Impact |
|------|--------|--------|

### Read
[2-3 sentences: overall verdict]
```

**If any tool call fails:** report the error inline and continue.

## Step 5 — Save to vault and cleanup

Save report via direct file write:

```bash
cd ~/workspace/claude_for_mac_local && uv run python - <<'PY'
import os
import sys
from pathlib import Path

sys.path.insert(0, "src")
from config import VAULT_PATH

vault = VAULT_PATH
out = vault / "Daily/NIFTY_ANALYSIS_YYYY-MM-DD.md"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text("...", encoding="utf-8")
PY
```

Then delete Tmp/ notes:

```bash
cd ~/workspace/claude_for_mac_local && uv run python - <<'PY'
import os
import sys
from pathlib import Path

sys.path.insert(0, "src")
from config import VAULT_PATH

vault = VAULT_PATH
for rel in ("Tmp/nifty_history.md", "Tmp/nifty_quotes.md", "Tmp/nifty_fii_dii.md"):
	fp = vault / rel
	if fp.exists():
		fp.unlink()
PY
```
