---
name: local-mac-whisper
description: Transcribe audio or video with whisper.cpp and output text or srt. Use for turning recordings into text.
user-invocable: true
---

Transcribe media locally.

## Scripts
- `tools/transcribe.sh` — whisper.cpp (whisper-cli) transcription
- `tools/convert_to_audio.sh` — extract audio from video first when needed

## Rules
- Runs locally on Apple Silicon; nothing is uploaded.
- Long media takes real time — say so before starting rather than appearing hung.
- Report the output path; do not paste a full transcript into the response.
