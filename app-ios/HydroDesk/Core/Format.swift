// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE

import Foundation

/// Kleine Hilfsfunktionen für deutsche Zahlen- und Datumsanzeige.
enum Format {
    static let deutsch = Locale(identifier: "de_DE")

    /// 1250 → „1.250“ (deutscher Tausenderpunkt, wie auf dem Display des Geräts)
    static func ml(_ wert: Int) -> String {
        let f = NumberFormatter()
        f.locale = deutsch
        f.numberStyle = .decimal
        f.usesGroupingSeparator = true
        return f.string(from: NSNumber(value: wert)) ?? String(wert)
    }

    /// Zahl mit fester Anzahl Nachkommastellen und Komma: 1.845 → „1,85“
    /// (kaufmännisch gerundet, unabhängig von Systemeinstellungen)
    static func dezimal(_ wert: Double, stellen: Int) -> String {
        let faktor = pow(10.0, Double(stellen))
        let gerundet = (wert * faktor).rounded() / faktor
        return String(format: "%.\(stellen)f", gerundet).replacingOccurrences(of: ".", with: ",")
    }

    /// 1250 → „1.250 ml“ (Leerzeichen vor der Einheit)
    static func mlEinheit(_ wert: Int) -> String { ml(wert) + " ml" }

    /// 45 → „45 %“ (Leerzeichen vor dem Prozentzeichen)
    static func prozent(_ wert: Int) -> String { "\(wert) %" }

    /// Liter mit einer Nachkommastelle: 1250 → „1,3 l“
    static func liter(_ ml: Int) -> String {
        dezimal(Double(ml) / 1000.0, stellen: 1) + " l"
    }

    private static func formatter(_ muster: String) -> DateFormatter {
        let f = DateFormatter()
        f.locale = deutsch
        f.dateFormat = muster
        return f
    }

    /// Zeitpunkt → „14:32“
    static func uhrzeit(_ datum: Date) -> String { formatter("HH:mm").string(from: datum) }

    /// Zeitpunkt → „14:32 Uhr“
    static func uhrzeitUhr(_ datum: Date) -> String { uhrzeit(datum) + " Uhr" }

    /// Tag → „Dienstag, 6. Oktober“
    static func datumLang(_ datum: Date) -> String { formatter("EEEE, d. MMMM").string(from: datum) }

    /// Tag → „Mo, 9. Nov.“ (abgekürzt, Wochentag ohne Punkt)
    static func datumKurz(_ datum: Date) -> String {
        wochentagKurz(datum) + ", " + formatter("d. MMM").string(from: datum)
    }

    /// Tag → „Di“
    static func wochentagKurz(_ datum: Date) -> String {
        var s = formatter("EE").string(from: datum)
        if s.hasSuffix(".") { s.removeLast() }
        return s
    }
}

/// Tagesgrenzen in der Zeitzone des Handys.
enum Tage {
    /// Beginn des Tages (00:00 Uhr), in dem `datum` liegt.
    static func start(_ datum: Date = Date(), kalender: Calendar = .current) -> Date {
        kalender.startOfDay(for: datum)
    }

    /// Beginn des nächsten Tages (Ende ist exklusiv).
    static func ende(_ datum: Date = Date(), kalender: Calendar = .current) -> Date {
        kalender.date(byAdding: .day, value: 1, to: start(datum, kalender: kalender)) ?? datum.addingTimeInterval(86_400)
    }

    static func vor(tage: Int, _ datum: Date = Date(), kalender: Calendar = .current) -> Date {
        kalender.date(byAdding: .day, value: -tage, to: start(datum, kalender: kalender)) ?? datum
    }

    /// Datum als Text „2026-11-11“ (Ortszeit) – dient als Schlüssel für Tagessummen.
    static func schluessel(_ datum: Date = Date(), kalender: Calendar = .current) -> String {
        let c = kalender.dateComponents([.year, .month, .day], from: datum)
        return String(format: "%04d-%02d-%02d", c.year ?? 0, c.month ?? 0, c.day ?? 0)
    }
}
