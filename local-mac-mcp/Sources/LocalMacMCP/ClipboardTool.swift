import AppKit

enum ClipboardTool {

    static func read(payload: [String: Any]) async throws -> Any {
        let pb = NSPasteboard.general
        guard let text = pb.string(forType: .string) else {
            return "Clipboard is empty or contains non-text content."
        }
        return text
    }

    static func write(payload: [String: Any]) async throws -> Any {
        guard let text = payload.string("text") else {
            throw CLIError("Missing required argument: text")
        }
        let pb = NSPasteboard.general
        pb.clearContents()
        pb.setString(text, forType: .string)
        let preview = String(text.prefix(80)).replacingOccurrences(of: "\n", with: " ")
        return "Copied to clipboard (\(text.utf8.count) bytes): \(preview)\(text.count > 80 ? "…" : "")"
    }
}
