// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE

import Foundation

/// Merkt sich den letzten „heute“-Wert des Geräts (pro Nutzer, Quelle und Tag).
/// In der App steckt dahinter `UserDefaults`, in den Tests ein Dictionary.
protocol GeraetewertSpeicher: AnyObject {
    func letzterWert(schluessel: String, tag: String) -> Int?
    func setLetzterWert(schluessel: String, tag: String, wert: Int)
}

/// SCHLUCK-ERKENNUNG – gleiche Logik wie `DrinkRepository.geraetewertVerarbeiten` in der Android-App.
///
/// Das Gerät schickt immer den Tagesstand („heute“). Jede ERHÖHUNG gegenüber dem
/// letzten Wert ist ein neuer Schluck: neu − alt = getrunkene Menge.
///
///  - Erster Wert des Tages (oder nach Neuinstallation): Vergleich mit der Summe,
///    die für dieses Gerät heute schon gespeichert ist. So werden Schlucke, die
///    ohne Verbindung getrunken wurden, beim Verbinden nachgetragen.
///  - Wert wird KLEINER (Gerät wurde zurückgesetzt): nur neuer Ausgangswert, kein Eintrag.
///  - Änderungen unter 5 ml werden ignoriert.
struct SchluckErkennung {
    static let minSchluckMl = 5

    let speicher: GeraetewertSpeicher

    /// - Parameters:
    ///   - userId: Nutzer-ID (oder „offline“)
    ///   - quelle: „HydroDesk“ oder „Demo“
    ///   - tag: heutiges Datum als Text „2026-11-11“
    ///   - heuteMl: Wert, den das Gerät meldet
    ///   - gespeicherteSumme: wird nur gebraucht (und dann aufgerufen), wenn es noch keinen
    ///     letzten Wert gibt: bisher gespeicherte Summe dieser Quelle für heute
    /// - Returns: erkannte Menge in ml oder `nil` (kein neuer Schluck)
    func verarbeiten(userId: String, quelle: String, tag: String, heuteMl: Int,
                     gespeicherteSumme: () -> Int) -> Int? {
        let schluessel = "\(userId)_\(quelle)"
        let letzter = speicher.letzterWert(schluessel: schluessel, tag: tag)
        let vergleich = letzter ?? gespeicherteSumme()
        speicher.setLetzterWert(schluessel: schluessel, tag: tag, wert: heuteMl)

        let differenz = heuteMl - vergleich
        return differenz >= Self.minSchluckMl ? differenz : nil
    }
}
