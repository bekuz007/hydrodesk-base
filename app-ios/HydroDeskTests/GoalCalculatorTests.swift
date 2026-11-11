// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE

import XCTest
#if canImport(HydroDeskCore)
@testable import HydroDeskCore
#else
@testable import HydroDesk
#endif

/// Unit-Tests für das Tagesziel – dieselben Fälle wie GoalCalculatorTest.kt (Android).
final class GoalCalculatorTests: XCTestCase {

    func testBeispielAusDerFirmware_70kg_175cm_ergibt_2750ml() {
        XCTAssertEqual(GoalCalculator.tageszielMl(gewichtKg: 70, groesseCm: 175), 2750)
    }

    func testKoerperoberflaecheNachMosteller() {
        XCTAssertEqual(GoalCalculator.koerperoberflaeche(gewichtKg: 70, groesseCm: 175), 1.845, accuracy: 0.001)
    }

    func testUntereGrenze_1500ml() {
        XCTAssertEqual(GoalCalculator.tageszielMl(gewichtKg: 30, groesseCm: 120), 1500)
    }

    func testObereGrenze_3500ml() {
        XCTAssertEqual(GoalCalculator.tageszielMl(gewichtKg: 250, groesseCm: 230), 3500)
    }

    func testErgebnisIstImmerAuf50Gerundet() {
        for kg in stride(from: 40, through: 120, by: 7) {
            for cm in stride(from: 150, through: 200, by: 9) {
                XCTAssertEqual(GoalCalculator.tageszielMl(gewichtKg: Double(kg), groesseCm: Double(cm)) % 50, 0)
            }
        }
    }

    func testWeitereReferenzwerte() {
        // von Hand nachgerechnet: sqrt(165*60/3600)=1,6583 m² -> 2487,5 ml -> 49,75 -> 50 -> 2500 ml
        XCTAssertEqual(GoalCalculator.tageszielMl(gewichtKg: 60, groesseCm: 165), 2500)
        // sqrt(180*90/3600)=2,1213 m² -> 3181,98 ml -> 63,64 -> 64 -> 3200 ml
        XCTAssertEqual(GoalCalculator.tageszielMl(gewichtKg: 90, groesseCm: 180), 3200)
    }
}
