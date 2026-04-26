import Foundation

enum NotesTool {

    private static func getDatabasePath() -> String {
        NSHomeDirectory() + "/Library/Group Containers/group.com.apple.notes/NoteStore.sqlite"
    }

    static func listNotes(payload: [String: Any]) async throws -> Any {
        let folder = payload.string("folder") ?? ""
        let limit = payload.int("limit") ?? 20

        let dbPath = getDatabasePath()

        let folderCondition = folder.isEmpty ? "" : "AND f.ZTITLE2 LIKE ?"
        let sql = """
        SELECT n.Z_PK, n.ZTITLE1, f.ZTITLE2,
               datetime(n.ZCREATIONDATE + 978307200, 'unixepoch'),
               datetime(n.ZMODIFICATIONDATE + 978307200, 'unixepoch'),
               n.ZSNIPPET, n.ZISPINNED, n.ZIDENTIFIER
        FROM ZICCLOUDSYNCINGOBJECT n
        LEFT JOIN ZICCLOUDSYNCINGOBJECT f ON n.ZFOLDER = f.Z_PK
        WHERE n.Z_ENT = 12 AND n.ZMARKEDFORDELETION IS NOT 1 \(folderCondition)
        ORDER BY n.ZMODIFICATIONDATE DESC
        LIMIT \(limit)
        """
        let params: [Any] = folder.isEmpty ? [] : ["\(folder)%"]
        let rows: [[String: String]]
        do {
            rows = try SQLiteHelper.queryWithParams(databasePath: dbPath, sql: sql, parameters: params)
        } catch let e as SQLiteError { throw e.asCLIError(database: "Notes") }

        struct NoteEntry: Encodable {
            let id: String; let title: String; let folder: String?
            let created: String; let modified: String
            let snippet: String; let pinned: Bool; let identifier: String
        }

        let notes = rows.map { row in
            NoteEntry(
                id: row["Z_PK"] ?? "",
                title: row["ZTITLE1"] ?? "",
                folder: row["ZTITLE2"],
                created: row["datetime(n.ZCREATIONDATE + 978307200, 'unixepoch')"] ?? "",
                modified: row["datetime(n.ZMODIFICATIONDATE + 978307200, 'unixepoch')"] ?? "",
                snippet: row["ZSNIPPET"] ?? "",
                pinned: row["ZISPINNED"] == "1",
                identifier: row["ZIDENTIFIER"] ?? ""
            )
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

        let sql = """
        SELECT n.ZTITLE1, f.ZTITLE2,
               datetime(n.ZCREATIONDATE + 978307200, 'unixepoch'),
               datetime(n.ZMODIFICATIONDATE + 978307200, 'unixepoch'),
               n.ZSNIPPET
        FROM ZICCLOUDSYNCINGOBJECT n
        LEFT JOIN ZICCLOUDSYNCINGOBJECT f ON n.ZFOLDER = f.Z_PK
        WHERE n.Z_ENT = 12 AND n.ZIDENTIFIER = ? AND n.ZMARKEDFORDELETION IS NOT 1
        LIMIT 1
        """
        let rows: [[String: String]]
        do {
            rows = try SQLiteHelper.queryWithParams(databasePath: dbPath, sql: sql, parameters: [noteId])
        } catch let e as SQLiteError { throw e.asCLIError(database: "Notes") }

        guard let row = rows.first else {
            throw CLIError("Note not found with identifier: \(noteId)")
        }

        let title = row["ZTITLE1"] ?? ""
        let folder = row["ZTITLE2"]
        let created = row["datetime(n.ZCREATIONDATE + 978307200, 'unixepoch')"] ?? ""
        let modified = row["datetime(n.ZMODIFICATIONDATE + 978307200, 'unixepoch')"] ?? ""
        let snippet = row["ZSNIPPET"] ?? ""

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

        let sql = """
        SELECT f.Z_PK, f.ZTITLE2, COUNT(n.Z_PK)
        FROM ZICCLOUDSYNCINGOBJECT f
        LEFT JOIN ZICCLOUDSYNCINGOBJECT n ON n.ZFOLDER = f.Z_PK
            AND n.Z_ENT = 12 AND n.ZMARKEDFORDELETION IS NOT 1
        WHERE f.Z_ENT = 15 AND f.ZMARKEDFORDELETION IS NOT 1
        GROUP BY f.Z_PK ORDER BY f.ZTITLE2 ASC
        """
        let rows: [[String: String]]
        do {
            rows = try SQLiteHelper.queryWithParams(databasePath: dbPath, sql: sql, parameters: [])
        } catch let e as SQLiteError { throw e.asCLIError(database: "Notes") }

        struct FolderEntry: Encodable { let id: String; let name: String; let noteCount: String }
        let folders = rows.map { row in
            FolderEntry(
                id: row["Z_PK"] ?? "",
                name: row["ZTITLE2"] ?? "",
                noteCount: row["COUNT(n.Z_PK)"] ?? "0"
            )
        }

        let encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        let data = try encoder.encode(folders)
        return (try? JSONSerialization.jsonObject(with: data)) ?? folders
    }
}
