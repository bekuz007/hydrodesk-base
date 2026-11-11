// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE

import Foundation
import Observation

/// DEMO-MODUS: tut so, als wäre ein HydroDesk verbunden.
/// Erzeugt dieselben Texte wie die Firmware („1250/2750 ml“) und schickt sie durch
/// denselben Parser – damit wird die komplette App-Logik ohne Hardware getestet.
///
/// Ab und zu (alle 15–40 s) wird zufällig ein Schluck von 50–300 ml simuliert.
/// Zusätzlich kann man per Taste einen Schluck auslösen (`schluckSimulieren`).
@MainActor
@Observable
final class DemoGeraet {
    static let quelle = "Demo"
    private static let demoZielMl = 2750

    private(set) var status: VerbindungsStatus = .getrennt
    private(set) var letzterMesswert: DeviceReading?

    /// Wird für jeden „gesendeten“ Wert aufgerufen (wie eine Benachrichtigung vom echten Gerät).
    @ObservationIgnored var beiMesswert: ((DeviceReading) -> Void)?

    @ObservationIgnored private var heuteMl = 0
    @ObservationIgnored private var aufgabe: Task<Void, Never>?

    /// - Parameter startwert: wie viel heute im Demo-Modus schon getrunken wurde
    func starten(startwert: Int) {
        guard aufgabe == nil else { return }
        aufgabe = Task { [weak self] in
            self?.status = .suchen
            try? await Task.sleep(for: .seconds(1))          // kurz „suchen“, wie beim echten Gerät
            guard !Task.isCancelled, let self else { return }
            self.heuteMl = startwert
            self.status = .demo
            self.senden()
            while !Task.isCancelled {
                try? await Task.sleep(for: .seconds(Double.random(in: 15...40)))
                guard !Task.isCancelled else { return }
                self.heuteMl += Int.random(in: 1...6) * 50    // 50 … 300 ml
                self.senden()
            }
        }
    }

    func stoppen() {
        aufgabe?.cancel()
        aufgabe = nil
        status = .getrennt
    }

    /// Für die Taste „Schluck simulieren“.
    func schluckSimulieren(ml: Int = 200) {
        guard status == .demo else { return }
        heuteMl += ml
        senden()
    }

    private func senden() {
        let text = "\(heuteMl)/\(Self.demoZielMl) ml"      // gleiches Format wie die Firmware
        guard let wert = BlePayloadParser.parse(text) else { return }
        letzterMesswert = wert
        beiMesswert?(wert)
    }
}
