#!/bin/bash
# Build local-mac-tool and install to ~/bin/

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

GIT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

swift build -c release "$@"

BINARY=".build/arm64-apple-macosx/release/LocalMacMCP"
DEST="$HOME/bin/local-mac-tool"

cp "$BINARY" "$DEST"
chmod +x "$DEST"

echo "✓ Built and installed: $DEST ($GIT_COMMIT)"
