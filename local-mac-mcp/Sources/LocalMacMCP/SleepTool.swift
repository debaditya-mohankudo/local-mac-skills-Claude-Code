import Foundation

enum SleepTool {

    static func sleepNow(payload: [String: Any]) async throws -> Any {
        try await quitAllApps()
        _ = try await runProcess("/usr/bin/pmset", arguments: ["sleepnow"])
        return "Sleeping now."
    }

    static func sleepIn(payload: [String: Any]) async throws -> Any {
        guard let minutes = payload.int("minutes"), minutes >= 1 else {
            throw CLIError("Missing or invalid argument: minutes (must be ≥ 1)")
        }
        let cmd = "pmset sleepnow"
        let output = try await runProcess("/bin/sh", arguments: ["-c", "echo '\(cmd)' | at now + \(minutes) minutes 2>&1"])
        return "Sleep scheduled in \(minutes) minute(s).\n\(output.trimmingCharacters(in: .whitespacesAndNewlines))"
    }

    static func cancelSleep(payload: [String: Any]) async throws -> Any {
        let jobs = try await runProcess("/usr/bin/atq", arguments: [])
        if jobs.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            return "No scheduled sleep jobs found."
        }
        _ = try await runProcess("/bin/sh", arguments: ["-c", "atq | awk '{print $1}' | xargs atrm"])
        return "Cancelled all scheduled at jobs:\n\(jobs.trimmingCharacters(in: .whitespacesAndNewlines))"
    }

    static func sleepStatus(payload: [String: Any]) async throws -> Any {
        let jobs = try await runProcess("/usr/bin/atq", arguments: [])
        let trimmed = jobs.trimmingCharacters(in: .whitespacesAndNewlines)
        if trimmed.isEmpty { return "No scheduled sleep (or at) jobs." }
        return "Scheduled at jobs:\n\(trimmed)"
    }

    static func winddown(payload: [String: Any]) async throws -> Any {
        let delay = payload.int("minutes") ?? 0
        if delay <= 0 {
            try await quitAllApps()
            _ = try await runProcess("/usr/bin/pmset", arguments: ["sleepnow"])
            return "Wind-down complete. Sleeping now."
        } else {
            let script = """
                #!/bin/bash
                APP_NAMES=$(osascript -e '
                  tell application "System Events"
                    set theNames to name of every application process whose background only is false and name is not in {"Code", "Finder", "SystemUIServer"}
                    set output to ""
                    repeat with n in theNames
                      set output to output & n & linefeed
                    end repeat
                    return output
                  end tell
                ' 2>/dev/null)
                while IFS= read -r appName; do
                  [[ -z "$appName" ]] && continue
                  osascript -e "tell application \\"System Events\\" to quit (first application process whose name is \\"$appName\\")" 2>/dev/null
                  sleep 1
                done <<< "$APP_NAMES"
                sleep 5
                pmset sleepnow
                """
            let tmpPath = "/tmp/sleep_winddown_\(Int(Date().timeIntervalSince1970)).sh"
            try script.write(toFile: tmpPath, atomically: true, encoding: .utf8)
            _ = try await runProcess("/bin/chmod", arguments: ["+x", tmpPath])
            let output = try await runProcess("/bin/sh", arguments: ["-c", "echo 'bash \(tmpPath)' | at now + \(delay) minutes 2>&1"])
            return "Wind-down scheduled in \(delay) minute(s).\n\(output.trimmingCharacters(in: .whitespacesAndNewlines))"
        }
    }

    private static func quitAllApps() async throws {
        let script = """
            tell application "System Events"
                set theNames to name of every application process whose background only is false and name is not in {"Code", "Finder", "SystemUIServer"}
                set output to ""
                repeat with n in theNames
                    set output to output & n & linefeed
                end repeat
                return output
            end tell
            """
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/usr/bin/osascript")
        process.arguments = ["-e", script]
        let outPipe = Pipe()
        process.standardOutput = outPipe
        process.standardError = Pipe()
        try process.run()
        process.waitUntilExit()
        let appNames = (String(data: outPipe.fileHandleForReading.readDataToEndOfFile(), encoding: .utf8) ?? "")
            .components(separatedBy: "\n")
            .map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
            .filter { !$0.isEmpty }

        for appName in appNames {
            let escaped = appName.replacingOccurrences(of: "\"", with: "\\\"")
            let quitScript = """
                tell application "System Events"
                    quit (first application process whose name is "\(escaped)")
                end tell
                """
            let qp = Process()
            qp.executableURL = URL(fileURLWithPath: "/usr/bin/osascript")
            qp.arguments = ["-e", quitScript]
            qp.standardOutput = Pipe()
            qp.standardError = Pipe()
            try? qp.run()
            qp.waitUntilExit()
            try await Task.sleep(nanoseconds: 1_000_000_000)
        }
        try await Task.sleep(nanoseconds: 5_000_000_000)
    }
}
