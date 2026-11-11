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

    /// Tagesziel wie auf „Heute“: Profil (mit Gewicht und Größe) → Gerät → Standardwert
    private var ziel: Int {
        let p = container.profile.profil
        return ZielAuswahl.bestimmen(
            profilZielMl: p?.dailyGoalMl, gewichtKg: p?.weightKg, groesseCm: p?.heightCm,
            geraetZielMl: container.geraete.letzterMesswert?.zielMl).ml
    }

    var body: some View {
        let summen = VerlaufRechner.tagesSummen(eintraege: eintraege.map { (zeit: $0.timestamp, ml: $0.ml) })
        let woche = VerlaufRechner.wochenBalken(summen: summen, heute: heute)
        let ziel = self.ziel

        BildschirmRahmen {
            if summen.isEmpty {
                Karte {
                    LeerZustand(symbol: "chart.bar",
                                text: "Noch keine Einträge. Verbinde den HydroDesk oder schalte den Demo-Modus ein.")
                }
            } else {
                Karte("Letzte 7 Tage") {
                    WochenDiagramm(woche: woche, zielMl: ziel)
                    Text("Gestrichelte Linie = Tagesziel (\(Format.mlEinheit(ziel))), grün = Ziel erreicht")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                Text("Letzte 30 Tage")
                    .font(.footnote)
                    .textCase(.uppercase)
                    .foregroundStyle(.secondary)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(.horizontal, 4)
                    .padding(.top, 4)
                    .accessibilityAddTraits(.isHeader)

                ForEach(summen) { tag in
                    TagesZeile(tag: tag, zielMl: ziel)
                }
            }
        }
    }
}

/// Balkendiagramm (Swift Charts) mit gestrichelter Ziel-Linie. Balken blau, bei erreichtem Ziel grün;
/// über den Balken steht der Wert in Litern („2,1 l“).
struct WochenDiagramm: View {
    let woche: [TagesBalken]
    let zielMl: Int

    var body: some View {
        // Höchster Wert bestimmt die Skala (mindestens das Ziel, plus 25 % Luft für die Werte über den Balken)
        let hoechster = Double(max(zielMl, woche.map(\.ml).max() ?? 0, 1)) * 1.25

        Chart {
            ForEach(woche) { balken in
                BarMark(
                    x: .value("Tag", Format.wochentagKurz(balken.tag)),
                    y: .value("Getrunken (ml)", balken.ml)
                )
                .foregroundStyle(balken.ml >= zielMl ? Theme.zielgruen : Theme.wasserblau)
                .cornerRadius(2)
                .annotation(position: .top, spacing: 2) {
                    if balken.ml > 0 {
                        Text(Format.liter(balken.ml))
                            .font(.caption2.weight(.semibold))
                            .foregroundStyle(.primary)
                            .monospacedDigit()
                    }
                }
                .accessibilityLabel(Format.datumKurz(balken.tag))
                .accessibilityValue(Format.mlEinheit(balken.ml) + (balken.ml >= zielMl ? ", Ziel erreicht" : ""))
            }
            RuleMark(y: .value("Ziel", zielMl))
                .lineStyle(StrokeStyle(lineWidth: 1.5, dash: [4, 3]))
                .foregroundStyle(Color.primary)
        }
        .chartYScale(domain: 0...hoechster)
        .chartYAxis(.hidden)
        .frame(height: 200)
    }
}

/// Karte je Tag: Titel („Montag, 9. November“), „11 Schlucke · 2.800 ml“, Häkchen bei erreichtem Ziel, schmaler Balken.
private struct TagesZeile: View {
    let tag: TagesSumme
    let zielMl: Int

    var body: some View {
        let erreicht = tag.totalMl >= zielMl
        Karte {
            VStack(alignment: .leading, spacing: 6) {
                Text(Format.datumLang(tag.tag)).font(.body.weight(.semibold))
                HStack(spacing: 6) {
                    Text(tag.schlucke == 1 ? "1 Schluck" : "\(tag.schlucke) Schlucke")
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                    Text("·").font(.footnote).foregroundStyle(.secondary)
                    Text(Format.mlEinheit(tag.totalMl))
                        .font(.footnote.weight(.semibold))
                        .foregroundStyle(erreicht ? Theme.zielgruen : Theme.wasserblau)
                        .monospacedDigit()
                    if erreicht {
                        Image(systemName: "checkmark.circle.fill")
                            .font(.footnote)
                            .foregroundStyle(Theme.zielgruen)
                            .accessibilityLabel("Ziel erreicht")
                    }
                }
                FortschrittsBalken(getrunkenMl: tag.totalMl, zielMl: zielMl)
                    .padding(.top, 2)
            }
        }
        .accessibilityElement(children: .combine)
    }
}
