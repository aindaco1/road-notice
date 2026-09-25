// swift-tools-version: 6.2
import PackageDescription

let package = Package(
    name: "FineMeNotCore",
    platforms: [.iOS(.v17), .macOS(.v15)],
    products: [.library(name: "CameraCore", targets: ["CameraCore"]), .library(name: "SupportCore", targets: ["SupportCore"])],
    dependencies: [.package(path: "shared/dust-wave-platform/support")],
    targets: [
        .target(name: "CameraCore"),
        .target(name: "SupportCore", dependencies: [.product(name: "DustWaveSupport", package: "support")], resources: [.process("Resources")]),
        .testTarget(name: "SupportCoreTests", dependencies: ["SupportCore"]),
        .testTarget(name: "CameraCoreTests", dependencies: ["CameraCore"])
    ]
)
