import Foundation

enum iMessageTool {

    static func sendMessage(payload: [String: Any]) async throws -> Any {
        guard let recipient = payload.string("recipient"), !recipient.isEmpty else {
            throw CLIError("Missing required argument: recipient (phone number or email)")
        }
        guard let message = payload.string("message"), !message.isEmpty else {
            throw CLIError("Missing required argument: message")
        }
        let delaySeconds = payload.int("delay_seconds") ?? 0
        try await sendViaiMessage(to: recipient, message: message, delaySeconds: delaySeconds)
        return "Message sent to \(recipient)\(delaySeconds > 0 ? " (scheduled for \(delaySeconds)s from now)" : "")"
    }

    private static func sendViaiMessage(to recipient: String, message: String, delaySeconds: Int) async throws {
        let escapedRecipient = recipient.replacingOccurrences(of: "\"", with: "\\\"")
        let escapedMessage = message.replacingOccurrences(of: "\"", with: "\\\"")
            .replacingOccurrences(of: "\n", with: "\\n")
        let appleScript: String
        if delaySeconds > 0 {
            appleScript = """
            delay \(delaySeconds)
            tell application "Messages"
                activate
                set targetBuddy to "\(escapedRecipient)"
                set targetService to 1st service whose service type = iMessage
                send "\(escapedMessage)" to buddy targetBuddy of targetService
            end tell
            """
        } else {
            appleScript = """
            tell application "Messages"
                activate
                set targetBuddy to "\(escapedRecipient)"
                set targetService to 1st service whose service type = iMessage
                send "\(escapedMessage)" to buddy targetBuddy of targetService
            end tell
            """
        }
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/usr/bin/osascript")
        process.arguments = ["-e", appleScript]
        let errorPipe = Pipe()
        process.standardError = errorPipe
        try process.run()
        process.waitUntilExit()
        guard process.terminationStatus == 0 else {
            let msg = String(data: errorPipe.fileHandleForReading.readDataToEndOfFile(), encoding: .utf8) ?? "Unknown error"
            throw CLIError(msg)
        }
    }

    static func readMessages(payload: [String: Any]) async throws -> Any {
        let limit = payload.int("limit") ?? 10
        let direction = payload.string("direction") ?? "received"
        let messages = try await readRecentMessages(limit: limit, direction: direction)
        if messages.isEmpty { return "No messages found." }
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        let data = try encoder.encode(messages)
        return (try? JSONSerialization.jsonObject(with: data)) ?? messages
    }

    private static func readRecentMessages(limit: Int, direction: String) async throws -> [[String: String]] {
        let dbPath = (NSHomeDirectory() as NSString).appendingPathComponent("Library/Messages/chat.db")
        let directionClause: String
        switch direction {
        case "sent": directionClause = "AND message.is_from_me = 1"
        case "all":  directionClause = ""
        default:     directionClause = "AND message.is_from_me = 0"
        }
        let sql = """
            SELECT datetime(message.date/1000000000 + 978307200, 'unixepoch', 'localtime') as date,
                   CASE WHEN message.is_from_me = 1 THEN 'me' ELSE COALESCE(handle.id, '') END as 'from',
                   message.is_from_me,
                   COALESCE(message.text, '') as text,
                   message.attributedBody
            FROM message
            LEFT JOIN handle ON message.handle_id = handle.ROWID
            WHERE (handle.id IS NOT NULL OR message.is_from_me = 1)
              \(directionClause)
            ORDER BY message.date DESC
            LIMIT ?
            """
        let results = try SQLiteHelper.queryWithParams(databasePath: dbPath, sql: sql, parameters: [limit])
        return results.map { row in
            var r = row
            if (r["text"] ?? "").isEmpty, let bodyHex = r["attributedBody"], !bodyHex.isEmpty {
                r["text"] = extractTextFromAttributedBody(bodyHex)
            }
            r.removeValue(forKey: "attributedBody")
            if let val = r["is_from_me"] {
                r["direction"] = val == "1" ? "sent" : "received"
                r.removeValue(forKey: "is_from_me")
            }
            return r
        }
    }

    private static func extractTextFromAttributedBody(_ hexOrRaw: String) -> String {
        // Convert hex string to Data if needed
        let data: Data
        if hexOrRaw.count % 2 == 0 && hexOrRaw.allSatisfy({ $0.isHexDigit }) {
            var bytes: [UInt8] = []
            var idx = hexOrRaw.startIndex
            while idx < hexOrRaw.endIndex {
                let next = hexOrRaw.index(idx, offsetBy: 2)
                bytes.append(UInt8(hexOrRaw[idx..<next], radix: 16) ?? 0)
                idx = next
            }
            data = Data(bytes)
        } else {
            data = Data(hexOrRaw.utf8)
        }
        // Decode as NSAttributedString via legacy sequential stream archive (NSUnarchiver)
        if let attributed = try? NSUnarchiver.unarchiveObject(with: data) as? NSAttributedString {
            return attributed.string
        }
        if let attributed = try? NSUnarchiver.unarchiveObject(with: data) as? NSMutableAttributedString {
            return attributed.string
        }
        // Fallback: scan for length-prefixed UTF-8 string at 0x01 0x2b marker
        let bytes = Array(data)
        for i in 0..<(bytes.count - 2) {
            if bytes[i] == 0x01 && bytes[i+1] == 0x2b {
                let len = Int(bytes[i+2])
                let start = i + 3
                let end = start + len
                if end <= bytes.count { return String(bytes: bytes[start..<end], encoding: .utf8) ?? "" }
            }
        }
        return ""
    }
}
