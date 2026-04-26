import Foundation

// Podcasts.app database path (sandboxed group container)
private let podcastsDBPath = NSHomeDirectory() +
    "/Library/Group Containers/243LU875E5.groups.com.apple.podcasts/Documents/MTLibrary.sqlite"

// Core Data timestamps are seconds since 2001-01-01 (Apple's NSDate epoch)
private let appleCoreDataEpoch: TimeInterval = 978307200

private func coreDataTimestampToISO(_ ts: String?) -> String? {
    guard let ts, let seconds = Double(ts), seconds > 0 else { return nil }
    let date = Date(timeIntervalSince1970: seconds + appleCoreDataEpoch)
    let fmt = ISO8601DateFormatter()
    fmt.formatOptions = [.withInternetDateTime]
    return fmt.string(from: date)
}

private func secondsToHMS(_ s: Double) -> String {
    let total = Int(s)
    let h = total / 3600
    let m = (total % 3600) / 60
    let sec = total % 60
    if h > 0 { return String(format: "%d:%02d:%02d", h, m, sec) }
    return String(format: "%d:%02d", m, sec)
}

enum PodcastsTool {

    // MARK: - List subscribed podcasts

    static func listPodcasts(payload: [String: Any]) async throws -> Any {
        let rows = try SQLiteHelper.queryWithParams(
            databasePath: podcastsDBPath,
            sql: """
                SELECT ZTITLE, ZAUTHOR, ZNEWEPISODESCOUNT, ZLIBRARYEPISODESCOUNT,
                       ZDOWNLOADEDEPISODESCOUNT, ZSUBSCRIBED, ZUUID
                FROM ZMTPODCAST
                ORDER BY ZTITLE ASC
                """,
            parameters: []
        )
        return rows.map { r -> [String: Any] in
            var d: [String: Any] = [:]
            if let v = r["ZTITLE"]                  { d["title"] = v }
            if let v = r["ZAUTHOR"]                 { d["author"] = v }
            if let v = r["ZNEWEPISODESCOUNT"]       { d["new_episodes"] = Int(v) ?? 0 }
            if let v = r["ZLIBRARYEPISODESCOUNT"]   { d["library_episodes"] = Int(v) ?? 0 }
            if let v = r["ZDOWNLOADEDEPISODESCOUNT"] { d["downloaded"] = Int(v) ?? 0 }
            if let v = r["ZSUBSCRIBED"]             { d["subscribed"] = v == "1" }
            if let v = r["ZUUID"]                   { d["uuid"] = v }
            return d
        }
    }

    // MARK: - List episodes for a podcast (by uuid or title substring)

    static func listEpisodes(payload: [String: Any]) async throws -> Any {
        let limit = payload.int("limit") ?? 20
        let onlyUnplayed = payload.bool("unplayed") ?? false

        // Resolve podcast by uuid or title match
        let podcastUUID: String
        if let uuid = payload.string("podcast_uuid") {
            podcastUUID = uuid
        } else if let title = payload.string("podcast_title") {
            let matches = try SQLiteHelper.queryWithParams(
                databasePath: podcastsDBPath,
                sql: "SELECT ZUUID FROM ZMTPODCAST WHERE ZTITLE LIKE ? LIMIT 1",
                parameters: ["%" + title + "%"]
            )
            guard let uuid = matches.first?["ZUUID"] else {
                throw CLIError("No podcast found matching: \(title)")
            }
            podcastUUID = uuid
        } else {
            throw CLIError("Provide podcast_uuid or podcast_title")
        }

        let unplayedFilter = onlyUnplayed ? "AND e.ZHASBEENPLAYED = 0 AND e.ZMARKASPLAYED = 0" : ""
        let rows = try SQLiteHelper.queryWithParams(
            databasePath: podcastsDBPath,
            sql: """
                SELECT e.ZTITLE, e.ZDURATION, e.ZPLAYHEAD, e.ZHASBEENPLAYED,
                       e.ZISNEW, e.ZSAVED, e.ZPUBDATE, e.ZUUID, e.ZENCLOSUREURL
                FROM ZMTEPISODE e
                WHERE e.ZPODCASTUUID = ?
                AND e.ZISHIDDEN = 0
                \(unplayedFilter)
                ORDER BY e.ZPUBDATE DESC
                LIMIT ?
                """,
            parameters: [podcastUUID, limit]
        )
        return rows.map { episodeDict($0) }
    }

    // MARK: - Recent episodes across all podcasts

    static func recentEpisodes(payload: [String: Any]) async throws -> Any {
        let limit = payload.int("limit") ?? 20
        let onlyNew = payload.bool("new_only") ?? false
        let newFilter = onlyNew ? "AND e.ZISNEW = 1" : ""

        let rows = try SQLiteHelper.queryWithParams(
            databasePath: podcastsDBPath,
            sql: """
                SELECT e.ZTITLE, e.ZDURATION, e.ZPLAYHEAD, e.ZHASBEENPLAYED,
                       e.ZISNEW, e.ZSAVED, e.ZPUBDATE, e.ZUUID,
                       p.ZTITLE as podcast_title
                FROM ZMTEPISODE e
                LEFT JOIN ZMTPODCAST p ON e.ZPODCASTUUID = p.ZUUID
                WHERE e.ZISHIDDEN = 0
                \(newFilter)
                ORDER BY e.ZPUBDATE DESC
                LIMIT ?
                """,
            parameters: [limit]
        )
        return rows.map { r -> [String: Any] in
            var d = episodeDict(r)
            if let v = r["podcast_title"] { d["podcast"] = v }
            return d
        }
    }

    // MARK: - In-progress episodes (started but not finished)

    static func inProgress(payload: [String: Any]) async throws -> Any {
        let rows = try SQLiteHelper.queryWithParams(
            databasePath: podcastsDBPath,
            sql: """
                SELECT e.ZTITLE, e.ZDURATION, e.ZPLAYHEAD, e.ZHASBEENPLAYED,
                       e.ZISNEW, e.ZSAVED, e.ZPUBDATE, e.ZUUID,
                       p.ZTITLE as podcast_title
                FROM ZMTEPISODE e
                LEFT JOIN ZMTPODCAST p ON e.ZPODCASTUUID = p.ZUUID
                WHERE e.ZISHIDDEN = 0
                AND e.ZPLAYHEAD > 0
                AND e.ZHASBEENPLAYED = 0
                ORDER BY e.ZLASTDATEPLAYED DESC
                LIMIT 20
                """,
            parameters: []
        )
        return rows.map { r -> [String: Any] in
            var d = episodeDict(r)
            if let v = r["podcast_title"] { d["podcast"] = v }
            return d
        }
    }

    // MARK: - Shared episode dict builder

    private static func episodeDict(_ r: [String: String]) -> [String: Any] {
        var d: [String: Any] = [:]
        if let v = r["ZTITLE"]          { d["title"] = v }
        if let v = r["ZUUID"]           { d["uuid"] = v }
        if let v = r["ZDURATION"], let s = Double(v) { d["duration"] = secondsToHMS(s) }
        if let v = r["ZPLAYHEAD"], let s = Double(v), s > 0 { d["playhead"] = secondsToHMS(s) }
        if let v = r["ZHASBEENPLAYED"]  { d["played"] = v == "1" }
        if let v = r["ZISNEW"]          { d["is_new"] = v == "1" }
        if let v = r["ZSAVED"]          { d["saved"] = v == "1" }
        if let v = r["ZPUBDATE"]        { d["published"] = coreDataTimestampToISO(v) ?? v }
        if let v = r["ZENCLOSUREURL"]   { d["audio_url"] = v }
        return d
    }
}
