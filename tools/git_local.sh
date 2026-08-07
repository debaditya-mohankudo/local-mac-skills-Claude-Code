#!/bin/bash
# Usage: git_local.sh [-y] [--push] [--repo <path>] COMMIT_MESSAGE
# Performs git add, commit, and optionally push.
# Without -y, prints a preview and exits (dry-run).
# Pass -y to confirm and actually commit.
# Pass --push to also push after committing.
# Pass --repo <path> to operate on a repo other than the current directory.

set -e

CONFIRM=0
SHOULD_PUSH=0
COMMIT_MSG=""
REPO_PATH=""

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
    --repo)
      REPO_PATH="$2"
      shift 2
      ;;
    *)
      COMMIT_MSG="$*"
      break
      ;;
  esac
done

if [[ -z "$COMMIT_MSG" ]]; then
  echo "Usage: git_local.sh [-y] [--push] [--repo <path>] COMMIT_MESSAGE" >&2
  exit 1
fi

# Build git command prefix — use -C <path> if --repo was specified
GIT="git"
if [[ -n "$REPO_PATH" ]]; then
  GIT="git -C $REPO_PATH"
fi

# Check if we're in a git repository
if ! $GIT rev-parse --git-dir > /dev/null 2>&1; then
  echo "Error: Not in a git repository${REPO_PATH:+ ($REPO_PATH)}" >&2
  exit 1
fi

REPO_ROOT=$($GIT rev-parse --show-toplevel)
echo "=== Repo: $REPO_ROOT ==="

# Show what would be staged
echo ""
echo "=== Git Status ==="
$GIT status --short

echo ""
echo "=== Changes to be committed ==="
if $GIT diff --cached --quiet; then
  echo "(no staged changes)"
else
  $GIT diff --cached --stat
fi

echo ""
echo "=== Unstaged changes ==="
if $GIT diff --quiet; then
  echo "(no unstaged changes)"
else
  $GIT diff --stat
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
$GIT add -A

# Perform the commit
$GIT commit -m "$COMMIT_MSG"

if [[ "$SHOULD_PUSH" -eq 1 ]]; then
  echo ""
  echo "=== Pushing to remote ==="
  CURRENT_BRANCH=$($GIT rev-parse --abbrev-ref HEAD)
  $GIT push origin "$CURRENT_BRANCH"
  echo "Pushed to origin/$CURRENT_BRANCH"
fi

echo ""
echo "✓ Done"
