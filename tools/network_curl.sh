#!/bin/bash
# Usage: network_curl.sh URL [METHOD] [DATA]
# Performs an HTTP request and returns status code + response body (truncated to 3000 chars).
# METHOD defaults to GET. DATA is optional request body (triggers POST if METHOD not set).

URL="$1"
METHOD="${2:-GET}"
DATA="$3"

if [[ -z "$URL" ]]; then
  echo "Usage: network_curl.sh URL [METHOD] [DATA]"
  exit 1
fi

# Warn on non-GET methods
if [[ "$METHOD" != "GET" && "$METHOD" != "HEAD" ]]; then
  echo "WARNING: sending $METHOD request to $URL"
fi

TMPFILE=$(mktemp)

if [[ -n "$DATA" ]]; then
  HTTP_CODE=$(curl -s -o "$TMPFILE" -w "%{http_code}" -X "$METHOD" \
    -H "Content-Type: application/json" \
    --data "$DATA" \
    --max-time 15 \
    "$URL" 2>&1)
else
  HTTP_CODE=$(curl -s -o "$TMPFILE" -w "%{http_code}" -X "$METHOD" \
    --max-time 15 \
    "$URL" 2>&1)
fi

BODY=$(cat "$TMPFILE")
rm -f "$TMPFILE"

echo "Status: $HTTP_CODE"
echo "---"
# Truncate to 3000 chars to avoid context overload
echo "${BODY:0:3000}"
[[ ${#BODY} -gt 3000 ]] && echo "... [truncated — ${#BODY} chars total]"
