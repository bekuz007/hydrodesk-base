// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE

import Foundation

/// Berechnet das Tagesziel aus Körpergewicht und Körpergröße.
///
/// GENAU dieselbe Formel wie in der ESP32-Firmware (`zielBerechnen()` in `wokwi/sketch.ino`)
/// und in der Android-App (`GoalCalculator.kt`):
///  1. Körperoberfläche (KOF) nach Mosteller:  KOF [m²] = Wurzel(cm × kg / 3600)
///  2. Tagesziel = KOF × 1500 ml pro m²
///  3. auf 50 ml runden, Grenzen 1500 … 3500 ml
///
/// Beispiel: 70 kg, 175 cm → KOF 1,845 m² → 2767 ml → 2750 ml
///
/// RICHTWERT, KEINE MEDIZINISCHE EMPFEHLUNG!
enum GoalCalculator {
    static let mlProM2 = 1500.0
    static let zielMinMl = 1500
    static let zielMaxMl = 3500
    /// Wenn noch kein Profil ausgefüllt ist
    static let standardZielMl = 2000

    /// Körperoberfläche in m² (Formel nach Mosteller).
    static func koerperoberflaeche(gewichtKg: Double, groesseCm: Double) -> Double {
        (groesseCm * gewichtKg / 3600.0).squareRoot()
    }

    /// Tagesziel in ml, auf 50 ml gerundet und auf 1500…3500 ml begrenzt.
    /// `.rounded()` rundet 0,5 weg von null – wie `lroundf` in der Firmware.
    static func tageszielMl(gewichtKg: Double, groesseCm: Double) -> Int {
        let kof = koerperoberflaeche(gewichtKg: gewichtKg, groesseCm: groesseCm)
        let ml = Int((kof * mlProM2 / 50.0).rounded()) * 50
        return min(max(ml, zielMinMl), zielMaxMl)
    }
}
