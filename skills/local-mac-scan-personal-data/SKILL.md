---
name: local-mac-scan-personal-data
description: Scan codebase for personal data patterns before committing or pushing
user-invocable: true
---

Scan the codebase for personal data patterns (phone numbers, emails, IP addresses, API keys) before pushing to git.

## How to use this skill

Scan the entire codebase:

```bash
~/workspace/claude_for_mac_local/tools/scan_personal_data.sh
```

Scan a specific directory:

```bash
~/workspace/claude_for_mac_local/tools/scan_personal_data.sh ./src
```

## Exit codes

- **0** — No personal data found, safe to push
- **1** — Personal data detected, push blocked

## What it checks for

- **Phone numbers** — Indian format (+91XXXXXXXXXX)
- **Email addresses** — Non-placeholder patterns
- **IP addresses** — Non-private ranges
- **API keys/tokens** — Common exposure patterns

## Used by

- **Pre-push hook** — Automatically runs before `git push` to prevent accidental leaks
- **Manual scanning** — Run anytime to verify code cleanliness

## Output

**Clean result:**
```
✓ Scan complete — no personal data found
```

**Issues found:**
```
✗ Found potential Indian phone numbers:
   ./file.md:10: +91XXXXXXXXXX
```

Fix any issues before pushing.
