// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE

import Foundation
import SwiftData

/// Ein Trink-Eintrag („Schluck“) in der lokalen Datenbank (SwiftData).
///
/// Die `id` ist eine UUID (kleingeschrieben), die schon auf dem iPhone erzeugt wird. Supabase bekommt
/// dieselbe id → doppeltes Hochladen erzeugt keine doppelten Einträge.
@Model
final class DrinkEntry {
    @Attribute(.unique) var id: String
    var userId: String        // Supabase-User-ID (oder „offline“)
    var timestamp: Date       // Zeitpunkt des Schlucks
    var ml: Int               // getrunkene Menge
    var device: String        // Quelle: „HydroDesk“, „Demo“ …
    var synced: Bool          // schon zu Supabase hochgeladen?

    init(id: String = UUID().uuidString.lowercased(), userId: String, timestamp: Date = Date(),
         ml: Int, device: String, synced: Bool = false) {
        self.id = id
        self.userId = userId
        self.timestamp = timestamp
        self.ml = ml
        self.device = device
        self.synced = synced
    }

    /// So wird der Eintrag zu Supabase geschickt.
    var dto: DrinkEntryDto {
        DrinkEntryDto(id: id, userId: userId, ts: ZeitText.text(timestamp), ml: ml, device: device)
    }

    /// Eintrag aus Supabase übernehmen (dort schon gespeichert → `synced = true`).
    static func aus(dto: DrinkEntryDto) -> DrinkEntry? {
        guard let zeit = ZeitText.datum(dto.ts) else { return nil }
        return DrinkEntry(id: dto.id.lowercased(), userId: dto.userId.lowercased(), timestamp: zeit,
                          ml: dto.ml, device: dto.device ?? "unbekannt", synced: true)
    }
}
