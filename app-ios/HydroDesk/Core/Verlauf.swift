// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE

import Foundation

/// Summe eines Tages (wird aus den Einträgen berechnet, keine eigene Tabelle).
struct TagesSumme: Equatable, Identifiable {
    var tag: Date          // Beginn des Tages
    var schluessel: String // „2026-11-11“
    var totalMl: Int
    var schlucke: Int
    var id: String { schluessel }
}

/// Ein Balken im Wochen-Diagramm.
struct TagesBalken: Equatable, Identifiable {
    var tag: Date
    var ml: Int
    var id: Date { tag }
}

/// Rechnet Einträge in Tagessummen und Wochen-Balken um (wie `VerlaufViewModel` in der Android-App).
enum VerlaufRechner {
    /// Summe pro Kalendertag, neuester Tag zuerst.
    static func tagesSummen(eintraege: [(zeit: Date, ml: Int)], kalender: Calendar = .current) -> [TagesSumme] {
        var proTag: [String: TagesSumme] = [:]
        for e in eintraege {
            let tag = Tage.start(e.zeit, kalender: kalender)
            let key = Tage.schluessel(e.zeit, kalender: kalender)
            var summe = proTag[key] ?? TagesSumme(tag: tag, schluessel: key, totalMl: 0, schlucke: 0)
            summe.totalMl += e.ml
            summe.schlucke += 1
            proTag[key] = summe
        }
        return proTag.values.sorted { $0.schluessel > $1.schluessel }
    }

    /// Die letzten 7 Tage (ältester zuerst) – auch Tage ohne Eintrag (dann 0 ml).
    static func wochenBalken(summen: [TagesSumme], heute: Date = Date(), kalender: Calendar = .current) -> [TagesBalken] {
        let proTag = Dictionary(uniqueKeysWithValues: summen.map { ($0.schluessel, $0.totalMl) })
        return (0..<7).reversed().map { vor in
            let tag = Tage.vor(tage: vor, heute, kalender: kalender)
            return TagesBalken(tag: tag, ml: proTag[Tage.schluessel(tag, kalender: kalender)] ?? 0)
        }
    }
}
