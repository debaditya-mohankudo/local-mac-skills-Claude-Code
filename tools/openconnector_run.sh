#!/bin/bash
# Usage: openconnector_run.sh
# Starts (or restarts) the local OpenConnector container via Apple's `container` CLI,
# pulling the encryption key + admin token from macOS Keychain rather than a file.
#
# First run: generate + store the secrets once —
#   security add-generic-password -a "$USER" -s "openconnector-encryption-key" -w "$(openssl rand -hex 32)" -U
#   security add-generic-password -a "$USER" -s "openconnector-admin-token"      -w "$(openssl rand -hex 24)" -U

set -e

DATA_DIR="$HOME/Library/Mobile Documents/com~apple~CloudDocs/Databases/openconnector"
NAME="openconnector"
IMAGE="ghcr.io/oomol-lab/open-connector:latest"

ENC_KEY=$(security find-generic-password -a "$USER" -s "openconnector-encryption-key" -w 2>/dev/null) || {
  echo "ERROR: no 'openconnector-encryption-key' found in Keychain. See usage comment above to create one." >&2
  exit 1
}
ADMIN_TOKEN=$(security find-generic-password -a "$USER" -s "openconnector-admin-token" -w 2>/dev/null) || {
  echo "ERROR: no 'openconnector-admin-token' found in Keychain. See usage comment above to create one." >&2
  exit 1
}

mkdir -p "$DATA_DIR"

# container's stop/start can race and leave the container unrecoverable (see task e5ea4b88) —
# always tear down and run fresh rather than trying to `container start` a stopped one.
if container list -a --format json 2>/dev/null | grep -q "\"$NAME\""; then
  container stop "$NAME" >/dev/null 2>&1 || true
  sleep 1
  container delete "$NAME" >/dev/null 2>&1 || true
fi

container run -d --name "$NAME" \
  -p 3000:3000 \
  -v "$DATA_DIR:/app/data" \
  -e OOMOL_CONNECT_DATA_DIR=/app/data \
  -e OOMOL_CONNECT_ENCRYPTION_KEY="$ENC_KEY" \
  -e OOMOL_CONNECT_ADMIN_TOKEN="$ADMIN_TOKEN" \
  "$IMAGE"

echo "OpenConnector starting — waiting for health check..."
for i in $(seq 1 10); do
  sleep 1
  if curl -sf http://localhost:3000/v1/health >/dev/null 2>&1; then
    echo "OK: http://localhost:3000/v1/health responding"
    exit 0
  fi
done

echo "ERROR: container did not become healthy within 10s" >&2
exit 1
