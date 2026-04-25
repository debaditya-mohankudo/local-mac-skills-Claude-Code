import Foundation

enum SafariTool {

    private static func exec(_ args: [String], timeout: TimeInterval = 15) async throws -> (String, Int32) {
        try await withCheckedThrowingContinuation { continuation in
            let process = Process()
            let outPipe = Pipe()
            let errPipe = Pipe()
            process.executableURL = URL(fileURLWithPath: "/usr/bin/osascript")
            process.arguments = args
            process.standardOutput = outPipe
            process.standardError = errPipe
            let timer = DispatchWorkItem {
                if process.isRunning { process.terminate() }
                continuation.resume(returning: ("timeout after \(Int(timeout))s", 1))
            }
            DispatchQueue.global().asyncAfter(deadline: .now() + timeout, execute: timer)
            process.terminationHandler = { p in
                timer.cancel()
                let data = outPipe.fileHandleForReading.readDataToEndOfFile()
                let out = String(data: data, encoding: .utf8)?
                    .trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
                continuation.resume(returning: (out, p.terminationStatus))
            }
            do { try process.run() } catch {
                timer.cancel()
                continuation.resume(throwing: error)
            }
        }
    }

    private static func checkAllowed(url: String) -> Bool {
        let cfgURL = FileManager.default.homeDirectoryForCurrentUser
            .appendingPathComponent("workspace/claude_for_mac_local/safari_config.sh")
        guard let content = try? String(contentsOf: cfgURL) else { return true }
        if content.range(of: #"(?m)^DISABLE_ALLOWLIST\s*=\s*true"#, options: .regularExpression) != nil { return true }
        guard let listRange = content.range(of: #"ALLOWED_URLS=\([^)]+\)"#, options: .regularExpression) else { return false }
        let block = String(content[listRange])
        var allowed: [String] = []
        if let re = try? NSRegularExpression(pattern: #""([^"]+)""#) {
            let ns = block as NSString
            for m in re.matches(in: block, range: NSRange(location: 0, length: ns.length)) {
                if m.numberOfRanges >= 2 { allowed.append(ns.substring(with: m.range(at: 1))) }
            }
        }
        guard !allowed.isEmpty else { return true }
        guard let host = URL(string: url)?.host else { return false }
        let bare = host.hasPrefix("www.") ? String(host.dropFirst(4)) : host
        return allowed.contains { bare == $0 || bare.hasSuffix("." + $0) }
    }

    private static func escapeJS(_ js: String) -> String {
        js.replacingOccurrences(of: "\\", with: "\\\\")
          .replacingOccurrences(of: "\"", with: "\\\"")
          .replacingOccurrences(of: "\n", with: "\\n")
          .replacingOccurrences(of: "\r", with: "\\r")
    }

    static func open(payload: [String: Any]) async throws -> Any {
        guard let url = payload.string("url") else { throw CLIError("Missing required argument: url") }
        guard checkAllowed(url: url) else { throw CLIError("BLOCKED: '\(url)' is not in the Safari allowlist.") }
        let (out, _) = try await exec(["-e", "tell application \"Safari\" to open location \"\(url)\""])
        return out.isEmpty ? "Opened: \(url)" : out
    }

    static func navigate(payload: [String: Any]) async throws -> Any {
        guard let url = payload.string("url") else { throw CLIError("Missing required argument: url") }
        guard checkAllowed(url: url) else { throw CLIError("BLOCKED: '\(url)' is not in the Safari allowlist.") }
        let (out, _) = try await exec(["-e", "tell application \"Safari\" to set URL of current tab of front window to \"\(url)\""])
        return out.isEmpty ? "Navigated: \(url)" : out
    }

    static func currentURL(payload: [String: Any]) async throws -> Any {
        let (out, _) = try await exec(["-e", "tell application \"Safari\" to return URL of current tab of front window"])
        return out
    }

    static func currentTitle(payload: [String: Any]) async throws -> Any {
        let (out, _) = try await exec(["-e", "tell application \"Safari\" to return name of current tab of front window"])
        return out
    }

    static func listTabs(payload: [String: Any]) async throws -> Any {
        let script = """
        tell application "Safari"
            set output to ""
            set winIdx to 0
            repeat with w in windows
                set winIdx to winIdx + 1
                set tabIdx to 0
                repeat with t in tabs of w
                    set tabIdx to tabIdx + 1
                    set output to output & "Window " & winIdx & " Tab " & tabIdx & ": " & name of t & " — " & URL of t & "\\n"
                end repeat
            end repeat
            return output
        end tell
        """
        let (out, _) = try await exec(["-e", script])
        return out.isEmpty ? "No tabs open." : out
    }

    static func closeTab(payload: [String: Any]) async throws -> Any {
        _ = try await exec(["-e", "tell application \"Safari\" to close current tab of front window"])
        return "Closed current tab."
    }

    static func closeAllTabs(payload: [String: Any]) async throws -> Any {
        _ = try await exec(["-e", "tell application \"Safari\" to close every tab of every window"])
        return "Closed all tabs."
    }

    static func reload(payload: [String: Any]) async throws -> Any {
        _ = try await exec(["-e", "tell application \"Safari\" to do JavaScript \"location.reload()\" in current tab of front window"])
        return "Reloaded."
    }

    static func back(payload: [String: Any]) async throws -> Any {
        _ = try await exec(["-e", "tell application \"Safari\" to do JavaScript \"history.back()\" in current tab of front window"])
        return "Went back."
    }

    static func forward(payload: [String: Any]) async throws -> Any {
        _ = try await exec(["-e", "tell application \"Safari\" to do JavaScript \"history.forward()\" in current tab of front window"])
        return "Went forward."
    }

    static func screenshot(payload: [String: Any]) async throws -> Any {
        let outfile = payload.string("outfile")
            ?? (FileManager.default.homeDirectoryForCurrentUser.path + "/Desktop/safari_screenshot.png")
        _ = try await exec(["-e", "tell application \"Safari\" to activate"])
        try await Task.sleep(nanoseconds: 400_000_000)
        let result = try await withCheckedThrowingContinuation { (continuation: CheckedContinuation<Int32, Error>) in
            let p = Process()
            p.executableURL = URL(fileURLWithPath: "/usr/sbin/screencapture")
            p.arguments = ["-x", "-o", outfile]
            p.terminationHandler = { continuation.resume(returning: $0.terminationStatus) }
            do { try p.run() } catch { continuation.resume(throwing: error) }
        }
        if result == 0 { return "Screenshot saved: \(outfile)" }
        throw CLIError("screencapture failed (exit \(result))")
    }

    static func runJS(payload: [String: Any]) async throws -> Any {
        guard let js = payload.string("js") else { throw CLIError("Missing required argument: js") }
        let escaped = escapeJS(js)
        let script = "tell application \"Safari\" to do JavaScript \"\(escaped)\" in current tab of front window"
        let (out, code) = try await exec(["-e", script])
        if code != 0 { throw CLIError("JS failed: \(out)") }
        return out
    }

    static func read(payload: [String: Any]) async throws -> Any {
        guard let mode = payload.string("mode") else {
            throw CLIError("Missing required argument: mode (text|html|links|title|selected)")
        }
        let js: String
        switch mode {
        case "text":     js = "document.body.innerText"
        case "html":     js = "document.documentElement.outerHTML"
        case "links":    js = "Array.from(document.querySelectorAll('a[href]')).map(a => a.href + ' | ' + a.innerText.trim()).join('\\n')"
        case "title":    js = "document.title"
        case "selected": js = "window.getSelection().toString()"
        default:         throw CLIError("Unknown mode: \(mode). Use: text|html|links|title|selected")
        }
        let escaped = escapeJS(js)
        let script = "tell application \"Safari\" to do JavaScript \"\(escaped)\" in current tab of front window"
        let (out, code) = try await exec(["-e", script])
        if code != 0 { throw CLIError("Read failed: \(out)") }
        return out
    }
}
