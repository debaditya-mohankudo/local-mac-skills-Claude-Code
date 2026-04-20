---
name: local-mac-whisper
description: Transcribe video or audio files to text using whisper.cpp (Apple Silicon optimised). Two-step pipeline — convert video to MP3 first, then transcribe. Supports MP4, MOV, MKV, AVI, WebM, MP3, M4A, WAV — any format ffmpeg can decode. Outputs plain .txt and timestamped .srt. Optionally saves transcript to Obsidian vault. Use when user asks to transcribe, extract text, or get subtitles from a video/audio file.
user-invocable: true
---

# local-mac-whisper

Transcribe video or audio files using whisper.cpp on Apple Silicon (M1/M2/M3).

Two-step pipeline:
1. **Convert** video → MP3 audio (`convert_to_audio.sh`)
2. **Transcribe** MP3 → text (`transcribe.sh` via `whisper-cli`)

---

## Steps

**1. Resolve the input file path**

- If the user gives a filename without a path, check `~/Downloads/` first, then ask.
- Expand `~` to the full path.

**2. If input is a video, convert to MP3 first**

```bash
~/workspace/claude_for_mac_local/tools/convert_to_audio.sh "<input_video>" ["<output_dir>"]
```

- Outputs a `.mp3` in the same directory as the video (or `output_dir` if specified).
- Prints the `.mp3` path on success.
- Skip this step if the input is already `.mp3`, `.wav`, `.m4a`, etc.

**3. Run the transcription**

```bash
~/workspace/claude_for_mac_local/tools/transcribe.sh "<input_audio>" ["<output_dir>"] ["<model>"]
```

- `input_audio` — full path to .mp3 (or other audio file)
- `output_dir` — optional. Defaults to same directory as input file.
- `model` — optional. Default: `~/.whisper/ggml-small.en-q5_1.bin`

The script prints the path to the `.txt` transcript on success. A `.srt` (timestamped subtitles) is also saved alongside.

**4. Display a summary**

After transcription completes:
- Show the first 500 characters of the transcript as a preview
- Show file sizes of `.txt` and `.srt`
- Show output paths

**5. Optionally save to vault**

If the user asks to save to vault, write the transcript to the appropriate vault note using `obsidian_write.sh`:

```bash
~/workspace/claude_for_mac_local/tools/obsidian_write.sh "<vault_note_path>" "<content>"
```

---

## Model

| Model | Path | Quality |
|-------|------|---------|
| `ggml-small.en-q5_1` | `~/.whisper/ggml-small.en-q5_1.bin` | Default — English only, fast on M1 |

---

## Example usage

- `/local-mac-whisper ~/Downloads/lecture.mp4` — convert + transcribe a video
- `/local-mac-whisper ~/Downloads/lecture.mp3` — transcribe an existing audio file
- `/local-mac-whisper ~/Downloads/lecture.mp4 save "Documentation/MSc_Maths/Lecture_4_transcript"` — transcribe and save to vault

---

## Supported Formats

Uses `ffmpeg` under the hood — accepts any format ffmpeg can decode:

| Type | Formats |
|------|---------|
| Video | `.mp4`, `.mov`, `.mkv`, `.avi`, `.webm`, `.m4v` |
| Audio | `.mp3`, `.m4a`, `.wav`, `.flac`, `.ogg`, `.aac`, `.opus` |

## Notes

- Model lives at `~/.whisper/ggml-small.en-q5_1.bin` (181 MB, English only)
- Uses GPU (Metal) automatically via whisper.cpp — no configuration needed
- Primary use case: MSc lecture transcription → save under `Documentation/MSc_Maths/`
- Output `.txt` is plain transcript; `.srt` has timestamps for reference
