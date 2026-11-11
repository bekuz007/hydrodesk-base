// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE

import Foundation

// Reine Anzeige-Logik (ohne SwiftUI), damit sie auch auf Linux/ohne Simulator getestet werden kann.
// Die Texte stehen so in app-ios/DESIGN_SPEC.md.

/// Woher das Tagesziel kommt (steuert die Zeile unter dem Ring auf „Heute“).
enum ZielHerkunft: Equatable {
    case profil
    case geraet
    case standard

    var text: String {
        switch self {
        case .profil: return "Tagesziel aus deinem Profil"
        case .geraet: return "Tagesziel vom HydroDesk"
        case .standard: return "Standardwert – bitte Profil ausfüllen"
        }
    }
}

enum ZielAuswahl {
    /// 1. berechnet aus dem Profil (nur wenn Gewicht UND Größe eingetragen sind),
    /// 2. vom Gerät gemeldet, 3. Standardwert.
    static func bestimmen(profilZielMl: Int?, gewichtKg: Double?, groesseCm: Int?,
                          geraetZielMl: Int?) -> (ml: Int, herkunft: ZielHerkunft) {
        if let z = profilZielMl, (gewichtKg ?? 0) > 0, (groesseCm ?? 0) > 0 { return (z, .profil) }
        if let z = geraetZielMl, z > 0 { return (z, .geraet) }
        return (GoalCalculator.standardZielMl, .standard)
    }
}

/// Fortschritt in Prozent (kann über 100 liegen: 2.900 von 2.750 ml → 105).
enum Fortschritt {
    static func prozent(getrunkenMl: Int, zielMl: Int) -> Int {
        guard zielMl > 0 else { return 0 }
        return Int((Double(getrunkenMl) / Double(zielMl) * 100).rounded())
    }

    /// 0…1 für Ring und Balken.
    static func anteil(getrunkenMl: Int, zielMl: Int) -> Double {
        guard zielMl > 0 else { return 0 }
        return min(max(Double(getrunkenMl) / Double(zielMl), 0), 1)
    }
}

/// Die drei Sync-Zustände (Zeile unten auf „Heute“ und im Profil).
enum SyncZustand: Equatable {
    case alleGespeichert
    case ausstehend(Int)
    case offline

    static func bestimmen(offlineKonto: Bool, offene: Int) -> SyncZustand {
        if offlineKonto { return .offline }
        return offene > 0 ? .ausstehend(offene) : .alleGespeichert
    }

    /// Zeile unten auf „Heute“.
    var zeilenText: String {
        switch self {
        case .alleGespeichert: return "Alle Einträge sind gespeichert."
        case .ausstehend(let n):
            return n == 1 ? "1 Eintrag wird hochgeladen, sobald Internet da ist."
                          : "\(n) Einträge werden hochgeladen, sobald Internet da ist."
        case .offline: return "Offline-Modus: Einträge werden nur auf diesem iPhone gespeichert."
        }
    }

    /// Wert der Zeile „Synchronisierung“ im Profil.
    var kurzText: String {
        switch self {
        case .alleGespeichert: return "alles hochgeladen"
        case .ausstehend(let n): return n == 1 ? "1 Eintrag wartet" : "\(n) Einträge warten"
        case .offline: return "Offline-Modus"
        }
    }

    /// Zeigt die Zeile das Sync-Symbol (arrow.triangle.2.circlepath)?
    var zeigtSymbol: Bool {
        if case .ausstehend = self { return true }
        return false
    }

    /// Text im Dialog „Abmelden?“ (mit offenen Einträgen oder ohne).
    static func abmeldeText(offene: Int, offlineKonto: Bool) -> String {
        guard offene > 0, !offlineKonto else { return "Deine Daten bleiben gespeichert." }
        return offene == 1
            ? "1 Eintrag ist noch nicht hochgeladen. Er bleibt auf dem iPhone und wird nach der nächsten Anmeldung hochgeladen."
            : "\(offene) Einträge sind noch nicht hochgeladen. Sie bleiben auf dem iPhone und werden nach der nächsten Anmeldung hochgeladen."
    }
}

// MARK: - Gerätekarte (sieben Zustände)

enum LichtlinienFarbe: Equatable { case blau, gruen, rot, aus }
enum StatusFarbe: Equatable { case blau, gruen, orange, grau }

enum GeraeteAktion: Equatable {
    case trennen
    case verbinden
    case erneutVersuchen
    case einstellungenOeffnen
    case schluckSimulieren
}

/// Alles, was die Gerätekarte je nach Zustand anzeigt (Tabelle in DESIGN_SPEC.md).
struct GeraeteKarteModell: Equatable {
    /// Ab so viel Prozent Akku gilt „Akku niedrig“ (Spec nennt keine Zahl → hier 15 %, siehe DESIGN_SPEC.md).
    static let akkuNiedrigGrenze = 15

    let status: VerbindungsStatus
    let demoModus: Bool
    let akkuProzent: Int?
    let zielErreicht: Bool

    var titel: String { demoModus ? "HydroDesk (Demo-Modus)" : "HydroDesk" }
    var statusText: String { status.text }

    var statusFarbe: StatusFarbe {
        switch status {
        case .suchen, .verbinden: return .blau
        case .verbunden, .demo: return .gruen
        case .bluetoothAus, .keineBerechtigung: return .orange
        case .getrennt: return .grau
        }
    }

    var zeigtSpinner: Bool { status == .suchen || status == .verbinden }

    var akkuNiedrig: Bool {
        guard let a = akkuProzent, status == .verbunden || status == .demo else { return false }
        return a <= Self.akkuNiedrigGrenze
    }

    var lichtlinie: LichtlinienFarbe {
        switch status {
        case .suchen, .verbinden: return .blau
        case .verbunden, .demo:
            if akkuNiedrig { return .rot }
            return zielErreicht ? .gruen : .blau
        case .getrennt, .bluetoothAus, .keineBerechtigung: return .aus
        }
    }

    /// Buttons von links nach rechts; der letzte ist der Hauptbutton, wenn mehrere da sind.
    var aktionen: [GeraeteAktion] {
        switch status {
        case .suchen, .verbinden, .verbunden: return [.trennen]
        case .demo: return [.trennen, .schluckSimulieren]
        case .getrennt: return [.verbinden]
        case .bluetoothAus: return [.erneutVersuchen]
        case .keineBerechtigung: return [.einstellungenOeffnen]
        }
    }

    /// Erklärtext unter dem Status (nil = keiner).
    var hinweis: String? {
        switch status {
        case .suchen where !demoModus:
            return "Der HydroDesk ist nur kurz nach dem Trinken bzw. Einschalten sichtbar. "
                + "Notfalls das Gerät kurz aus- und einschalten."
        case .bluetoothAus:
            return "Bitte Bluetooth in den Einstellungen oder im Kontrollzentrum einschalten."
        case .keineBerechtigung:
            return "Ohne Bluetooth-Berechtigung kann die App das Gerät nicht finden."
        default:
            return nil
        }
    }

    var akkuHinweis: String? { akkuNiedrig ? "Akku niedrig – bitte bald laden." : nil }

    /// „Gerät meldet: 1.250 / 2.750 ml“ (nur beim echten Gerät, nicht im Demo-Modus).
    static func meldetText(_ messwert: DeviceReading) -> String {
        if let ziel = messwert.zielMl {
            return "Gerät meldet: \(Format.ml(messwert.heuteMl)) / \(Format.mlEinheit(ziel))"
        }
        return "Gerät meldet: \(Format.mlEinheit(messwert.heuteMl))"
    }

    /// SF-Symbol für den Akku (Rahmen mit Füllung).
    static func akkuSymbol(_ prozent: Int) -> String {
        switch prozent {
        case ..<13: return "battery.0percent"
        case ..<38: return "battery.25percent"
        case ..<63: return "battery.50percent"
        case ..<88: return "battery.75percent"
        default: return "battery.100percent"
        }
    }
}
