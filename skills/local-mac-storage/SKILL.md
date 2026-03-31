---
name: local-mac-storage
description: Use this skill when the user asks to check Mac storage, clean up disk space, find what's using storage, or runs /local-mac-storage.
user-invocable: true
---

Analyze Mac storage and report what's consuming space, then suggest safe cleanup actions.

**Step 1 — Disk overview:**

```bash
~/workspace/claude_for_mac_local/tools/storage_overview.sh
```

**Step 2 — Detailed Library breakdown:**

```bash
~/workspace/claude_for_mac_local/tools/storage_detail.sh
```

**Step 3 — Produce the report in this format:**

```
## Mac Storage Report — [DATE]

### Disk Status
Total: X GB | Used: X GB | Available: X GB | Capacity: X%

### Top Space Consumers
| Size  | Location | What it is |
|-------|----------|------------|
| X GB  | path     | description |
...

### Safe Cleanup Recommendations
**Immediate wins (safe to delete):**
- item — X GB — how to clean

**Requires review before deleting:**
- item — X GB — what to check first
```

**Rules for the report:**
- Flag anything over 1 GB
- Docker (`com.docker.docker`) — recommend `docker system prune -a` if unused images/containers likely
- Pip cache — recommend `pip cache purge`
- Homebrew cache — recommend `brew cleanup`
- Browser caches (Chrome, Edge, Firefox) — safe to delete, auto-rebuilt
- `ms-playwright` cache — only remove if Playwright tests not in use
- Claude VM bundle (`vm_bundles/claudevm.bundle`) — note it's the local model VM, only remove from Claude app settings
- Do NOT recommend deleting: `Application Support` app data, `~/Library/Preferences`, system files

**If available space is under 5 GB:** lead with a warning — `⚠️ Critical: only X GB free — immediate cleanup needed`.

**Step 4 — Cache the report:**

After producing the report, write it to `~/Documents/claude_cache_data/claude_for_mac_local/mac-storage-YYYY-MM-DD.md` using today's date.

- **If the file already exists for today:** overwrite the full report output to the file. Note `Cache: written ✓`.
- **If it does not exist:** write the full report output to the file. Note `Cache: written ✓`.

Example path: `~/Documents/claude_cache_data/claude_for_mac_local/mac-storage-2026-03-21.md`
