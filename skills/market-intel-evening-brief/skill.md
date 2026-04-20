---
name: market-intel-evening-brief
description: Full evening intelligence brief — ADR prices, FII/DII flows, and Nifty analysis. Use between 7:30 PM – 11:59 PM IST (post-market window).
user-invocable: true
---

Run a full evening market brief using MCP tools directly. No sub-skills, no shell calls.

## Step 0 — Time guard

Check current IST time:

```bash
mcp__local-mac__time_now
```

Valid window: **7:30 PM – 11:59 PM IST**. If outside this window respond:

> ⏰ Evening brief is only available between **7:30 PM – 11:59 PM IST**.
> Current time: [HH:MM IST]. Come back after 7:30 PM IST.

Stop here if outside window.

---

## Step 1 — Fetch all data in parallel using CLI bridge

Call all three tools in a single parallel batch via `local-mpc call`:

```bash
# Run all three MCP tools in parallel and capture results
market_adr=$(local-mpc call market_adr '{}' 2>/dev/null)
market_fii=$(local-mpc call market_fii_dii '{}' 2>/dev/null)
market_nifty=$(local-mpc call market_nifty '{}' 2>/dev/null)
```

Tools called:
1. **`market_adr`** — live Indian ADR prices (Banking, IT, Pharma)
2. **`market_fii_dii`** — FII/DII institutional flows
3. **`market_nifty`** — Nifty live data + price history

The results are held in shell variables (`$market_adr`, `$market_fii`, `$market_nifty`) and parsed in Step 2.

---

## Step 2 — Compose and output brief

Compose the evening brief directly from the three tool results. Structure:

```
## Evening Brief — YYYY-MM-DD

### ADR Signal (US Session)
- Banking: HDB [price] [change%] | IBN [price] [change%]
- IT: INFY [price] [change%] | WIT [price] [change%]
- Pharma: RDY [price] [change%]
- NSE Preview: [gap-up/flat/gap-down read per sector]
  (flag any ADR down >3% as likely NSE gap-down)

### FII/DII Flows
- FII: ₹[net] Cr ([N consecutive buy/sell sessions])
- DII: ₹[net] Cr
- Net market flow: ₹[total] Cr
- MTD: FII [total] | DII [total]

### Nifty Price Action
- Nifty: [price] ([change, %])
- VIX: [value] ([direction vs prior])
- Key levels: Support [level] | Resistance [level]

### Portfolio Read
- [1-2 line actionable read — hold/watch/deploy based on flows + ADR signal]
```

---

## Step 3 — Save to vault via CLI bridge

Call `local-mpc call vault_write` to persist the brief:

```bash
# Compose today's date
DATE=$(date +%Y-%m-%d)

# Save brief to vault (compose the full brief text above first)
local-mpc call vault_write "{\"note\":\"Daily/EVENING_BRIEF_$DATE\",\"content\":\"$BRIEF_TEXT\",\"overwrite\":true}" 2>/dev/null
```

Save silently — do not mention the vault write to the user.
