#!/bin/bash
# Usage: wifi_control.sh <status|on|off|current|list>
# Controls Wi-Fi on macOS via networksetup.

CMD="$1"
IFACE="Wi-Fi"

usage() {
  echo "Usage: wifi_control.sh <status|on|off|current|list>"
  echo ""
  echo "  status   — show Wi-Fi power state (on/off)"
  echo "  on       — turn Wi-Fi on"
  echo "  off      — turn Wi-Fi off"
  echo "  current  — show currently connected SSID and signal info"
  echo "  list     — list available Wi-Fi networks (requires Wi-Fi on)"
  exit 1
}

if [[ -z "$CMD" ]]; then
  usage
fi

# Verify Wi-Fi interface exists
if ! networksetup -listallhardwareports 2>/dev/null | grep -q "Wi-Fi"; then
  echo "ERROR: No Wi-Fi interface found on this machine."
  exit 1
fi

case "$CMD" in
  status)
    STATE=$(networksetup -getairportpower "$IFACE" 2>/dev/null | awk '{print $NF}')
    if [[ -z "$STATE" ]]; then
      echo "ERROR: Could not read Wi-Fi power state."
      exit 1
    fi
    echo "Wi-Fi is $STATE"
    ;;

  on)
    networksetup -setairportpower "$IFACE" on 2>/dev/null
    sleep 1
    STATE=$(networksetup -getairportpower "$IFACE" 2>/dev/null | awk '{print $NF}')
    echo "Wi-Fi turned on (state: $STATE)"
    ;;

  off)
    networksetup -setairportpower "$IFACE" off 2>/dev/null
    sleep 1
    STATE=$(networksetup -getairportpower "$IFACE" 2>/dev/null | awk '{print $NF}')
    echo "Wi-Fi turned off (state: $STATE)"
    ;;

  current)
    SSID=$(networksetup -getairportnetwork "$IFACE" 2>/dev/null)
    if echo "$SSID" | grep -q "You are not associated"; then
      echo "Not connected to any Wi-Fi network."
    else
      echo "$SSID"
      # Also show IP address on Wi-Fi interface
      IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null)
      [[ -n "$IP" ]] && echo "IP address: $IP"
    fi
    ;;

  list)
    STATE=$(networksetup -getairportpower "$IFACE" 2>/dev/null | awk '{print $NF}')
    if [[ "$STATE" != "On" ]]; then
      echo "ERROR: Wi-Fi is off. Turn it on first with: wifi_control.sh on"
      exit 1
    fi
    # airport utility path
    AIRPORT="/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"
    if [[ -x "$AIRPORT" ]]; then
      "$AIRPORT" -s 2>/dev/null | head -30
    else
      # Fallback: use networksetup preferred networks
      echo "Available networks scan not supported on this macOS version."
      echo "Preferred networks:"
      networksetup -listpreferredwirelessnetworks "$IFACE" 2>/dev/null
    fi
    ;;

  *)
    echo "ERROR: Unknown command: $CMD"
    usage
    ;;
esac
