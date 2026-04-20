---
name: market-intel-ceasefire-reached
description: Ceasefire signal check — which of the 4 signals fired, current status, and risk level. Use when you want a fast read without full morning brief.
user-invocable: true
---

Run a quick ceasefire signal check.

**Run all 4 calls in parallel** — they are independent:

1. `check_ceasefire_signals()` — report which of the 4 signals fired:
   - Oil drop >15% in 1 day
   - Gold rise >4% in 1 day (safe-haven demand surge = war premium rising = ceasefire not yet priced in)
   - India VIX <20
   - Nifty +5% in 1 day

2. `get_signal_risk_level()` — report risk score and ceasefire probability.

3. `get_latest_market_data()` — show current values for the 4 signal assets (Brent, Gold, VIX, Nifty).

4. **Calendar noise check** — read `WIKI_CALENDAR_2026.md` from vault, filter rows matching today's date:

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

Scan the table for today's date (YYYY-MM-DD). Any matching rows are active market events that may produce noise. A single signal firing on an expiry day carries significantly less weight.

**Step 5 — Intraday vs cache comparison (always run):**

Call `get_realtime_quotes()` and compare against `get_latest_market_data()` (prior close). These can run in parallel with steps 1–4.

Compute for each asset: intraday value, prior close value, absolute change, % change.

Show a comparison table:

| Asset | Prior Close | Intraday | Change | % |
|-------|-------------|----------|--------|---|
| Brent | ... | ... | ... | ... |
| Gold | ... | ... | ... | ... |
| Nifty50 | ... | ... | ... | ... |
| India VIX | ... | ... | ... | ... |
| DXY | ... | ... | ... | ... |
| USD/INR | ... | ... | ... | ... |

**Signal re-evaluation:** After computing intraday values, re-check all 4 signals against intraday data (not just prior close). If intraday signal status differs from cached status, flag it explicitly:
- e.g., "VIX was <20 at close but is now 21.4 intraday → signal reversed, count drops to 0/4"
- e.g., "Gold down −4.2% intraday → new signal fired, count upgrades to 2/4"

Use intraday signal count as the **authoritative status** for the session.

**Note:** Market data may be from prior day's close. If the user needs intraday signals, advise running `/market-refresh` first.

Report status clearly:

- **0 signals** → ACTIVE — war ongoing, hold defensive positioning
- **1 signal** → WATCH — check news for diplomatic context; 1 signal alone is insufficient (could be SPR release, margin calls, F&O expiry)
- **2+ signals** → CONFIRMED — ceasefire likely; stop defensive positioning, hold equity

**Expiry caveat:** If today's date matches any row in `WIKI_CALENDAR_2026.md`, add a ⚠️ Expiry Warning to the output explaining which signal(s) could be noise. Specifically:
- NSE F&O expiry (Thursday) → Nifty +5% signal unreliable
- COMEX roll week / MCX expiry → Gold drop signal unreliable
- SHFE expiry → Gold drop signal unreliable

**Step 6 — Gold drop web search (conditional):**

After steps 1–5, check the Gold intraday % change.

| Gold move | Action |
|-----------|--------|
| > −3% | No search |
| ≤ −3% | **Run two web searches in parallel:** |
| | `"gold price fall reason [TODAY'S DATE]"` |
| | `"gold drop [TODAY'S DATE] Fed dollar margin call ceasefire"` |

The second search catches the most common non-war reasons for gold drops: Fed hawkishness, dollar surge, margin calls during equity selloffs, and ceasefire/de-escalation signals.

If the search runs, append a **### Gold Drop — Why** section to the output:
- 2–3 bullet points explaining the cause
- Classify: **Ceasefire signal** / **Fed/Dollar** / **Margin call/Risk-off** / **Technical (COMEX/MCX expiry)**
- If COMEX roll week or MCX expiry is today (from `WIKI_CALENDAR_2026.md`), flag it — drop may be expiry noise, not a real signal
- If ceasefire-driven: note it may count toward the 2-of-4 confirmation threshold (but needs corroboration)
- If Fed/dollar-driven: note it does NOT count as a ceasefire signal

**Step 7 — Nifty drop web search (conditional):**

After steps 1–5, check the Nifty intraday % change (prefer intraday over cached `changes.nifty_pct` if available).

| Nifty move | Action |
|------------|--------|
| > −2% | No search |
| ≤ −2% | **Run four web searches in parallel:** |
| | `"Nifty fall reason [TODAY'S DATE]"` |
| | `"India stock market crash [TODAY'S DATE]"` |
| | `"India RBI rupee policy rate budget earnings [TODAY'S DATE]"` |
| | `"Nifty Bank BankNifty HDFC Reliance Infosys TCS crash drop [TODAY'S DATE]"` |

If the search runs, append a **### Nifty Drop — Why** section to the output:
- 2–4 bullet points explaining the cause — check for both global AND local triggers
- Classify the cause: **War-driven** / **Global risk-off** / **Domestic** / **Sector/Stock-specific** / **Technical (expiry/squeeze)**

Output format:
```
## Signal Check — [DATE]

Signals fired: X/4  *(intraday)*
- [list fired signals with actual intraday values]
- [list unfired signals]

Status: [ACTIVE / WATCH / CONFIRMED]
Risk Level: [LOW / MEDIUM / HIGH / CRITICAL] (score: X/10)
Ceasefire probability: X%

### Intraday vs Prior Close
| Asset | Prior Close | Intraday | Change | % |
|-------|-------------|----------|--------|---|
| Brent | ... | ... | ... | ... |
| Gold | ... | ... | ... | ... |
| Nifty50 | ... | ... | ... | ... |
| India VIX | ... | ... | ... | ... |
| DXY | ... | ... | ... | ... |
| USD/INR | ... | ... | ... | ... |

[Flag any signal reversals or new signals vs prior close]

### Calendar
[No expiry today — signals at full weight]
OR
⚠️ [event name] today — [which signal(s) may be noise and why]

### Gold Drop — Why  *(only if Gold ≤ −3% intraday)*
Cause: [Ceasefire signal / Fed/Dollar / Margin call / Technical]
- [bullet 1]
- [bullet 2]

Signal weight: [Counts toward ceasefire confirmation / Does NOT count — non-war cause]

### Nifty Drop — Why  *(only if Nifty ≤ −2% intraday)*
Cause: [War-driven / Global risk-off / Domestic / Technical]
- [bullet 1]
- [bullet 2]

Note: [any relevant news context]
```
