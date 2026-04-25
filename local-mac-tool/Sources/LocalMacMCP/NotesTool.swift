import Foundation
import SQLite3

enum NotesTool {

    private static func getDatabasePath() -> String {
        NSHomeDirectory() + "/Library/Group Containers/group.com.apple.notes/NoteStore.sqlite"
    }

    static func listNotes(payload: [String: Any]) async throws -> Any {
        let folder = payload.string("folder") ?? ""
        let limit = payload.int("limit") ?? 20

        let dbPath = getDatabasePath()
        guard FileManager.default.fileExists(atPath: dbPath) else {
            throw CLIError("Notes database not found at \(dbPath).")
        }

        var db: OpaquePointer?
        guard sqlite3_open_v2(dbPath, &db, SQLITE_OPEN_READONLY, nil) == SQLITE_OK, let database = db else {
            throw CLIError("Failed to open Notes database.")
        }
        defer { sqlite3_close(database) }

        let folderCondition = folder.isEmpty ? "" : "AND f.ZTITLE2 LIKE '\(folder.replacingOccurrences(of: "'", with: "''"))%'"
        let sql = """
        SELECT n.Z_PK, n.ZTITLE3, f.ZTITLE2,
               datetime(n.ZCREATIONDATE + 978307200, 'unixepoch'),
               datetime(n.ZMODIFICATIONDATE + 978307200, 'unixepoch'),
               n.ZSNIPPET, n.ZISPINNED, n.ZIDENTIFIER
        FROM ZICCLOUDSYNCINGOBJECT n
        LEFT JOIN ZICCLOUDSYNCINGOBJECT f ON n.ZFOLDER = f.Z_PK
        WHERE n.Z_ENT = 12 AND n.ZMARKEDFORDELETION IS NOT 1 \(folderCondition)
        ORDER BY n.ZMODIFICATIONDATE DESC
        LIMIT \(limit)
        """

        var stmt: OpaquePointer?
        guard sqlite3_prepare_v2(database, sql, -1, &stmt, nil) == SQLITE_OK, let statement = stmt else {
            throw CLIError("Failed to prepare query.")
        }
        defer { sqlite3_finalize(statement) }

        struct NoteEntry: Encodable {
            let id: Int64; let title: String; let folder: String?
            let created: String; let modified: String
            let snippet: String; let pinned: Bool; let identifier: String
        }

        var notes: [NoteEntry] = []
        while sqlite3_step(statement) == SQLITE_ROW {
            notes.append(NoteEntry(
                id: sqlite3_column_int64(statement, 0),
                title: String(cString: sqlite3_column_text(statement, 1)),
                folder: sqlite3_column_text(statement, 2).map { String(cString: $0) },
                created: String(cString: sqlite3_column_text(statement, 3)),
                modified: String(cString: sqlite3_column_text(statement, 4)),
                snippet: String(cString: sqlite3_column_text(statement, 5)),
                pinned: sqlite3_column_int(statement, 6) != 0,
                identifier: String(cString: sqlite3_column_text(statement, 7))
            ))
        }

        let encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        let data = try encoder.encode(notes)
        return (try? JSONSerialization.jsonObject(with: data)) ?? notes
    }

    static func readNote(payload: [String: Any]) async throws -> Any {
        guard let noteId = payload.string("id"), !noteId.isEmpty else {
            throw CLIError("Missing required argument: id")
        }

        let dbPath = getDatabasePath()
        guard FileManager.default.fileExists(atPath: dbPath) else {
            throw CLIError("Notes database not found.")
        }

        var db: OpaquePointer?
        guard sqlite3_open_v2(dbPath, &db, SQLITE_OPEN_READONLY, nil) == SQLITE_OK, let database = db else {
            throw CLIError("Failed to open Notes database.")
        }
        defer { sqlite3_close(database) }

        let escapedId = noteId.replacingOccurrences(of: "'", with: "''")
        let sql = """
        SELECT n.ZTITLE3, f.ZTITLE2,
               datetime(n.ZCREATIONDATE + 978307200, 'unixepoch'),
               datetime(n.ZMODIFICATIONDATE + 978307200, 'unixepoch'),
               n.ZSNIPPET
        FROM ZICCLOUDSYNCINGOBJECT n
        LEFT JOIN ZICCLOUDSYNCINGOBJECT f ON n.ZFOLDER = f.Z_PK
        WHERE n.Z_ENT = 12 AND n.ZIDENTIFIER = '\(escapedId)' AND n.ZMARKEDFORDELETION IS NOT 1
        LIMIT 1
        """

        var stmt: OpaquePointer?
        guard sqlite3_prepare_v2(database, sql, -1, &stmt, nil) == SQLITE_OK, let statement = stmt else {
            throw CLIError("Failed to prepare query.")
        }
        defer { sqlite3_finalize(statement) }

        guard sqlite3_step(statement) == SQLITE_ROW else {
            throw CLIError("Note not found with identifier: \(noteId)")
        }

        let title = String(cString: sqlite3_column_text(statement, 0))
        let folder = sqlite3_column_text(statement, 1).map { String(cString: $0) }
        let created = String(cString: sqlite3_column_text(statement, 2))
        let modified = String(cString: sqlite3_column_text(statement, 3))
        let snippet = String(cString: sqlite3_column_text(statement, 4))

        let bodyScript = """
        tell application "Notes"
            try
                set theNote to first note whose id is "x-coredata://\(noteId)"
                return plaintext of theNote
            on error
                return "[Note body unavailable]"
            end try
        end tell
        """
        var appleScriptError: NSDictionary?
        let script = NSAppleScript(source: bodyScript)
        let result = script?.executeAndReturnError(&appleScriptError)
        let body = result?.stringValue ?? "[Note body unavailable]"

        struct NoteDetail: Encodable {
            let id: String; let title: String; let folder: String?
            let created: String; let modified: String; let snippet: String; let body: String
        }

        let note = NoteDetail(id: noteId, title: title, folder: folder, created: created,
                               modified: modified, snippet: snippet, body: body)
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        let data = try encoder.encode(note)
        return (try? JSONSerialization.jsonObject(with: data)) ?? note
    }

    static func addNote(payload: [String: Any]) async throws -> Any {
        guard let title = payload.string("title"), !title.isEmpty else {
            throw CLIError("Missing required argument: title")
        }
        let body = payload.string("body") ?? ""
        let folder = payload.string("folder") ?? "Claude"

        let escapedTitle = title.replacingOccurrences(of: "\"", with: "\\\"")
        let escapedBody = body.replacingOccurrences(of: "\"", with: "\\\"")
        let escapedFolder = folder.replacingOccurrences(of: "\"", with: "\\\"")

        let script = """
        tell application "Notes"
            tell folder "\(escapedFolder)"
                make new note with properties {name:"\(escapedTitle)", body:"\(escapedBody)"}
            end tell
        end tell
        """
        var error: NSDictionary?
        NSAppleScript(source: script)?.executeAndReturnError(&error)
        if let err = error { throw CLIError("AppleScript error: \(err["NSAppleScriptErrorMessage"] ?? "unknown")") }
        return "Created note '\(title)' in folder '\(folder)'"
    }

    static func deleteNote(payload: [String: Any]) async throws -> Any {
        guard let title = payload.string("title"), !title.isEmpty else {
            throw CLIError("Missing required argument: title")
        }
        let folder = payload.string("folder") ?? "Claude"

        let escapedTitle = title.replacingOccurrences(of: "\"", with: "\\\"")
        let escapedFolder = folder.replacingOccurrences(of: "\"", with: "\\\"")

        let script = """
        tell application "Notes"
            tell folder "\(escapedFolder)"
                set matchNote to first note whose name is "\(escapedTitle)"
                delete matchNote
            end tell
        end tell
        """
        var error: NSDictionary?
        NSAppleScript(source: script)?.executeAndReturnError(&error)
        if let err = error { throw CLIError("AppleScript error: \(err["NSAppleScriptErrorMessage"] ?? "unknown")") }
        return "Deleted note '\(title)' from folder '\(folder)'"
    }

    static func listFolders(payload: [String: Any]) async throws -> Any {
        let dbPath = getDatabasePath()
        guard FileManager.default.fileExists(atPath: dbPath) else {
            throw CLIError("Notes database not found.")
        }

        var db: OpaquePointer?
        guard sqlite3_open_v2(dbPath, &db, SQLITE_OPEN_READONLY, nil) == SQLITE_OK, let database = db else {
            throw CLIError("Failed to open Notes database.")
        }
        defer { sqlite3_close(database) }

        let sql = """
        SELECT f.Z_PK, f.ZTITLE2, COUNT(n.Z_PK)
        FROM ZICCLOUDSYNCINGOBJECT f
        LEFT JOIN ZICCLOUDSYNCINGOBJECT n ON n.ZFOLDER = f.Z_PK
            AND n.Z_ENT = 12 AND n.ZMARKEDFORDELETION IS NOT 1
        WHERE f.Z_ENT = 15 AND f.ZMARKEDFORDELETION IS NOT 1
        GROUP BY f.Z_PK ORDER BY f.ZTITLE2 ASC
        """

        var stmt: OpaquePointer?
        guard sqlite3_prepare_v2(database, sql, -1, &stmt, nil) == SQLITE_OK, let statement = stmt else {
            throw CLIError("Failed to prepare query.")
        }
        defer { sqlite3_finalize(statement) }

        struct FolderEntry: Encodable { let id: Int64; let name: String; let noteCount: Int64 }
        var folders: [FolderEntry] = []
        while sqlite3_step(statement) == SQLITE_ROW {
            folders.append(FolderEntry(
                id: sqlite3_column_int64(statement, 0),
                name: String(cString: sqlite3_column_text(statement, 1)),
                noteCount: sqlite3_column_int64(statement, 2)
            ))
        }

        let encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        let data = try encoder.encode(folders)
        return (try? JSONSerialization.jsonObject(with: data)) ?? folders
    }
}
