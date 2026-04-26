import Foundation
import SQLite3

enum MailTool {

    static func readEmails(payload: [String: Any]) async throws -> Any {
        let limit = payload.int("limit") ?? 20
        let folder = payload.string("folder") ?? "INBOX"
        let emails = try await readRecentEmails(limit: limit, folder: folder)
        if emails.isEmpty { return "No emails found in \(folder)." }
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        let data = try encoder.encode(emails)
        return (try? JSONSerialization.jsonObject(with: data)) ?? emails
    }

    private static func readRecentEmails(limit: Int, folder: String) async throws -> [[String: String]] {
        let dbPath = (NSHomeDirectory() as NSString).appendingPathComponent("Library/Mail/V10/MailData/Envelope Index")
        let encodedFolder = folder
            .replacingOccurrences(of: "[", with: "%5B")
            .replacingOccurrences(of: "]", with: "%5D")
            .replacingOccurrences(of: " ", with: "%20")
        let sql = """
            SELECT
                datetime(messages.date_received + 978307200, 'unixepoch') as date,
                COALESCE(addresses.address, '') as sender,
                COALESCE(subjects.subject, '(no subject)') as subject,
                summaries.summary as preview
            FROM messages
            LEFT JOIN addresses ON messages.sender = addresses.ROWID
            LEFT JOIN subjects ON messages.subject = subjects.ROWID
            LEFT JOIN summaries ON messages.summary = summaries.ROWID
            LEFT JOIN mailboxes ON messages.mailbox = mailboxes.ROWID
            WHERE messages.deleted = 0
                AND (
                    mailboxes.url LIKE '%imap%/\(encodedFolder)' OR
                    mailboxes.url LIKE '%/\(encodedFolder)'
                )
                AND messages.date_received IS NOT NULL
            ORDER BY messages.date_received DESC
            LIMIT \(limit)
            """
        var results: [[String: String]] = []
        var db: OpaquePointer?
        let openResult = sqlite3_open_v2(dbPath, &db, SQLITE_OPEN_READONLY, nil)
        guard openResult == SQLITE_OK, let database = db else {
            throw CLIError("Failed to open Mail database")
        }
        defer { sqlite3_close(database) }
        var statement: OpaquePointer?
        guard sqlite3_prepare_v2(database, sql, -1, &statement, nil) == SQLITE_OK, let stmt = statement else {
            throw CLIError("Failed to prepare statement")
        }
        defer { sqlite3_finalize(stmt) }
        while sqlite3_step(stmt) == SQLITE_ROW {
            var rowDict: [String: String] = [:]
            let columnCount = sqlite3_column_count(stmt)
            for col in 0..<columnCount {
                let columnName = String(cString: sqlite3_column_name(stmt, col))
                if let text = sqlite3_column_text(stmt, col) {
                    rowDict[columnName] = String(cString: text)
                } else if sqlite3_column_type(stmt, col) == SQLITE_INTEGER {
                    rowDict[columnName] = String(sqlite3_column_int64(stmt, col))
                }
            }
            results.append(rowDict)
        }
        return results
    }

    static func searchEmails(payload: [String: Any]) async throws -> Any {
        guard let query = payload.string("query"), !query.isEmpty else {
            throw CLIError("Missing required field: query")
        }
        let folder = payload.string("folder") ?? ""
        let limit = payload.int("limit") ?? 50
        let dbPath = (NSHomeDirectory() as NSString).appendingPathComponent("Library/Mail/V10/MailData/Envelope Index")
        let escapedQuery = query.replacingOccurrences(of: "'", with: "''")
        let folderFilter: String
        if folder.isEmpty {
            folderFilter = ""
        } else {
            let encodedFolder = folder
                .replacingOccurrences(of: "[", with: "%5B")
                .replacingOccurrences(of: "]", with: "%5D")
                .replacingOccurrences(of: " ", with: "%20")
            folderFilter = """
                AND (
                    mailboxes.url LIKE '%imap%/\(encodedFolder)' OR
                    mailboxes.url LIKE '%/\(encodedFolder)'
                )
                """
        }
        let sql = """
            SELECT
                datetime(messages.date_received + 978307200, 'unixepoch') as date,
                COALESCE(addresses.address, '') as sender,
                COALESCE(subjects.subject, '(no subject)') as subject,
                COALESCE(summaries.summary, '') as preview
            FROM messages
            LEFT JOIN addresses ON messages.sender = addresses.ROWID
            LEFT JOIN subjects ON messages.subject = subjects.ROWID
            LEFT JOIN summaries ON messages.summary = summaries.ROWID
            LEFT JOIN mailboxes ON messages.mailbox = mailboxes.ROWID
            WHERE messages.deleted = 0
                AND messages.date_received IS NOT NULL
                \(folderFilter)
                AND (
                    COALESCE(subjects.subject, '') LIKE '%\(escapedQuery)%' OR
                    COALESCE(summaries.summary, '') LIKE '%\(escapedQuery)%' OR
                    COALESCE(addresses.address, '') LIKE '%\(escapedQuery)%'
                )
            ORDER BY messages.date_received DESC
            LIMIT \(limit)
            """
        var results: [[String: String]] = []
        var db: OpaquePointer?
        guard sqlite3_open_v2(dbPath, &db, SQLITE_OPEN_READONLY, nil) == SQLITE_OK, let database = db else {
            throw CLIError("Failed to open Mail database")
        }
        defer { sqlite3_close(database) }
        var statement: OpaquePointer?
        guard sqlite3_prepare_v2(database, sql, -1, &statement, nil) == SQLITE_OK, let stmt = statement else {
            throw CLIError("Failed to prepare statement")
        }
        defer { sqlite3_finalize(stmt) }
        while sqlite3_step(stmt) == SQLITE_ROW {
            var rowDict: [String: String] = [:]
            let columnCount = sqlite3_column_count(stmt)
            for col in 0..<columnCount {
                let columnName = String(cString: sqlite3_column_name(stmt, col))
                if let text = sqlite3_column_text(stmt, col) {
                    rowDict[columnName] = String(cString: text)
                }
            }
            results.append(rowDict)
        }
        if results.isEmpty { return "No emails found matching '\(query)'." }
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        let data = try encoder.encode(results)
        return (try? JSONSerialization.jsonObject(with: data)) ?? results
    }

    static func composeMail(payload: [String: Any]) async throws -> Any {
        guard let to = payload.string("to") else {
            throw CLIError("Missing required field: to")
        }
        let subject = payload.string("subject") ?? ""
        let body = payload.string("body") ?? ""

        let escapedTo = to.replacingOccurrences(of: "\"", with: "\\\"")
        let escapedSubject = subject.replacingOccurrences(of: "\"", with: "\\\"")
        let escapedBody = body.replacingOccurrences(of: "\\", with: "\\\\")
                              .replacingOccurrences(of: "\"", with: "\\\"")

        let script = """
        tell application "Mail"
            activate
            set newMsg to make new outgoing message with properties {subject:"\(escapedSubject)", content:"\(escapedBody)", visible:true}
            tell newMsg
                make new to recipient with properties {address:"\(escapedTo)"}
            end tell
        end tell
        """

        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/usr/bin/osascript")
        process.arguments = ["-e", script]
        let errorPipe = Pipe()
        process.standardError = errorPipe
        try process.run()
        process.waitUntilExit()
        guard process.terminationStatus == 0 else {
            let msg = String(data: errorPipe.fileHandleForReading.readDataToEndOfFile(), encoding: .utf8) ?? "Unknown error"
            throw CLIError(msg)
        }
        return ["status": "composed", "to": to, "subject": subject]
    }

    static func listMailboxes(payload: [String: Any]) async throws -> Any {
        let dbPath = (NSHomeDirectory() as NSString).appendingPathComponent("Library/Mail/V10/MailData/Envelope Index")
        let sql = """
            SELECT url as name, CAST(unread_count AS TEXT) as unread, CAST(total_count AS TEXT) as total
            FROM mailboxes ORDER BY url
            """
        let results: [[String: String]]
        do {
            results = try SQLiteHelper.queryWithParams(databasePath: dbPath, sql: sql, parameters: [])
        } catch let e as SQLiteError { throw e.asCLIError(database: "Mail") }
        if results.isEmpty { return "No mailboxes found." }
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        let data = try encoder.encode(results)
        return (try? JSONSerialization.jsonObject(with: data)) ?? results
    }
}
