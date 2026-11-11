// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE

import XCTest
#if canImport(HydroDeskCore)
@testable import HydroDeskCore
#else
@testable import HydroDesk
#endif

final class BlePayloadParserTests: XCTestCase {

    func testTextFormatDerFirmware() throws {
        let wert = try XCTUnwrap(BlePayloadParser.parse("1250/2750 ml"))
        XCTAssertEqual(wert.heuteMl, 1250)
        XCTAssertEqual(wert.zielMl, 2750)
        XCTAssertNil(wert.akkuProzent)
        XCTAssertEqual(wert.rohtext, "1250/2750 ml")
    }

    func testTextOhneLeerzeichenUndOhneMl() throws {
        let wert = try XCTUnwrap(BlePayloadParser.parse("0/2000"))
        XCTAssertEqual(wert.heuteMl, 0)
        XCTAssertEqual(wert.zielMl, 2000)
    }

    func testBytesMitNullzeichenAmEnde() throws {
        let daten = Data("1450/2750 ml".utf8) + Data([0])
        let wert = try XCTUnwrap(BlePayloadParser.parse(daten))
        XCTAssertEqual(wert.heuteMl, 1450)
        XCTAssertEqual(wert.zielMl, 2750)
    }

    func testGrossUndKleinschreibungBeiMl() {
        XCTAssertEqual(BlePayloadParser.parse("100/2000 ML")?.heuteMl, 100)
    }

    func testJsonFormat() throws {
        let wert = try XCTUnwrap(BlePayloadParser.parse(#"{"heute":1250,"ziel":2750,"akku":88}"#))
        XCTAssertEqual(wert.heuteMl, 1250)
        XCTAssertEqual(wert.zielMl, 2750)
        XCTAssertEqual(wert.akkuProzent, 88)
    }

    func testUngueltigeTexteWerdenIgnoriert() {
        XCTAssertNil(BlePayloadParser.parse(""))
        XCTAssertNil(BlePayloadParser.parse("hallo"))
        XCTAssertNil(BlePayloadParser.parse("{kaputt"))
        XCTAssertNil(BlePayloadParser.parse(#"{"ziel":2750}"#))
        XCTAssertNil(BlePayloadParser.parse("12/ml"))
        XCTAssertNil(BlePayloadParser.parse("-5/2000"))
    }

    func testUUIDsSindGueltigUndPassenZurFirmware() {
        XCTAssertNotNil(UUID(uuidString: HydroBleKonstanten.serviceUUID))
        XCTAssertNotNil(UUID(uuidString: HydroBleKonstanten.werteUUID))
        XCTAssertEqual(HydroBleKonstanten.serviceUUID, "4f9a0001-6c1e-4b8e-9d6a-2b7c1e0a4d10")
        XCTAssertEqual(HydroBleKonstanten.werteUUID, "4f9a0002-6c1e-4b8e-9d6a-2b7c1e0a4d10")
        XCTAssertEqual(HydroBleKonstanten.geraetename, "HydroDesk")
    }

    func testStatusTexte() {
        XCTAssertEqual(VerbindungsStatus.suchen.text, "Suchen …")
        XCTAssertEqual(VerbindungsStatus.verbunden.text, "Verbunden")
        XCTAssertEqual(VerbindungsStatus.getrennt.text, "Getrennt")
        XCTAssertTrue(VerbindungsStatus.suchen.aktiv)
        XCTAssertFalse(VerbindungsStatus.getrennt.aktiv)
    }
}
