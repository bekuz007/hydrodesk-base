// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE

import Foundation
import Observation

/// Wählt je nach Demo-Schalter das echte Gerät (BLE) oder das Demo-Gerät aus und
/// gibt jeden empfangenen Wert an den `DrinkService` weiter (Schluck-Erkennung).
/// Läuft in der ganzen App (nicht nur auf einem Bildschirm).
@MainActor
@Observable
final class GeraeteManager {
    let ble: HydroBleManager
    let demo: DemoGeraet

    @ObservationIgnored private let settings: AppSettings
    @ObservationIgnored private let auth: AuthService
    @ObservationIgnored private let drinks: DrinkService

    init(ble: HydroBleManager, demo: DemoGeraet, settings: AppSettings, auth: AuthService, drinks: DrinkService) {
        self.ble = ble
        self.demo = demo
        self.settings = settings
        self.auth = auth
        self.drinks = drinks
        ble.beiMesswert = { [weak self] wert in self?.verarbeiten(wert, quelle: HydroBleManager.quelle) }
        demo.beiMesswert = { [weak self] wert in self?.verarbeiten(wert, quelle: DemoGeraet.quelle) }
    }

    var demoModus: Bool { settings.demoModus }
    var status: VerbindungsStatus { demoModus ? demo.status : ble.status }
    var letzterMesswert: DeviceReading? { demoModus ? demo.letzterMesswert : ble.letzterMesswert }

    private func verarbeiten(_ wert: DeviceReading, quelle: String) {
        guard let nutzer = auth.zustand.nutzer else { return }
        drinks.geraetewertVerarbeiten(userId: nutzer.userId, wert: wert, quelle: quelle)
    }

    // MARK: - Bedienung

    func verbinden() {
        if demoModus { demoStarten() } else { ble.starten() }
    }

    func trennen() {
        if demoModus { demo.stoppen() } else { ble.stoppen() }
    }

    func schluckSimulieren(ml: Int = 200) { demo.schluckSimulieren(ml: ml) }

    /// Demo-Schalter im Profil: altes Gerät stoppen, Demo gleich starten (nur wenn angemeldet).
    func setDemoModus(_ an: Bool) {
        guard an != settings.demoModus else { return }
        demo.stoppen()
        ble.stoppen()
        settings.setDemoModus(an)
        if an { demoStarten() }
    }

    /// Wird von der Oberfläche aufgerufen, wenn sich der Login-Zustand ändert (und beim Start).
    func authGeaendert(_ zustand: AuthZustand) {
        switch zustand {
        case .abgemeldet:
            demo.stoppen()
            ble.stoppen()
        case .angemeldet:
            if demoModus { demoStarten() }
        case .laedt:
            break
        }
    }

    private func demoStarten() {
        guard let nutzer = auth.zustand.nutzer else { return }
        let start = drinks.heuteSummeFuerQuelle(userId: nutzer.userId, quelle: DemoGeraet.quelle)
        demo.starten(startwert: start)
    }
}
