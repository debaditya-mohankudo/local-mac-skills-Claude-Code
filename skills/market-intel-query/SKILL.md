---
name: market-intel-query
description: Hybrid query — runs a price condition against the historical parquet DB, clusters results into regimes, fetches news context around each regime, then synthesises a vault-grounded answer. Use when the user asks "what happened last time X was above/below Y?" or references a QUERY_*.md note.
user-invocable: true
---

Answer questions of the form: *"What happened last time [asset] was [above/below] [threshold]?"*

This skill executes a **3-leg hybrid query**:

1. **DB leg** — run `run_query()` against parquet price history to find all regimes
2. **Vault leg** — read the relevant `QUERY_*.md` note for analyst context and wikilinks
3. **Synthesis leg** — Claude merges numbers + news + vault interpretation into a structured answer

---

## When to Use

Trigger phrases:
- "What happened last time oil was below $80?"
- "When did gold last trade above $3,500?"
- "Show me all Brent < 80 regimes"
- "Run QUERY_OIL_BELOW_80"
- "VIX above 25 — when did that happen?"

---

## Step 0 — Clean Tmp/

```bash
cd ~/workspace/claude_for_mac_local && uv run python - <<'PY'
import os
import sys
from pathlib import Path

sys.path.insert(0, "src")
from config import VAULT_PATH

vault = VAULT_PATH
for rel in ("Tmp/query_result.md", "Tmp/query_note.md"):
	fp = vault / rel
	if fp.exists():
		fp.unlink()
PY
```

---

## Step 1 — Parse the user's question

Extract three values:
- `column`: map the asset to the parquet column name

| User says | column |
|-----------|--------|
| oil / crude / brent | `Brent` |
| gold | `Gold` |
| nifty / indian equity | `Nifty50` |
| dollar / dxy | `DXY` |
| rupee / usdinr / inr | `USDINR` |
| vix / india vix | `IndiaVIX` |
| yen / usdjpy | `USDJPY` |
| nasdaq | `Nasdaq` |
| 10y / us rates / yield | `US10Y` |

- `operator`: `<`, `<=`, `>`, `>=`
- `threshold`: numeric value (e.g. 80, 3000, 25)

Also identify the relevant `QUERY_*.md` note if one exists (e.g. `QUERY_OIL_BELOW_80`).

---

## Step 2 — Run in parallel

**Leg A** — execute the price query:

```bash
RESULT=$(cd ~/workspace/claude_for_mac_local && uv run python -c "
import sys, json; sys.path.insert(0, 'src')
from tools import run_query
print(json.dumps(run_query('{{column}}', '{{operator}}', {{threshold}}), indent=2, default=str))
" 2>&1 | grep -v "^warning\|Loaded cache\|Date range\|Last updated")
cd ~/workspace/claude_for_mac_local && RESULT="$RESULT" uv run python - <<'PY'
import os
import sys
from pathlib import Path

sys.path.insert(0, "src")
from config import VAULT_PATH

vault = VAULT_PATH
out = vault / "Tmp/query_result.md"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(os.environ.get("RESULT", ""), encoding="utf-8")
PY
```

**Leg B** — read the vault QUERY note (if it exists):

```bash
cd ~/workspace/claude_for_mac_local && uv run python - <<'PY'
import os
import sys
from pathlib import Path

sys.path.insert(0, "src")
from config import VAULT_PATH

name = "{{NAME}}".strip()
vault = VAULT_PATH
query_fp = vault / f"Documentation/market-intel/QUERY_{name}.md"
tmp_fp = vault / "Tmp/query_note.md"
tmp_fp.parent.mkdir(parents=True, exist_ok=True)

if query_fp.exists():
	tmp_fp.write_text(query_fp.read_text(encoding="utf-8"), encoding="utf-8")
	print(tmp_fp)
PY
```

Save output to `Tmp/query_note.md`. If the note doesn't exist, skip gracefully.

---

## Step 3 — Synthesise

Read both Tmp/ files. Compose an answer structured as:

### Answer: [Asset] [operator] [threshold] — [N] regimes found

**Data range:** [parquet date range]

#### Regimes

| # | Start | End | Days | Avg [asset] | Min | What was happening |
|---|-------|-----|------|-------------|-----|--------------------|
| 1 | ... | ... | ... | ... | ... | [1-line from news or vault context] |

> [!NOTE] Most Recent Regime
> Highlight the most recent regime's start, end, length, avg price, and the key macro driver.

> [!TIP] Portfolio Implication
> Pull this from the QUERY_*.md note's "Portfolio Implication" section if it exists. Otherwise derive from [[WIKI_CRUDE_GOLD]], [[WIKI_SIGNALS]], or [[WIKI_PORTFOLIO]] as appropriate.

#### News Context
List any news articles found (from the news DB, within ± 14 days of each regime). If news_count = 0 for all regimes, note that news DB only covers 2026 and historical context must come from vault wikilinks.

#### Vault Links
Always include relevant wikilinks from CLAUDE.md or the QUERY note:
- [[WIKI_CRUDE_GOLD]] for oil queries
- [[WIKI_GOLD]] for gold queries
- [[WIKI_SIGNALS]] for ceasefire/deployment signal context
- [[WIKI_PORTFOLIO]] for portfolio implication

---

## Step 4 — Save to vault

Save the answer to `Documentation/market-intel/` using the Market Note Protocol:

```
YYYY-MM-DD_query_{{column}}_{{operator}}_{{threshold}}.md
```

Tags: `[query, market-intel, asset/{{asset_tag}}, timeframe/macro, signal]`

Add entry to INDEX under **Query Contracts** section.

---

## Step 5 — Clean Tmp/

```bash
cd ~/workspace/claude_for_mac_local && uv run python - <<'PY'
import os
import sys
from pathlib import Path

sys.path.insert(0, "src")
from config import VAULT_PATH

vault = VAULT_PATH
for rel in ("Tmp/query_result.md", "Tmp/query_note.md"):
	fp = vault / rel
	if fp.exists():
		fp.unlink()
PY
```

---

## Notes

- `run_query()` lives in `~/workspace/claude_for_mac_local/src/tools.py`
- Parquet data covers **2021-03-25 → present** (updated daily)
- News DB covers **2026 only** — for earlier regimes, macro context comes from vault wikilinks
- `min_regime_days=3` by default — single-day dips are noise, not regimes
- `max_gap_days=5` merges weekend/holiday gaps within the same regime
