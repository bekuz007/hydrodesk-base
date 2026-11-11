// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE

import Foundation
import Observation
import SwiftData
import os

/// Trink-Einträge: lokal speichern (SwiftData) und mit Supabase synchronisieren.
///
/// OFFLINE-FIRST: Jeder Schluck wird ZUERST auf dem iPhone gespeichert (`synced = false`).
/// Danach wird hochgeladen, sobald Internet da ist (Sync läuft beim Schluck, beim Öffnen der App,
/// stündlich solange die App offen ist und auf Knopfdruck).
@MainActor
@Observable
final class DrinkService {
    private(set) var syncLaeuft = false
    private(set) var letzteSyncMeldung: String?

    @ObservationIgnored private let context: ModelContext
    @ObservationIgnored private let settings: AppSettings
    @ObservationIgnored private let remote: RemoteService?
    @ObservationIgnored private let log = Logger(subsystem: "de.hydrodesk", category: "DrinkService")

    init(context: ModelContext, settings: AppSettings, remote: RemoteService?) {
        self.context = context
        self.settings = settings
        self.remote = remote
    }

    // MARK: - Lesen

    /// Wie viel für diese Quelle (z. B. „Demo“) heute schon gespeichert ist.
    func heuteSummeFuerQuelle(userId: String, quelle: String) -> Int {
        let von = Tage.start()
        let bis = Tage.ende()
        let abfrage = FetchDescriptor<DrinkEntry>(predicate: #Predicate<DrinkEntry> {
            $0.userId == userId && $0.device == quelle && $0.timestamp >= von && $0.timestamp < bis
        })
        let treffer = (try? context.fetch(abfrage)) ?? []
        return treffer.reduce(0) { $0 + $1.ml }
    }

    // MARK: - Schluck-Erkennung

    /// Verarbeitet einen Messwert des Geräts (Logik siehe `SchluckErkennung`).
    /// - Returns: die erkannte Menge in ml oder nil (kein neuer Schluck)
    @discardableResult
    func geraetewertVerarbeiten(userId: String, wert: DeviceReading, quelle: String) -> Int? {
        let erkennung = SchluckErkennung(speicher: settings)
        let menge = erkennung.verarbeiten(
            userId: userId, quelle: quelle, tag: Tage.schluessel(), heuteMl: wert.heuteMl,
            gespeicherteSumme: { self.heuteSummeFuerQuelle(userId: userId, quelle: quelle) }
        )
        guard let menge else { return nil }

        context.insert(DrinkEntry(userId: userId, ml: menge, device: quelle))
        do { try context.save() } catch { log.error("Speichern fehlgeschlagen: \(error.localizedDescription)") }
        log.info("Neuer Schluck: +\(menge) ml (\(quelle), Gerät meldet \(wert.heuteMl) ml)")
        syncAnstossen()
        return menge
    }

    // MARK: - Synchronisieren

    /// Startet den Abgleich im Hintergrund (Ergebnis siehe `letzteSyncMeldung`).
    func syncAnstossen() {
        Task { _ = await synchronisieren() }
    }

    /// Abgleich mit Supabase:
    ///  1. offene lokale Einträge hochladen
    ///  2. Einträge der letzten 30 Tage herunterladen (z. B. nach einem Handywechsel)
    /// - Returns: Anzahl hochgeladener Einträge
    @discardableResult
    func synchronisieren() async -> Result<Int, FehlerText> {
        guard let remote, !settings.offlineKonto else { return .success(0) }   // nichts zu tun
        guard let userId = remote.gespeicherteSitzung()?.userId else { return .success(0) } // nicht angemeldet
        guard !syncLaeuft else { return .success(0) }
        syncLaeuft = true
        defer { syncLaeuft = false }

        do {
            let offenAbfrage = FetchDescriptor<DrinkEntry>(predicate: #Predicate<DrinkEntry> {
                $0.userId == userId && $0.synced == false
            })
            let offen = try context.fetch(offenAbfrage)
            if !offen.isEmpty {
                try await remote.eintraegeHochladen(offen.map(\.dto))
                for eintrag in offen { eintrag.synced = true }
                try context.save()
            }

            let seit = Date().addingTimeInterval(-30 * 86_400)
            let entfernt = try await remote.eintraegeLaden(userId: userId, seit: seit)
            let vorhandenAbfrage = FetchDescriptor<DrinkEntry>(predicate: #Predicate<DrinkEntry> {
                $0.userId == userId && $0.timestamp >= seit
            })
            let vorhandeneEintraege = try context.fetch(vorhandenAbfrage)
            let vorhanden = Set(vorhandeneEintraege.map(\.id))
            for dto in entfernt where !vorhanden.contains(dto.id.lowercased()) {
                if let neu = DrinkEntry.aus(dto: dto) { context.insert(neu) }
            }
            // In Supabase gelöschte Einträge auch auf dem iPhone entfernen
            // (nur bereits hochgeladene; noch nicht hochgeladene bleiben immer erhalten).
            let aufServer = Set(entfernt.map { $0.id.lowercased() })
            for eintrag in vorhandeneEintraege where eintrag.synced && !aufServer.contains(eintrag.id) {
                context.delete(eintrag)
            }
            try context.save()

            log.info("Sync fertig: \(offen.count) hochgeladen, \(entfernt.count) aus Supabase geprüft")
            letzteSyncMeldung = nil
            return .success(offen.count)
        } catch {
            let text = AuthFehler.uebersetzen(error.localizedDescription)
            log.error("Sync fehlgeschlagen: \(error.localizedDescription)")
            letzteSyncMeldung = "Synchronisierung fehlgeschlagen: \(text)"
            return .failure(FehlerText(text: text))
        }
    }
}
