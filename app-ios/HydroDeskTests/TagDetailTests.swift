import XCTest
#if canImport(HydroDeskCore)
@testable import HydroDeskCore
#else
@testable import HydroDesk
#endif

/// Tests für die Tagesseite im Verlauf: Einträge eines Tages filtern und zusammenfassen.
final class TagDetailTests: XCTestCase {

    private var kalender: Calendar {
        var k = Calendar(identifier: .gregorian)
        k.timeZone = TimeZone(identifier: "Europe/Berlin")!
        k.locale = Locale(identifier: "de_DE")
        return k
    }

    private func zeit(_ t: Int, _ h: Int, _ min: Int = 0, monat: Int = 11) -> Date {
        kalender.date(from: DateComponents(year: 2026, month: monat, day: t, hour: h, minute: min))!
    }

    private typealias E = (zeit: Date, ml: Int)

    func testNurEintraegeDesTagesNeuesterZuerst() {
        let alle: [E] = [
            (zeit(11, 9, 5), 150), (zeit(10, 23, 59), 300), (zeit(11, 14, 32), 200),
            (zeit(12, 0, 0), 250), (zeit(11, 10, 20), 200),
        ]
        let treffer = TagDetailRechner.eintraegeDesTages(alle, zeit: { $0.zeit }, tag: zeit(11, 18), kalender: kalender)
        XCTAssertEqual(treffer.map(\.ml), [200, 200, 150])
        XCTAssertEqual(treffer.map { $0.zeit }, [zeit(11, 14, 32), zeit(11, 10, 20), zeit(11, 9, 5)])
    }

    func testTagesgrenzenMitternachtInklusiveBisExklusive() {
        let alle: [E] = [(zeit(11, 0, 0), 100), (zeit(10, 23, 59), 50), (zeit(12, 0, 0), 70)]
        let treffer = TagDetailRechner.eintraegeDesTages(alle, zeit: { $0.zeit }, tag: zeit(11, 12), kalender: kalender)
        XCTAssertEqual(treffer.map(\.ml), [100])
    }

    func testTagOhneEintraege() {
        let treffer = TagDetailRechner.eintraegeDesTages([E](), zeit: { $0.zeit }, tag: zeit(11, 12), kalender: kalender)
        XCTAssertTrue(treffer.isEmpty)
        let u = TagesUebersicht(mengenMl: [], zielMl: 2750)
        XCTAssertEqual(u.schlucke, 0)
        XCTAssertEqual(u.totalMl, 0)
        XCTAssertEqual(u.prozent, 0)
        XCTAssertFalse(u.erreicht)
    }

    func testUebersichtNormal() {
        let u = TagesUebersicht(mengenMl: [200, 250, 200, 250, 200, 150], zielMl: 2750)
        XCTAssertEqual(u.schlucke, 6)
        XCTAssertEqual(u.totalMl, 1250)
        XCTAssertEqual(u.prozent, 45)
        XCTAssertFalse(u.erreicht)
        XCTAssertEqual(u.schluckeText, "6 Schlucke")
    }

    func testUebersichtZielErreicht() {
        let u = TagesUebersicht(mengenMl: [1000, 1000, 900], zielMl: 2750)
        XCTAssertEqual(u.totalMl, 2900)
        XCTAssertEqual(u.prozent, 105)
        XCTAssertTrue(u.erreicht)
        XCTAssertTrue(TagesUebersicht(mengenMl: [2750], zielMl: 2750).erreicht)   // genau das Ziel zählt
        XCTAssertEqual(TagesUebersicht(mengenMl: [200], zielMl: 2750).schluckeText, "1 Schluck")
    }

    func testTitelDerTagesseite() {
        XCTAssertEqual(Format.datumTitel(zeit(11, 12)), "Mittwoch, 11. Nov.")
        XCTAssertEqual(Format.datumTitel(zeit(9, 12)), "Montag, 9. Nov.")
    }
}
