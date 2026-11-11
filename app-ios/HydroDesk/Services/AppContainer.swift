// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE

import Foundation
import Observation
import SwiftData

/// „Manuelle Dependency Injection“: erzeugt alle Dienste genau einmal (kein Framework nötig).
/// Die Oberfläche holt sich den Container mit `@Environment(AppContainer.self)`.
@MainActor
@Observable
final class AppContainer {
    let settings: AppSettings
    let remote: RemoteService?
    let auth: AuthService
    let profile: ProfileService
    let drinks: DrinkService
    let geraete: GeraeteManager
    let ble: HydroBleManager
    let demo: DemoGeraet

    /// Heutiges Datum (Beginn des Tages) – ändert sich nach Mitternacht, dann baut sich „Heute“ neu auf.
    private(set) var heute: Date = Tage.start()

    init(modelContext: ModelContext) {
        let settings = AppSettings()
        let remote = RemoteService(url: Konfiguration.supabaseURL, key: Konfiguration.supabaseAnonKey)
        let auth = AuthService(remote: remote, settings: settings)
        let drinks = DrinkService(context: modelContext, settings: settings, remote: remote)
        let ble = HydroBleManager()
        let demo = DemoGeraet()

        self.settings = settings
        self.remote = remote
        self.auth = auth
        self.profile = ProfileService(remote: remote, settings: settings)
        self.drinks = drinks
        self.ble = ble
        self.demo = demo
        self.geraete = GeraeteManager(ble: ble, demo: demo, settings: settings, auth: auth, drinks: drinks)
    }

    /// Prüft, ob ein neuer Tag begonnen hat.
    func tagPruefen() {
        let jetzt = Tage.start()
        if jetzt != heute { heute = jetzt }
    }
}

/// Liest Supabase-URL und Key aus der Info.plist.
/// Dort stehen `$(SUPABASE_URL)` und `$(SUPABASE_ANON_KEY)`, die Xcode beim Bauen aus
/// `Config/Secrets.xcconfig` einsetzt. Die Werte stehen NICHT im Quellcode und nicht auf GitHub.
enum Konfiguration {
    static var supabaseURL: String { wert("SupabaseURL") }
    static var supabaseAnonKey: String { wert("SupabaseAnonKey") }

    private static func wert(_ schluessel: String) -> String {
        let roh = Bundle.main.object(forInfoDictionaryKey: schluessel) as? String ?? ""
        // Nicht ersetzte Platzhalter (z. B. "$(SUPABASE_URL)") zählen als „nicht gesetzt“
        return roh.hasPrefix("$(") ? "" : roh.trimmingCharacters(in: .whitespacesAndNewlines)
    }
}
