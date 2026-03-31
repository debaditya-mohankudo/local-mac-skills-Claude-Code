#!/bin/bash
# Docker Cleanup with Guardrails
# Usage: ./docker_cleanup.sh

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BOLD='\033[1m'
NC='\033[0m'

confirm() {
    local prompt="$1"
    echo -e "${YELLOW}$prompt${NC} (y/N) "
    read -r reply
    [[ "$reply" =~ ^[Yy]$ ]]
}

# Check Docker is running
if ! docker info &>/dev/null; then
    echo -e "${RED}Docker is not running. Start Docker Desktop first.${NC}"
    exit 1
fi

echo -e "${BOLD}=== Docker Disk Usage ===${NC}"
docker system df
echo ""

# ── 1. Stopped containers ──────────────────────────────────────────────────
STOPPED=$(docker ps -aq --filter status=exited --filter status=created | wc -l | tr -d ' ')
if [[ "$STOPPED" -gt 0 ]]; then
    echo -e "${BOLD}[1] Stopped containers:${NC} $STOPPED found"
    docker ps -a --filter status=exited --filter status=created --format "  {{.Names}} ({{.Image}}) — stopped {{.RunningFor}}"
    echo ""
    if confirm "Remove $STOPPED stopped container(s)?"; then
        docker container prune -f
        echo -e "${GREEN}Done.${NC}"
    else
        echo "Skipped."
    fi
else
    echo -e "[1] Stopped containers: ${GREEN}none${NC}"
fi
echo ""

# ── 2. Dangling images (untagged) ──────────────────────────────────────────
DANGLING=$(docker images -f dangling=true -q | wc -l | tr -d ' ')
if [[ "$DANGLING" -gt 0 ]]; then
    echo -e "${BOLD}[2] Dangling images (untagged):${NC} $DANGLING found"
    docker images -f dangling=true --format "  {{.ID}} — {{.Size}} — {{.CreatedSince}}"
    echo ""
    if confirm "Remove $DANGLING dangling image(s)?"; then
        docker image prune -f
        echo -e "${GREEN}Done.${NC}"
    else
        echo "Skipped."
    fi
else
    echo -e "[2] Dangling images: ${GREEN}none${NC}"
fi
echo ""

# ── 3. All unused images ───────────────────────────────────────────────────
echo -e "${BOLD}[3] All images (including tagged):${NC}"
docker images --format "  {{.Repository}}:{{.Tag}}\t{{.Size}}\t{{.CreatedSince}}" | sort -k2 -rh
echo ""
echo -e "${RED}WARNING: This removes ALL images not used by a running container.${NC}"
echo -e "         You will need to re-pull them before next use."
if confirm "Remove ALL unused images?"; then
    docker image prune -af
    echo -e "${GREEN}Done.${NC}"
else
    echo "Skipped."
fi
echo ""

# ── 4. Unused volumes ─────────────────────────────────────────────────────
VOLUMES=$(docker volume ls -qf dangling=true | wc -l | tr -d ' ')
if [[ "$VOLUMES" -gt 0 ]]; then
    echo -e "${BOLD}[4] Unused volumes:${NC} $VOLUMES found"
    docker volume ls -f dangling=true --format "  {{.Name}}"
    echo ""
    echo -e "${RED}WARNING: Volume data is PERMANENT — this cannot be undone.${NC}"
    if confirm "Remove $VOLUMES unused volume(s)?"; then
        docker volume prune -f
        echo -e "${GREEN}Done.${NC}"
    else
        echo "Skipped."
    fi
else
    echo -e "[4] Unused volumes: ${GREEN}none${NC}"
fi
echo ""

# ── 5. Build cache ─────────────────────────────────────────────────────────
CACHE_SIZE=$(docker system df --format "{{.BuildCache}}" 2>/dev/null || docker system df | awk '/Build Cache/ {print $4}')
echo -e "${BOLD}[5] Build cache:${NC} $CACHE_SIZE"
echo "    Safe to delete — Docker rebuilds cache on next build (slower first run)."
if confirm "Clear all build cache?"; then
    docker builder prune -af
    echo -e "${GREEN}Done.${NC}"
else
    echo "Skipped."
fi
echo ""

# ── 6. Reclaim VM disk space (Docker.raw compaction) ──────────────────────
RAW_FILE="$HOME/Library/Containers/com.docker.docker/Data/vms/0/data/Docker.raw"
if [[ -f "$RAW_FILE" ]]; then
    RAW_SIZE=$(du -sh "$RAW_FILE" | awk '{print $1}')
    echo -e "${BOLD}[6] Docker VM disk (Docker.raw):${NC} $RAW_SIZE on disk"
    echo "    The VM disk file grows as you use Docker but never shrinks automatically."
    echo "    Compaction reclaims space freed by deleted images/cache."
    echo ""
    ARCH=$(uname -m)
    if [[ "$ARCH" == "arm64" ]]; then
        echo -e "${YELLOW}Apple Silicon detected.${NC} CLI compaction is unreliable on arm64."
        echo "    Recommended: Docker Desktop → Settings → Resources → Advanced → 'Reclaim disk space'"
        if confirm "Try CLI compaction anyway (may not work on Apple Silicon)?"; then
            echo "Running compaction..."
            docker run --privileged --pid=host docker/desktop-reclaim-space 2>&1
            NEW_SIZE=$(du -sh "$RAW_FILE" | awk '{print $1}')
            echo -e "Docker.raw: ${RAW_SIZE} → ${NEW_SIZE}"
        else
            echo "Skipped. Use Docker Desktop UI to reclaim space."
        fi
    else
        if confirm "Compact Docker.raw to reclaim freed space (~${RAW_SIZE} current)?"; then
            echo "Running compaction (this may take a minute)..."
            docker run --privileged --pid=host docker/desktop-reclaim-space 2>&1
            NEW_SIZE=$(du -sh "$RAW_FILE" | awk '{print $1}')
            echo -e "${GREEN}Docker.raw: ${RAW_SIZE} → ${NEW_SIZE}${NC}"
        else
            echo "Skipped."
        fi
    fi
else
    echo -e "[6] Docker VM disk: ${GREEN}not found${NC}"
fi
echo ""

# ── Summary ────────────────────────────────────────────────────────────────
echo -e "${BOLD}=== After Cleanup ===${NC}"
docker system df
echo ""
df -h /
