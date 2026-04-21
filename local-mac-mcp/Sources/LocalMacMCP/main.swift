import Foundation

// CLI dispatcher — reads command from argv[1], JSON payload from stdin, writes JSON to stdout.
// Usage: local-mac-tool <command>
// Stdin:  JSON object with named arguments
// Stdout: {"status":"ok","data":<result>}  or {"status":"error","message":"..."}

let args = CommandLine.arguments
guard args.count > 1 else {
    fputs("Usage: local-mac-tool <command>\n", stderr)
    exit(1)
}

let command = args[1]
let stdinData = FileHandle.standardInput.readDataToEndOfFile()
let payload = (try? JSONSerialization.jsonObject(with: stdinData.isEmpty ? "{}".data(using: .utf8)! : stdinData)) as? [String: Any] ?? [:]

func respond(_ data: Any) {
    let envelope: [String: Any] = ["status": "ok", "data": data]
    let json = try! JSONSerialization.data(withJSONObject: envelope, options: [.prettyPrinted])
    print(String(data: json, encoding: .utf8)!)
}

func respondError(_ message: String) {
    let envelope: [String: Any] = ["status": "error", "message": message]
    let json = try! JSONSerialization.data(withJSONObject: envelope)
    fputs(String(data: json, encoding: .utf8)! + "\n", stderr)
    exit(1)
}

do {
    switch command {

    // MARK: Mail
    case "mail-read":
        let result = try await MailTool.readEmails(payload: payload)
        respond(result)
    case "mail-list-mailboxes":
        let result = try await MailTool.listMailboxes(payload: payload)
        respond(result)
    case "mail-compose":
        let result = try await MailTool.composeMail(payload: payload)
        respond(result)

    // MARK: iMessage
    case "imessage-send":
        let result = try await iMessageTool.sendMessage(payload: payload)
        respond(result)
    case "imessage-read":
        let result = try await iMessageTool.readMessages(payload: payload)
        respond(result)

    // MARK: Music
    case "music-play":
        let result = try await MusicTool.play(payload: payload)
        respond(result)
    case "music-pause":
        let result = try await MusicTool.pause(payload: payload)
        respond(result)
    case "music-next":
        let result = try await MusicTool.nextTrack(payload: payload)
        respond(result)
    case "music-previous":
        let result = try await MusicTool.previousTrack(payload: payload)
        respond(result)
    case "music-now-playing":
        let result = try await MusicTool.nowPlaying(payload: payload)
        respond(result)
    case "music-volume":
        let result = try await MusicTool.setVolume(payload: payload)
        respond(result)
    case "music-search-play":
        let result = try await MusicTool.searchAndPlay(payload: payload)
        respond(result)
    case "music-list-playlists":
        let result = try await MusicTool.listPlaylists(payload: payload)
        respond(result)
    case "music-play-playlist":
        let result = try await MusicTool.playPlaylist(payload: payload)
        respond(result)
    case "music-play-track":
        let result = try await MusicTool.playTrack(payload: payload)
        respond(result)
    case "music-list-tracks":
        let result = try await MusicTool.listTracks(payload: payload)
        respond(result)

    // MARK: Safari
    case "safari-open":
        let result = try await SafariTool.open(payload: payload)
        respond(result)
    case "safari-navigate":
        let result = try await SafariTool.navigate(payload: payload)
        respond(result)
    case "safari-current-url":
        let result = try await SafariTool.currentURL(payload: payload)
        respond(result)
    case "safari-current-title":
        let result = try await SafariTool.currentTitle(payload: payload)
        respond(result)
    case "safari-list-tabs":
        let result = try await SafariTool.listTabs(payload: payload)
        respond(result)
    case "safari-close-tab":
        let result = try await SafariTool.closeTab(payload: payload)
        respond(result)
    case "safari-close-all-tabs":
        let result = try await SafariTool.closeAllTabs(payload: payload)
        respond(result)
    case "safari-reload":
        let result = try await SafariTool.reload(payload: payload)
        respond(result)
    case "safari-back":
        let result = try await SafariTool.back(payload: payload)
        respond(result)
    case "safari-forward":
        let result = try await SafariTool.forward(payload: payload)
        respond(result)
    case "safari-screenshot":
        let result = try await SafariTool.screenshot(payload: payload)
        respond(result)
    case "safari-js":
        let result = try await SafariTool.runJS(payload: payload)
        respond(result)
    case "safari-read":
        let result = try await SafariTool.read(payload: payload)
        respond(result)

    // MARK: Sleep
    case "sleep-now":
        let result = try await SleepTool.sleepNow(payload: payload)
        respond(result)
    case "sleep-in":
        let result = try await SleepTool.sleepIn(payload: payload)
        respond(result)
    case "sleep-cancel":
        let result = try await SleepTool.cancelSleep(payload: payload)
        respond(result)
    case "sleep-status":
        let result = try await SleepTool.sleepStatus(payload: payload)
        respond(result)
    case "sleep-winddown":
        let result = try await SleepTool.winddown(payload: payload)
        respond(result)

    // MARK: Notify
    case "notify-send":
        let result = try await NotifyTool.send(payload: payload)
        respond(result)

    // MARK: Contacts
    case "contacts-search":
        let result = try await ContactsTool.searchContacts(payload: payload)
        respond(result)

    // MARK: Clipboard
    case "clipboard-read":
        let result = try await ClipboardTool.read(payload: payload)
        respond(result)
    case "clipboard-write":
        let result = try await ClipboardTool.write(payload: payload)
        respond(result)

    // MARK: Calendar
    case "calendar-list-events":
        let result = try await CalendarTool.listEvents(payload: payload)
        respond(result)
    case "calendar-add-event":
        let result = try await CalendarTool.addEvent(payload: payload)
        respond(result)
    case "calendar-delete-event":
        let result = try await CalendarTool.deleteEvent(payload: payload)
        respond(result)
    case "calendar-get-events-by-date":
        let result = try await CalendarQueryTool.getEventsByDate(payload: payload)
        respond(result)
    case "calendar-get-upcoming-events":
        let result = try await CalendarQueryTool.getUpcomingEvents(payload: payload)
        respond(result)
    case "calendar-get-noise-summary":
        let result = try await CalendarQueryTool.getNoiseSummary(payload: payload)
        respond(result)

    // MARK: Reminders
    case "reminders-list":
        let result = try await RemindersTool.list(payload: payload)
        respond(result)
    case "reminders-create":
        let result = try await RemindersTool.create(payload: payload)
        respond(result)
    case "reminders-complete":
        let result = try await RemindersTool.complete(payload: payload)
        respond(result)
    case "reminders-delete":
        let result = try await RemindersTool.delete(payload: payload)
        respond(result)

    // MARK: Time
    case "time-now":
        let result = try await TimeTool.now(payload: payload)
        respond(result)
    case "time-alarm":
        let result = try await TimeTool.alarm(payload: payload)
        respond(result)
    case "time-wait":
        let result = try await TimeTool.wait(payload: payload)
        respond(result)

    // MARK: Notes
    case "notes-list":
        let result = try await NotesTool.listNotes(payload: payload)
        respond(result)
    case "notes-read":
        let result = try await NotesTool.readNote(payload: payload)
        respond(result)
    case "notes-folders":
        let result = try await NotesTool.listFolders(payload: payload)
        respond(result)
    case "notes-add":
        let result = try await NotesTool.addNote(payload: payload)
        respond(result)
    case "notes-delete":
        let result = try await NotesTool.deleteNote(payload: payload)
        respond(result)

    // MARK: Process
    case "process-list":
        let result = try await ProcessTool.listProcesses(payload: payload)
        respond(result)
    case "process-kill":
        let result = try await ProcessTool.killProcess(payload: payload)
        respond(result)

    // MARK: iCloud / Finder
    case "icloud-list":
        let result = try await iCloudDriveTool.list(payload: payload)
        respond(result)
    case "finder-search":
        let result = try await FinderTool.search(payload: payload)
        respond(result)

    // MARK: Foundation Models (stays Swift permanently)
    case "foundation-models-query":
        let result = try await FoundationModelsTool.query(payload: payload)
        respond(result)

    default:
        respondError("Unknown command: \(command)")
    }
} catch {
    respondError(error.localizedDescription)
}
