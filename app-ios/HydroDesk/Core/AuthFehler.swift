// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE

import Foundation

/// Gemeinsame Konstanten.
enum HydroKonstanten {
    /// Nutzer-ID im Modus „Ohne Konto testen“
    static let offlineUserId = "offline"
    static let nichtKonfiguriert = "Supabase ist nicht eingerichtet (Config/Secrets.xcconfig)."
    static let appVersion = "1.0"
}

/// Übersetzt Fehlermeldungen von Supabase (englisch) in verständliches Deutsch
/// (gleiche Texte wie in der Android-App).
enum AuthFehler {
    static func uebersetzen(_ original: String) -> String {
        let text = original.lowercased()
        switch true {
        case text.contains(HydroKonstanten.nichtKonfiguriert.lowercased()):
            return HydroKonstanten.nichtKonfiguriert
        case text.contains("invalid login credentials"):
            return "E-Mail oder Passwort ist falsch."
        case text.contains("email not confirmed"):
            return "Die E-Mail-Adresse ist noch nicht bestätigt. Bitte den Link in der E-Mail öffnen."
        case text.contains("already registered") || text.contains("already exists"):
            return "Für diese E-Mail gibt es schon ein Konto. Bitte anmelden."
        case text.contains("password") && text.contains("at least"):
            return "Das Passwort ist zu kurz (mindestens 6 Zeichen)."
        case text.contains("invalid") && text.contains("email"):
            return "Die E-Mail-Adresse ist ungültig."
        case text.contains("rate limit"):
            return "Zu viele Versuche. Bitte kurz warten."
        case text.contains("offline") || text.contains("timed out") || text.contains("timeout")
            || text.contains("could not connect") || text.contains("network") || text.contains("internet"):
            return "Keine Verbindung zum Server. Bitte Internet prüfen."
        default:
            return "Fehler: \(original)"
        }
    }
}
