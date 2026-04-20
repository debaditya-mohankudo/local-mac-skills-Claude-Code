#!/bin/bash
# Convert a video file to MP3 audio using ffmpeg.
#
# Usage:
#   ./convert_to_audio.sh <input_file> [output_dir]
#
# Arguments:
#   input_file  — path to .mp4, .mov, .mkv, .avi, .webm, etc.
#   output_dir  — where to save the .mp3 (default: same dir as input)
#
# Prints the path to the .mp3 on success.

set -euo pipefail

INPUT_FILE="${1:-}"
OUTPUT_DIR="${2:-}"

if [[ -z "$INPUT_FILE" ]]; then
    echo "Usage: $0 <input_file> [output_dir]" >&2
    exit 1
fi

if [[ ! -f "$INPUT_FILE" ]]; then
    echo "Error: file not found: $INPUT_FILE" >&2
    exit 1
fi

if [[ -z "$OUTPUT_DIR" ]]; then
    OUTPUT_DIR="$(dirname "$INPUT_FILE")"
fi

mkdir -p "$OUTPUT_DIR"

BASENAME="$(basename "$INPUT_FILE")"
STEM="${BASENAME%.*}"
MP3_PATH="$OUTPUT_DIR/${STEM}.mp3"

echo "Converting: $INPUT_FILE → $MP3_PATH" >&2
ffmpeg -i "$INPUT_FILE" -vn -ar 44100 -ac 2 -b:a 128k "$MP3_PATH" -y -loglevel error

echo "$MP3_PATH"
