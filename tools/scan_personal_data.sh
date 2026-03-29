#!/bin/bash
# scan_personal_data.sh
# Scans the codebase for personal data patterns (phone numbers, emails, IPs, API keys)
# Usage: ./tools/scan_personal_data.sh

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCAN_DIR="${1:-.}"

# Color codes
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

FOUND_ISSUES=0

echo "🔍 Scanning for personal data patterns..."
echo "   Project root: $PROJECT_ROOT"
echo ""

# Exclude patterns (already in .gitignore, or not part of committed code)
EXCLUDE_DIRS="--exclude-dir=.venv --exclude-dir=.git --exclude-dir=.claude --exclude-dir=node_modules --exclude-dir=.cache --exclude-dir=dist --exclude-dir=build"
EXCLUDE_FILES="--exclude=*.lock --exclude=*.whl"
FILE_TYPES="--include=*.md --include=*.sh --include=*.py --include=*.json --include=*.yml --include=*.yaml"

# 1. Check for Indian phone numbers (real format: +91XXXXXXXXXX)
echo "1️⃣  Checking for Indian phone numbers..."
if grep -r '\+91[0-9]\{10\}' $FILE_TYPES $EXCLUDE_DIRS $EXCLUDE_FILES "$SCAN_DIR" 2>/dev/null | grep -v 'XXXXXXXXXX' > /tmp/phones.txt 2>&1; then
  if [[ -s /tmp/phones.txt ]]; then
    echo -e "${RED}✗ Found potential Indian phone numbers:${NC}"
    head -20 /tmp/phones.txt | sed 's/^/   /'
    FOUND_ISSUES=1
  else
    echo -e "${GREEN}✓ No Indian phone numbers found${NC}"
  fi
else
  echo -e "${GREEN}✓ No Indian phone numbers found${NC}"
fi
echo ""

# 2. Check for non-placeholder emails
echo "2️⃣  Checking for non-placeholder email addresses..."
if grep -rE '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}' $FILE_TYPES $EXCLUDE_DIRS $EXCLUDE_FILES "$SCAN_DIR" 2>/dev/null | grep -v 'example.com' | grep -v '@github' | grep -v 'git@' | grep -v 'user@' > /tmp/emails.txt 2>&1; then
  if [[ -s /tmp/emails.txt ]]; then
    echo -e "${RED}✗ Found potential personal email addresses:${NC}"
    head -20 /tmp/emails.txt | sed 's/^/   /'
    FOUND_ISSUES=1
  else
    echo -e "${GREEN}✓ No suspicious email addresses found${NC}"
  fi
else
  echo -e "${GREEN}✓ No suspicious email addresses found${NC}"
fi
echo ""

# 3. Check for non-placeholder IP addresses
echo "3️⃣  Checking for IP addresses..."
if grep -rE '\b([0-9]{1,3}\.){3}[0-9]{1,3}\b' $FILE_TYPES $EXCLUDE_DIRS $EXCLUDE_FILES "$SCAN_DIR" 2>/dev/null | grep -v '192.168' | grep -v '172.16' | grep -v '10.0' | grep -v '127.0' > /tmp/ips.txt 2>&1; then
  if [[ -s /tmp/ips.txt ]]; then
    echo -e "${RED}✗ Found potential IP addresses:${NC}"
    head -20 /tmp/ips.txt | sed 's/^/   /'
    FOUND_ISSUES=1
  else
    echo -e "${GREEN}✓ No suspicious IP addresses found${NC}"
  fi
else
  echo -e "${GREEN}✓ No suspicious IP addresses found${NC}"
fi
echo ""

# 4. Check for API keys/tokens (actual value patterns)
echo "4️⃣  Checking for exposed API keys/secrets..."
# Look for actual exposed values like: api_key = "abc123..." (non-placeholder)
if grep -rE '(api.?key|secret|token|password)\s*[=:]\s*["\047][a-zA-Z0-9+/=]{20,}' $FILE_TYPES $EXCLUDE_DIRS $EXCLUDE_FILES "$SCAN_DIR" 2>/dev/null | grep -v 'PLACEHOLDER\|EXAMPLE\|XXXXXXXXXX\|xxxxxxxx' > /tmp/keys.txt 2>&1; then
  if [[ -s /tmp/keys.txt ]]; then
    echo -e "${RED}✗ Found potential exposed API keys:${NC}"
    head -20 /tmp/keys.txt | sed 's/^/   /'
    FOUND_ISSUES=1
  else
    echo -e "${GREEN}✓ No exposed API keys/tokens found${NC}"
  fi
else
  echo -e "${GREEN}✓ No exposed API keys/tokens found${NC}"
fi
echo ""

# Cleanup
rm -f /tmp/phones.txt /tmp/emails.txt /tmp/ips.txt /tmp/keys.txt

# Summary
echo "════════════════════════════════════════════"
if [[ $FOUND_ISSUES -eq 0 ]]; then
  echo -e "${GREEN}✓ Scan complete — no personal data found${NC}"
  exit 0
else
  echo -e "${RED}⚠️  Scan found issues — review and fix before committing${NC}"
  exit 1
fi
