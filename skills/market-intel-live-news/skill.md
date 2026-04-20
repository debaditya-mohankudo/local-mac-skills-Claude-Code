---
name: market-intel-live-news
description: Live news digest via RSS — BBC World News + ET Markets. Fetches fresh headlines, classifies them, and stores to db/market.sqlite.
user-invocable: true
---

Fetch today's live news digest via RSS feeds.

**Step 1:** Call `get_daily_news_digest()`:

```bash
cd ~/workspace/claude_for_mac_local && uv run python -c "
import sys, json; sys.path.insert(0, 'src')
from tools import get_daily_news_digest
print(json.dumps(get_daily_news_digest(), indent=2, default=str))
" 2>&1 | grep -v "Loaded cache\|Date range\|Last updated"
```

**Step 2:** Display the `digest` field from the result as-is (it is already formatted markdown).

**Step 3:** Show a one-line summary footer:

```
Articles: X  |  🔴 Escalation: X  |  🟡 Supply: X  |  🟢 Diplomatic: X  |  ⚪ Other: X
Source: RSS  |  [timestamp]
```

**Step 4 (conditional):** If the result contains any error field, report it under a `⚠️ Source Errors` heading.

**Step 5 — Save to vault:**

Save the digest to `Daily/NEWS_YYYY-MM-DD.md` using direct filesystem write:

```bash
cd ~/workspace/claude_for_mac_local && uv run python - <<'PY'
import os
import sys
from pathlib import Path

sys.path.insert(0, "src")
from config import VAULT_PATH

vault = VAULT_PATH
out = vault / "Daily/NEWS_YYYY-MM-DD.md"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text("""---
tags: [market-intel, news, daily, geopolitical/iran-war]
date: YYYY-MM-DD
related: ["[[Documentation/market-intel/WIKI_SITUATION]]", "[[Documentation/market-intel/WIKI_SIGNALS]]"]
skill: market-intel-live-news
---

[[Documentation/market-intel/WIKI_SITUATION]] [[Documentation/market-intel/WIKI_SIGNALS]]

[digest markdown]

---
Articles: X  |  🔴 Escalation: X  |  🟡 Supply: X  |  🟢 Diplomatic: X  |  ⚪ Other: X
Source: RSS  |  [timestamp]""", encoding="utf-8")
PY
```

Save silently — do not mention the vault write to the user.
