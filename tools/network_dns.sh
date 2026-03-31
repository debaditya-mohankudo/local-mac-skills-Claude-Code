#!/bin/bash
# Usage: network_dns.sh HOST [TYPE]
# DNS lookup for a host. TYPE defaults to A (also supports MX, TXT, CNAME, NS, AAAA).

HOST="$1"
TYPE="${2:-A}"

if [[ -z "$HOST" ]]; then
  echo "Usage: network_dns.sh HOST [TYPE]"
  exit 1
fi

ALLOWED_TYPES="A AAAA MX TXT CNAME NS PTR SOA"
if ! echo "$ALLOWED_TYPES" | grep -qw "$TYPE"; then
  echo "ERROR: unsupported record type: $TYPE (allowed: $ALLOWED_TYPES)"
  exit 1
fi

dig +short "$TYPE" "$HOST" 2>&1 || nslookup -type="$TYPE" "$HOST" 2>&1
