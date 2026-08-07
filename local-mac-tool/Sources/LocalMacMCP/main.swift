import Foundation

// CLI dispatcher — reads command from argv[1], JSON payload from stdin, writes JSON to stdout.
// Usage: local-mac-tool <command>
// Stdin:  JSON object with named arguments
// Stdout: {"status":"ok","data":<result>}  or {"status":"error","message":"..."}

let args = CommandLine.arguments
guard args.count > 1 else {
    fputs("Usage: local-mac-tool <command>\n", stderr)
    exit(1)
}

let command = args[1]
let stdinData = FileHandle.standardInput.readDataToEndOfFile()
let payload = (try? JSONSerialization.jsonObject(with: stdinData.isEmpty ? "{}".data(using: .utf8)! : stdinData)) as? [String: Any] ?? [:]

func respond(_ data: Any) {
    let envelope: [String: Any] = ["status": "ok", "data": data]
    let json = try! JSONSerialization.data(withJSONObject: envelope, options: [.prettyPrinted])
    print(String(data: json, encoding: .utf8)!)
}

func respondError(_ message: String) {
    let envelope: [String: Any] = ["status": "error", "message": message]
    let json = try! JSONSerialization.data(withJSONObject: envelope)
    fputs(String(data: json, encoding: .utf8)! + "\n", stderr)
    exit(1)
}

do {
    switch command {

    // MARK: Foundation Models
    // Stays Swift permanently: Apple's FoundationModels framework has no
    // Python or PyObjC binding, so the on-device path cannot be reached from
    // the Python side. The Python tool implements only the HTTP fallback.
    case "foundation-models-query":
        let result = try await FoundationModelsTool.query(payload: payload)
        respond(result)

    // MARK: Sound
    // Stays Swift: switching the audio output device is CoreAudio. AppleScript
    // can set the system volume but cannot enumerate or select devices, so this
    // is the one tool family with no AppleScript equivalent.
    case "sound-list-devices":
        let result = try await SoundTool.listDevices(payload: payload)
        respond(result)
    case "sound-get-output":
        let result = try await SoundTool.getOutput(payload: payload)
        respond(result)
    case "sound-set-output":
        let result = try await SoundTool.setOutput(payload: payload)
        respond(result)
    case "sound-get-volume":
        let result = try await SoundTool.getVolume(payload: payload)
        respond(result)
    case "sound-set-volume":
        let result = try await SoundTool.setVolume(payload: payload)
        respond(result)
    case "sound-mute":
        let result = try await SoundTool.mute(payload: payload)
        respond(result)
    case "sound-unmute":
        let result = try await SoundTool.unmute(payload: payload)
        respond(result)

    default:
        respondError("Unknown command: \(command)")
    }
} catch {
    respondError(error.localizedDescription)
}
