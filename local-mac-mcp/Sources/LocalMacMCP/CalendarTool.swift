import EventKit
import Foundation

enum CalendarTool {

    private static let store = EKEventStore()

    static func addEvent(payload: [String: Any]) async throws -> Any {
        guard let title = payload.string("title"), !title.isEmpty else {
            throw CLIError("Missing required argument: title")
        }
        guard let startStr = payload.string("start_date") else {
            throw CLIError("Missing required argument: start_date (ISO-8601)")
        }
        let calendarName = payload.string("calendar") ?? "Work"
        let endStr = payload.string("end_date")
        let notes = payload.string("notes")

        guard let startDate = parseISO8601(startStr) else {
            throw CLIError("Invalid start_date format. Use ISO-8601, e.g. 2026-04-10T09:00:00Z")
        }
        let endDate: Date
        if let endStr = endStr, let parsed = parseISO8601(endStr) {
            endDate = parsed
        } else {
            endDate = startDate.addingTimeInterval(3600)
        }

        let granted: Bool = try await withCheckedThrowingContinuation { continuation in
            store.requestAccess(to: .event) { granted, error in
                if let error { continuation.resume(throwing: error) }
                else { continuation.resume(returning: granted) }
            }
        }
        guard granted else {
            throw CLIError("Calendar access denied. Grant access in System Settings > Privacy & Security > Calendars.")
        }

        let calendars = store.calendars(for: .event)
        guard let targetCalendar = calendars.first(where: { $0.title == calendarName }) else {
            let available = calendars.map { $0.title }.joined(separator: ", ")
            throw CLIError("Calendar '\(calendarName)' not found. Available: \(available)")
        }

        let event = EKEvent(eventStore: store)
        event.title = title
        event.startDate = startDate
        event.endDate = endDate
        event.notes = notes
        event.calendar = targetCalendar

        try store.save(event, span: .thisEvent)
        let iso = ISO8601DateFormatter()
        return "Added '\(title)' to \(calendarName) on \(iso.string(from: startDate))"
    }

    static func deleteEvent(payload: [String: Any]) async throws -> Any {
        guard let titlePattern = payload.string("title"), !titlePattern.isEmpty else {
            throw CLIError("Missing required argument: title")
        }
        let calendarName = payload.string("calendar") ?? "Work"

        let granted: Bool = try await withCheckedThrowingContinuation { continuation in
            store.requestAccess(to: .event) { granted, error in
                if let error { continuation.resume(throwing: error) }
                else { continuation.resume(returning: granted) }
            }
        }
        guard granted else {
            throw CLIError("Calendar access denied. Grant access in System Settings > Privacy & Security > Calendars.")
        }

        let calendars = store.calendars(for: .event)
        guard let targetCalendar = calendars.first(where: { $0.title == calendarName }) else {
            throw CLIError("Calendar '\(calendarName)' not found.")
        }

        let now = Date()
        let predicate = store.predicateForEvents(
            withStart: now.addingTimeInterval(-30 * 24 * 3600),
            end: now.addingTimeInterval(30 * 24 * 3600),
            calendars: [targetCalendar]
        )
        let events = store.events(matching: predicate)
        let matching = events.filter { ($0.title ?? "").localizedCaseInsensitiveContains(titlePattern) }

        guard !matching.isEmpty else {
            throw CLIError("No events found matching '\(titlePattern)' in \(calendarName).")
        }
        guard matching.count == 1 else {
            let titles = matching.map { $0.title ?? "(no title)" }.joined(separator: ", ")
            throw CLIError("Multiple events match '\(titlePattern)': \(titles). Please be more specific.")
        }

        let eventToDelete = matching[0]
        try store.remove(eventToDelete, span: .thisEvent)
        return "Deleted '\(eventToDelete.title ?? "(no title)")' from \(calendarName)."
    }

    static func listEvents(payload: [String: Any]) async throws -> Any {
        guard let startStr = payload.string("start_date"), let endStr = payload.string("end_date") else {
            throw CLIError("Missing required arguments: start_date, end_date")
        }

        guard let start = parseISO8601(startStr), let end = parseISO8601(endStr) else {
            throw CLIError("Invalid date format. Use ISO-8601, e.g. 2026-04-10T00:00:00Z")
        }

        let localStore = EKEventStore()
        let granted: Bool = try await withCheckedThrowingContinuation { continuation in
            localStore.requestAccess(to: .event) { granted, error in
                if let error { continuation.resume(throwing: error) }
                else { continuation.resume(returning: granted) }
            }
        }
        guard granted else {
            throw CLIError("Calendar access denied. Grant access in System Settings > Privacy & Security > Calendars.")
        }

        let calendars = localStore.calendars(for: .event)
        let predicate = localStore.predicateForEvents(withStart: start, end: end, calendars: calendars)
        let events = localStore.events(matching: predicate)

        if events.isEmpty { return "No events found between \(startStr) and \(endStr)." }

        struct EventEntry: Encodable {
            let calendar: String
            let title: String
            let start: String
            let end: String
            let location: String?
            let notes: String?
            let isAllDay: Bool
        }

        let iso = ISO8601DateFormatter()
        let entries = events.map { e in
            EventEntry(
                calendar: e.calendar.title,
                title: e.title ?? "(no title)",
                start: iso.string(from: e.startDate),
                end: iso.string(from: e.endDate),
                location: e.location,
                notes: e.notes,
                isAllDay: e.isAllDay
            )
        }

        let encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        let data = try encoder.encode(entries)
        return (try? JSONSerialization.jsonObject(with: data)) ?? entries
    }

    private static func parseISO8601(_ s: String) -> Date? {
        let f1 = ISO8601DateFormatter()
        f1.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        if let d = f1.date(from: s) { return d }
        let f2 = ISO8601DateFormatter()
        return f2.date(from: s)
    }
}
