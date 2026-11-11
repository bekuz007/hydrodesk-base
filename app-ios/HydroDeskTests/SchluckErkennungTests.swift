// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE

import XCTest
#if canImport(HydroDeskCore)
@testable import HydroDeskCore
#else
@testable import HydroDesk
#endif

private final class TestSpeicher: GeraetewertSpeicher {
    var werte: [String: Int] = [:]
    func letzterWert(schluessel: String, tag: String) -> Int? { werte["\(schluessel)|\(tag)"] }
    func setLetzterWert(schluessel: String, tag: String, wert: Int) { werte["\(schluessel)|\(tag)"] = wert }
}

/// Schluck-Erkennung: dieselben Regeln wie DrinkRepository.geraetewertVerarbeiten (Android).
final class SchluckErkennungTests: XCTestCase {
    private let tag = "2026-11-11"
    private var speicher = TestSpeicher()
    private var erkennung: SchluckErkennung { SchluckErkennung(speicher: speicher) }

    override func setUp() { speicher = TestSpeicher() }

    private func melde(_ ml: Int, summe: Int = 0, nutzer: String = "u1", quelle: String = "HydroDesk") -> Int? {
        erkennung.verarbeiten(userId: nutzer, quelle: quelle, tag: tag, heuteMl: ml, gespeicherteSumme: { summe })
    }

    func testErsterWertDesTages_wirdAlsNachtragEingetragen() {
        XCTAssertEqual(melde(1250, summe: 0), 1250)
    }

    func testErsterWertMitSchonGespeicherterSumme_nurDieDifferenz() {
        XCTAssertEqual(melde(1450, summe: 1250), 200)
    }

    func testAbDemZweitenWert_zaehltDerLetzteWert_nichtDieSumme() {
        XCTAssertEqual(melde(1250, summe: 0), 1250)
        // Summe in der Datenbank ist jetzt 1250, aber der zuletzt gemeldete Wert zählt
        XCTAssertEqual(melde(1450, summe: 9999), 200)
        XCTAssertEqual(melde(1700, summe: 9999), 250)
    }

    func testGleicherWert_keinSchluck() {
        _ = melde(1000, summe: 1000)
        XCTAssertNil(melde(1000, summe: 1000))
    }

    func testUnter5ml_wirdIgnoriert() {
        _ = melde(1000, summe: 1000)
        XCTAssertNil(melde(1004))
        // 4 ml wurden "verbraucht": der Vergleichswert ist jetzt 1004, nicht 1000
        XCTAssertEqual(melde(1009), 5)
    }

    func testGenau5ml_wirdErkannt() {
        _ = melde(1000, summe: 1000)
        XCTAssertEqual(melde(1005), 5)
    }

    func testWertSinkt_GeraetZurueckgesetzt_keinEintrag_aberNeuerAusgangswert() {
        _ = melde(1000, summe: 1000)
        XCTAssertNil(melde(0))                    // Reset am Gerät
        XCTAssertEqual(melde(250), 250)           // danach zählt wieder ab 0
    }

    func testNutzerUndQuelleSindGetrennt() {
        _ = melde(500, nutzer: "u1", quelle: "HydroDesk")
        XCTAssertEqual(melde(300, nutzer: "u2", quelle: "HydroDesk"), 300)
        XCTAssertEqual(melde(300, nutzer: "u1", quelle: "Demo"), 300)
        XCTAssertEqual(melde(700, nutzer: "u1", quelle: "HydroDesk"), 200)
    }

    func testNeuerTagBeginntNeu() {
        _ = melde(2000, summe: 2000)
        let morgen = erkennung.verarbeiten(userId: "u1", quelle: "HydroDesk", tag: "2026-11-12",
                                           heuteMl: 100, gespeicherteSumme: { 0 })
        XCTAssertEqual(morgen, 100)
    }

    func testSummeWirdNurGebraucht_wennEsNochKeinenLetztenWertGibt() {
        _ = melde(100)
        var aufgerufen = false
        _ = erkennung.verarbeiten(userId: "u1", quelle: "HydroDesk", tag: tag, heuteMl: 200,
                                  gespeicherteSumme: { aufgerufen = true; return 0 })
        XCTAssertFalse(aufgerufen)
    }
}
