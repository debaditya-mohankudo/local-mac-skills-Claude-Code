#!/bin/bash
# Transcribe an audio/video file using whisper.cpp (whisper-cli via Homebrew).
#
# Usage:
#   ./transcribe.sh <input_file> [output_dir] [model]
#
# Arguments:
#   input_file  — path to .mp3, .mp4, .wav, .m4a, .mov, etc.
#   output_dir  — where to save transcript (default: same dir as input)
#   model       — path to ggml model file (default: ~/.whisper/ggml-small.en-q5_1.bin)
#
# Output:
#   <output_dir>/<filename>.txt  — plain text transcript
#   <output_dir>/<filename>.srt  — timestamped subtitles
#
# Prints the path to the .txt transcript on success.

set -euo pipefail

INPUT_FILE="${1:-}"
OUTPUT_DIR="${2:-}"
MODEL="${3:-$HOME/.whisper/ggml-small.en-q5_1.bin}"

if [[ -z "$INPUT_FILE" ]]; then
    echo "Usage: $0 <input_file> [output_dir] [model]" >&2
    exit 1
fi

if [[ ! -f "$INPUT_FILE" ]]; then
    echo "Error: file not found: $INPUT_FILE" >&2
    exit 1
fi

if [[ ! -f "$MODEL" ]]; then
    echo "Error: model not found: $MODEL" >&2
    exit 1
fi

if [[ -z "$OUTPUT_DIR" ]]; then
    OUTPUT_DIR="$(dirname "$INPUT_FILE")"
fi

mkdir -p "$OUTPUT_DIR"

BASENAME="$(basename "$INPUT_FILE")"
STEM="${BASENAME%.*}"
TXT_PATH="$OUTPUT_DIR/${STEM}.txt"
SRT_PATH="$OUTPUT_DIR/${STEM}.srt"

echo "Transcribing: $INPUT_FILE" >&2
echo "Model: $MODEL" >&2
echo "Output: $OUTPUT_DIR/" >&2

# whisper-cli outputs files named <stem>.txt and <stem>.srt in the output dir
whisper-cli \
    --model "$MODEL" \
    --output-txt \
    --output-srt \
    --output-file "$OUTPUT_DIR/$STEM" \
    "$INPUT_FILE"

echo "$TXT_PATH"
