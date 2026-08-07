// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "local-mac-tool",
    platforms: [.macOS(.v14)],
    targets: [
        .executableTarget(
            name: "LocalMacMCP",
            path: "Sources/LocalMacMCP",
            linkerSettings: [
                .linkedLibrary("sqlite3"),
            ]
        ),
    ]
)
