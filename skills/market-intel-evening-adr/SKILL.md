---
name: market-intel-evening-adr
description: Evening ADR check — live prices for key Indian ADRs on NYSE (Banking, IT, Pharma). Use between 7 PM – 9:15 AM IST (US market hours through NSE open).
user-invocable: true
---

Run an evening ADR check for key Indian stocks listed on NYSE.

## Step 0 — Time guard

Before doing anything else, run:

```bash
mcp__local-mac__time_now
```

Parse the current IST hour and minute. The valid window is **7:00 PM – 9:15 AM IST** (US market hours through NSE open). If the time is outside this window (i.e., between 9:16 AM and 6:59 PM), do NOT run the check. Instead respond:

> ⏰ Evening ADR check is only available between **7:00 PM – 9:15 AM IST** (US market hours through NSE open).
> Current time: [HH:MM IST]. Come back after 7 PM IST or before 9:15 AM IST.

Stop here — do not execute any further steps.

If the time is within 7:00 PM – 9:15 AM IST, proceed.

---

## Step 1 — Fetch live ADR quotes

Call `get_india_adr_quotes()` to get live prices for all 5 Indian ADRs grouped by sector.

## Step 2 — Report

Output in this format:

```
## India ADR Check — [DATE] | [market_note]

| Sector | Ticker | Name | Price (USD) | Prev Close | Change | % |
|--------|--------|------|-------------|------------|--------|---|
| Banking | HDB | HDFC Bank | $XX.XX | $XX.XX | [+/-]X.XX | [+/-]X.XX% |
| Banking | IBN | ICICI Bank | ... | ... | ... | ... |
| IT | INFY | Infosys | ... | ... | ... | ... |
| IT | WIT | Wipro | ... | ... | ... | ... |
| Pharma | RDY | Dr. Reddy's | ... | ... | ... | ... |

### NSE Preview
[2-3 sentences: which sectors/stocks are under pressure, which are holding,
and what this implies for the NSE open tomorrow. Flag any stock down >3%
as a likely gap-down on NSE.]
```

**Arrows:** Use ▲ for positive, ▼ for negative.

**NSE Preview rules:**
- ADR down >3% → flag as likely NSE gap-down tomorrow
- ADR down 1–3% → moderate pressure, watch opening
- ADR up >2% → likely positive NSE open for that stock
- If US markets are pre-market or after-hours, note that prices may not be final

**Errors:** If any ticker fails, note it but do not fail the whole report.
