// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE

import SwiftData
import SwiftUI

/// Tagesseite (aus dem Verlauf oder „… und N weitere“ auf Heute): Zusammenfassung des Tages und
/// ALLE Einträge dieses Tages, neuester zuerst. Daten aus der lokalen Datenbank (SwiftData),
/// gefiltert nach Nutzer:in und den Tagesgrenzen in der Ortszeit des Handys.
struct TagDetailView: View {
    let nutzer: AngemeldeterNutzer
    let tag: Date
    @Environment(AppContainer.self) private var container
    @Query private var eintraege: [DrinkEntry]

    init(nutzer: AngemeldeterNutzer, tag: Date) {
        self.nutzer = nutzer
        self.tag = tag
        let uid = nutzer.userId
        let von = Tage.start(tag)
        let bis = Tage.ende(tag)
        _eintraege = Query(
            filter: #Predicate<DrinkEntry> { $0.userId == uid && $0.timestamp >= von && $0.timestamp < bis },
            sort: \DrinkEntry.timestamp, order: .reverse)
    }

    var body: some View {
        let ziel = container.aktuellesZielMl
        let uebersicht = TagesUebersicht(mengenMl: eintraege.map(\.ml), zielMl: ziel)

        BildschirmRahmen {
            zusammenfassung(uebersicht)
            Karte("Alle Einträge") {
                if eintraege.isEmpty {
                    LeerZustand(symbol: "drop", text: "An diesem Tag gibt es keine Einträge.")
                } else {
                    VStack(spacing: 0) {
                        ForEach(eintraege) { e in
                            Divider()
                            SchluckZeile(eintrag: e, nochNichtHochgeladen: !e.synced && !nutzer.offline)
                        }
                    }
                }
            }
        }
        .navigationTitle(Format.datumTitel(tag))
        .navigationBarTitleDisplayMode(.inline)
    }

    private func zusammenfassung(_ u: TagesUebersicht) -> some View {
        Karte {
            VStack(alignment: .leading, spacing: 8) {
                HStack(alignment: .firstTextBaseline, spacing: 6) {
                    Text(Format.ml(u.totalMl))
                        .font(.system(.title, design: .rounded).weight(.bold))
                        .monospacedDigit()
                    Text("/ \(Format.mlEinheit(u.zielMl))")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                        .monospacedDigit()
                    Spacer(minLength: 8)
                    Text(Format.prozent(u.prozent))
                        .font(.subheadline.weight(.semibold))
                        .foregroundStyle(u.erreicht ? Theme.zielgruen : Theme.wasserblau)
                        .monospacedDigit()
                }
                FortschrittsBalken(getrunkenMl: u.totalMl, zielMl: u.zielMl)
                HStack {
                    Text(u.schluckeText).font(.footnote).foregroundStyle(.secondary)
                    Spacer(minLength: 8)
                    if u.erreicht {
                        Label("Ziel erreicht", systemImage: "checkmark.circle.fill")
                            .font(.footnote.weight(.semibold))
                            .foregroundStyle(Theme.zielgruen)
                    }
                }
            }
        }
        .accessibilityElement(children: .combine)
    }
}
