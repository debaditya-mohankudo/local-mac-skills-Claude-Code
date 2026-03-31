#!/bin/bash

# Contacts Cache & Search Tool
# Dynamically searches contacts and manages quick-access cache (without storing personal data)

CACHE_FILE="$HOME/.contacts_cache"
CACHE_BACKUP="$HOME/.contacts_cache.bak"
CONTACTS_SCRIPT="~/workspace/claude_for_mac_local/tools/contacts_search.sh"

# Create backup
if [ -f "$CACHE_FILE" ]; then
  cp "$CACHE_FILE" "$CACHE_BACKUP"
fi

# Initialize cache if it doesn't exist
if [ ! -f "$CACHE_FILE" ]; then
  cat > "$CACHE_FILE" << 'EOF'
{
  "frequently_used": [],
  "favorites": [],
  "cached_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "notes": "Contacts cache - cached locally, not in git"
}
EOF
fi

# Function to search cache first, then system contacts
search_contact() {
  local name="$1"

  if [ -z "$name" ]; then
    echo "Usage: search_contact <name>"
    return 1
  fi

  echo "🔍 Searching for: $name"

  # Check cache first
  if command -v jq &> /dev/null; then
    local cache_result=$(jq -r ".frequently_used[] | select(.name | ascii_downcase | contains(\"$(echo $name | tr '[:upper:]' '[:lower:]')\")) | \"\(.name) | \(.phone) | \(.type) | Cached\"" "$CACHE_FILE" 2>/dev/null)

    if [ ! -z "$cache_result" ]; then
      echo "📦 Found in cache:"
      echo "$cache_result"
      return 0
    fi
  fi

  # If not in cache, search system contacts
  echo "📱 Searching system contacts..."
  eval "$CONTACTS_SCRIPT '$name'" 2>/dev/null
}

# Function to add contact to cache
add_contact() {
  local name="$1"
  local phone="$2"
  local type="${3:-mobile}"

  if command -v jq &> /dev/null; then
    jq --arg name "$name" --arg phone "$phone" --arg type "$type" \
      '.frequently_used += [{
        "name": $name,
        "phone": $phone,
        "type": $type,
        "last_contacted": now | todate,
        "frequency": "manual"
      }]' "$CACHE_FILE" > "$CACHE_FILE.tmp" && \
      mv "$CACHE_FILE.tmp" "$CACHE_FILE"
  else
    echo "jq not found. Install with: brew install jq"
    return 1
  fi
}

# Function to add favorite (alias)
add_favorite() {
  local name="$1"
  local phone="$2"
  local alias="$3"

  if command -v jq &> /dev/null; then
    jq --arg name "$name" --arg phone "$phone" --arg alias "$alias" \
      '.favorites += [{
        "name": $name,
        "phone": $phone,
        "alias": $alias
      }]' "$CACHE_FILE" > "$CACHE_FILE.tmp" && \
      mv "$CACHE_FILE.tmp" "$CACHE_FILE"
  fi
}

# Function to list cache
list_cache() {
  if command -v jq &> /dev/null; then
    echo ""
    echo "=== Frequently Used Contacts ==="
    jq -r '.frequently_used[] | "  \(.name) | \(.phone) | \(.type) | Last: \(.last_contacted)"' "$CACHE_FILE"

    echo ""
    echo "=== Favorites (Quick Access) ==="
    jq -r '.favorites[] | "  \(.alias) → \(.name) (\(.phone))"' "$CACHE_FILE"
  else
    cat "$CACHE_FILE"
  fi
}

# Function to update timestamp
update_timestamp() {
  if command -v jq &> /dev/null; then
    jq ".cached_at = (now | todate)" "$CACHE_FILE" > "$CACHE_FILE.tmp" && \
      mv "$CACHE_FILE.tmp" "$CACHE_FILE"
  fi
}

# Main menu
case "${1:-help}" in
  add)
    if [ -z "$2" ] || [ -z "$3" ]; then
      echo "Usage: $0 add <name> <phone> [type]"
      echo "Example: $0 add 'John' '+1XXXXXXXXXX' mobile"
      exit 1
    fi
    add_contact "$2" "$3" "${4:-mobile}"
    update_timestamp
    echo "✅ Added: $2"
    ;;

  search)
    if [ -z "$2" ]; then
      echo "Usage: $0 search <name>"
      echo "Example: $0 search John"
      exit 1
    fi
    search_contact "$2"
    ;;

  favorite)
    if [ -z "$2" ] || [ -z "$3" ] || [ -z "$4" ]; then
      echo "Usage: $0 favorite <name> <phone> <alias>"
      echo "Example: $0 favorite 'John' '+1XXXXXXXXXX' 'J'"
      exit 1
    fi
    add_favorite "$2" "$3" "$4"
    update_timestamp
    echo "⭐ Added favorite: $4 → $2"
    ;;

  list|show)
    list_cache
    ;;

  recent)
    echo "🔄 Checking recent iMessage contacts..."
    # Get top 5 most recent unique contacts from last 30 days
    ~/workspace/claude_for_mac_local/tools/imessage_check.sh 43200 | \
      grep "|" | \
      awk -F'|' '{print $3}' | \
      grep -v "^\[" | \
      grep -v "^Me$" | \
      sort | uniq -c | sort -rn | head -5 | while read count contact; do
        if [ ! -z "$contact" ]; then
          echo "  👤 $contact (contacted $count times)"
        fi
      done
    ;;


  backup)
    if [ -f "$CACHE_BACKUP" ]; then
      echo "Latest backup: $(ls -lh $CACHE_BACKUP | awk '{print $6, $7, $8}')"
      echo ""
      cat "$CACHE_BACKUP"
    else
      echo "No backup found"
    fi
    ;;

  restore)
    if [ -f "$CACHE_BACKUP" ]; then
      cp "$CACHE_BACKUP" "$CACHE_FILE"
      echo "✅ Restored from backup"
    else
      echo "No backup found"
    fi
    ;;

  reset)
    read -p "⚠️  Reset cache? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
      cat > "$CACHE_FILE" << 'EOF'
{
  "frequently_used": [],
  "favorites": [],
  "cached_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "notes": "Contacts cache - cached locally, not in git"
}
EOF
      echo "✅ Cache reset"
    fi
    ;;

  *)
    cat << 'EOF'
📱 Contacts Cache Manager

Usage: contacts_cache_update.sh [command] [args]

Commands:
  add <name> <phone> [type]      - Add contact to cache
  search <name>                  - Search for contact by name (live lookup)
  favorite <name> <phone> <a>    - Add quick-access favorite (alias)
  list|show                      - Show all cached contacts
  recent                         - Show top 5 recent iMessage contacts
  backup                         - Show latest backup
  restore                        - Restore from backup
  reset                          - Clear cache
  help                           - Show this help

Examples:
  $0 add "John" "+1XXXXXXXXXX" mobile
  $0 favorite "John" "+1XXXXXXXXXX" "J"
  $0 search "John"
  $0 recent
  $0 list

Notes:
  - Cache is stored locally in ~/.contacts_cache (git-ignored)
  - Personal data is cached locally but never pushed to git
  - Search queries your system contacts in real-time

Cache location: ~/.contacts_cache (git-ignored)
Backup location: ~/.contacts_cache.bak
EOF
    ;;
esac
