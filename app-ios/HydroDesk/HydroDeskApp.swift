// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE

import SwiftData
import SwiftUI

/// Einstiegspunkt der App.
@main
@MainActor
struct HydroDeskApp: App {
    /// Lokale Datenbank (SwiftData): speichert alle Schlucke auf dem iPhone.
    private let modelContainer: ModelContainer
    /// Alle Dienste (Login, Profil, Bluetooth, Sync …), einmal erzeugt.
    @State private var container: AppContainer

    init() {
        let datenbank: ModelContainer
        do {
            datenbank = try ModelContainer(for: DrinkEntry.self)
        } catch {
            fatalError("Lokale Datenbank konnte nicht angelegt werden: \(error)")
        }
        modelContainer = datenbank
        _container = State(initialValue: AppContainer(modelContext: datenbank.mainContext))
    }

    var body: some Scene {
        WindowGroup {
            RootView()
                .environment(container)
                .tint(Theme.wasserblau)
        }
        .modelContainer(modelContainer)
    }
}
