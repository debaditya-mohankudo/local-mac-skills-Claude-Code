---
name: local-mac-storage
description: Check disk usage and run guided, safe-only storage cleanup. Use when the Mac is short on space.
user-invocable: true
---

Inspect and reclaim disk space.

## Scripts
- `tools/storage_overview.sh` — volume-level usage
- `tools/storage_detail.sh` — per-directory breakdown
- `tools/safe_to_del.sh` — candidates that are safe to remove

## Guardrails
Cleanup is safe-only: never application data, never system directories, never
anything unrecognised. Show what will be removed and how much it frees, then ask.
Deleting to reclaim space is not worth losing data over.
