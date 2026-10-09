// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE

package de.hydrodesk.app.data.remote

import de.hydrodesk.app.data.local.DrinkEntry
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import java.time.Instant
import java.time.OffsetDateTime

/*
 * DTOs = "Data Transfer Objects": so sehen die Zeilen in Supabase aus.
 * @SerialName verbindet Kotlin-Namen (camelCase) mit Spaltennamen (snake_case).
 */

/** Zeile der Tabelle profiles. */
@Serializable
data class ProfileDto(
    val id: String,
    val name: String? = null,
    val email: String? = null,
    @SerialName("weight_kg") val weightKg: Double? = null,
    @SerialName("height_cm") val heightCm: Int? = null,
    @SerialName("daily_goal_ml") val dailyGoalMl: Int? = null,
    val role: String = "user",
) {
    val istAdmin: Boolean get() = role == "admin"
}

/** Zum Speichern des Profils – absichtlich OHNE role (die darf nur der Admin ändern). */
@Serializable
data class ProfileUpdateDto(
    val id: String,
    val name: String,
    @SerialName("weight_kg") val weightKg: Double,
    @SerialName("height_cm") val heightCm: Int,
    @SerialName("daily_goal_ml") val dailyGoalMl: Int,
)

/** Zeile der Tabelle drink_entries. */
@Serializable
data class DrinkEntryDto(
    val id: String,
    @SerialName("user_id") val userId: String,
    val ts: String,          // Zeitstempel als ISO-Text, z. B. "2026-10-06T12:30:00Z"
    val ml: Int,
    val device: String? = null,
)

/** Zeile der Ansicht (View) user_today – nur für die Admin-Übersicht. */
@Serializable
data class UserTodayDto(
    val id: String,
    val name: String? = null,
    val email: String? = null,
    val role: String = "user",
    @SerialName("daily_goal_ml") val dailyGoalMl: Int? = null,
    @SerialName("heute_ml") val heuteMl: Int = 0,
    val drinks: Int = 0,
)

// --- Umwandlung lokal <-> Supabase ---

fun DrinkEntry.zuDto() = DrinkEntryDto(
    id = id,
    userId = userId,
    ts = Instant.ofEpochMilli(timestamp).toString(),
    ml = ml,
    device = device,
)

fun DrinkEntryDto.zuEntity() = DrinkEntry(
    id = id,
    userId = userId,
    timestamp = OffsetDateTime.parse(ts).toInstant().toEpochMilli(),
    ml = ml,
    device = device ?: "unbekannt",
    synced = true,
)
