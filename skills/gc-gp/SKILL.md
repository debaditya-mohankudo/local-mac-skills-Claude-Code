---
name: gc-gp
description: Git commit and push wrapper — stage all changes, commit with a message, optionally push to remote. Use when you need to commit and/or push code changes.
user-invocable: true
---

Git commit and push operations via `git_local.sh`.

## How to use this skill

When invoked directly (e.g. `/gc-gp`), ask the user for:
0. **Check Memory** — decide what to push, confirm with user with the decision.
1. **Commit message** — the message describing the changes
2. **Push?** — whether to push after committing (yes/no)

If the user has already provided the commit message in the same request, skip asking for it.

## Pre-Commit Personal Data Check

**CRITICAL: Before committing, always check for personal data in staged changes:**

```bash
git diff --cached | grep -E '\+91[0-9]{10}|[^x][0-9]{10}|@[a-z]+\.[a-z]+' && echo "⚠️  Personal data found!" || echo "✓ Clear"
```

**If personal data is detected:**
- **STOP** — Do not commit
- Report: `⚠️ Personal data detected in changes. Replace with placeholders before committing.`
- Suggest: Use `+1XXXXXXXXXX` for phone numbers, `user@example.com` for emails, etc.

**Personal data patterns to watch for:**
- Phone numbers: `+91XXXXXXXXXX` or 10-digit Indian numbers
- Email addresses: anything@domain.com (except example.com)
- API keys/tokens: secret values longer than 10 chars
- IP addresses: actual IPs (not 192.168.x.x or 10.0.x.x)

## Committing changes (dry-run preview)

To see what will be committed without actually committing:

```bash
~/workspace/claude_for_mac_local/tools/git_local.sh "Your commit message here"
```

This shows:
- Current git status
- Staged changes (if any)
- Unstaged changes (if any)
- The commit message that would be used

## Committing changes (confirmed)

To actually stage all changes and commit:

```bash
~/workspace/claude_for_mac_local/tools/git_local.sh -y "Your commit message here"
```

The `-y` flag confirms the operation. Without it, the script runs as a dry-run.

## Committing and pushing

To commit and immediately push to the remote:

```bash
~/workspace/claude_for_mac_local/tools/git_local.sh -y --push "Your commit message here"
```

The `--push` flag enables push after commit.

## After committing

Confirm to the user: `✓ Committed: "Your commit message"` or `✓ Committed and pushed: "Your commit message"` if `--push` was used.

If the script errors:
- Check the error message (e.g., "not in a git repository", merge conflicts, push rejection)
- Suggest the user resolve any conflicts or check branch tracking

## Examples

**Preview changes before committing:**
```bash
~/workspace/claude_for_mac_local/tools/git_local.sh "Fix authentication bug"
```

**Commit changes:**
```bash
~/workspace/claude_for_mac_local/tools/git_local.sh -y "Fix authentication bug"
```

**Commit and push:**
```bash
~/workspace/claude_for_mac_local/tools/git_local.sh -y --push "Fix authentication bug"
```
