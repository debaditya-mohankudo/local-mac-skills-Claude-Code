import Foundation

enum FinderTool {

    static func search(payload: [String: Any]) async throws -> Any {
        guard let query = payload.string("query"), !query.isEmpty else {
            throw CLIError("Missing required argument: query")
        }
        let scopePath = payload.string("path")

        var args: [String]
        if query.contains("==") || query.hasPrefix("kMDItem") {
            args = [query]
        } else {
            args = ["-name", query]
        }
        if let path = scopePath { args = ["-onlyin", path] + args }

        let output = try await runProcess("/usr/bin/mdfind", arguments: args)
        if output.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            return "No files found."
        }
        let files = output.split(separator: "\n", omittingEmptySubsequences: true).map(String.init)
        let encoder = JSONEncoder()
        encoder.outputFormatting = .prettyPrinted
        let data = try encoder.encode(files)
        return (try? JSONSerialization.jsonObject(with: data)) ?? files
    }
}
