import Foundation

enum MusicTool {

    static func play(payload: [String: Any]) async throws -> Any {
        try runAppleScript("tell application \"Music\" to play")
        return "Playback started."
    }

    static func pause(payload: [String: Any]) async throws -> Any {
        try runAppleScript("tell application \"Music\" to pause")
        return "Playback paused."
    }

    static func nextTrack(payload: [String: Any]) async throws -> Any {
        try runAppleScript("tell application \"Music\" to next track")
        return "Skipped to next track."
    }

    static func previousTrack(payload: [String: Any]) async throws -> Any {
        try runAppleScript("tell application \"Music\" to previous track")
        return "Went to previous track."
    }

    static func setVolume(payload: [String: Any]) async throws -> Any {
        guard let volume = payload.int("volume"), (0...100).contains(volume) else {
            throw CLIError("Missing or invalid argument: volume (0–100)")
        }
        try runAppleScript("tell application \"Music\" to set sound volume to \(volume)")
        return "Volume set to \(volume)."
    }

    static func nowPlaying(payload: [String: Any]) async throws -> Any {
        let script = """
            tell application "Music"
                if player state is playing or player state is paused then
                    set t to current track
                    set n to name of t
                    set a to artist of t
                    set al to album of t
                    set d to duration of t
                    set pos to player position
                    set vol to sound volume as string
                    set ps to player state
                    set stateStr to "paused"
                    if ps is playing then set stateStr to "playing"
                    return n & "|||" & a & "|||" & al & "|||" & ((round d) as string) & "|||" & ((round pos) as string) & "|||" & vol & "|||" & stateStr
                else
                    return "stopped|||||||"
                end if
            end tell
            """
        let result = try runAppleScriptRaw(script)
        let parts = result.components(separatedBy: "|||")
        if parts.count < 7 || parts[0] == "stopped" { return "Music is stopped." }
        let name = parts[0], artist = parts[1], album = parts[2]
        let duration = Int(parts[3]) ?? 0
        let position = Int(parts[4]) ?? 0
        let volume = parts[5]
        let state = parts[6].trimmingCharacters(in: .whitespacesAndNewlines)
        let dMin = duration / 60, dSec = duration % 60
        let pMin = position / 60, pSec = position % 60
        return [
            "state": state, "track": name, "artist": artist, "album": album,
            "position": "\(pMin):\(String(format: "%02d", pSec))",
            "duration": "\(dMin):\(String(format: "%02d", dSec))",
            "volume": volume
        ] as [String: Any]
    }

    static func searchAndPlay(payload: [String: Any]) async throws -> Any {
        guard let query = payload.string("query"), !query.isEmpty else {
            throw CLIError("Missing required argument: query")
        }
        let escaped = query.replacingOccurrences(of: "\"", with: "\\\"")
        try runAppleScript("""
            tell application "Music"
                set results to (search playlist "Library" for "\(escaped)")
                if results is {} then error "No results found for: \(escaped)"
                play item 1 of results
            end tell
            """)
        return "Playing: \(query)"
    }

    static func listPlaylists(payload: [String: Any]) async throws -> Any {
        let result = try runAppleScriptRaw("""
            tell application "Music"
                set output to ""
                repeat with p in playlists
                    set output to output & (name of p) & "\\n"
                end repeat
                return output
            end tell
            """).trimmingCharacters(in: .whitespacesAndNewlines)
        if result.isEmpty { return "No playlists found." }
        return result
    }

    static func playPlaylist(payload: [String: Any]) async throws -> Any {
        guard let name = payload.string("name"), !name.isEmpty else {
            throw CLIError("Missing required argument: name")
        }
        let escaped = name.replacingOccurrences(of: "\"", with: "\\\"")
        try runAppleScript("tell application \"Music\" to play playlist \"\(escaped)\"")
        return "Playing playlist: \(name)"
    }

    static func playTrack(payload: [String: Any]) async throws -> Any {
        guard let playlist = payload.string("playlist"), !playlist.isEmpty,
              let index = payload.int("index"), index >= 1 else {
            throw CLIError("Missing required arguments: playlist, index (1-based)")
        }
        let escaped = playlist.replacingOccurrences(of: "\"", with: "\\\"")
        try runAppleScript("""
            tell application "Music"
                set pl to playlist "\(escaped)"
                set tr to track \(index) of pl
                play tr
            end tell
            """)
        return "Playing track \(index) of \"\(playlist)\"."
    }

    static func listTracks(payload: [String: Any]) async throws -> Any {
        guard let name = payload.string("playlist"), !name.isEmpty else {
            throw CLIError("Missing required argument: playlist")
        }
        let escaped = name.replacingOccurrences(of: "\"", with: "\\\"")
        let result = try runAppleScriptRaw("""
            tell application "Music"
                set output to ""
                set pl to playlist "\(escaped)"
                repeat with t in tracks of pl
                    set output to output & (name of t) & "|||" & (artist of t) & "\\n"
                end repeat
                return output
            end tell
            """).trimmingCharacters(in: .whitespacesAndNewlines)
        if result.isEmpty { return "No tracks found in playlist: \(name)" }
        let lines = result.split(separator: "\n", omittingEmptySubsequences: true)
        var tracks: [[String: String]] = []
        for (i, line) in lines.enumerated() {
            let parts = line.components(separatedBy: "|||")
            tracks.append(["index": String(i + 1), "title": parts[0], "artist": parts.count > 1 ? parts[1] : ""])
        }
        return ["playlist": name, "count": tracks.count, "tracks": tracks] as [String: Any]
    }

    // MARK: - Helpers

    @discardableResult
    private static func runAppleScript(_ script: String) throws -> String {
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/usr/bin/osascript")
        process.arguments = ["-e", script]
        let errPipe = Pipe()
        process.standardError = errPipe
        try process.run()
        process.waitUntilExit()
        guard process.terminationStatus == 0 else {
            let msg = String(data: errPipe.fileHandleForReading.readDataToEndOfFile(), encoding: .utf8) ?? "Unknown error"
            throw CLIError("AppleScript error: \(msg)")
        }
        return ""
    }

    private static func runAppleScriptRaw(_ script: String) throws -> String {
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/usr/bin/osascript")
        process.arguments = ["-e", script]
        let outPipe = Pipe()
        let errPipe = Pipe()
        process.standardOutput = outPipe
        process.standardError = errPipe
        try process.run()
        process.waitUntilExit()
        guard process.terminationStatus == 0 else {
            let msg = String(data: errPipe.fileHandleForReading.readDataToEndOfFile(), encoding: .utf8) ?? "Unknown error"
            throw CLIError(msg)
        }
        return String(data: outPipe.fileHandleForReading.readDataToEndOfFile(), encoding: .utf8) ?? ""
    }
}
