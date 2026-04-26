import Foundation

// MARK: - CLI Error

struct CLIError: Error, LocalizedError {
    let message: String
    init(_ message: String) { self.message = message }
    var errorDescription: String? { message }
}

// MARK: - SQLiteError → CLIError mapping

extension SQLiteError {
    /// Returns a user-facing CLIError with an actionable message.
    func asCLIError(database: String = "database") -> CLIError {
        switch self {
        case .dbNotFound(let path):
            return CLIError("The \(database) was not found at: \(path)")
        case .openFailed(let code):
            return CLIError("Could not open the \(database) (error \(code)). It may be in use by another process.")
        case .locked(let msg):
            return CLIError("The \(database) is locked — another app may have it open. Close the app and retry. (\(msg))")
        case .prepareFailed(_, let msg):
            return CLIError("Query failed against \(database): \(msg)")
        case .bindFailed(let i, let msg):
            return CLIError("Failed to bind query parameter \(i) for \(database): \(msg)")
        case .stepFailed(let msg):
            return CLIError("Query execution failed on \(database): \(msg)")
        case .unsupportedParamType(let t):
            return CLIError("Unsupported query parameter type '\(t)' for \(database) query")
        }
    }
}

// MARK: - AnyCodable Helper (for mixed type encoding)

enum AnyCodable: Codable {
    case string(String)
    case number(Double)
    case array([AnyCodable])
    case object([String: AnyCodable])
    case bool(Bool)
    case null

    var stringValue: String? {
        if case .string(let value) = self { return value }
        return nil
    }

    var numberValue: Double? {
        if case .number(let value) = self { return value }
        return nil
    }

    var arrayValue: [AnyCodable]? {
        if case .array(let value) = self { return value }
        return nil
    }

    var objectValue: [String: AnyCodable]? {
        if case .object(let value) = self { return value }
        return nil
    }

    var boolValue: Bool? {
        if case .bool(let value) = self { return value }
        return nil
    }

    var isNull: Bool {
        if case .null = self { return true }
        return false
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        switch self {
        case .string(let value): try container.encode(value)
        case .number(let value): try container.encode(value)
        case .bool(let value):   try container.encode(value)
        case .array(let value):  try container.encode(value)
        case .object(let value): try container.encode(value)
        case .null:              try container.encodeNil()
        }
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        if container.decodeNil() {
            self = .null
        } else if let value = try? container.decode(String.self) {
            self = .string(value)
        } else if let value = try? container.decode(Double.self) {
            self = .number(value)
        } else if let value = try? container.decode(Bool.self) {
            self = .bool(value)
        } else if let value = try? container.decode([AnyCodable].self) {
            self = .array(value)
        } else if let value = try? container.decode([String: AnyCodable].self) {
            self = .object(value)
        } else {
            self = .null
        }
    }
}
