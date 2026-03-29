# SSH Skill Configuration

# Allowed remote hosts — only these IPs/hostnames can be connected to.
# Format: "nickname=ip"  (just the IP or hostname, no user@ prefix)
# The skill uses the nickname; the tools enforce the IP allowlist.
#
# To disable the allowlist and allow ALL hosts, set DISABLE_HOST_RESTRICTION=true.
# WARNING: Disabling removes all host restrictions.
DISABLE_HOST_RESTRICTION=false

ALLOWED_HOSTS=(
    # "dev=192.168.x.x"
    # "staging=10.0.0.x"
    # "ml=10.0.0.x"
    # "pi=192.168.x.x"
    # "nas=192.168.x.x"
    "sandbox=localhost"
)

# ---

# Default number of log lines to fetch (docker logs --tail)
LOG_TAIL_LINES=500

# Absolute path to the Docker Compose project on the remote machine
# Example: "/home/ubuntu/myapp"  or  "~/project"
COMPOSE_PATH=""
# COMPOSE_PATH="/home/ubuntu/myapp"
# COMPOSE_PATH="/home/ubuntu/services"

# Local directory to cache fetched docker logs, disk reports, DB dumps, and fetched files
LOG_CACHE_DIR="/tmp/claude"

# Delete cached files older than this many days (used by ssh_cache_clean.sh)
CACHE_RETENTION_DAYS=7

# ---

# Database defaults (used by ssh_db_dump.sh and ssh_db_query.sh)
# DB_CONTAINER — name of the database container on the remote
# DB_NAME      — default database to dump/query
# DB_USER      — database user
# DB_TYPE      — "mysql" or "postgres"
# DB_READONLY_USER — dedicated read-only MySQL user (recommended); falls back to DB_USER if not set

# MySQL example:
# DB_CONTAINER="mysql"
# DB_NAME="appdb"
# DB_USER="root"
# DB_TYPE="mysql"
# DB_READONLY_USER="readonly"

# Postgres example:
# DB_CONTAINER="postgres"
# DB_NAME="appdb"
# DB_USER="postgres"
# DB_TYPE="postgres"

# ---

# File transfer and git operations (ssh_copy.sh, ssh_fetch.sh, ssh_git.sh)
# Local source files are unrestricted — you control your own machine.
# Remote destinations and sources are restricted to REMOTE_DIRS below.
# Subdirectories of listed dirs are automatically allowed.
#
# Format: "nickname=absolute_path"
# Use nickname:path syntax when calling scripts — e.g. "app:logs/error.log"
#
# Set to true to allow any remote path, bypassing REMOTE_DIRS restriction.
# WARNING: disables remote path guardrails — use only if you know what you're doing.
DISABLE_DIR_RESTRICTION=false

REMOTE_DIRS=(
    "tmp=/tmp"
    # "home=/home/ubuntu"
    # "app=/home/ubuntu/myapp"
    # "services=/home/ubuntu/services"
    # "logs=/var/log"
    # "nginx=/etc/nginx"
    # "data=/home/ubuntu/data"
)
