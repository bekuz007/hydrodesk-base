import XCTest
#if canImport(HydroDeskCore)
@testable import HydroDeskCore
#else
@testable import HydroDesk
#endif

/// Tests für die Anzeige-Logik aus dem Design (DESIGN_SPEC.md): Zielherkunft, Sync-Texte, Gerätekarte, Formate.
final class AnzeigeTests: XCTestCase {

    // MARK: Zielherkunft

    func testZielAusProfilNurMitGewichtUndGroesse() {
        let z = ZielAuswahl.bestimmen(profilZielMl: 2750, gewichtKg: 70, groesseCm: 175, geraetZielMl: 3000)
        XCTAssertEqual(z.ml, 2750)
        XCTAssertEqual(z.herkunft, .profil)
        XCTAssertEqual(z.herkunft.text, "Tagesziel aus deinem Profil")
    }

    func testZielVomGeraetWennProfilLeer() {
        let z = ZielAuswahl.bestimmen(profilZielMl: 2000, gewichtKg: nil, groesseCm: nil, geraetZielMl: 2750)
        XCTAssertEqual(z.ml, 2750)
        XCTAssertEqual(z.herkunft, .geraet)
        XCTAssertEqual(z.herkunft.text, "Tagesziel vom HydroDesk")
    }

    func testStandardwert() {
        let z = ZielAuswahl.bestimmen(profilZielMl: nil, gewichtKg: nil, groesseCm: nil, geraetZielMl: nil)
        XCTAssertEqual(z.ml, 2000)
        XCTAssertEqual(z.herkunft, .standard)
        XCTAssertEqual(z.herkunft.text, "Standardwert – bitte Profil ausfüllen")
    }

    // MARK: Fortschritt

    func testProzentWieImDesign() {
        XCTAssertEqual(Fortschritt.prozent(getrunkenMl: 1250, zielMl: 2750), 45)
        XCTAssertEqual(Fortschritt.prozent(getrunkenMl: 2900, zielMl: 2750), 105)
        XCTAssertEqual(Fortschritt.prozent(getrunkenMl: 600, zielMl: 2750), 22)
        XCTAssertEqual(Fortschritt.prozent(getrunkenMl: 0, zielMl: 2000), 0)
        XCTAssertEqual(Fortschritt.prozent(getrunkenMl: 100, zielMl: 0), 0)
        XCTAssertEqual(Fortschritt.anteil(getrunkenMl: 2900, zielMl: 2750), 1.0)
    }

    // MARK: Sync

    func testSyncTexte() {
        XCTAssertEqual(SyncZustand.bestimmen(offlineKonto: false, offene: 0), .alleGespeichert)
        XCTAssertEqual(SyncZustand.bestimmen(offlineKonto: false, offene: 3), .ausstehend(3))
        XCTAssertEqual(SyncZustand.bestimmen(offlineKonto: true, offene: 3), .offline)
        XCTAssertEqual(SyncZustand.alleGespeichert.zeilenText, "Alle Einträge sind gespeichert.")
        XCTAssertEqual(SyncZustand.ausstehend(3).zeilenText, "3 Einträge werden hochgeladen, sobald Internet da ist.")
        XCTAssertEqual(SyncZustand.ausstehend(1).zeilenText, "1 Eintrag wird hochgeladen, sobald Internet da ist.")
        XCTAssertEqual(SyncZustand.offline.zeilenText, "Offline-Modus: Einträge werden nur auf diesem iPhone gespeichert.")
        XCTAssertEqual(SyncZustand.alleGespeichert.kurzText, "alles hochgeladen")
        XCTAssertEqual(SyncZustand.ausstehend(3).kurzText, "3 Einträge warten")
        XCTAssertEqual(SyncZustand.offline.kurzText, "Offline-Modus")
        XCTAssertTrue(SyncZustand.ausstehend(2).zeigtSymbol)
        XCTAssertFalse(SyncZustand.alleGespeichert.zeigtSymbol)
    }

    func testAbmeldeText() {
        XCTAssertEqual(SyncZustand.abmeldeText(offene: 0, offlineKonto: false), "Deine Daten bleiben gespeichert.")
        XCTAssertEqual(SyncZustand.abmeldeText(offene: 5, offlineKonto: true), "Deine Daten bleiben gespeichert.")
        XCTAssertTrue(SyncZustand.abmeldeText(offene: 3, offlineKonto: false)
            .hasPrefix("3 Einträge sind noch nicht hochgeladen. Sie bleiben auf dem iPhone"))
    }

    // MARK: Gerätekarte – die sieben Zustände

    private func karte(_ s: VerbindungsStatus, demo: Bool = false, akku: Int? = 88, erreicht: Bool = false) -> GeraeteKarteModell {
        GeraeteKarteModell(status: s, demoModus: demo, akkuProzent: akku, zielErreicht: erreicht)
    }

    func testSuchen() {
        let k = karte(.suchen)
        XCTAssertEqual(k.statusText, "Suchen …")
        XCTAssertEqual(k.statusFarbe, .blau)
        XCTAssertTrue(k.zeigtSpinner)
        XCTAssertEqual(k.lichtlinie, .blau)
        XCTAssertEqual(k.aktionen, [.trennen])
        XCTAssertTrue(k.hinweis?.hasPrefix("Der HydroDesk ist nur kurz nach dem Trinken") == true)
    }

    func testVerbinden() {
        let k = karte(.verbinden)
        XCTAssertEqual(k.statusText, "Verbinden …")
        XCTAssertTrue(k.zeigtSpinner)
        XCTAssertEqual(k.lichtlinie, .blau)
        XCTAssertEqual(k.aktionen, [.trennen])
        XCTAssertNil(k.hinweis)
    }

    func testVerbundenUndZielErreicht() {
        XCTAssertEqual(karte(.verbunden).statusFarbe, .gruen)
        XCTAssertEqual(karte(.verbunden).lichtlinie, .blau)
        XCTAssertEqual(karte(.verbunden, erreicht: true).lichtlinie, .gruen)
        XCTAssertEqual(karte(.verbunden).aktionen, [.trennen])
    }

    func testAkkuNiedrigMachtLichtlinieRotMitHinweis() {
        let k = karte(.verbunden, akku: 10, erreicht: true)
        XCTAssertTrue(k.akkuNiedrig)
        XCTAssertEqual(k.lichtlinie, .rot)
        XCTAssertNotNil(k.akkuHinweis)
        XCTAssertFalse(karte(.verbunden, akku: 16).akkuNiedrig)
        XCTAssertFalse(karte(.verbunden, akku: nil).akkuNiedrig)
        XCTAssertFalse(karte(.getrennt, akku: 5).akkuNiedrig)
    }

    func testGetrennt() {
        let k = karte(.getrennt)
        XCTAssertEqual(k.statusText, "Getrennt")
        XCTAssertEqual(k.statusFarbe, .grau)
        XCTAssertEqual(k.lichtlinie, .aus)
        XCTAssertEqual(k.aktionen, [.verbinden])
    }

    func testBluetoothAus() {
        let k = karte(.bluetoothAus)
        XCTAssertEqual(k.statusText, "Bluetooth ist aus")
        XCTAssertEqual(k.statusFarbe, .orange)
        XCTAssertEqual(k.lichtlinie, .aus)
        XCTAssertEqual(k.aktionen, [.erneutVersuchen])
        XCTAssertEqual(k.hinweis, "Bitte Bluetooth in den Einstellungen oder im Kontrollzentrum einschalten.")
    }

    func testKeineBerechtigung() {
        let k = karte(.keineBerechtigung)
        XCTAssertEqual(k.statusText, "Keine Berechtigung")
        XCTAssertEqual(k.statusFarbe, .orange)
        XCTAssertEqual(k.lichtlinie, .aus)
        XCTAssertEqual(k.aktionen, [.einstellungenOeffnen])
        XCTAssertEqual(k.hinweis, "Ohne Bluetooth-Berechtigung kann die App das Gerät nicht finden.")
    }

    func testDemoModus() {
        let k = karte(.demo, demo: true, akku: nil)
        XCTAssertEqual(k.titel, "HydroDesk (Demo-Modus)")
        XCTAssertEqual(k.statusText, "Verbunden (Demo)")
        XCTAssertEqual(k.statusFarbe, .gruen)
        XCTAssertEqual(k.aktionen, [.trennen, .schluckSimulieren])
        XCTAssertNil(k.hinweis)
        XCTAssertEqual(karte(.getrennt).titel, "HydroDesk")
    }

    func testGeraetMeldetText() {
        let r = DeviceReading(heuteMl: 1250, zielMl: 2750, akkuProzent: 88)
        XCTAssertEqual(GeraeteKarteModell.meldetText(r), "Gerät meldet: 1.250 / 2.750 ml")
        XCTAssertEqual(GeraeteKarteModell.meldetText(DeviceReading(heuteMl: 80)), "Gerät meldet: 80 ml")
        XCTAssertEqual(GeraeteKarteModell.akkuSymbol(80), "battery.75percent")
        XCTAssertEqual(GeraeteKarteModell.akkuSymbol(100), "battery.100percent")
        XCTAssertEqual(GeraeteKarteModell.akkuSymbol(5), "battery.0percent")
    }

    // MARK: Formate (de-DE)

    func testFormateWieInDerSpec() {
        XCTAssertEqual(Format.mlEinheit(1250), "1.250 ml")
        XCTAssertEqual(Format.prozent(45), "45 %")
        XCTAssertEqual(Format.liter(2100), "2,1 l")
    }

    func testDatumUndUhrzeitFormate() {
        var k = Calendar(identifier: .gregorian)
        k.timeZone = TimeZone.current
        let montag = k.date(from: DateComponents(year: 2026, month: 11, day: 9, hour: 14, minute: 32))!
        XCTAssertEqual(Format.uhrzeitUhr(montag), "14:32 Uhr")
        XCTAssertEqual(Format.datumLang(montag), "Montag, 9. November")
        XCTAssertEqual(Format.datumKurz(montag), "Mo, 9. Nov.")
    }
}
