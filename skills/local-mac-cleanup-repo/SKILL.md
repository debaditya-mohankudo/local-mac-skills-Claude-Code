---
name: local-mac-cleanup-repo
description: Clean repository history by removing all commits and pushing fresh, verified-clean code to GitHub
user-invocable: true
---

Completely clean a repository's git history by removing all commits and pushing only verified-clean code to GitHub.

## Why use this skill

When a repository has accumulated sensitive data (personal numbers, API keys, emails) in its git history that needs to be completely removed from GitHub, a simple force-push isn't enough — GitHub retains old commits in the history.

This skill provides a complete cleanup workflow:
1. Scan codebase for personal data
2. Delete old repository from GitHub (via `gh`)
3. Reinitialize git locally with clean history
4. Recreate repository on GitHub
5. Push verified-clean code

## How to use this skill

### Step 1: Verify code is clean

```bash
./tools/scan_personal_data.sh
```

Confirm: **No personal data found**

### Step 2: Delete old repository on GitHub

Using `gh` CLI:
```bash
gh repo delete <owner>/<repo> --confirm
```

Or manually:
- Go to GitHub → Repo → Settings → Danger Zone → Delete repository

### Step 3: Reinitialize git locally

```bash
rm -rf .git
git init
git config user.email "you@example.com"
git config user.name "Your Name"
git add -A
git commit -m "Initial commit - verified clean"
```

### Step 4: Recreate on GitHub

Using `gh`:
```bash
gh repo create <repo-name> --public --source=. --remote=origin --push
```

Or manually create on GitHub, then:
```bash
git remote add origin https://github.com/<owner>/<repo>.git
git branch -M main
git push -u origin main
```

### Step 5: Verify pre-push hook is active

```bash
git push
```

The pre-push hook (if configured) should scan and confirm clean before push succeeds.

## Output

**Success:**
```
✓ Scan complete — no personal data found
✓ Repo created and pushed to GitHub
```

**Failure (if personal data found):**
```
✗ Found potential personal data
Fix issues and retry
```

## Notes

- This is a **destructive operation** — all old commits are permanently removed from GitHub
- Only use when absolutely necessary (old commits contain sensitive data)
- Always scan first with `scan_personal_data.sh` before cleanup
- Requires GitHub CLI (`gh`) or manual GitHub access
- Takes 2-5 minutes total

## Related Skills

- `local-mac-scan-personal-data` — scan codebase for personal data patterns
- `local-mac-edit-personal-data` — safely edit config files with personal data
