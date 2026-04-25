import Foundation

// Payload accessor — thin wrapper around [String: Any] from JSON stdin.
// Replaces the MCP Value enum accessors (stringValue, intValue, boolValue).

extension Dictionary where Key == String, Value == Any {

    func string(_ key: String) -> String? {
        self[key] as? String
    }

    func int(_ key: String) -> Int? {
        if let v = self[key] as? Int { return v }
        if let v = self[key] as? Double { return Int(v) }
        if let s = self[key] as? String { return Int(s) }
        return nil
    }

    func bool(_ key: String) -> Bool? {
        if let v = self[key] as? Bool { return v }
        if let v = self[key] as? Int { return v != 0 }
        return nil
    }

    func double(_ key: String) -> Double? {
        if let v = self[key] as? Double { return v }
        if let v = self[key] as? Int { return Double(v) }
        return nil
    }

    func array(_ key: String) -> [Any]? {
        self[key] as? [Any]
    }

    func dict(_ key: String) -> [String: Any]? {
        self[key] as? [String: Any]
    }
}
