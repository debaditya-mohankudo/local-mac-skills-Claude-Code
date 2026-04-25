import Foundation

enum iCloudDriveTool {

    private static let iCloudRoot = FileManager.default.homeDirectoryForCurrentUser
        .appendingPathComponent("Library/Mobile Documents/com~apple~CloudDocs")

    static func list(payload: [String: Any]) async throws -> Any {
        let subpath = payload.string("path") ?? ""
        let target: URL
        if subpath.isEmpty {
            target = iCloudRoot
        } else {
            target = iCloudRoot.appendingPathComponent(subpath).resolvingSymlinksInPath()
        }

        var isDir: ObjCBool = false
        guard FileManager.default.fileExists(atPath: target.path, isDirectory: &isDir), isDir.boolValue else {
            throw CLIError("Path not found or not a directory: \(subpath)")
        }

        let contents = try FileManager.default.contentsOfDirectory(
            at: target,
            includingPropertiesForKeys: [.isDirectoryKey, .fileSizeKey, .contentModificationDateKey],
            options: [.skipsHiddenFiles]
        )

        let formatter = ISO8601DateFormatter()
        var entries: [[String: String]] = []
        for url in contents.sorted(by: { $0.lastPathComponent < $1.lastPathComponent }) {
            let rv = try? url.resourceValues(forKeys: [.isDirectoryKey, .fileSizeKey, .contentModificationDateKey])
            let isDirectory = rv?.isDirectory ?? false
            entries.append([
                "name": url.lastPathComponent,
                "type": isDirectory ? "folder" : "file",
                "size": isDirectory ? "—" : (rv?.fileSize.map { "\($0) bytes" } ?? "—"),
                "modified": rv?.contentModificationDate.map { formatter.string(from: $0) } ?? "—",
                "path": subpath.isEmpty ? url.lastPathComponent : "\(subpath)/\(url.lastPathComponent)"
            ])
        }

        let encoder = JSONEncoder()
        encoder.outputFormatting = .prettyPrinted
        let data = try encoder.encode(entries)
        return (try? JSONSerialization.jsonObject(with: data)) ?? entries
    }
}
