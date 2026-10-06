package de.hydrodesk.app.data.local

import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey
import java.util.UUID

/**
 * Ein Trink-Eintrag ("Schluck") in der lokalen Datenbank (Tabelle drink_entries).
 *
 * Die id ist eine UUID, die schon auf dem Handy erzeugt wird. Supabase bekommt
 * dieselbe id -> doppeltes Hochladen erzeugt keine doppelten Einträge.
 */
@Entity(
    tableName = "drink_entries",
    indices = [Index("userId"), Index("timestamp")],
)
data class DrinkEntry(
    @PrimaryKey val id: String = UUID.randomUUID().toString(),
    val userId: String,          // Supabase-User-ID (oder "offline")
    val timestamp: Long,         // Zeitpunkt in Millisekunden seit 1970 (UTC)
    val ml: Int,                 // getrunkene Menge
    val device: String,          // Quelle: "HydroDesk", "Demo" ...
    val synced: Boolean = false, // schon zu Supabase hochgeladen?
)

/** Ergebnis der Tages-Abfrage (keine eigene Tabelle, wird aus drink_entries berechnet). */
data class DailySummary(
    val day: String,     // Datum als Text "2026-10-06"
    val totalMl: Int,    // Summe des Tages
    val drinks: Int,     // Anzahl Einträge
)
