import Foundation

enum SurfsharkTool {

    // MARK: - Public entry points

    static func status(payload: [String: Any]) async throws -> Any {
        let connections = try await scutilList()
        let activeConn = connections.first(where: { $0.state == "Connected" })
        let isConnected = activeConn != nil

        var result: [String: Any] = [
            "connected": isConnected,
            "connections": connections.map { ["name": $0.name, "state": $0.state, "protocol": $0.vpnProtocol] }
        ]

        if isConnected, let conn = activeConn {
            if let detail = try? await scutilDetail(name: conn.name) {
                result["ip_address"] = detail.vpnIP
                result["dns_servers"] = detail.dnsServers
                result["interface"] = detail.interface
            }
            if let session = readSessionInfo() {
                result["server"] = session.locationName
                result["country_code"] = session.countryCode
                result["server_address"] = session.serverAddress
                result["vpn_protocol"] = session.vpnProtocol
                result["transport"] = session.transportProtocol
                result["post_quantum"] = session.isPostQuantum
            }
        }

        return result
    }

    // MARK: - scutil helpers

    private struct Connection {
        let name: String
        let state: String
        let vpnProtocol: String
    }

    private struct Detail {
        let vpnIP: String
        let dnsServers: [String]
        let interface: String
    }

    private static func scutilList() async throws -> [Connection] {
        let output = try await runProcess("/usr/sbin/scutil", arguments: ["--nc", "list"])
        var result: [Connection] = []

        for line in output.components(separatedBy: "\n") {
            guard line.contains("com.surfshark") else { continue }
            // Format: * (Connected)   UUID VPN (bundle) "Name"
            let state = line.contains("(Connected)") ? "Connected" : "Disconnected"
            let name: String
            if let range = line.range(of: "\""), let end = line.range(of: "\"", options: .backwards),
               range.lowerBound != end.lowerBound {
                name = String(line[line.index(after: range.lowerBound)..<end.lowerBound])
            } else {
                name = "Unknown"
            }
            let proto: String
            if line.contains("WireGuard") { proto = "WireGuard" }
            else if line.contains("OpenVPN") { proto = "OpenVPN" }
            else if line.contains("IKEv2") { proto = "IKEv2" }
            else { proto = "VPN" }

            result.append(Connection(name: name, state: state, vpnProtocol: proto))
        }

        return result
    }

    private static func scutilDetail(name: String) async throws -> Detail {
        let output = try await runProcess("/usr/sbin/scutil", arguments: ["--nc", "status", name])
        var vpnIP = ""
        var dns: [String] = []
        var iface = ""

        for line in output.components(separatedBy: "\n") {
            let trimmed = line.trimmingCharacters(in: .whitespaces)
            if trimmed.hasPrefix("0 :") && vpnIP.isEmpty {
                // First Addresses entry
                let parts = trimmed.components(separatedBy: ":")
                if parts.count >= 2 { vpnIP = parts[1].trimmingCharacters(in: .whitespaces) }
            }
            if trimmed.hasPrefix("InterfaceName") {
                iface = trimmed.components(separatedBy: ":").dropFirst().joined(separator: ":").trimmingCharacters(in: .whitespaces)
            }
            if trimmed.hasPrefix("0 :") && dns.isEmpty && iface.isEmpty {
                // Could be DNS — check context by position but simpler: collect all "N :" lines
            }
        }

        // Parse DNS servers — they appear under DNSServers array
        var inDNS = false
        for line in output.components(separatedBy: "\n") {
            let t = line.trimmingCharacters(in: .whitespaces)
            if t.hasPrefix("DNSServers") { inDNS = true; continue }
            if inDNS {
                if t.hasPrefix("}") { inDNS = false; continue }
                if t.hasPrefix("0 :") || t.hasPrefix("1 :") {
                    let ip = t.components(separatedBy: ":").dropFirst().joined(separator: ":").trimmingCharacters(in: .whitespaces)
                    if !ip.isEmpty { dns.append(ip) }
                }
            }
        }

        // Parse VPN IP from Addresses array
        var inAddresses = false
        for line in output.components(separatedBy: "\n") {
            let t = line.trimmingCharacters(in: .whitespaces)
            if t.hasPrefix("Addresses") { inAddresses = true; continue }
            if inAddresses {
                if t.hasPrefix("}") { inAddresses = false; continue }
                if t.hasPrefix("0 :") {
                    vpnIP = t.components(separatedBy: ":").dropFirst().joined(separator: ":").trimmingCharacters(in: .whitespaces)
                }
            }
        }

        // InterfaceName
        for line in output.components(separatedBy: "\n") {
            let t = line.trimmingCharacters(in: .whitespaces)
            if t.hasPrefix("InterfaceName") {
                iface = t.components(separatedBy: ":").dropFirst().joined(separator: ":").trimmingCharacters(in: .whitespaces)
                break
            }
        }

        return Detail(vpnIP: vpnIP, dnsServers: dns, interface: iface)
    }

    // MARK: - Session info from tunnel plist

    private struct SessionInfo {
        let locationName: String
        let countryCode: String
        let serverAddress: String
        let vpnProtocol: String
        let transportProtocol: String
        let isPostQuantum: Bool
    }

    private static func readSessionInfo() -> SessionInfo? {
        let home = NSHomeDirectory()
        let path = "\(home)/Library/Group Containers/YHUG37CKN8.com.surfshark.vpn.tunnel/Library/Preferences/YHUG37CKN8.com.surfshark.vpn.tunnel.plist"
        guard let dict = NSDictionary(contentsOfFile: path),
              let rawData = dict["vpnSessionInfo"] as? Data,
              let json = try? JSONSerialization.jsonObject(with: rawData) as? [String: Any]
        else { return nil }

        let server = json["vpnServer"] as? [String: Any] ?? [:]
        return SessionInfo(
            locationName: server["locationName"] as? String ?? "",
            countryCode: server["countryCode"] as? String ?? "",
            serverAddress: server["serverAddress"] as? String ?? "",
            vpnProtocol: json["vpnProtocol"] as? String ?? "",
            transportProtocol: json["transportProtocol"] as? String ?? "",
            isPostQuantum: json["isPostQuantumSecureConnection"] as? Bool ?? false
        )
    }
}
