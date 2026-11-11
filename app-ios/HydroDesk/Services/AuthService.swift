// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE

import Foundation
import Observation

/// Der angemeldete Nutzer (oder der lokale Nutzer im Modus „Ohne Konto testen“).
struct AngemeldeterNutzer: Hashable {
    var userId: String
    var email: String
    var offline: Bool
}

/// Ist jemand angemeldet?
enum AuthZustand: Hashable {
    case laedt
    case abgemeldet
    case angemeldet(AngemeldeterNutzer)

    var nutzer: AngemeldeterNutzer? {
        if case .angemeldet(let n) = self { return n }
        return nil
    }
}

enum RegistrierErgebnis {
    case angemeldet
    case bestaetigungNoetig
}

/// Login, Registrierung und Logout über Supabase Auth.
/// Die Sitzung speichert supabase-swift selbst im Schlüsselbund des iPhones –
/// nach dem Neustart der App ist man weiter angemeldet.
@MainActor
@Observable
final class AuthService {
    private(set) var zustand: AuthZustand = .laedt

    @ObservationIgnored private let remote: RemoteService?
    @ObservationIgnored private let settings: AppSettings
    /// Letzte Meldung von Supabase (nil = noch nichts gehört)
    @ObservationIgnored private var sitzung: SitzungsEreignis?

    var supabaseEingerichtet: Bool { remote != nil }

    init(remote: RemoteService?, settings: AppSettings) {
        self.remote = remote
        self.settings = settings
        if let remote {
            // Gespeicherte Sitzung sofort nutzen (auch ohne Internet), der Strom bestätigt sie gleich
            if let gespeichert = remote.gespeicherteSitzung() { sitzung = .angemeldet(gespeichert) }
        } else {
            sitzung = .abgemeldet
        }
        aktualisieren()

        if let remote {
            Task { [weak self] in
                for await ereignis in remote.sitzungsStrom() {
                    self?.sitzung = ereignis
                    self?.aktualisieren()
                }
            }
        }
    }

    private func aktualisieren() {
        if settings.offlineKonto {
            zustand = .angemeldet(AngemeldeterNutzer(
                userId: HydroKonstanten.offlineUserId, email: "Ohne Konto – nur dieses iPhone", offline: true))
            return
        }
        switch sitzung {
        case .none: zustand = .laedt
        case .some(.abgemeldet): zustand = .abgemeldet
        case .some(.angemeldet(let info)):
            zustand = .angemeldet(AngemeldeterNutzer(userId: info.userId, email: info.email, offline: false))
        }
    }

    /// - Returns: Fehlermeldung auf Deutsch oder nil bei Erfolg
    func anmelden(email: String, passwort: String) async -> String? {
        guard let remote else { return HydroKonstanten.nichtKonfiguriert }
        do {
            try await remote.anmelden(email: email, passwort: passwort)
            return nil
        } catch {
            return AuthFehler.uebersetzen(error.localizedDescription)
        }
    }

    func registrieren(name: String, email: String, passwort: String) async -> Result<RegistrierErgebnis, FehlerText> {
        guard let remote else { return .failure(FehlerText(text: HydroKonstanten.nichtKonfiguriert)) }
        do {
            let sofort = try await remote.registrieren(name: name, email: email, passwort: passwort)
            return .success(sofort ? .angemeldet : .bestaetigungNoetig)
        } catch {
            return .failure(FehlerText(text: AuthFehler.uebersetzen(error.localizedDescription)))
        }
    }

    func abmelden() async {
        if settings.offlineKonto {
            settings.setOfflineKonto(false)
            aktualisieren()
            return
        }
        // Ohne Internet schlägt der Server-Aufruf fehl – die lokale Sitzung ist dann trotzdem gelöscht
        await remote?.abmelden()
        sitzung = .abgemeldet
        aktualisieren()
    }

    /// Ohne Konto weitermachen: Daten bleiben nur auf dem iPhone.
    func offlineStarten() {
        settings.setOfflineKonto(true)
        aktualisieren()
    }
}

/// Kleine Hülle, damit ein Text als Fehler in einem `Result` benutzt werden kann.
struct FehlerText: Error, Equatable {
    var text: String
}
