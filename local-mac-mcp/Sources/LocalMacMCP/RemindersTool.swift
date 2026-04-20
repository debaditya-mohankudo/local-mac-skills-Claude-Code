import EventKit
import Foundation

enum RemindersTool {

    static func list(payload: [String: Any]) async throws -> Any {
        let store = EKEventStore()
        guard try await requestRemindersAccess(store) else {
            throw CLIError("Reminders access denied. Grant access in System Settings > Privacy & Security > Reminders.")
        }

        let listName = payload.string("list")
        let includeCompleted = payload.bool("include_completed") ?? false

        let calendars = store.calendars(for: .reminder).filter {
            listName == nil || $0.title.lowercased() == listName!.lowercased()
        }
        if calendars.isEmpty {
            throw CLIError("No reminder list found\(listName.map { ": \($0)" } ?? "")")
        }

        let predicate = includeCompleted
            ? store.predicateForReminders(in: calendars)
            : store.predicateForIncompleteReminders(withDueDateStarting: nil, ending: nil, calendars: calendars)

        let reminders: [EKReminder] = try await withCheckedThrowingContinuation { continuation in
            store.fetchReminders(matching: predicate) { results in
                continuation.resume(returning: results ?? [])
            }
        }

        struct ReminderEntry: Encodable {
            let id: String
            let title: String
            let list: String
            let completed: Bool
            let dueDate: String?
            let notes: String?
            let priority: Int
        }

        let iso = ISO8601DateFormatter()
        let entries = reminders.map { r in
            ReminderEntry(
                id: r.calendarItemIdentifier,
                title: r.title ?? "(no title)",
                list: r.calendar.title,
                completed: r.isCompleted,
                dueDate: r.dueDateComponents.flatMap { Calendar.current.date(from: $0) }.map { iso.string(from: $0) },
                notes: r.notes,
                priority: r.priority
            )
        }.sorted { !$0.completed && $1.completed }

        if entries.isEmpty { return "No reminders found." }

        let encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        let data = try encoder.encode(entries)
        return (try? JSONSerialization.jsonObject(with: data)) ?? entries
    }

    static func create(payload: [String: Any]) async throws -> Any {
        guard let title = payload.string("title"), !title.isEmpty else {
            throw CLIError("Missing required argument: title")
        }

        let store = EKEventStore()
        guard try await requestRemindersAccess(store) else {
            throw CLIError("Reminders access denied.")
        }

        let listName = payload.string("list")
        let dueDateStr = payload.string("due_date")
        let notes = payload.string("notes")

        let calendars = store.calendars(for: .reminder)
        let targetCalendar: EKCalendar
        if let name = listName, let match = calendars.first(where: { $0.title.lowercased() == name.lowercased() }) {
            targetCalendar = match
        } else {
            guard let def = store.defaultCalendarForNewReminders() else {
                throw CLIError("No default reminders list found.")
            }
            targetCalendar = def
        }

        let reminder = EKReminder(eventStore: store)
        reminder.title = title
        reminder.calendar = targetCalendar
        reminder.notes = notes

        if let ds = dueDateStr {
            guard let date = ISO8601DateFormatter().date(from: ds) else {
                throw CLIError("Invalid due_date format. Use ISO-8601, e.g. 2026-04-11T09:00:00Z")
            }
            reminder.dueDateComponents = Calendar.current.dateComponents([.year, .month, .day, .hour, .minute], from: date)
        }

        try store.save(reminder, commit: true)
        return "Created reminder '\(title)' in '\(targetCalendar.title)'"
    }

    static func complete(payload: [String: Any]) async throws -> Any {
        guard let id = payload.string("id"), !id.isEmpty else {
            throw CLIError("Missing required argument: id")
        }

        let store = EKEventStore()
        guard try await requestRemindersAccess(store) else {
            throw CLIError("Reminders access denied.")
        }
        guard let reminder = store.calendarItem(withIdentifier: id) as? EKReminder else {
            throw CLIError("Reminder not found: \(id)")
        }

        reminder.isCompleted = true
        try store.save(reminder, commit: true)
        return "Completed: '\(reminder.title ?? id)'"
    }

    static func delete(payload: [String: Any]) async throws -> Any {
        guard let id = payload.string("id"), !id.isEmpty else {
            throw CLIError("Missing required argument: id")
        }
        let store = EKEventStore()
        guard try await requestRemindersAccess(store) else {
            throw CLIError("Reminders access denied.")
        }
        guard let reminder = store.calendarItem(withIdentifier: id) as? EKReminder else {
            throw CLIError("Reminder not found: \(id)")
        }
        let title = reminder.title ?? id
        try store.remove(reminder, commit: true)
        return "Deleted reminder '\(title)'"
    }

    private static func requestRemindersAccess(_ store: EKEventStore) async throws -> Bool {
        try await withCheckedThrowingContinuation { continuation in
            store.requestAccess(to: .reminder) { granted, error in
                if let error { continuation.resume(throwing: error) }
                else { continuation.resume(returning: granted) }
            }
        }
    }
}
