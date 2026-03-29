#!/bin/bash
# Usage: safari_read.sh [mode]
# Modes:
#   text        — innerText of the full page (default)
#   html        — full outerHTML
#   links       — all href links on the page
#   title       — document title
#   selected    — currently selected text

MODE="${1:-text}"

case "$MODE" in
  text)
    osascript -e 'tell application "Safari" to do JavaScript "document.body.innerText" in current tab of front window'
    ;;
  html)
    osascript -e 'tell application "Safari" to do JavaScript "document.documentElement.outerHTML" in current tab of front window'
    ;;
  links)
    osascript -e 'tell application "Safari" to do JavaScript "Array.from(document.querySelectorAll(\"a[href]\")).map(a => a.href + \" | \" + a.innerText.trim()).join(\"\\n\")" in current tab of front window'
    ;;
  title)
    osascript -e 'tell application "Safari" to do JavaScript "document.title" in current tab of front window'
    ;;
  selected)
    osascript -e 'tell application "Safari" to do JavaScript "window.getSelection().toString()" in current tab of front window'
    ;;
  *)
    echo "Usage: safari_read.sh text|html|links|title|selected"
    exit 1
    ;;
esac
