import Foundation

enum ProcessTool {

    static func listProcesses(payload: [String: Any]) async throws -> Any {
        let nameFilter = payload.string("name") ?? ""
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/bin/sh")
        process.arguments = ["-c", "ps aux | head -1; ps aux | grep -i '\(nameFilter)' | grep -v grep | head -30"]
        let pipe = Pipe()
        process.standardOutput = pipe
        process.standardError = pipe
        try process.run()
        process.waitUntilExit()
        return String(data: pipe.fileHandleForReading.readDataToEndOfFile(), encoding: .utf8) ?? "No processes found."
    }

    static func killProcess(payload: [String: Any]) async throws -> Any {
        guard let pidValue = payload.int("pid") else {
            throw CLIError("Missing required argument: pid")
        }
        let pid = Int32(pidValue)
        guard pid > 100 else {
            throw CLIError("Cannot kill system processes (PID must be > 100).")
        }
        let blockedProcesses = ["launchd", "kernel_task", "WindowServer", "loginwindow"]
        let processName = getProcessName(pid: pid)
        if blockedProcesses.contains(processName) {
            throw CLIError("Cannot kill system process: \(processName)")
        }
        let useForce = payload.bool("force") ?? false
        let signal = Int32(useForce ? 9 : 15)
        let result = kill(pid, signal)
        if result == 0 {
            return "Sent \(useForce ? "SIGKILL" : "SIGTERM") to process \(pid) (\(processName))"
        } else {
            throw CLIError("Failed to kill process \(pid): \(String(cString: strerror(errno)))")
        }
    }

    private static func getProcessName(pid: Int32) -> String {
        let p = Process()
        p.executableURL = URL(fileURLWithPath: "/bin/ps")
        p.arguments = ["-p", String(pid), "-o", "comm="]
        let pipe = Pipe()
        p.standardOutput = pipe
        do {
            try p.run()
            p.waitUntilExit()
            return String(data: pipe.fileHandleForReading.readDataToEndOfFile(), encoding: .utf8)?
                .trimmingCharacters(in: .whitespacesAndNewlines) ?? "unknown"
        } catch { return "unknown" }
    }
}
