// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE

import XCTest
#if canImport(HydroDeskCore)
@testable import HydroDeskCore
#else
@testable import HydroDesk
#endif

/// V5: Steuerung per App – Befehle, Status-JSON und Antworten der Firmware.
final class SteuerungTests: XCTestCase {

    func testBefehleWieImSeriellenMonitor() {
        XCTAssertEqual(GeraeteBefehl.profil(gewichtKg: 75, groesseCm: 180).text, "profil 75.0 180")
        XCTAssertEqual(GeraeteBefehl.profil(gewichtKg: 72.46, groesseCm: 168).text, "profil 72.5 168")
        XCTAssertEqual(GeraeteBefehl.tara.text, "tara")
        XCTAssertEqual(GeraeteBefehl.eichen(gramm: 203).text, "eichen 203")
        XCTAssertEqual(GeraeteBefehl.flascheLeer.text, "leer")
        XCTAssertEqual(GeraeteBefehl.flascheVoll.text, "voll")
        XCTAssertEqual(GeraeteBefehl.tagZuruecksetzen.text, "reset")
        XCTAssertEqual(GeraeteBefehl.heuteSetzen(ml: 1250).text, "heute 1250")
        XCTAssertEqual(GeraeteBefehl.heuteSetzen(ml: -5).text, "heute 0")          // nie negativ
        XCTAssertEqual(GeraeteBefehl.heuteSetzen(ml: 99_999).text, "heute 20000")  // Grenze der Firmware
    }

    /// Der Stand, den die App dem Gerät schickt, darf danach NICHT als Schluck zählen.
    func testUebernommenerTagesstandIstKeinSchluck() {
        final class Speicher: GeraetewertSpeicher {
            var werte: [String: Int] = [:]
            func letzterWert(schluessel: String, tag: String) -> Int? { werte["\(schluessel)|\(tag)"] }
            func setLetzterWert(schluessel: String, tag: String, wert: Int) { werte["\(schluessel)|\(tag)"] = wert }
        }
        let e = SchluckErkennung(speicher: Speicher())
        let tag = "2026-11-16"
        // Gerät meldet 800 ml (selbst gezählt)
        XCTAssertNil(e.verarbeiten(userId: "u", quelle: "HydroDesk", tag: tag, heuteMl: 800, gespeicherteSumme: { 800 }))
        // App schickt den Stand der Datenbank (1250 ml), Gerät bestätigt → kein Schluck
        e.uebernehmen(userId: "u", quelle: "HydroDesk", tag: tag, heuteMl: 1250)
        XCTAssertNil(e.verarbeiten(userId: "u", quelle: "HydroDesk", tag: tag, heuteMl: 1250, gespeicherteSumme: { 0 }))
        // Danach echter Schluck auf dem Gerät: +150 ml
        XCTAssertEqual(e.verarbeiten(userId: "u", quelle: "HydroDesk", tag: tag, heuteMl: 1400, gespeicherteSumme: { 0 }), 150)
    }

    func testStatusJsonDerFirmware() throws {
        let json = #"{"heute":1250,"ziel":2750,"g":420,"ruhig":1,"kg":75.0,"cm":180,"leer":312,"voll":1012,"kap":700,"fl":108,"kalib":1,"zu":"MESSEN","akku":-1,"nass":0,"waage":1}"#
        let s = try XCTUnwrap(GeraeteStatus.parse(Data(json.utf8)))
        XCTAssertEqual(s.heuteMl, 1250)
        XCTAssertEqual(s.zielMl, 2750)
        XCTAssertEqual(s.gewichtG, 420)
        XCTAssertTrue(s.ruhig)
        XCTAssertEqual(s.profilKg, 75.0, accuracy: 0.001)
        XCTAssertEqual(s.profilCm, 180)
        XCTAssertEqual(s.leerG, 312)
        XCTAssertEqual(s.vollG, 1012)
        XCTAssertEqual(s.kapazitaetMl, 700)
        XCTAssertEqual(s.flascheMl, 108)
        XCTAssertTrue(s.flascheKalibriert)
        XCTAssertEqual(s.zustand, "MESSEN")
        XCTAssertNil(s.akkuProzent)      // -1 = kein Akku
        XCTAssertFalse(s.nass)
        XCTAssertTrue(s.waageOk)
    }

    func testStatusMitNulZeichenUndNegativemGewicht() throws {
        var daten = Data(#"{"heute":0,"ziel":2000,"g":-3,"ruhig":0,"kg":70.0,"cm":175,"akku":88}"#.utf8)
        daten.append(0)
        let s = try XCTUnwrap(GeraeteStatus.parse(daten))
        XCTAssertEqual(s.gewichtG, -3)
        XCTAssertFalse(s.ruhig)
        XCTAssertEqual(s.akkuProzent, 88)
    }

    func testKaputterStatusGibtNil() {
        XCTAssertNil(GeraeteStatus.parse(Data("1250/2750 ml".utf8)))
        XCTAssertNil(GeraeteStatus.parse(Data(#"{"heute":1}"#.utf8)))   // "ziel" fehlt
    }

    func testProfilVergleich() throws {
        let s = try XCTUnwrap(GeraeteStatus.parse(Data(#"{"heute":0,"ziel":2750,"kg":70.0,"cm":175}"#.utf8)))
        XCTAssertTrue(s.profilPasst(gewichtKg: 70, groesseCm: 175))
        XCTAssertTrue(s.profilPasst(gewichtKg: 70.04, groesseCm: 175))
        XCTAssertFalse(s.profilPasst(gewichtKg: 75, groesseCm: 180))
        XCTAssertFalse(s.profilPasst(gewichtKg: 70, groesseCm: 176))
    }

    func testAntwort() throws {
        let a = try XCTUnwrap(GeraeteAntwort.parse(Data("3|Leer gespeichert: 312 g".utf8)))
        XCTAssertEqual(a.nummer, 3)
        XCTAssertEqual(a.text, "Leer gespeichert: 312 g")
        // "|" im Text bleibt erhalten
        XCTAssertEqual(GeraeteAntwort.parse(Data("4|a|b".utf8))?.text, "a|b")
        XCTAssertNil(GeraeteAntwort.parse(Data("ohne Nummer".utf8)))
    }
}
