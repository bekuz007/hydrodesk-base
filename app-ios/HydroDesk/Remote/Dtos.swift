// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE

import Foundation

/*
 DTOs = „Data Transfer Objects“: so sehen die Zeilen in Supabase aus.
 CodingKeys verbinden Swift-Namen (camelCase) mit den Spaltennamen (snake_case).
 Dieselben Tabellen wie in der Android-App (app-android/supabase/schema.sql).
 */

/// Zeile der Tabelle `profiles`.
struct ProfileDto: Codable, Equatable {
    var id: String
    var name: String?
    var email: String?
    var weightKg: Double?
    var heightCm: Int?
    var dailyGoalMl: Int?
    var role: String

    init(id: String, name: String? = nil, email: String? = nil, weightKg: Double? = nil,
         heightCm: Int? = nil, dailyGoalMl: Int? = nil, role: String = "user") {
        self.id = id; self.name = name; self.email = email; self.weightKg = weightKg
        self.heightCm = heightCm; self.dailyGoalMl = dailyGoalMl; self.role = role
    }

    enum CodingKeys: String, CodingKey {
        case id, name, email, role
        case weightKg = "weight_kg"
        case heightCm = "height_cm"
        case dailyGoalMl = "daily_goal_ml"
    }

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        id = try c.decode(String.self, forKey: .id)
        name = try c.decodeIfPresent(String.self, forKey: .name)
        email = try c.decodeIfPresent(String.self, forKey: .email)
        weightKg = try c.decodeIfPresent(Double.self, forKey: .weightKg)
        heightCm = try c.decodeIfPresent(Int.self, forKey: .heightCm)
        dailyGoalMl = try c.decodeIfPresent(Int.self, forKey: .dailyGoalMl)
        role = try c.decodeIfPresent(String.self, forKey: .role) ?? "user"
    }

    var istAdmin: Bool { role == "admin" }
}

/// Zum Speichern des Profils – absichtlich OHNE `role` (die darf nur der Admin ändern).
struct ProfileUpdateDto: Codable, Equatable {
    var id: String
    var name: String
    var weightKg: Double
    var heightCm: Int
    var dailyGoalMl: Int

    enum CodingKeys: String, CodingKey {
        case id, name
        case weightKg = "weight_kg"
        case heightCm = "height_cm"
        case dailyGoalMl = "daily_goal_ml"
    }
}

/// Zeile der Tabelle `drink_entries`.
struct DrinkEntryDto: Codable, Equatable {
    var id: String
    var userId: String
    /// Zeitstempel als ISO-Text, z. B. „2026-11-11T12:30:00Z“
    var ts: String
    var ml: Int
    var device: String?

    enum CodingKeys: String, CodingKey {
        case id, ts, ml, device
        case userId = "user_id"
    }
}

/// Zeile der Ansicht (View) `user_today` – nur für die Admin-Übersicht.
struct UserTodayDto: Codable, Equatable, Identifiable {
    var id: String
    var name: String?
    var email: String?
    var role: String
    var dailyGoalMl: Int?
    var heuteMl: Int
    var drinks: Int

    enum CodingKeys: String, CodingKey {
        case id, name, email, role, drinks
        case dailyGoalMl = "daily_goal_ml"
        case heuteMl = "heute_ml"
    }

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        id = try c.decode(String.self, forKey: .id)
        name = try c.decodeIfPresent(String.self, forKey: .name)
        email = try c.decodeIfPresent(String.self, forKey: .email)
        role = try c.decodeIfPresent(String.self, forKey: .role) ?? "user"
        dailyGoalMl = try c.decodeIfPresent(Int.self, forKey: .dailyGoalMl)
        heuteMl = try c.decodeIfPresent(Int.self, forKey: .heuteMl) ?? 0
        drinks = try c.decodeIfPresent(Int.self, forKey: .drinks) ?? 0
    }
}

/// Umwandlung Zeitstempel ↔ Text (ISO 8601). Supabase liefert z. B. „2026-11-11T12:30:00+00:00“
/// oder mit Bruchteilen „…:00.123456+00:00“.
enum ZeitText {
    static func text(_ datum: Date) -> String {
        let f = ISO8601DateFormatter()
        f.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        return f.string(from: datum)
    }

    static func datum(_ text: String) -> Date? {
        let mitBruchteilen = ISO8601DateFormatter()
        mitBruchteilen.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        if let d = mitBruchteilen.date(from: text) { return d }
        let ohne = ISO8601DateFormatter()
        ohne.formatOptions = [.withInternetDateTime]
        if let d = ohne.date(from: text) { return d }
        // Postgres liefert manchmal 6 Nachkommastellen – die kann ISO8601DateFormatter nicht immer lesen
        if let punkt = text.firstIndex(of: "."),
           let ende = text[punkt...].firstIndex(where: { $0 == "+" || $0 == "-" || $0 == "Z" }) {
            let kurz = String(text[..<punkt]) + String(text[ende...])
            return ohne.date(from: kurz)
        }
        return nil
    }
}
