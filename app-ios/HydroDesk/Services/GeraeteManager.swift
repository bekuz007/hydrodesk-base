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
    @ObservationIgnored private let profile: ProfileService
    /// V5: wann zuletzt das Profil ans Gerät geschickt wurde (nicht bei jedem Status erneut senden)
    @ObservationIgnored private var letzterProfilVersand: Date?

    init(ble: HydroBleManager, demo: DemoGeraet, settings: AppSettings, auth: AuthService, drinks: DrinkService,
         profile: ProfileService) {
        self.ble = ble
        self.demo = demo
        self.settings = settings
        self.auth = auth
        self.drinks = drinks
        self.profile = profile
        ble.beiMesswert = { [weak self] wert in self?.verarbeiten(wert, quelle: HydroBleManager.quelle) }
        demo.beiMesswert = { [weak self] wert in self?.verarbeiten(wert, quelle: DemoGeraet.quelle) }
        ble.beiGeraeteStatus = { [weak self] status in self?.profilAbgleichen(status) }
    }

    var demoModus: Bool { settings.demoModus }
    var status: VerbindungsStatus { demoModus ? demo.status : ble.status }
    var letzterMesswert: DeviceReading? { demoModus ? demo.letzterMesswert : ble.letzterMesswert }

    // MARK: - Steuerung (V5)

    /// Kann die App das echte Gerät gerade steuern? (verbunden + Firmware ab V5, nicht im Demo-Modus)
    var steuerbar: Bool { !demoModus && ble.steuerbar }
    /// Zustand des Geräts (Gewicht, Profil, Flasche …) – nil im Demo-Modus oder bei alter Firmware
    var geraeteStatus: GeraeteStatus? { demoModus ? nil : ble.geraeteStatus }
    /// letzte Rückmeldung des Geräts auf einen Befehl
    var letzteAntwort: GeraeteAntwort? { demoModus ? nil : ble.letzteAntwort }

    @discardableResult
    func senden(_ befehl: GeraeteBefehl) -> Bool {
        guard steuerbar else { return false }
        return ble.senden(befehl)
    }

    /// Profil aus der App (Gewicht, Größe) sofort ans Gerät schicken, z. B. nach „Speichern“.
    /// - Returns: true, wenn gesendet wurde
    @discardableResult
    func profilSenden() -> Bool {
        guard let p = profile.profil, let kg = p.weightKg, let cm = p.heightCm else { return false }
        guard senden(.profil(gewichtKg: kg, groesseCm: cm)) else { return false }
        letzterProfilVersand = Date()
        return true
    }

    /// Bei jedem neuen Gerätestatus: weicht das Profil auf dem Gerät von der App ab → App-Profil senden.
    /// Die App ist die Quelle (Profil steht auch in Supabase). Höchstens alle 10 s, damit nichts hin- und herpendelt.
    private func profilAbgleichen(_ status: GeraeteStatus) {
        guard let p = profile.profil, let kg = p.weightKg, let cm = p.heightCm,
              !status.profilPasst(gewichtKg: kg, groesseCm: cm) else { return }
        if let zuletzt = letzterProfilVersand, Date().timeIntervalSince(zuletzt) < 10 { return }
        profilSenden()
    }

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
