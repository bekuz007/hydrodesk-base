// swift-tools-version:5.9
// Hilfs-Paket NUR für Tests der reinen Logik (ohne Xcode-Projekt):
//   cd app-ios && swift test        (läuft auf dem Mac und auf Linux)
// Die App selbst baut man mit HydroDesk.xcodeproj.
import PackageDescription

let package = Package(
    name: "HydroDeskCore",
    platforms: [.iOS(.v17), .macOS(.v14)],
    products: [
        .library(name: "HydroDeskCore", targets: ["HydroDeskCore"]),
        .library(name: "HydroDeskRemote", targets: ["HydroDeskRemote"]),
    ],
    dependencies: [
        .package(url: "https://github.com/supabase/supabase-swift.git", exact: "2.55.6"),
    ],
    targets: [
        .target(name: "HydroDeskCore", path: "HydroDesk/Core"),
        .target(
            name: "HydroDeskRemote",
            dependencies: [.product(name: "Supabase", package: "supabase-swift")],
            path: "HydroDesk/Remote"
        ),
        .testTarget(name: "HydroDeskCoreTests", dependencies: ["HydroDeskCore"], path: "HydroDeskTests"),
    ]
)
