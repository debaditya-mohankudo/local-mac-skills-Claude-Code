import Foundation

enum NotifyTool {

    static func send(payload: [String: Any]) async throws -> Any {
        guard let title = payload.string("title") else {
            throw CLIError("Missing required argument: title")
        }
        let body = payload.string("body") ?? ""

        let safeTitle = title.replacingOccurrences(of: "\\", with: "\\\\")
                             .replacingOccurrences(of: "\"", with: "\\\"")
        let safeBody  = body.replacingOccurrences(of: "\\", with: "\\\\")
                            .replacingOccurrences(of: "\"", with: "\\\"")

        let script = "display notification \"\(safeBody)\" with title \"\(safeTitle)\" sound name \"Ping\""
        _ = try await runProcess("/usr/bin/osascript", arguments: ["-e", script])
        return "Notification sent: \(title)"
    }
}
