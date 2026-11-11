// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE

import SwiftData
import SwiftUI
import UIKit

/// Bildschirm „Heute“: Menge, Ziel, Fortschritt, Bluetooth-Status, letzter Schluck.
struct HeuteView: View {
    let nutzer: AngemeldeterNutzer
    @Environment(AppContainer.self) private var container
    @Environment(\.openURL) private var openURL

    @Query private var eintraege: [DrinkEntry]   // nur heute, neuester zuerst
    @Query private var offene: [DrinkEntry]      // noch nicht hochgeladen

    init(nutzer: AngemeldeterNutzer, heute: Date) {
        self.nutzer = nutzer
        let uid = nutzer.userId
        let von = Tage.start(heute)
        let bis = Tage.ende(heute)
        _eintraege = Query(
            filter: #Predicate<DrinkEntry> { $0.userId == uid && $0.timestamp >= von && $0.timestamp < bis },
            sort: \DrinkEntry.timestamp, order: .reverse)
        _offene = Query(filter: #Predicate<DrinkEntry> { $0.userId == uid && $0.synced == false })
    }

    private var heuteMl: Int { eintraege.reduce(0) { $0 + $1.ml } }
    private var geraete: GeraeteManager { container.geraete }

    /// Tagesziel: 1. aus dem Profil, 2. vom Gerät, 3. Standardwert
    private var ziel: (ml: Int, herkunft: String) {
        if let z = container.profile.profil?.dailyGoalMl { return (z, "aus deinem Profil") }
        if let z = geraete.letzterMesswert?.zielMl { return (z, "vom HydroDesk") }
        return (GoalCalculator.standardZielMl, "Standardwert – bitte Profil ausfüllen")
    }

    var body: some View {
        let ziel = self.ziel
        let anteil = ziel.ml > 0 ? Double(heuteMl) / Double(ziel.ml) : 0
        let erreicht = heuteMl >= ziel.ml

        BildschirmRahmen {
            // ---------------- Große Anzeige: getrunken / Ziel
            Karte {
                VStack(spacing: 12) {
                    ZStack {
                        FortschrittsRing(anteil: anteil, erreicht: erreicht)
                            .frame(width: 220, height: 220)
                        VStack(spacing: 2) {
                            Text(Format.ml(heuteMl)).font(.system(size: 44, weight: .bold, design: .rounded))
                            Text("/ \(Format.ml(ziel.ml)) ml").font(.title3)
                            Text("\(Int(anteil * 100)) %").font(.subheadline).foregroundStyle(.secondary)
                        }
                    }
                    .padding(.vertical, 8)
                    Text(erreicht ? "Ziel erreicht ✓" : "noch \(Format.ml(ziel.ml - heuteMl)) ml")
                        .font(.headline)
                        .foregroundStyle(erreicht ? Theme.zielGruen : Color.primary)
                    Text("Tagesziel \(ziel.herkunft)").font(.footnote).foregroundStyle(.secondary)
                }
                .frame(maxWidth: .infinity)
            }

            geraetKarte

            // ---------------- Letzter Schluck + heutige Einträge
            Karte("Heutige Schlucke") {
                if let letzter = eintraege.first {
                    Text("Zuletzt: +\(Format.ml(letzter.ml)) ml um \(Format.uhrzeit(letzter.timestamp)) Uhr")
                        .font(.headline)
                    ForEach(eintraege.prefix(8)) { e in
                        Divider()
                        HStack {
                            Text("\(Format.uhrzeit(e.timestamp)) Uhr").frame(maxWidth: .infinity, alignment: .leading)
                            Text(e.device).font(.footnote).foregroundStyle(.secondary)
                                .frame(maxWidth: .infinity, alignment: .leading)
                            Text("+\(Format.ml(e.ml)) ml" + ((e.synced || nutzer.offline) ? "" : " ⟳"))
                        }
                    }
                    if eintraege.count > 8 {
                        Text("… und \(eintraege.count - 8) weitere").font(.footnote).foregroundStyle(.secondary)
                    }
                } else {
                    Text("Heute noch nichts getrunken.")
                }
            }

            // ---------------- Sync-Hinweis
            Text(syncText)
                .font(.footnote)
                .foregroundStyle(.secondary)
                .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    private var syncText: String {
        if nutzer.offline { return "Offline-Modus: Einträge werden nur auf diesem iPhone gespeichert." }
        if let meldung = container.drinks.letzteSyncMeldung { return meldung }
        if offene.isEmpty { return "✓ Alle Einträge sind in Supabase gespeichert." }
        return "⟳ \(offene.count) Einträge werden hochgeladen, sobald Internet da ist."
    }

    // ---------------- Bluetooth / Gerät
    private var geraetKarte: some View {
        let status = geraete.status
        let demo = geraete.demoModus
        return Karte(demo ? "HydroDesk (Demo-Modus)" : "HydroDesk") {
            HStack(spacing: 8) {
                Circle().fill(statusFarbe(status)).frame(width: 14, height: 14)
                Text(status.text).font(.headline)
            }
            if let messwert = geraete.letzterMesswert {
                Text("Gerät meldet: \(messwert.rohtext)" + (messwert.akkuProzent.map { " · Akku \($0) %" } ?? ""))
                    .font(.footnote)
            }
            if status == .suchen && !demo {
                Text("Tipp: Der HydroDesk ist nur kurz nach dem Trinken bzw. Einschalten sichtbar. "
                    + "Notfalls das Gerät kurz aus- und einschalten.")
                    .font(.footnote)
            }
            if status == .keineBerechtigung && !demo {
                Text("Ohne Bluetooth-Berechtigung kann die App das Gerät nicht finden.")
                    .font(.footnote)
                    .foregroundStyle(.red)
                Button("iPhone-Einstellungen öffnen") {
                    if let url = URL(string: UIApplication.openSettingsURLString) { openURL(url) }
                }
                .buttonStyle(.bordered)
            }
            if status == .bluetoothAus && !demo {
                Text("Bluetooth ist ausgeschaltet. Bitte in den iPhone-Einstellungen oder im Kontrollzentrum einschalten.")
                    .font(.footnote)
            }
            HStack {
                if status.aktiv {
                    Button("Trennen") { geraete.trennen() }.buttonStyle(.bordered)
                } else {
                    Button(status == .bluetoothAus && !demo ? "Erneut versuchen" : "Verbinden") {
                        geraete.verbinden()
                    }
                    .buttonStyle(.borderedProminent)
                }
                if demo && status == .demo {
                    Button("Schluck simulieren (+200 ml)") { geraete.schluckSimulieren() }
                        .buttonStyle(.borderedProminent)
                }
            }
            .padding(.top, 4)
        }
    }

    /// Farbiger Punkt: grün = verbunden, blau = suchen, orange = Problem, grau = getrennt.
    private func statusFarbe(_ status: VerbindungsStatus) -> Color {
        switch status {
        case .verbunden, .demo: return Theme.zielGruen
        case .suchen, .verbinden: return Theme.wasserBlau
        case .keineBerechtigung, .bluetoothAus: return Theme.warnOrange
        case .getrennt: return .gray
        }
    }
}

/// Runder Fortschrittsring: blau, bei erreichtem Ziel grün.
struct FortschrittsRing: View {
    let anteil: Double
    let erreicht: Bool

    var body: some View {
        ZStack {
            Circle().stroke(Color.secondary.opacity(0.2), lineWidth: 18)
            Circle()
                .trim(from: 0, to: min(max(anteil, 0), 1))
                .stroke(erreicht ? Theme.zielGruen : Theme.wasserBlau,
                        style: StrokeStyle(lineWidth: 18, lineCap: .round))
                .rotationEffect(.degrees(-90))
                .animation(.easeOut(duration: 0.4), value: anteil)
        }
    }
}
