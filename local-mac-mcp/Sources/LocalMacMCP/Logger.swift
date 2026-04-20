import Foundation

// Simple stderr logger — replaces swift-log dependency.
enum logger {
    static func info(_ msg: String)    { fputs("[INFO]  \(msg)\n", stderr) }
    static func debug(_ msg: String)   { fputs("[DEBUG] \(msg)\n", stderr) }
    static func warning(_ msg: String) { fputs("[WARN]  \(msg)\n", stderr) }
    static func error(_ msg: String)   { fputs("[ERROR] \(msg)\n", stderr) }
}
