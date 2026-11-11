// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE

import XCTest
#if canImport(HydroDeskCore)
@testable import HydroDeskCore
#else
@testable import HydroDesk
#endif

final class LogikTests: XCTestCase {

    private var kalender: Calendar {
        var k = Calendar(identifier: .gregorian)
        k.timeZone = TimeZone(identifier: "Europe/Berlin")!
        return k
    }

    private func datum(_ j: Int, _ m: Int, _ t: Int, _ h: Int = 12, _ min: Int = 0) -> Date {
        kalender.date(from: DateComponents(year: j, month: m, day: t, hour: h, minute: min))!
    }

    // MARK: Format

    func testMlMitDeutschemTausenderpunkt() {
        XCTAssertEqual(Format.ml(1250), "1.250")
        XCTAssertEqual(Format.ml(2750), "2.750")
        XCTAssertEqual(Format.ml(80), "80")
    }

    func testDezimalMitKomma() {
        XCTAssertEqual(Format.dezimal(1.845, stellen: 2), "1,85")   // Zahl gerundet auf 2 Stellen
        XCTAssertEqual(Format.liter(1250), "1,3 l")
    }

    func testTagesSchluessel() {
        XCTAssertEqual(Tage.schluessel(datum(2026, 11, 11), kalender: kalender), "2026-11-11")
        XCTAssertEqual(Tage.schluessel(datum(2026, 1, 5, 23, 59), kalender: kalender), "2026-01-05")
    }

    func testTagesgrenzen() {
        let d = datum(2026, 11, 11, 15, 30)
        XCTAssertEqual(Tage.start(d, kalender: kalender), datum(2026, 11, 11, 0, 0))
        XCTAssertEqual(Tage.ende(d, kalender: kalender), datum(2026, 11, 12, 0, 0))
    }

    // MARK: Verlauf

    func testTagesSummenSortiertNeuesterZuerst() {
        let e: [(zeit: Date, ml: Int)] = [
            (datum(2026, 11, 10, 9), 200),
            (datum(2026, 11, 11, 8), 300),
            (datum(2026, 11, 11, 14), 150),
        ]
        let s = VerlaufRechner.tagesSummen(eintraege: e, kalender: kalender)
        XCTAssertEqual(s.map(\.schluessel), ["2026-11-11", "2026-11-10"])
        XCTAssertEqual(s[0].totalMl, 450)
        XCTAssertEqual(s[0].schlucke, 2)
        XCTAssertEqual(s[1].totalMl, 200)
    }

    func testWochenBalkenHatImmer7TageUndFuelltLueckenMitNull() {
        let e: [(zeit: Date, ml: Int)] = [(datum(2026, 11, 11, 8), 300), (datum(2026, 11, 8, 8), 900)]
        let summen = VerlaufRechner.tagesSummen(eintraege: e, kalender: kalender)
        let b = VerlaufRechner.wochenBalken(summen: summen, heute: datum(2026, 11, 11, 20), kalender: kalender)
        XCTAssertEqual(b.count, 7)
        XCTAssertEqual(Tage.schluessel(b.first!.tag, kalender: kalender), "2026-11-05")
        XCTAssertEqual(Tage.schluessel(b.last!.tag, kalender: kalender), "2026-11-11")
        XCTAssertEqual(b.map(\.ml), [0, 0, 0, 900, 0, 0, 300])
    }

    // MARK: Profil

    func testGewichtMitKommaUndPunkt() {
        XCTAssertEqual(ProfilPruefung.gewicht("72,5"), 72.5)
        XCTAssertEqual(ProfilPruefung.gewicht("72.5"), 72.5)
        XCTAssertNil(ProfilPruefung.gewicht("abc"))
    }

    func testZielVorschau() throws {
        let v = try XCTUnwrap(ProfilPruefung.zielVorschau(gewichtText: "70", groesseText: "175"))
        XCTAssertEqual(v.zielMl, 2750)
        XCTAssertEqual(v.kof, 1.845, accuracy: 0.001)
        XCTAssertNil(ProfilPruefung.zielVorschau(gewichtText: "20", groesseText: "175"))
        XCTAssertNil(ProfilPruefung.zielVorschau(gewichtText: "70", groesseText: ""))
    }

    func testProfilFehlermeldungen() {
        XCTAssertEqual(ProfilPruefung.fehler(name: " ", gewichtText: "70", groesseText: "175"), "Bitte einen Namen eingeben.")
        XCTAssertEqual(ProfilPruefung.fehler(name: "A", gewichtText: "20", groesseText: "175"), "Gewicht bitte zwischen 30 und 250 kg angeben.")
        XCTAssertEqual(ProfilPruefung.fehler(name: "A", gewichtText: "70", groesseText: "300"), "Größe bitte zwischen 120 und 230 cm angeben.")
        XCTAssertNil(ProfilPruefung.fehler(name: "A", gewichtText: "70", groesseText: "175"))
    }

    // MARK: Fehlertexte

    func testAuthFehlerUebersetzung() {
        XCTAssertEqual(AuthFehler.uebersetzen("Invalid login credentials"), "E-Mail oder Passwort ist falsch.")
        XCTAssertEqual(AuthFehler.uebersetzen("User already registered"), "Für diese E-Mail gibt es schon ein Konto. Bitte anmelden.")
        XCTAssertEqual(AuthFehler.uebersetzen("Password should be at least 6 characters"), "Das Passwort ist zu kurz (mindestens 6 Zeichen).")
        XCTAssertEqual(AuthFehler.uebersetzen("The Internet connection appears to be offline."), "Keine Verbindung zum Server. Bitte Internet prüfen.")
        XCTAssertEqual(AuthFehler.uebersetzen("kaputt"), "Fehler: kaputt")
    }
}
