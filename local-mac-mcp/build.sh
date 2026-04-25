#!/bin/bash
# Build script for local-mac-mcp with git commit and build date embedding

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Get current git commit hash (short form)
GIT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

# Get build timestamp in UTC
BUILD_DATE=$(date -u +'%Y-%m-%d %H:%M:%S UTC')

# Update BuildInfo in CLI/main.swift
CLI_MAIN="Sources/CLI/main.swift"
sed -i '' "s/GIT_COMMIT_PLACEHOLDER/$GIT_COMMIT/" "$CLI_MAIN"
sed -i '' "s|BUILD_DATE_PLACEHOLDER|$BUILD_DATE|" "$CLI_MAIN"

echo "BuildInfo: $GIT_COMMIT built at $BUILD_DATE"

# Build with Swift
swift build -c release "$@"

echo "✓ Build complete: local-mpc ($GIT_COMMIT)"
