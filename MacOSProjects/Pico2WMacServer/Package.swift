// swift-tools-version:5.5
import PackageDescription

let package = Package(
    name: "Pico2WMacServer",
    platforms: [
        .macOS(.v10_15)
    ],
    products: [
        .executable(name: "Pico2WMacServer", targets: ["Pico2WMacServer"])
    ],
    dependencies: [],
    targets: [
        .executableTarget(
            name: "Pico2WMacServer",
            dependencies: []
        )
    ]
)
