---
name: local-mac-scan-personal-data
description: Scan the repository for personal data before commit or push. Use as a pre-publication gate.
user-invocable: true
---

Guardrail scan for personal data.

## Script
`tools/scan_personal_data.sh`

Checks for phone numbers, non-placeholder email addresses, IP addresses, and
exposed API keys or tokens.

## Rules
- Run before any commit that will be published, and before changing repo visibility.
- Placeholders must use `example.com` — the scan treats other domains as suspect.
- A finding is not automatically a blocker, but every finding must be explained
  before proceeding. Do not silence the scan by loosening its patterns.
- The scan reads the working tree. It does not read git history, and history is
  published too — a clean scan does not prove old commits are clean.
