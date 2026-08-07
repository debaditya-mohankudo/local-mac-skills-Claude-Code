---
name: local-mac-cleanup-repo
description: Reset a repository's history and publish a fresh verified-clean state. Use before making a repo public.
user-invocable: true
---

Flatten a repository to a single clean commit.

Destructive and irreversible on the remote. Do not run any part of it without
walking the user through the whole sequence first.

## Sequence
1. `git bundle create <path>.bundle --all` and `git bundle verify` it. Store it OUTSIDE
   the repo. This is the only copy of the discarded history.
2. Enumerate remote branches — flattening one branch leaves history on the others.
3. Remove whatever made the history unpublishable, and verify the working tree with
   `/local-mac-scan-personal-data`.
4. `rm -rf .git`, `git init -b main`, re-add the remote, stage.
5. Before committing, check nothing sensitive is staged: `.env`, `*.db`, `*.sqlite`, keys.
6. Commit once, `git push --force`, then delete every other remote branch.

## Rules
- Confirm branch loss explicitly. Branches with unique commits survive only in the bundle.
- A force push does NOT immediately purge data from the host: unreachable commits can stay
  fetchable by SHA until the host garbage-collects. Deleting and recreating the repository
  is the only way to be certain — say so rather than implying the push was sufficient.
- Never delete the bundle as part of cleanup.
