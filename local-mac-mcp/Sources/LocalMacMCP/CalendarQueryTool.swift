import Foundation
import SQLite3

enum CalendarQueryTool {

    struct CalendarEvent: Codable {
        let date: String
        let eventType: String
        let label: String
        let noiseLevel: String
        let noiseAssets: [String]
        let notes: String?
        let referenceMonth: String?
        let confirmed: Bool

        enum CodingKeys: String, CodingKey {
            case date, label, notes
            case eventType = "event_type"
            case noiseLevel = "noise_level"
            case noiseAssets = "noise_assets"
            case referenceMonth = "reference_month"
            case confirmed
        }
    }

    static func getEventsByDate(payload: [String: Any]) async throws -> Any {
        guard let dateStr = payload.string("date") else {
            throw CLIError("Missing required argument: date (YYYY-MM-DD)")
        }
        let events = try queryEventsByDate(dateStr)
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        let data = try encoder.encode(events)
        return (try? JSONSerialization.jsonObject(with: data)) ?? events
    }

    static func getUpcomingEvents(payload: [String: Any]) async throws -> Any {
        let daysAhead = payload.int("days_ahead") ?? 7
        let fromDateStr = payload.string("from_date") ?? ""
        let events = try queryUpcomingEvents(daysAhead: daysAhead, fromDate: fromDateStr)
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        let data = try encoder.encode(events)
        return (try? JSONSerialization.jsonObject(with: data)) ?? events
    }

    static func getNoiseSummary(payload: [String: Any]) async throws -> Any {
        guard let dateStr = payload.string("date") else {
            throw CLIError("Missing required argument: date (YYYY-MM-DD)")
        }
        let events = try queryEventsByDate(dateStr)
        let assets = ["gold", "crude", "nifty", "usdinr", "dxy"]
        var noiseScores: [String: String] = [:]
        for asset in assets {
            var maxLevel = "low"
            for event in events {
                if event.noiseAssets.contains(asset) {
                    if event.noiseLevel == "high" { maxLevel = "high" }
                    else if event.noiseLevel == "medium" && maxLevel != "high" { maxLevel = "medium" }
                }
            }
            noiseScores[asset] = maxLevel
        }
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        let eventsData = try encoder.encode(events)
        let eventsJSON = (try? JSONSerialization.jsonObject(with: eventsData)) ?? []
        let summary: [String: Any] = [
            "date": dateStr,
            "events_count": events.count,
            "high_noise_events": events.filter { $0.noiseLevel == "high" }.count,
            "noise_assets": noiseScores,
            "events": eventsJSON
        ]
        return summary
    }

    private static func getDatabasePath() -> String {
        NSHomeDirectory() + "/Documents/claude_cache_data/market-intel/market.sqlite"
    }

    private static func queryEventsByDate(_ dateStr: String) throws -> [CalendarEvent] {
        let dbPath = getDatabasePath()
        guard FileManager.default.fileExists(atPath: dbPath) else {
            throw CLIError("Database not found at \(dbPath)")
        }
        var db: OpaquePointer?
        guard sqlite3_open_v2(dbPath, &db, SQLITE_OPEN_READONLY, nil) == SQLITE_OK, let database = db else {
            throw CLIError("Failed to open database")
        }
        defer { sqlite3_close(database) }

        let sql = """
        SELECT date, event_type, label, noise_level, noise_assets, notes, reference_month, confirmed
        FROM calendar
        WHERE date = '\(dateStr.replacingOccurrences(of: "'", with: "''"))'
        ORDER BY CASE noise_level WHEN 'high' THEN 0 WHEN 'medium' THEN 1 ELSE 2 END
        """
        var stmt: OpaquePointer?
        guard sqlite3_prepare_v2(database, sql, -1, &stmt, nil) == SQLITE_OK, let statement = stmt else {
            throw CLIError("Failed to prepare statement")
        }
        defer { sqlite3_finalize(statement) }
        return readEvents(from: statement)
    }

    private static func queryUpcomingEvents(daysAhead: Int, fromDate: String) throws -> [CalendarEvent] {
        let dbPath = getDatabasePath()
        guard FileManager.default.fileExists(atPath: dbPath) else {
            throw CLIError("Database not found at \(dbPath)")
        }

        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withFullDate, .withDashSeparatorInDate]
        let startDate: Date = (!fromDate.isEmpty ? formatter.date(from: fromDate) : nil) ?? Date()
        let endDate = Calendar.current.date(byAdding: .day, value: daysAhead, to: startDate) ?? startDate
        let startStr = formatter.string(from: startDate)
        let endStr = formatter.string(from: endDate)

        var db: OpaquePointer?
        guard sqlite3_open_v2(dbPath, &db, SQLITE_OPEN_READONLY, nil) == SQLITE_OK, let database = db else {
            throw CLIError("Failed to open database")
        }
        defer { sqlite3_close(database) }

        let sql = """
        SELECT date, event_type, label, noise_level, noise_assets, notes, reference_month, confirmed
        FROM calendar
        WHERE date >= '\(startStr.replacingOccurrences(of: "'", with: "''"))'
          AND date <= '\(endStr.replacingOccurrences(of: "'", with: "''"))'
        ORDER BY date ASC, CASE noise_level WHEN 'high' THEN 0 WHEN 'medium' THEN 1 ELSE 2 END
        """
        var stmt: OpaquePointer?
        guard sqlite3_prepare_v2(database, sql, -1, &stmt, nil) == SQLITE_OK, let statement = stmt else {
            throw CLIError("Failed to prepare statement")
        }
        defer { sqlite3_finalize(statement) }
        return readEvents(from: statement)
    }

    private static func readEvents(from statement: OpaquePointer) -> [CalendarEvent] {
        var events: [CalendarEvent] = []
        while sqlite3_step(statement) == SQLITE_ROW {
            let date = String(cString: sqlite3_column_text(statement, 0))
            let eventType = String(cString: sqlite3_column_text(statement, 1))
            let label = String(cString: sqlite3_column_text(statement, 2))
            let noiseLevel = String(cString: sqlite3_column_text(statement, 3))
            let noiseAssetsStr = sqlite3_column_text(statement, 4).map { String(cString: $0) } ?? "[]"
            let noiseAssets = (try? JSONSerialization.jsonObject(with: noiseAssetsStr.data(using: .utf8)!)) as? [String] ?? []
            let notes = sqlite3_column_text(statement, 5).map { String(cString: $0) }
            let referenceMonth = sqlite3_column_text(statement, 6).map { String(cString: $0) }
            let confirmed = sqlite3_column_int(statement, 7) != 0
            events.append(CalendarEvent(date: date, eventType: eventType, label: label, noiseLevel: noiseLevel,
                                        noiseAssets: noiseAssets, notes: notes, referenceMonth: referenceMonth, confirmed: confirmed))
        }
        return events
    }
}
