import Foundation
import SQLite3

enum SQLiteError: Error, CustomStringConvertible {
    case dbNotFound(path: String)
    case openFailed(code: Int32)
    case prepareFailed(sql: String, message: String)
    case bindFailed(index: Int32, message: String)
    case unsupportedParamType(String)
    case stepFailed(message: String)
    case locked(message: String)

    var description: String {
        switch self {
        case .dbNotFound(let path):       return "Database not found: \(path)"
        case .openFailed(let code):       return "Failed to open database (SQLite error \(code))"
        case .prepareFailed(_, let msg):  return "Query preparation failed: \(msg)"
        case .bindFailed(let i, let msg): return "Failed to bind parameter \(i): \(msg)"
        case .unsupportedParamType(let t): return "Unsupported parameter type: \(t)"
        case .stepFailed(let msg):        return "Query execution failed: \(msg)"
        case .locked(let msg):            return "Database is locked: \(msg)"
        }
    }
}

/// Helper to query SQLite databases safely using C API
enum SQLiteHelper {

    /// Query a SQLite database and return results as array of dictionaries with optional values
    static func queryWithParams(
        databasePath: String,
        sql: String,
        parameters: [Any]
    ) throws -> [[String: String]] {
        guard FileManager.default.fileExists(atPath: databasePath) else {
            throw SQLiteError.dbNotFound(path: databasePath)
        }

        var db: OpaquePointer?
        let openResult = sqlite3_open_v2(databasePath, &db, SQLITE_OPEN_READONLY, nil)

        guard openResult == SQLITE_OK, let database = db else {
            throw SQLiteError.openFailed(code: openResult)
        }

        defer { sqlite3_close(database) }

        var statement: OpaquePointer?
        let prepareResult = sqlite3_prepare_v2(database, sql, -1, &statement, nil)

        guard prepareResult == SQLITE_OK, let stmt = statement else {
            let msg = String(cString: sqlite3_errmsg(database))
            throw SQLiteError.prepareFailed(sql: sql, message: msg)
        }

        defer { sqlite3_finalize(stmt) }

        // MARK: - Bind Parameters Safely with Proper Memory Management
        for (index, param) in parameters.enumerated() {
            let paramIndex = Int32(index + 1)
            let rc: Int32

            switch param {
            case let str as String:
                // Pass nil as destructor to use SQLITE_TRANSIENT behavior (SQLite copies the string immediately)
                rc = sqlite3_bind_text(stmt, paramIndex, str, -1, nil)

            case let int as Int:
                rc = sqlite3_bind_int64(stmt, paramIndex, Int64(int))

            case let int64 as Int64:
                rc = sqlite3_bind_int64(stmt, paramIndex, int64)

            case let double as Double:
                rc = sqlite3_bind_double(stmt, paramIndex, double)

            case let bool as Bool:
                rc = sqlite3_bind_int(stmt, paramIndex, bool ? 1 : 0)

            case is NSNull:
                rc = sqlite3_bind_null(stmt, paramIndex)

            default:
                throw SQLiteError.unsupportedParamType("\(type(of: param))")
            }

            guard rc == SQLITE_OK else {
                let msg = String(cString: sqlite3_errmsg(database))
                throw SQLiteError.bindFailed(index: paramIndex, message: msg)
            }
        }

        // MARK: - Execute Query
        var results: [[String: String]] = []

        while true {
            let stepResult = sqlite3_step(stmt)

            if stepResult == SQLITE_ROW {
                var row: [String: String] = [:]
                let columnCount = sqlite3_column_count(stmt)

                for col in 0..<columnCount {
                    let columnName = String(cString: sqlite3_column_name(stmt, col))
                    let type = sqlite3_column_type(stmt, col)

                    switch type {
                    case SQLITE_TEXT:
                        if let cString = sqlite3_column_text(stmt, col) {
                            row[columnName] = String(cString: cString)
                        }

                    case SQLITE_INTEGER:
                        let intValue = sqlite3_column_int64(stmt, col)
                        row[columnName] = String(intValue)

                    case SQLITE_FLOAT:
                        let doubleValue = sqlite3_column_double(stmt, col)
                        row[columnName] = String(doubleValue)

                    case SQLITE_NULL:
                        // Skip NULL values for [String: String] dictionary
                        break

                    case SQLITE_BLOB:
                        // Convert blob to hex string
                        if let bytes = sqlite3_column_blob(stmt, col) {
                            let size = Int(sqlite3_column_bytes(stmt, col))
                            let data = Data(bytes: bytes, count: size)
                            row[columnName] = data.map { String(format: "%02x", $0) }.joined()
                        }

                    default:
                        break
                    }
                }

                results.append(row)

            } else if stepResult == SQLITE_DONE {
                break

            } else {
                let msg = String(cString: sqlite3_errmsg(database))
                if stepResult == SQLITE_LOCKED || stepResult == SQLITE_BUSY {
                    throw SQLiteError.locked(message: msg)
                }
                throw SQLiteError.stepFailed(message: msg)
            }
        }

        return results
    }
}
