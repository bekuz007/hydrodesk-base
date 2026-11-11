// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE

import SwiftData
import SwiftUI

/// Bildschirm „Heute“ (Hauptscreen): 1. Fortschrittsring, 2. Gerätekarte, 3. heutige Schlucke, 4. Sync-Zeile.
struct HeuteView: View {
    let nutzer: AngemeldeterNutzer
    /// Wechselt zum Tab „Profil“ (für den Link „Standardwert – bitte Profil ausfüllen“)
    var zumProfil: () -> Void = {}
    @Environment(AppContainer.self) private var container

    @Query private var eintraege: [DrinkEntry]   // nur heute, neuester zuerst
    @Query private var offene: [DrinkEntry]      // noch nicht hochgeladen

    /// So viele Zeilen zeigt die Liste höchstens, dann „… und 3 weitere“.
    private let maxZeilen = 8

    init(nutzer: AngemeldeterNutzer, heute: Date, zumProfil: @escaping () -> Void = {}) {
        self.nutzer = nutzer
        self.zumProfil = zumProfil
        let uid = nutzer.userId
        let von = Tage.start(heute)
        let bis = Tage.ende(heute)
        _eintraege = Query(
            filter: #Predicate<DrinkEntry> { $0.userId == uid && $0.timestamp >= von && $0.timestamp < bis },
            sort: \DrinkEntry.timestamp, order: .reverse)
        _offene = Query(filter: #Predicate<DrinkEntry> { $0.userId == uid && $0.synced == false })
    }

    private var heuteMl: Int { eintraege.reduce(0) { $0 + $1.ml } }

    /// Tagesziel: 1. aus dem Profil, 2. vom Gerät, 3. Standardwert
    private var ziel: (ml: Int, herkunft: ZielHerkunft) {
        let p = container.profile.profil
        return ZielAuswahl.bestimmen(
            profilZielMl: p?.dailyGoalMl, gewichtKg: p?.weightKg, groesseCm: p?.heightCm,
            geraetZielMl: container.geraete.letzterMesswert?.zielMl)
    }

    var body: some View {
        let ziel = self.ziel
        let erreicht = heuteMl >= ziel.ml

        BildschirmRahmen {
            fortschrittKarte(ziel: ziel, erreicht: erreicht)
            GeraeteKarte(zielErreicht: erreicht)
            schluckeKarte
            syncZeile
        }
    }

    // ---------------- 1. Fortschritt
    private func fortschrittKarte(ziel: (ml: Int, herkunft: ZielHerkunft), erreicht: Bool) -> some View {
        Karte {
            VStack(spacing: 12) {
                FortschrittsRing(getrunkenMl: heuteMl, zielMl: ziel.ml)
                    .padding(.top, 4)
                Lichtlinie(farbe: erreicht ? .gruen : .blau)
                    .padding(.vertical, 4)
                if erreicht {
                    Label("Ziel erreicht", systemImage: "checkmark.circle.fill")
                        .font(.headline)
                        .foregroundStyle(Theme.zielgruen)
                } else {
                    Text("noch \(Format.mlEinheit(ziel.ml - heuteMl))").font(.headline)
                }
                if ziel.herkunft == .standard {
                    Button(action: zumProfil) {
                        HStack(spacing: 4) {
                            Text(ziel.herkunft.text)
                            Image(systemName: "chevron.right").imageScale(.small)
                        }
                        .font(.footnote.weight(.semibold))
                        .foregroundStyle(Theme.wasserblau)
                        .frame(minHeight: Theme.tippflaeche)
                    }
                    .accessibilityHint("Öffnet das Profil")
                } else {
                    Text(ziel.herkunft.text).font(.footnote).foregroundStyle(.secondary)
                }
            }
            .frame(maxWidth: .infinity)
        }
    }

    // ---------------- 3. Heutige Schlucke
    private var schluckeKarte: some View {
        Karte("Heutige Schlucke") {
            if let letzter = eintraege.first {
                Text("Zuletzt: +\(Format.mlEinheit(letzter.ml)) um \(Format.uhrzeitUhr(letzter.timestamp))")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                VStack(spacing: 0) {
                    ForEach(eintraege.prefix(maxZeilen)) { e in
                        Divider()
                        SchluckZeile(eintrag: e, nochNichtHochgeladen: !e.synced && !nutzer.offline)
                    }
                }
                if eintraege.count > maxZeilen {
                    Text("… und \(eintraege.count - maxZeilen) weitere")
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                }
            } else {
                LeerZustand(symbol: "drop", text: "Heute noch nichts getrunken.")
            }
        }
    }

    // ---------------- 4. Sync-Zeile
    private var syncZeile: some View {
        let zustand = SyncZustand.bestimmen(offlineKonto: nutzer.offline, offene: offene.count)
        // Schlägt der Abgleich fehl, steht hier die Fehlermeldung statt des normalen Texts
        let meldung = nutzer.offline ? nil : container.drinks.letzteSyncMeldung
        return SyncZeile(zustand: zustand, textUeberschreiben: meldung)
    }
}

/// Eine Zeile der Schluckliste: Uhrzeit, Quelle, Menge (+ Sync-Symbol, solange nicht hochgeladen). Mind. 40 pt hoch.
private struct SchluckZeile: View {
    let eintrag: DrinkEntry
    let nochNichtHochgeladen: Bool

    var body: some View {
        HStack(spacing: 12) {
            Text(Format.uhrzeitUhr(eintrag.timestamp))
                .font(.body)
                .monospacedDigit()
            Text(eintrag.device)
                .font(.subheadline)
                .foregroundStyle(.secondary)
            Spacer(minLength: 8)
            if nochNichtHochgeladen {
                Image(systemName: "arrow.triangle.2.circlepath")
                    .font(.footnote)
                    .foregroundStyle(.secondary)
                    .accessibilityLabel("noch nicht hochgeladen")
            }
            Text("+\(Format.mlEinheit(eintrag.ml))")
                .font(.body.weight(.semibold))
                .foregroundStyle(Theme.wasserblau)
                .monospacedDigit()
        }
        .frame(minHeight: 40)
        .accessibilityElement(children: .combine)
    }
}
