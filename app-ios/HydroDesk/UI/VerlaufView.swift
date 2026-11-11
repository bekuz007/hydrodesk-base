// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE

import Charts
import SwiftData
import SwiftUI

/// Bildschirm „Verlauf“: Balkendiagramm der letzten 7 Tage (Swift Charts) + Liste pro Tag (30 Tage).
struct VerlaufView: View {
    let nutzer: AngemeldeterNutzer
    @Environment(AppContainer.self) private var container
    @Query private var eintraege: [DrinkEntry]   // letzte 30 Tage
    private let heute: Date

    init(nutzer: AngemeldeterNutzer, heute: Date) {
        self.nutzer = nutzer
        self.heute = heute
        let uid = nutzer.userId
        let von = Tage.vor(tage: 29, heute)
        _eintraege = Query(filter: #Predicate<DrinkEntry> { $0.userId == uid && $0.timestamp >= von },
                           sort: \DrinkEntry.timestamp, order: .reverse)
    }

    private var ziel: Int { container.profile.profil?.dailyGoalMl ?? GoalCalculator.standardZielMl }

    var body: some View {
        let summen = VerlaufRechner.tagesSummen(eintraege: eintraege.map { (zeit: $0.timestamp, ml: $0.ml) })
        let woche = VerlaufRechner.wochenBalken(summen: summen, heute: heute)
        let ziel = self.ziel

        BildschirmRahmen {
            Karte("Letzte 7 Tage") {
                WochenDiagramm(woche: woche, zielMl: ziel)
                Text("Gestrichelte Linie = Tagesziel (\(Format.ml(ziel)) ml), grün = Ziel erreicht")
                    .font(.footnote)
                    .foregroundStyle(.secondary)
            }

            if summen.isEmpty {
                Text("Noch keine Einträge. Verbinde den HydroDesk oder schalte den Demo-Modus ein.")
                    .frame(maxWidth: .infinity, alignment: .leading)
            }
            ForEach(summen) { tag in
                TagesZeile(tag: tag, zielMl: ziel)
            }
        }
    }
}

/// Balkendiagramm mit gestrichelter Ziel-Linie (Swift Charts).
struct WochenDiagramm: View {
    let woche: [TagesBalken]
    let zielMl: Int

    var body: some View {
        // Höchster Wert bestimmt die Skala (mindestens das Ziel, plus 10 % Luft nach oben)
        let hoechster = Double(max(zielMl, woche.map(\.ml).max() ?? 0, 1)) * 1.1

        Chart {
            ForEach(woche) { balken in
                BarMark(
                    x: .value("Tag", Format.wochentagKurz(balken.tag)),
                    y: .value("Getrunken (ml)", balken.ml)
                )
                .foregroundStyle(balken.ml >= zielMl ? Theme.zielGruen : Theme.wasserBlau)
                .cornerRadius(6)
                .annotation(position: .top) {
                    if balken.ml > 0 {
                        Text(Format.liter(balken.ml)).font(.caption2).foregroundStyle(.secondary)
                    }
                }
            }
            RuleMark(y: .value("Ziel", zielMl))
                .lineStyle(StrokeStyle(lineWidth: 2, dash: [6, 4]))
                .foregroundStyle(Theme.zielGruen)
        }
        .chartYScale(domain: 0...hoechster)
        .frame(height: 200)
    }
}

private struct TagesZeile: View {
    let tag: TagesSumme
    let zielMl: Int

    var body: some View {
        let erreicht = tag.totalMl >= zielMl
        Karte {
            HStack {
                VStack(alignment: .leading) {
                    Text(Format.datumLang(tag.tag)).font(.headline)
                    Text("\(tag.schlucke) Schlucke").font(.footnote).foregroundStyle(.secondary)
                }
                Spacer()
                Text("\(Format.ml(tag.totalMl)) ml" + (erreicht ? " ✓" : ""))
                    .font(.headline)
                    .foregroundStyle(erreicht ? Theme.zielGruen : Color.primary)
            }
            ProgressView(value: min(Double(tag.totalMl) / Double(max(zielMl, 1)), 1))
                .tint(erreicht ? Theme.zielGruen : Theme.wasserBlau)
        }
    }
}
