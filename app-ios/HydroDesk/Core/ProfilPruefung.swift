// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE

import Foundation

/// Prüfung und Umrechnung der Eingaben im Profil (gleiche Grenzen wie Firmware und Android-App).
enum ProfilPruefung {
    static let gewichtBereich = 30.0...250.0
    static let groesseBereich = 120...230

    /// „72,5“ oder „72.5“ → 72.5
    static func gewicht(_ text: String) -> Double? {
        Double(text.trimmingCharacters(in: .whitespaces).replacingOccurrences(of: ",", with: "."))
    }

    static func groesse(_ text: String) -> Int? {
        Int(text.trimmingCharacters(in: .whitespaces))
    }

    /// Live-Vorschau des Tagesziels (nil = Eingabe unvollständig oder außerhalb der Grenzen).
    static func zielVorschau(gewichtText: String, groesseText: String) -> (zielMl: Int, kof: Double)? {
        guard let kg = gewicht(gewichtText), let cm = groesse(groesseText),
              gewichtBereich.contains(kg), groesseBereich.contains(cm) else { return nil }
        return (GoalCalculator.tageszielMl(gewichtKg: kg, groesseCm: Double(cm)),
                GoalCalculator.koerperoberflaeche(gewichtKg: kg, groesseCm: Double(cm)))
    }

    /// Fehlermeldung oder nil, wenn alles passt.
    static func fehler(name: String, gewichtText: String, groesseText: String) -> String? {
        if name.trimmingCharacters(in: .whitespaces).isEmpty { return "Bitte einen Namen eingeben." }
        guard let kg = gewicht(gewichtText), gewichtBereich.contains(kg) else {
            return "Gewicht bitte zwischen 30 und 250 kg angeben."
        }
        guard let cm = groesse(groesseText), groesseBereich.contains(cm) else {
            return "Größe bitte zwischen 120 und 230 cm angeben."
        }
        return nil
    }
}
