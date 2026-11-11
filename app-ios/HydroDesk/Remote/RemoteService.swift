// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE

import Foundation
import Supabase
#if os(Linux)
import Auth
#endif

/// Angemeldeter Nutzer, wie ihn Supabase liefert.
struct SitzungInfo: Equatable {
    var userId: String   // kleingeschrieben, wie in der Datenbank
    var email: String
}

/// Wird gesendet, wenn sich der Login-Zustand ändert.
enum SitzungsEreignis: Equatable {
    case angemeldet(SitzungInfo)
    case abgemeldet
}

/// Alles, was mit Supabase (Login + Datenbank) zu tun hat, an einer Stelle.
/// Dieselben Tabellen und Views wie die Android-App: `profiles`, `drink_entries`, `user_today`.
final class RemoteService {
    let client: SupabaseClient

    /// true, wenn in `Secrets.xcconfig` echte Werte eingetragen sind.
    static func istKonfiguriert(url: String, key: String) -> Bool {
        url.hasPrefix("https://") && !url.contains("DEIN-PROJEKT") && key.count > 20
            && !key.contains("dein-anon")
    }

    /// Liefert nil, wenn URL/Key fehlen oder ungültig sind (dann geht nur „Ohne Konto testen“).
    init?(url: String, key: String) {
        guard Self.istKonfiguriert(url: url, key: key), let adresse = URL(string: url) else { return nil }
        #if os(Linux)
        // Nur für die Prüfung auf Linux (dort gibt es keinen Schlüsselbund). Auf iPhone/Mac gilt der Zweig unten.
        client = SupabaseClient(
            supabaseURL: adresse, supabaseKey: key,
            options: SupabaseClientOptions(auth: .init(storage: SpeicherNurImRAM()))
        )
        #else
        // Die Sitzung speichert supabase-swift selbst im Schlüsselbund (Keychain) des iPhones.
        client = SupabaseClient(supabaseURL: adresse, supabaseKey: key)
        #endif
    }

    // MARK: - Login

    private static func info(_ session: Session) -> SitzungInfo {
        SitzungInfo(userId: session.user.id.uuidString.lowercased(), email: session.user.email ?? "")
    }

    /// Gespeicherte Sitzung (auch wenn das Token abgelaufen ist – so bleibt man offline angemeldet).
    func gespeicherteSitzung() -> SitzungInfo? {
        client.auth.currentSession.map(Self.info)
    }

    /// Strom aller Änderungen: erster Wert = Zustand beim Start.
    func sitzungsStrom() -> AsyncStream<SitzungsEreignis> {
        let quelle = client.auth.authStateChanges
        let auth = client.auth
        return AsyncStream { fortsetzung in
            let aufgabe = Task {
                for await (ereignis, session) in quelle {
                    switch ereignis {
                    case .signedOut, .userDeleted:
                        fortsetzung.yield(.abgemeldet)
                    case .initialSession:
                        // Abgelaufenes Token ohne Internet: gespeicherte Sitzung trotzdem behalten
                        if let s = session ?? auth.currentSession {
                            fortsetzung.yield(.angemeldet(Self.info(s)))
                        } else {
                            fortsetzung.yield(.abgemeldet)
                        }
                    default:
                        if let s = session { fortsetzung.yield(.angemeldet(Self.info(s))) }
                    }
                }
                fortsetzung.finish()
            }
            fortsetzung.onTermination = { _ in aufgabe.cancel() }
        }
    }

    func anmelden(email: String, passwort: String) async throws {
        try await client.auth.signIn(email: email.trimmingCharacters(in: .whitespaces), password: passwort)
    }

    /// Registriert ein neues Konto. Der Name wird als „user metadata“ mitgeschickt;
    /// der Trigger in `schema.sql` legt damit automatisch die Zeile in `profiles` an.
    /// - Returns: true = sofort angemeldet, false = erst E-Mail bestätigen
    func registrieren(name: String, email: String, passwort: String) async throws -> Bool {
        let antwort = try await client.auth.signUp(
            email: email.trimmingCharacters(in: .whitespaces),
            password: passwort,
            data: ["name": .string(name.trimmingCharacters(in: .whitespaces))]
        )
        if case .session = antwort { return true }
        return false
    }

    /// Ohne Internet schlägt der Server-Aufruf fehl – die lokale Sitzung wird trotzdem zuerst gelöscht.
    func abmelden() async {
        try? await client.auth.signOut()
    }

    // MARK: - Profil

    func profilLaden(userId: String) async throws -> ProfileDto? {
        let zeilen: [ProfileDto] = try await client.from("profiles")
            .select()
            .eq("id", value: userId)
            .execute()
            .value
        return zeilen.first
    }

    func profilSpeichern(_ profil: ProfileUpdateDto) async throws {
        try await client.from("profiles")
            .upsert(profil, onConflict: "id")
            .execute()
    }

    // MARK: - Trink-Einträge

    /// `ignoreDuplicates`: schon vorhandene ids werden übersprungen (kein Doppel-Eintrag).
    func eintraegeHochladen(_ eintraege: [DrinkEntryDto]) async throws {
        guard !eintraege.isEmpty else { return }
        try await client.from("drink_entries")
            .upsert(eintraege, onConflict: "id", ignoreDuplicates: true)
            .execute()
    }

    func eintraegeLaden(userId: String, seit: Date) async throws -> [DrinkEntryDto] {
        try await client.from("drink_entries")
            .select()
            .eq("user_id", value: userId)
            .gte("ts", value: ZeitText.text(seit))
            .execute()
            .value
    }

    // MARK: - Admin

    /// View `user_today`: Nur Admins sehen ALLE Zeilen (Row Level Security in Supabase).
    func alleNutzerHeute() async throws -> [UserTodayDto] {
        try await client.from("user_today")
            .select()
            .order("name", ascending: true)
            .execute()
            .value
    }
}

#if os(Linux)
/// Nur für die Linux-Prüfung (siehe oben).
private final class SpeicherNurImRAM: AuthLocalStorage, @unchecked Sendable {
    private var daten: [String: Data] = [:]
    func store(key: String, value: Data) throws { daten[key] = value }
    func retrieve(key: String) throws -> Data? { daten[key] }
    func remove(key: String) throws { daten[key] = nil }
}
#endif
