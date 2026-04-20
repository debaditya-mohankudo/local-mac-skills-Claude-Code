import Foundation

enum TimeTool {

    static func now(payload: [String: Any]) async throws -> Any {
        let tz = TimeZone(identifier: "Asia/Kolkata") ?? .current
        var cal = Calendar.current
        cal.timeZone = tz
        let formatter = DateFormatter()
        formatter.timeZone = tz
        formatter.dateFormat = "EEEE, dd MMM yyyy  HH:mm:ss zzz"
        return formatter.string(from: Date())
    }

    // Schedules an alarm at HH:MM (24h) using `at`. Optionally creates an Apple Reminder.
    static func alarm(payload: [String: Any]) async throws -> Any {
        guard let target = payload.string("time"), !target.isEmpty else {
            throw CLIError("Missing required argument: time (HH:MM)")
        }
        let label = payload.string("label") ?? "Alarm"
        let addReminder = payload.bool("reminder") ?? false

        // Validate HH:MM
        let parts = target.split(separator: ":").map { String($0) }
        guard parts.count == 2, let h = Int(parts[0]), let m = Int(parts[1]),
              h >= 0, h <= 23, m >= 0, m <= 59 else {
            throw CLIError("Invalid time format. Use HH:MM (24-hour).")
        }

        var cal = Calendar.current
        let now = Date()
        var comps = cal.dateComponents([.year, .month, .day], from: now)
        comps.hour = h; comps.minute = m; comps.second = 0
        var targetDate = cal.date(from: comps)!
        if targetDate <= now { targetDate = cal.date(byAdding: .day, value: 1, to: targetDate)! }

        let humanTime = String(format: "%02d:%02d", h, m)
        let humanDate = DateFormatter().apply { f in
            f.dateFormat = "HH:mm 'on' EEE dd MMM"
        }.string(from: targetDate)

        let atTime = DateFormatter().apply { f in f.dateFormat = "HH:mm" }.string(from: targetDate)
        let notifyCmd = """
        osascript -e 'display notification "Alarm: \(humanTime)" with title "⏰ \(label)" sound name "Glass"'; \
        osascript -e 'display alert "⏰ \(label)" message "It is now \(humanTime)"'
        """
        let atResult = shellRun("echo \(shellQuote(notifyCmd)) | at \(atTime)", shell: true)

        var parts2: [String] = ["Alarm set: \"\(label)\" at \(humanDate) (scheduled via at)"]
        if !atResult.isEmpty { parts2.append(atResult) }

        if addReminder {
            let iso = ISO8601DateFormatter()
            iso.timeZone = .current
            let dueStr = iso.string(from: targetDate)
            _ = try await RemindersTool.create(payload: ["title": "⏰ \(label)", "due_date": dueStr])
            parts2[0] += " + Apple Reminder"
        }

        return parts2.joined(separator: "\n")
    }

    // Schedules a wait-N-minutes timer via `at`.
    static func wait(payload: [String: Any]) async throws -> Any {
        guard let minutesRaw = payload["minutes"] else {
            throw CLIError("Missing required argument: minutes")
        }
        let minutes: Double
        if let d = minutesRaw as? Double { minutes = d }
        else if let i = minutesRaw as? Int { minutes = Double(i) }
        else if let s = minutesRaw as? String, let d = Double(s) { minutes = d }
        else { throw CLIError("Invalid minutes value.") }

        guard minutes > 0 else { throw CLIError("minutes must be positive.") }

        let label = payload.string("label") ?? "Timer"
        let atMins = max(1, Int((minutes + 0.5).rounded()))
        let finishDate = Date().addingTimeInterval(Double(atMins) * 60)
        let finishStr = DateFormatter().apply { f in f.dateFormat = "HH:mm" }.string(from: finishDate)

        let notifyCmd = """
        osascript -e 'display notification "\(minutes) min elapsed" with title "⏱ \(label)" sound name "Glass"'; \
        osascript -e 'display alert "⏱ \(label)" message "\(minutes) minute(s) are up!"'
        """
        let atResult = shellRun("echo \(shellQuote(notifyCmd)) | at now + \(atMins) minutes", shell: true)

        var msg = "Timer started: \"\(label)\" — \(minutes) min, finishes ~\(finishStr) (scheduled via at)"
        if !atResult.isEmpty { msg += "\n\(atResult)" }
        return msg
    }

    private static func shellQuote(_ s: String) -> String {
        "'" + s.replacingOccurrences(of: "'", with: "'\\''") + "'"
    }

    private static func shellRun(_ cmd: String, shell: Bool) -> String {
        let proc = Process()
        proc.executableURL = URL(fileURLWithPath: "/bin/sh")
        proc.arguments = ["-c", cmd]
        let pipe = Pipe()
        proc.standardOutput = pipe
        proc.standardError = pipe
        try? proc.run()
        proc.waitUntilExit()
        return String(data: pipe.fileHandleForReading.readDataToEndOfFile(), encoding: .utf8)?
            .trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
    }
}

private extension DateFormatter {
    @discardableResult func apply(_ block: (DateFormatter) -> Void) -> DateFormatter {
        block(self); return self
    }
}
