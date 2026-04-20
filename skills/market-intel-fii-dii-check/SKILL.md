---
name: market-intel-fii-dii-check
description: FII/DII institutional flow check — today's net buy/sell, consecutive streak, and monthly totals. Use to gauge institutional sentiment.
user-invocable: true
---

Run a FII/DII institutional flow check.

## Step 0 — Time guard

Before doing anything else, run:

```bash
mcp__local-mac__time_now
```

Parse the current IST hour and minute. The valid window is **7:30 PM – 11:59 PM IST** (NSE publishes FII/DII data after market close). If the time is outside this window, do NOT run the check. Instead respond:

> ⏰ FII/DII check is only available between **7:30 PM – 11:59 PM IST** (post-market window, after NSE publishes data).
> Current time: [HH:MM IST]. Come back after 7:30 PM IST.

Stop here — do not execute any further steps.

If the time is within 7:30 PM – 11:59 PM IST, proceed.

---

## Step 0b — Weekend / holiday guard

Check today's day of week. If it is **Saturday or Sunday**, skip Step 1 entirely — NSE is closed, there is no new data. Go directly to Step 2 and report using the most recent vault entry. Note in the report header that markets are closed and data shown is from the last trading day.

## Step 0c — Clean Tmp/

```bash
cd ~/workspace/claude_for_mac_local && uv run python - <<'PY'
import os
import sys
from pathlib import Path

sys.path.insert(0, "src")
from config import VAULT_PATH

vault = VAULT_PATH
fp = vault / "Tmp/fii_dii_today.md"
if fp.exists():
    fp.unlink()
PY
```

## Step 1 — Fetch today's data (weekdays only)

> [!NOTE] Always persist tool output to vault Tmp/ — never hold in context memory.

Call `get_fii_dii_activity()`, save to `Tmp/fii_dii_today`:

```bash
FIIDII=$(cd ~/workspace/claude_for_mac_local && uv run python -c "
import sys, json; sys.path.insert(0, 'src')
from tools import get_fii_dii_activity
print(json.dumps(get_fii_dii_activity(), indent=2, default=str))
" 2>&1 | grep -v "Loaded cache\|Date range\|Last updated")
```

Then save via Obsidian CLI:

```bash
cd ~/workspace/claude_for_mac_local && FIIDII="$FIIDII" uv run python - <<'PY'
import os
import sys
from pathlib import Path

sys.path.insert(0, "src")
from config import VAULT_PATH

vault = VAULT_PATH
fp = vault / "Tmp/fii_dii_today.md"
fp.parent.mkdir(parents=True, exist_ok=True)
fp.write_text(os.environ.get("FIIDII", ""), encoding="utf-8")
PY
```

If it fails, fall back to Playwright scraping of Upstox:

```bash
uv run python -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=['--no-sandbox'])
    page = browser.new_context().new_page()
    page.goto('https://upstox.com/fii-dii-data/', timeout=30000)
    page.wait_for_selector('table', timeout=15000)
    rows = page.query_selector_all('table:first-of-type tr')
    for row in rows:
        txt = row.inner_text().strip()
        if txt and '202' in txt:
            print(txt)
    browser.close()
"
```

## Step 2 — Compute streak and monthly totals from vault

Read the current month's vault note:

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

From the table, compute:
1. **Consecutive streak** — from the most recent entry going backwards, how many sessions in a row has FII been net negative (or net positive)?
2. **Monthly totals** — already in the note footer; verify or recompute.
3. **Cumulative net** — read prior months (`FII_DII_2026-01`, `02`, `03`, etc.) and sum all monthly FII net totals.

## Step 3 — Append today's data to vault

If today's data is new (date not already in the month's note), read the note, edit in the new row, and overwrite via direct file write. Update the Monthly totals footer line.

## Step 4 — Report

```
## FII/DII Check — [DATE]

### Today
| | Buy (₹ Cr) | Sell (₹ Cr) | Net (₹ Cr) |
|---|---|---|---|
| FII | X,XXX | X,XXX | [+/-]X,XXX |
| DII | X,XXX | X,XXX | [+/-]X,XXX |
| Net market flow | | | [+/-]X,XXX |

### Streak
FII: [X consecutive selling/buying sessions] (since [date])

### Monthly Summary
| Month | FII Net (₹ Cr) | DII Net (₹ Cr) |
|-------|----------------|----------------|
| 2026-01 | [+/-]X,XXX | [+/-]X,XXX |
| 2026-02 | [+/-]X,XXX | [+/-]X,XXX |
| 2026-03 | [+/-]X,XXX | [+/-]X,XXX |
| 2026-04 | [+/-]X,XXX | [+/-]X,XXX |

### Cumulative
Total FII net (Jan–today): [+/-]₹X,XXX Cr

### Read
[1-2 sentence interpretation — is FII selling accelerating, decelerating, or reversing?]
```

**Data sources:**
- Primary: `get_fii_dii_activity()` (NSE scrape)
- Fallback: Upstox Playwright scrape
- History: vault `Daily/FII_DII_2026-MM.md` notes

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
out = vault / "Daily/FII_DII_CHECK_YYYY-MM-DD.md"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text("""---
tags: [market-intel, fii-dii, daily, asset/fii-dii]
date: YYYY-MM-DD
related: ["[[Documentation/market-intel/WIKI_FII_POSITIONING]]", "[[Documentation/market-intel/WIKI_SIGNALS]]"]
---

[[Documentation/market-intel/WIKI_FII_POSITIONING]] [[Documentation/market-intel/WIKI_SIGNALS]]

[report content]""", encoding="utf-8")
PY
```

Then delete Tmp/ note:

```bash
cd ~/workspace/claude_for_mac_local && uv run python - <<'PY'
import os
import sys
from pathlib import Path

sys.path.insert(0, "src")
from config import VAULT_PATH

vault = VAULT_PATH
fp = vault / "Tmp/fii_dii_today.md"
if fp.exists():
    fp.unlink()
PY
```

Done silently.
