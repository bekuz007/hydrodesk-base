// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE

import Foundation

/// Zusammenfassung eines Tages (Karte oben auf der Tagesseite im Verlauf).
struct TagesUebersicht: Equatable {
    let schlucke: Int
    let totalMl: Int
    let zielMl: Int

    init(mengenMl: [Int], zielMl: Int) {
        self.schlucke = mengenMl.count
        self.totalMl = mengenMl.reduce(0, +)
        self.zielMl = zielMl
    }

    var prozent: Int { Fortschritt.prozent(getrunkenMl: totalMl, zielMl: zielMl) }
    var erreicht: Bool { totalMl >= zielMl }
    var schluckeText: String { schlucke == 1 ? "1 Schluck" : "\(schlucke) Schlucke" }
}

/// Alle Einträge eines Kalendertages (Ortszeit des Handys) – für die Tagesseite.
enum TagDetailRechner {
    /// Einträge, deren Zeit in diesem Tag liegt (00:00 Uhr inklusive bis 00:00 Uhr des Folgetags exklusive),
    /// neuester zuerst.
    static func eintraegeDesTages<T>(_ alle: [T], zeit: (T) -> Date, tag: Date,
                                     kalender: Calendar = .current) -> [T] {
        let von = Tage.start(tag, kalender: kalender)
        let bis = Tage.ende(tag, kalender: kalender)
        return alle
            .filter { zeit($0) >= von && zeit($0) < bis }
            .sorted { zeit($0) > zeit($1) }
    }
}
