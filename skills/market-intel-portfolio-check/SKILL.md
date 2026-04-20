---
name: market-intel-portfolio-check
description: Full portfolio snapshot — allocation, deployment triggers, dry powder, and constraint checks. Use before any deployment decision.
user-invocable: true
---

Run a full portfolio status check.

## Step 0 — Clean Tmp/

Before fetching any data, delete stale notes from a previous run:

```bash
cd ~/workspace/claude_for_mac_local && uv run python - <<'PY'
import os
import sys
from pathlib import Path

sys.path.insert(0, "src")
from config import VAULT_PATH

vault = VAULT_PATH
for rel in ("Tmp/portfolio_status.md", "Tmp/portfolio_triggers.md", "Tmp/portfolio_market.md"):
	fp = vault / rel
	if fp.exists():
		fp.unlink()
PY
```

(Errors are expected if files don't exist — ignore them.)

> [!NOTE] Always persist tool output to vault Tmp/ — never hold in context memory.
> Write each tool result to `Tmp/` immediately. Read from vault when composing the report. Delete Tmp/ notes after report is saved. See [[Key Concepts/TOOL_OUTPUT_TO_FILE]].

**Run all 3 calls in parallel**, saving each to vault Tmp/:

```bash
# portfolio status → Tmp/portfolio_status.md
STATUS=$(cd ~/workspace/claude_for_mac_local && uv run python -c "
import sys, json; sys.path.insert(0, 'src')
from tools import get_portfolio_status
print(json.dumps(get_portfolio_status(), indent=2, default=str))
" 2>&1 | grep -v "Loaded cache\|Date range\|Last updated")
cd ~/workspace/claude_for_mac_local && STATUS="$STATUS" uv run python - <<'PY'
import os
import sys
from pathlib import Path

sys.path.insert(0, "src")
from config import VAULT_PATH

vault = VAULT_PATH
fp = vault / "Tmp/portfolio_status.md"
fp.parent.mkdir(parents=True, exist_ok=True)
fp.write_text(os.environ.get("STATUS", ""), encoding="utf-8")
PY

# deployment triggers → Tmp/portfolio_triggers.md
TRIGGERS=$(cd ~/workspace/claude_for_mac_local && uv run python -c "
import sys, json; sys.path.insert(0, 'src')
from tools import check_deployment_triggers
print(json.dumps(check_deployment_triggers(), indent=2, default=str))
" 2>&1 | grep -v "Loaded cache\|Date range\|Last updated")
cd ~/workspace/claude_for_mac_local && TRIGGERS="$TRIGGERS" uv run python - <<'PY'
import os
import sys
from pathlib import Path

sys.path.insert(0, "src")
from config import VAULT_PATH

vault = VAULT_PATH
fp = vault / "Tmp/portfolio_triggers.md"
fp.parent.mkdir(parents=True, exist_ok=True)
fp.write_text(os.environ.get("TRIGGERS", ""), encoding="utf-8")
PY

# market data → Tmp/portfolio_market.md
MARKET=$(cd ~/workspace/claude_for_mac_local && uv run python -c "
import sys, json; sys.path.insert(0, 'src')
from tools import get_latest_market_data
print(json.dumps(get_latest_market_data(), indent=2, default=str))
" 2>&1 | grep -v "Loaded cache\|Date range\|Last updated")
cd ~/workspace/claude_for_mac_local && MARKET="$MARKET" uv run python - <<'PY'
import os
import sys
from pathlib import Path

sys.path.insert(0, "src")
from config import VAULT_PATH

vault = VAULT_PATH
fp = vault / "Tmp/portfolio_market.md"
fp.parent.mkdir(parents=True, exist_ok=True)
fp.write_text(os.environ.get("MARKET", ""), encoding="utf-8")
PY
```

Read all three from vault when composing the report:
```bash
cd ~/workspace/claude_for_mac_local && uv run python - <<'PY'
import os
import sys
from pathlib import Path

sys.path.insert(0, "src")
from config import VAULT_PATH

vault = VAULT_PATH
for rel in ("Tmp/portfolio_status.md", "Tmp/portfolio_triggers.md", "Tmp/portfolio_market.md"):
	print(f"\n--- {rel} ---")
	print((vault / rel).read_text(encoding="utf-8"))
PY
```

**Step 2:** Read the `[[deployment_log]]` entries at the bottom of `portfolio.toml` to show deployment history.

Report the result in this format:

```
## Portfolio Check — [DATE]

### Allocation (₹X.XXCr total corpus)
| Bucket        | Amount  | Target% | Actual% | Status |
|---------------|---------|---------|---------|--------|
| Debt          | ₹XX.XXL | 52%     | XX%     | ✓/⚠    |
| Hard Assets   | ₹XX.XXL | 19.5%   | XX%     | ✓/⚠    |
| Hybrid Growth | ₹XX.XXL | 20.7%   | XX%     | ✓/⚠    |
| Liquid Buffer | ₹XX.XXL | 8.3%    | XX%     | ✓/⚠    |

Ceilings: Equity ≤30% ✓/⚠ | Gold ≤25% ✓/⚠

### Deployment Triggers
Dry powder: ₹XL
Min liquid reserve: ₹5L (hard floor — never breach)
Single spike cap: ₹XL (50% of dry powder — max deployable in any one event)

| Trigger Level | Tranche | Status     |
|--------------|---------|------------|
| Nifty XXXXX  | ₹XL     | ✅ DONE / 🔴 ACTIVE / ⏳ PENDING |
...

52-week drawdown: X.X% from high (halt at 30%)
Deployment status: [NORMAL / HALTED]

### Deployment History
[List from [[deployment_log]] in portfolio.toml — date, amount, asset, Nifty level at time]

### Constraints
[List any breached ceilings, low liquidity warnings, or halt conditions]

### Action
[HOLD / DEPLOY ₹XL at Nifty XXXXX / REVIEW ALLOCATION]
```

Hard rules — flag clearly if any are at risk:
- Do NOT break fixed deposits early
- Do NOT panic sell gold
- Do NOT breach ₹5L minimum liquid reserve
- Halt equity deployment if Nifty drawdown ≥30% from 52-week high
- Max 50% of dry powder in any single spike event (e.g. ₹3L dry powder → max ₹1.5L per event)

## Save to vault and cleanup

Save report to vault:

```bash
cd ~/workspace/claude_for_mac_local && uv run python - <<'PY'
import os
import sys
from pathlib import Path

sys.path.insert(0, "src")
from config import VAULT_PATH

vault = VAULT_PATH
out = vault / "Daily/PORTFOLIO_CHECK_YYYY-MM-DD.md"
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
for rel in ("Tmp/portfolio_status.md", "Tmp/portfolio_triggers.md", "Tmp/portfolio_market.md"):
	fp = vault / rel
	if fp.exists():
		fp.unlink()
PY
```

Done silently.
