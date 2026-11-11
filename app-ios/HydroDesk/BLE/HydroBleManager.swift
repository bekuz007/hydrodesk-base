// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE

import CoreBluetooth
import Foundation
import Observation
import os

/// Verbindung zum echten HydroDesk-Gerät über Bluetooth Low Energy (BLE) mit CoreBluetooth.
///
/// Ablauf (wie `HydroBleManager.kt` in der Android-App):
///  1. Scannen nach Geräten mit der HydroDesk-Dienst-UUID (steht im Werbepaket der Firmware)
///  2. Verbinden, Dienst und Characteristic suchen
///  3. Benachrichtigungen (notify) der Werte-Characteristic einschalten und den Wert einmal lesen
///  4. Jeder empfangene Text („1250/2750 ml“) wird in einen `DeviceReading` übersetzt
///  5. Bei Trennung: nach 3 s automatisch neu suchen (solange der Nutzer verbunden sein will)
///
/// UUIDs: siehe `HydroBleKonstanten` (müssen mit `wokwi/sketch.ino` übereinstimmen).
///
/// Alle CoreBluetooth-Rückrufe laufen auf der Main-Queue (`queue: .main`).
@MainActor
@Observable
final class HydroBleManager: NSObject {
    static let quelle = "HydroDesk"

    private static let serviceUUID = CBUUID(string: HydroBleKonstanten.serviceUUID)
    private static let werteUUID = CBUUID(string: HydroBleKonstanten.werteUUID)
    private static let scanDauer: Duration = .seconds(30)      // so lange suchen …
    private static let scanPause: Duration = .seconds(15)      // … dann Pause, dann wieder suchen
    private static let wiederverbinden: Duration = .seconds(3) // Wartezeit nach einer Trennung

    private(set) var status: VerbindungsStatus = .getrennt
    private(set) var letzterMesswert: DeviceReading?

    /// Wird für jeden empfangenen Wert aufgerufen.
    @ObservationIgnored var beiMesswert: ((DeviceReading) -> Void)?

    @ObservationIgnored private var zentrale: CBCentralManager?
    @ObservationIgnored private var geraet: CBPeripheral?
    @ObservationIgnored private var werte: CBCharacteristic?
    /// Will der Nutzer verbunden sein? Nur dann wird automatisch neu verbunden.
    @ObservationIgnored private var gewuenscht = false
    @ObservationIgnored private var scanLaeuft = false
    @ObservationIgnored private var zeitAufgabe: Task<Void, Never>?
    @ObservationIgnored private let log = Logger(subsystem: "de.hydrodesk", category: "HydroBle")

    // MARK: - Bedienung

    /// Verbindung aufbauen (vom Nutzer per Taste „Verbinden“ ausgelöst).
    /// Beim allerersten Aufruf fragt iOS nach der Bluetooth-Berechtigung.
    func starten() {
        gewuenscht = true
        zeitAufgabe?.cancel()
        if zentrale == nil {
            // Das Anlegen löst die Berechtigungsabfrage aus; weiter geht es in centralManagerDidUpdateState
            zentrale = CBCentralManager(delegate: self, queue: .main,
                                        options: [CBCentralManagerOptionShowPowerAlertKey: true])
            return
        }
        weiter()
    }

    /// Verbindung trennen und NICHT automatisch neu verbinden.
    func stoppen() {
        gewuenscht = false
        zeitAufgabe?.cancel()
        scanStoppen()
        verbindungSchliessen()
        status = .getrennt
    }

    // MARK: - Zustandsmaschine

    /// Prüft Berechtigung und Bluetooth-Zustand und startet dann die Suche.
    private func weiter() {
        guard gewuenscht, let zentrale else { return }
        switch CBCentralManager.authorization {
        case .denied, .restricted:
            status = .keineBerechtigung
            return
        default: break
        }
        switch zentrale.state {
        case .poweredOn:
            if geraet != nil || scanLaeuft { return }   // läuft schon
            scanStarten()
        case .poweredOff:
            status = .bluetoothAus
        case .unauthorized:
            status = .keineBerechtigung
        case .unsupported:
            status = .bluetoothAus
        default:
            break   // .unknown / .resetting: auf den nächsten Zustandswechsel warten
        }
    }

    private func scanStarten() {
        guard let zentrale else { return }
        // Nur nach der HydroDesk-Dienst-UUID suchen (nötig für Hintergrund und spart Strom)
        zentrale.scanForPeripherals(withServices: [Self.serviceUUID],
                                    options: [CBCentralManagerScanOptionAllowDuplicatesKey: false])
        scanLaeuft = true
        status = .suchen
        log.info("Suche nach HydroDesk gestartet")

        // Das Gerät sucht nur kurz nach dem Trinken bzw. Einschalten → nicht endlos scannen
        zeitAufgabe?.cancel()
        zeitAufgabe = Task { [weak self] in
            try? await Task.sleep(for: Self.scanDauer)
            guard !Task.isCancelled, let self, self.scanLaeuft else { return }
            self.log.info("Kein HydroDesk gefunden – neuer Versuch in 15 s")
            self.scanStoppen()
            self.status = .getrennt
            self.spaeterNeuVersuchen(Self.scanPause)
        }
    }

    private func scanStoppen() {
        guard scanLaeuft else { return }
        scanLaeuft = false
        zentrale?.stopScan()
    }

    private func verbindungSchliessen() {
        if let g = geraet { zentrale?.cancelPeripheralConnection(g) }
        geraet = nil
        werte = nil
    }

    private func spaeterNeuVersuchen(_ warten: Duration) {
        guard gewuenscht else { return }
        zeitAufgabe?.cancel()
        zeitAufgabe = Task { [weak self] in
            try? await Task.sleep(for: warten)
            guard !Task.isCancelled, let self else { return }
            if self.gewuenscht, self.geraet == nil, !self.scanLaeuft { self.starten() }
        }
    }

    private func verarbeiten(_ daten: Data) {
        guard let wert = BlePayloadParser.parse(daten) else {
            log.warning("Unbekanntes Format: \(String(decoding: daten, as: UTF8.self))")
            return
        }
        letzterMesswert = wert
        beiMesswert?(wert)
    }

    /// Verbindung ist weg (getrennt oder fehlgeschlagen).
    private func getrenntBehandeln() {
        geraet = nil
        werte = nil
        status = .getrennt
        spaeterNeuVersuchen(Self.wiederverbinden)
    }
}

// MARK: - CoreBluetooth-Rückrufe
// Die Rückrufe sind „nonisolated“ (so verlangt es das Protokoll). Weil die Main-Queue benutzt wird,
// laufen sie tatsächlich auf dem Main-Thread → `MainActor.assumeIsolated` ist erlaubt.

extension HydroBleManager: CBCentralManagerDelegate, CBPeripheralDelegate {

    nonisolated func centralManagerDidUpdateState(_ central: CBCentralManager) {
        MainActor.assumeIsolated {
            switch central.state {
            case .poweredOff:
                // Bluetooth wurde ausgeschaltet: Verbindung ist weg
                scanLaeuft = false
                geraet = nil
                werte = nil
                if gewuenscht { status = .bluetoothAus }
            case .poweredOn:
                if gewuenscht { weiter() }
            default:
                if gewuenscht { weiter() }
            }
        }
    }

    nonisolated func centralManager(_ central: CBCentralManager, didDiscover peripheral: CBPeripheral,
                                    advertisementData: [String: Any], rssi RSSI: NSNumber) {
        MainActor.assumeIsolated {
            guard scanLaeuft, geraet == nil else { return }
            log.info("Gefunden: \(peripheral.identifier.uuidString) (RSSI \(RSSI.intValue))")
            scanStoppen()
            zeitAufgabe?.cancel()
            geraet = peripheral            // festhalten, sonst gibt iOS das Objekt frei
            peripheral.delegate = self
            status = .verbinden
            central.connect(peripheral, options: nil)
        }
    }

    nonisolated func centralManager(_ central: CBCentralManager, didConnect peripheral: CBPeripheral) {
        MainActor.assumeIsolated {
            log.info("Verbunden – Dienste suchen")
            peripheral.discoverServices([Self.serviceUUID])
        }
    }

    nonisolated func centralManager(_ central: CBCentralManager, didFailToConnect peripheral: CBPeripheral,
                                    error: Error?) {
        MainActor.assumeIsolated {
            log.warning("Verbinden fehlgeschlagen: \(error?.localizedDescription ?? "-")")
            getrenntBehandeln()
        }
    }

    nonisolated func centralManager(_ central: CBCentralManager, didDisconnectPeripheral peripheral: CBPeripheral,
                                    error: Error?) {
        MainActor.assumeIsolated {
            log.info("Getrennt: \(error?.localizedDescription ?? "ohne Fehler")")
            // Beim Trennen durch den Nutzer (stoppen) ist `geraet` schon nil → nichts zu tun
            guard geraet != nil else { return }
            getrenntBehandeln()
        }
    }

    nonisolated func peripheral(_ peripheral: CBPeripheral, didDiscoverServices error: Error?) {
        MainActor.assumeIsolated {
            guard let dienst = peripheral.services?.first(where: { $0.uuid == Self.serviceUUID }) else {
                log.warning("HydroDesk-Dienst nicht gefunden – falsches Gerät?")
                zentrale?.cancelPeripheralConnection(peripheral)
                return
            }
            peripheral.discoverCharacteristics([Self.werteUUID], for: dienst)
        }
    }

    nonisolated func peripheral(_ peripheral: CBPeripheral, didDiscoverCharacteristicsFor service: CBService,
                                error: Error?) {
        MainActor.assumeIsolated {
            guard let zeichen = service.characteristics?.first(where: { $0.uuid == Self.werteUUID }) else {
                log.warning("Werte-Characteristic nicht gefunden")
                zentrale?.cancelPeripheralConnection(peripheral)
                return
            }
            werte = zeichen
            peripheral.setNotifyValue(true, for: zeichen)   // Benachrichtigungen einschalten
        }
    }

    nonisolated func peripheral(_ peripheral: CBPeripheral, didUpdateNotificationStateFor characteristic: CBCharacteristic,
                                error: Error?) {
        MainActor.assumeIsolated {
            if let error {
                log.warning("Notify fehlgeschlagen: \(error.localizedDescription)")
                zentrale?.cancelPeripheralConnection(peripheral)
                return
            }
            guard characteristic.isNotifying else { return }
            status = .verbunden
            // Aktuellen Wert einmal lesen – das Gerät sendet sonst erst bei der nächsten Änderung
            peripheral.readValue(for: characteristic)
        }
    }

    nonisolated func peripheral(_ peripheral: CBPeripheral, didUpdateValueFor characteristic: CBCharacteristic,
                                error: Error?) {
        MainActor.assumeIsolated {
            guard error == nil, characteristic.uuid == Self.werteUUID, let daten = characteristic.value else { return }
            verarbeiten(daten)
        }
    }
}
