---
name: local-mac-sound
description: Switch audio output device, set volume, mute and unmute. Use for audio routing on macOS.
user-invocable: true
---

Control CoreAudio output.

## Tools
`sound__list_devices` `sound__get_output` `sound__set_output`
`sound__get_volume` `sound__set_volume` `sound__mute` `sound__unmute`

## Rules
- List devices before switching — device names change as hardware connects.
- Report the device actually selected afterwards; a set can silently no-op if the device vanished.
