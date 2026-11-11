// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE

import Foundation
import Observation

/// Kleine Einstellungen, die auf dem iPhone gespeichert werden (UserDefaults).
/// Für große Datenmengen ist SwiftData da – hier nur einzelne Werte.
@Observable
final class AppSettings: GeraetewertSpeicher {
    @ObservationIgnored private let defaults: UserDefaults

    /// Demo-Modus: simuliert das Gerät, damit die App ohne Hardware vorführbar ist
    private(set) var demoModus: Bool
    /// Modus „Ohne Konto testen“ (Daten bleiben nur auf dem iPhone)
    private(set) var offlineKonto: Bool

    init(defaults: UserDefaults = .standard) {
        self.defaults = defaults
        demoModus = defaults.bool(forKey: Schluessel.demo)
        offlineKonto = defaults.bool(forKey: Schluessel.offline)
    }

    func setDemoModus(_ an: Bool) {
        defaults.set(an, forKey: Schluessel.demo)
        demoModus = an
    }

    func setOfflineKonto(_ an: Bool) {
        defaults.set(an, forKey: Schluessel.offline)
        offlineKonto = an
    }

    /// Profil als JSON zwischenspeichern (damit es auch ohne Internet angezeigt wird)
    var profilJson: String? {
        get { defaults.string(forKey: Schluessel.profil) }
        set { defaults.set(newValue, forKey: Schluessel.profil) }
    }

    // MARK: GeraetewertSpeicher – letzter „heute“-Wert des Geräts pro Quelle und Tag

    func letzterWert(schluessel: String, tag: String) -> Int? {
        guard defaults.string(forKey: "geraet_tag_\(schluessel)") == tag else { return nil }
        return defaults.integer(forKey: "geraet_wert_\(schluessel)")
    }

    func setLetzterWert(schluessel: String, tag: String, wert: Int) {
        defaults.set(tag, forKey: "geraet_tag_\(schluessel)")
        defaults.set(wert, forKey: "geraet_wert_\(schluessel)")
    }

    private enum Schluessel {
        static let demo = "demo_modus"
        static let offline = "offline_konto"
        static let profil = "profil_json"
    }
}
