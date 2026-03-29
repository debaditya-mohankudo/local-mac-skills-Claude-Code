#!/bin/bash
# Usage: git_local.sh [-y] [--push] COMMIT_MESSAGE
# Performs git add, commit, and optionally push.
# Without -y, prints a preview and exits (dry-run).
# Pass -y to confirm and actually commit.
# Pass --push to also push after committing.

set -e

CONFIRM=0
SHOULD_PUSH=0
COMMIT_MSG=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    -y)
      CONFIRM=1
      shift
      ;;
    --push)
      SHOULD_PUSH=1
      shift
      ;;
    *)
      COMMIT_MSG="$*"
      break
      ;;
  esac
done

if [[ -z "$COMMIT_MSG" ]]; then
  echo "Usage: git_local.sh [-y] [--push] COMMIT_MESSAGE" >&2
  exit 1
fi

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
  echo "Error: Not in a git repository" >&2
  exit 1
fi

# Show what would be staged
echo "=== Git Status ==="
git status --short

echo ""
echo "=== Changes to be committed ==="
if git diff --cached --quiet; then
  echo "(no staged changes)"
else
  git diff --cached --stat
fi

echo ""
echo "=== Unstaged changes ==="
if git diff --quiet; then
  echo "(no unstaged changes)"
else
  git diff --stat
fi

if [[ "$CONFIRM" -ne 1 ]]; then
  echo ""
  echo "DRY RUN — nothing committed."
  echo "Commit message: $COMMIT_MSG"
  if [[ "$SHOULD_PUSH" -eq 1 ]]; then
    echo "Will also push to remote."
  fi
  echo "Re-run with -y to commit."
  exit 0
fi

echo ""
echo "=== Staging and committing ==="

# Stage all changes
git add -A

# Perform the commit
git commit -m "$COMMIT_MSG"

if [[ "$SHOULD_PUSH" -eq 1 ]]; then
  echo ""
  echo "=== Pushing to remote ==="
  # Get current branch name
  CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
  git push origin "$CURRENT_BRANCH"
  echo "Pushed to origin/$CURRENT_BRANCH"
fi

echo ""
echo "✓ Done"
