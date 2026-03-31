#!/bin/bash
# screencapture_control.sh — start, stop, status, list screen recordings
# Usage: screencapture_control.sh start|stop|status|list [output_dir]

ACTION="$1"
OUTPUT_DIR="${2:-$HOME/Movies/Recordings}"
PID_FILE="/tmp/screencapture_recording.pid"

if [[ -z "$ACTION" ]]; then
  echo "Usage: screencapture_control.sh start|stop|status|list [output_dir]"
  exit 1
fi

case "$ACTION" in
  start)
    if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
      echo "ERROR: Recording already in progress (PID $(cat "$PID_FILE"))"
      exit 1
    fi
    mkdir -p "$OUTPUT_DIR"
    FILENAME="recording-$(date +%Y-%m-%d-%H-%M-%S).mov"
    OUTPUT_PATH="$OUTPUT_DIR/$FILENAME"
    screencapture -v -x -C "$OUTPUT_PATH" &
    echo $! > "$PID_FILE"
    echo "Recording started: $OUTPUT_PATH"
    ;;

  stop)
    if [[ ! -f "$PID_FILE" ]]; then
      echo "ERROR: No active recording found"
      exit 1
    fi
    PID=$(cat "$PID_FILE")
    if ! kill -0 "$PID" 2>/dev/null; then
      echo "ERROR: Recording process not found (PID $PID)"
      rm -f "$PID_FILE"
      exit 1
    fi
    kill -INT "$PID"
    rm -f "$PID_FILE"
    echo "Recording stopped (PID $PID). File saved to $OUTPUT_DIR."
    ;;

  status)
    if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
      echo "Recording in progress (PID $(cat "$PID_FILE"))"
    else
      rm -f "$PID_FILE" 2>/dev/null
      echo "No active recording"
    fi
    ;;

  list)
    mkdir -p "$OUTPUT_DIR"
    FILES=$(ls -t "$OUTPUT_DIR"/*.mov 2>/dev/null)
    if [[ -z "$FILES" ]]; then
      echo "No recordings found in $OUTPUT_DIR"
    else
      echo "Recordings in $OUTPUT_DIR:"
      ls -lht "$OUTPUT_DIR"/*.mov
    fi
    ;;

  *)
    echo "Usage: screencapture_control.sh start|stop|status|list [output_dir]"
    exit 1
    ;;
esac
