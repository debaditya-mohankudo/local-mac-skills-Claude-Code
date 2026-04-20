import Contacts
import Foundation

enum ContactsTool {

    private static func getVaultContactsPath() -> String {
        let envVaultPath = ProcessInfo.processInfo.environment["VAULT_PATH"]
        let basePath = envVaultPath ?? (NSHomeDirectory() + "/workspace/claude_documents")
        return basePath + "/LIFE_OS/Contacts"
    }

    static func searchContacts(payload: [String: Any]) async throws -> Any {
        guard let searchName = payload.string("name"), !searchName.isEmpty else {
            throw CLIError("Missing required argument: name")
        }
        let includeEmail = payload.bool("include_email") ?? false

        // Vault contacts first
        if let vaultResults = try searchVaultContacts(searchName: searchName, includeEmail: includeEmail) {
            logger.info("ContactsTool: vault hit for '\(searchName)' — \(vaultResults.count) result(s)")
            let encoder = JSONEncoder()
            encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
            let data = try encoder.encode(vaultResults)
            return (try? JSONSerialization.jsonObject(with: data)) ?? vaultResults
        }

        // Fallback to CNContactStore
        let store = CNContactStore()
        let granted: Bool = try await withCheckedThrowingContinuation { continuation in
            store.requestAccess(for: .contacts) { granted, error in
                if let error { continuation.resume(throwing: error) }
                else { continuation.resume(returning: granted) }
            }
        }
        guard granted else {
            throw CLIError("Contacts access denied. Grant access in System Settings > Privacy & Security > Contacts.")
        }

        let predicate = CNContact.predicateForContacts(matchingName: searchName)
        var keys: [CNKeyDescriptor] = [
            CNContactGivenNameKey as CNKeyDescriptor,
            CNContactFamilyNameKey as CNKeyDescriptor,
            CNContactPhoneNumbersKey as CNKeyDescriptor,
        ]
        if includeEmail { keys.append(CNContactEmailAddressesKey as CNKeyDescriptor) }

        let contacts = try store.unifiedContacts(matching: predicate, keysToFetch: keys)
        if contacts.isEmpty { return "No contacts found matching '\(searchName)'." }

        struct PhoneEntry: Encodable { let label: String; let value: String }
        struct EmailEntry: Encodable { let label: String; let value: String }
        struct ContactEntry: Encodable {
            let name: String
            let phoneNumbers: [PhoneEntry]
            let emailAddresses: [EmailEntry]?
        }

        let entries = contacts.map { contact -> ContactEntry in
            let phones = contact.phoneNumbers.map { p in
                PhoneEntry(
                    label: CNLabeledValue<CNPhoneNumber>.localizedString(forLabel: p.label ?? "") ?? "phone",
                    value: p.value.stringValue
                )
            }
            let emails = includeEmail ? contact.emailAddresses.map { e in
                EmailEntry(
                    label: CNLabeledValue<NSString>.localizedString(forLabel: e.label ?? "") ?? "email",
                    value: e.value as String
                )
            } : nil
            var parts: [String] = []
            if !contact.givenName.isEmpty  { parts.append(contact.givenName) }
            if !contact.familyName.isEmpty { parts.append(contact.familyName) }
            let displayName = parts.joined(separator: " ").trimmingCharacters(in: .whitespaces)
            return ContactEntry(name: displayName.isEmpty ? "(no name)" : displayName, phoneNumbers: phones, emailAddresses: emails)
        }

        let encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        let data = try encoder.encode(entries)
        return (try? JSONSerialization.jsonObject(with: data)) ?? entries
    }

    private static func searchVaultContacts(searchName: String, includeEmail: Bool) throws -> [[String: AnyCodable]]? {
        let contactsPath = getVaultContactsPath()
        let fileManager = FileManager.default
        guard fileManager.fileExists(atPath: contactsPath) else { return nil }
        let files = try fileManager.contentsOfDirectory(atPath: contactsPath)
        let mdFiles = files.filter { $0.hasSuffix(".md") }
        var allContacts: [[String: AnyCodable]] = []
        for file in mdFiles {
            let filePath = (contactsPath as NSString).appendingPathComponent(file)
            let content = try String(contentsOfFile: filePath, encoding: .utf8)
            if let contactData = parseContactFile(content, includeEmail: includeEmail) {
                allContacts.append(contactData)
            }
        }
        let searchLower = searchName.lowercased()
        var results = allContacts.filter { ($0["name"]?.stringValue ?? "").lowercased() == searchLower }
        if results.isEmpty {
            results = allContacts.filter { contact in
                if case .array(let nicknames) = contact["nicknames"] {
                    for nickname in nicknames {
                        if case .string(let nick) = nickname, nick.lowercased().contains(searchLower) { return true }
                    }
                }
                return false
            }
        }
        if results.isEmpty {
            results = allContacts.filter { ($0["name"]?.stringValue ?? "").lowercased().hasPrefix(searchLower) }
        }
        return results.isEmpty ? nil : results
    }

    private static func parseContactFile(_ content: String, includeEmail: Bool) -> [String: AnyCodable]? {
        let lines = content.split(separator: "\n", omittingEmptySubsequences: false).map(String.init)
        var inFrontmatter = false
        var frontmatterLines: [String] = []
        var frontmatterEnd = -1
        for (index, line) in lines.enumerated() {
            if line == "---" {
                if !inFrontmatter { inFrontmatter = true }
                else { frontmatterEnd = index; break }
            } else if inFrontmatter { frontmatterLines.append(line) }
        }
        guard frontmatterEnd >= 0 else { return nil }
        var contact: [String: AnyCodable] = [:]
        for line in frontmatterLines {
            let parts = line.split(separator: ":", maxSplits: 1, omittingEmptySubsequences: false).map(String.init)
            guard parts.count == 2 else { continue }
            let key = parts[0].trimmingCharacters(in: .whitespaces)
            let value = parts[1].trimmingCharacters(in: .whitespaces)
            if value.hasPrefix("[") && value.hasSuffix("]") {
                let arrayStr = String(value.dropFirst().dropLast())
                let items = arrayStr.split(separator: ",").map { String($0).trimmingCharacters(in: .whitespaces) }
                contact[key] = .array(items.map { .string($0) })
            } else {
                contact[key] = .string(value)
            }
        }
        guard contact["name"] != nil else { return nil }
        if let phone = contact["phone"]?.stringValue, !phone.isEmpty {
            contact.removeValue(forKey: "phone")
            contact["phoneNumbers"] = .array([.object(["label": .string("mobile"), "value": .string(phone)])])
        }
        if includeEmail, let email = contact["email"]?.stringValue, !email.isEmpty {
            contact["emailAddresses"] = .array([.object(["label": .string("email"), "value": .string(email)])])
        }
        contact.removeValue(forKey: "email")
        contact.removeValue(forKey: "date_of_birth")
        contact.removeValue(forKey: "last_contacted")
        contact.removeValue(forKey: "priority")
        contact.removeValue(forKey: "tags")
        return contact.isEmpty ? nil : contact
    }
}
