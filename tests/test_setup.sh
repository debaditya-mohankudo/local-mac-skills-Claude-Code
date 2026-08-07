#!/bin/bash
# Sets up the Docker SSH sandbox used by the sandbox tests in test_tools.sh.
# Safe to run multiple times — skips steps that are already done.
#
# Usage:
#   bash tests/test_setup.sh          # start sandbox
#   bash tests/test_setup.sh --stop   # stop and remove sandbox

CONTAINER="ssh-sandbox"
PORT=2222
IMAGE="lscr.io/linuxserver/openssh-server:latest"
REMOTE_USER="testuser"
PUBKEY="$HOME/.ssh/id_ed25519.pub"

# --- stop/teardown ---
if [[ "${1}" == "--stop" ]]; then
  echo "Stopping $CONTAINER..."
  docker stop "$CONTAINER" 2>/dev/null && echo "  Stopped." || echo "  Not running."
  docker rm   "$CONTAINER" 2>/dev/null && echo "  Removed." || echo "  Already gone."
  exit 0
fi

# --- preflight ---
if ! command -v docker &>/dev/null; then
  echo "ERROR: docker not found. Install Docker Desktop and try again."
  exit 1
fi

if [[ ! -f "$PUBKEY" ]]; then
  echo "ERROR: No public key at $PUBKEY."
  echo "Generate one with: ssh-keygen -t ed25519"
  exit 1
fi

# --- start container if not already running ---
if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER}$"; then
  echo "Container '$CONTAINER' already running — skipping start."
else
  if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER}$"; then
    echo "Removing stopped container '$CONTAINER'..."
    docker rm "$CONTAINER"
  fi

  echo "Pulling image $IMAGE..."
  docker pull "$IMAGE"

  echo "Starting $CONTAINER on port $PORT..."
  docker run -d \
    --name "$CONTAINER" \
    -p "${PORT}:2222" \
    -e PUID=1000 \
    -e PGID=1000 \
    -e USER_NAME="$REMOTE_USER" \
    -e PASSWORD_ACCESS=false \
    "$IMAGE"

  echo "Waiting for sshd to start..."
  for i in $(seq 1 15); do
    if docker exec "$CONTAINER" pgrep sshd &>/dev/null; then
      break
    fi
    sleep 1
  done
fi

# --- install public key ---
# linuxserver/openssh-server sets home to /config — keys go in /config/.ssh/
echo "Installing public key for $REMOTE_USER..."
PUBKEY_CONTENT=$(cat "$PUBKEY")
docker exec "$CONTAINER" bash -c "
  mkdir -p /config/.ssh &&
  echo '$PUBKEY_CONTENT' >> /config/.ssh/authorized_keys &&
  sort -u /config/.ssh/authorized_keys -o /config/.ssh/authorized_keys &&
  chmod 700 /config/.ssh &&
  chmod 600 /config/.ssh/authorized_keys &&
  chown -R ${REMOTE_USER}:users /config/.ssh
"

# --- verify connectivity ---
echo "Verifying SSH connection..."
if ssh -o BatchMode=yes -o ConnectTimeout=10 -o StrictHostKeyChecking=accept-new \
     -p "$PORT" "${REMOTE_USER}@localhost" echo ok 2>/dev/null | grep -q ok; then
  echo ""
  echo "Sandbox ready — ${REMOTE_USER}@localhost:${PORT}"
  echo "Run tests: bash tests/test_tools.sh"
else
  echo ""
  echo "ERROR: Could not connect after setup. Check 'docker logs $CONTAINER' for details."
  exit 1
fi
