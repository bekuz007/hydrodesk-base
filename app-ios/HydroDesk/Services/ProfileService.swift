// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE

import Foundation
import Observation

/// Profil (Name, Gewicht, Größe, Tagesziel) aus der Supabase-Tabelle `profiles`.
/// Eine Kopie liegt auf dem iPhone, damit das Profil auch offline sichtbar ist.
@MainActor
@Observable
final class ProfileService {
    private(set) var profil: ProfileDto?

    @ObservationIgnored private let remote: RemoteService?
    @ObservationIgnored private let settings: AppSettings

    init(remote: RemoteService?, settings: AppSettings) {
        self.remote = remote
        self.settings = settings
        if let json = settings.profilJson, let daten = json.data(using: .utf8) {
            profil = try? JSONDecoder().decode(ProfileDto.self, from: daten)
        }
    }

    /// Profil für diesen Nutzer aus Supabase laden (ohne Internet bleibt die lokale Kopie).
    func laden(userId: String) async -> String? {
        // Profil eines ANDEREN Nutzers (nach Kontowechsel) nicht anzeigen
        if let p = profil, p.id != userId { profil = nil }
        guard userId != HydroKonstanten.offlineUserId, let remote else { return nil }
        do {
            if let geladen = try await remote.profilLaden(userId: userId) { merken(geladen) }
            return nil
        } catch {
            return error.localizedDescription
        }
    }

    /// Speichert Name, Gewicht und Größe; das Tagesziel wird dabei neu berechnet.
    /// - Returns: das neue Tagesziel und ggf. eine Meldung, falls Supabase nicht erreichbar war
    func speichern(userId: String, name: String, gewichtKg: Double, groesseCm: Int) async -> (ziel: Int, fehler: String?) {
        let ziel = GoalCalculator.tageszielMl(gewichtKg: gewichtKg, groesseCm: Double(groesseCm))
        var neu = (profil?.id == userId ? profil : nil) ?? ProfileDto(id: userId)
        neu.name = name
        neu.weightKg = gewichtKg
        neu.heightCm = groesseCm
        neu.dailyGoalMl = ziel
        merken(neu)   // lokal sofort übernehmen (offline-first)

        guard userId != HydroKonstanten.offlineUserId, let remote else { return (ziel, nil) }
        do {
            try await remote.profilSpeichern(ProfileUpdateDto(
                id: userId, name: name, weightKg: gewichtKg, heightCm: groesseCm, dailyGoalMl: ziel))
            _ = await laden(userId: userId)   // neu laden, damit z. B. role und email aktuell sind
            return (ziel, nil)
        } catch {
            return (ziel, error.localizedDescription)
        }
    }

    private func merken(_ p: ProfileDto) {
        profil = p
        if let daten = try? JSONEncoder().encode(p) { settings.profilJson = String(data: daten, encoding: .utf8) }
    }
}
