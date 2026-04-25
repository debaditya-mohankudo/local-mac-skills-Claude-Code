import Foundation
import Darwin

/// Runs a subprocess with timeout. Returns stdout or throws TimeoutError if exceeds limit.
func runProcess(_ executable: String, arguments: [String], timeout: TimeInterval = 15.0) async throws -> String {
    return try await withCheckedThrowingContinuation { continuation in
        let process = Process()
        let pipe = Pipe()
        process.executableURL = URL(fileURLWithPath: executable)
        process.arguments = arguments
        process.standardOutput = pipe
        process.standardError = Pipe() // discard stderr

        let finished = NSLock()
        var didFinish = false

        process.terminationHandler = { _ in
            finished.lock()
            defer { finished.unlock() }
            guard !didFinish else { return }
            didFinish = true
            let data = pipe.fileHandleForReading.readDataToEndOfFile()
            let output = String(data: data, encoding: .utf8) ?? ""
            continuation.resume(returning: output)
        }

        do {
            try process.launch()

            // Schedule timeout
            DispatchQueue.global().asyncAfter(deadline: .now() + timeout) {
                finished.lock()
                defer { finished.unlock() }
                guard !didFinish else { return }
                didFinish = true
                if process.isRunning {
                    process.terminate()
                }
                continuation.resume(throwing: NSError(domain: "ProcessTimeout", code: -1, userInfo: [NSLocalizedDescriptionKey: "Process exceeded \(Int(timeout))s timeout"]))
            }
        } catch {
            continuation.resume(throwing: error)
        }
    }
}
