// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE

package de.hydrodesk.app.data.repository

import de.hydrodesk.app.data.remote.ProfileDto
import de.hydrodesk.app.data.remote.ProfileUpdateDto
import de.hydrodesk.app.data.settings.AppSettings
import de.hydrodesk.app.domain.GoalCalculator
import io.github.jan.supabase.SupabaseClient
import io.github.jan.supabase.postgrest.from
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.serialization.json.Json

/**
 * Profil (Name, Gewicht, Größe, Tagesziel) aus der Supabase-Tabelle profiles.
 * Eine Kopie liegt auf dem Handy, damit das Profil auch offline sichtbar ist.
 */
class ProfileRepository(
    private val supabase: SupabaseClient?,
    private val settings: AppSettings,
) {
    private val json = Json { ignoreUnknownKeys = true }

    private val _profil = MutableStateFlow(gespeichertesProfil())
    val profil: StateFlow<ProfileDto?> = _profil.asStateFlow()

    /** Profil für diesen Nutzer aus Supabase laden (ohne Internet bleibt die lokale Kopie). */
    suspend fun laden(userId: String): Result<ProfileDto?> {
        // Profil eines ANDEREN Nutzers (nach Kontowechsel) nicht anzeigen
        if (_profil.value?.id != userId) _profil.value = null
        val sb = supabase
        if (userId == AuthRepository.OFFLINE_USER_ID || sb == null) {
            return Result.success(_profil.value)
        }
        return runCatching {
            sb.from("profiles")
                .select { filter { eq("id", userId) } }
                .decodeSingleOrNull<ProfileDto>()
        }.onSuccess { geladen ->
            if (geladen != null) merken(geladen)
        }
    }

    /** Speichert Name, Gewicht und Größe; das Tagesziel wird dabei neu berechnet. */
    suspend fun speichern(userId: String, name: String, gewichtKg: Double, groesseCm: Int): Result<ProfileDto> {
        val ziel = GoalCalculator.tageszielMl(gewichtKg, groesseCm.toDouble())
        val alt = _profil.value?.takeIf { it.id == userId }
        val neu = (alt ?: ProfileDto(id = userId)).copy(
            name = name,
            weightKg = gewichtKg,
            heightCm = groesseCm,
            dailyGoalMl = ziel,
        )
        merken(neu)   // lokal sofort übernehmen (offline-first)

        val sb = supabase
        if (userId == AuthRepository.OFFLINE_USER_ID || sb == null) return Result.success(neu)
        return runCatching {
            sb.from("profiles").upsert(
                ProfileUpdateDto(userId, name, gewichtKg, groesseCm, ziel)
            ) { onConflict = "id" }
            // Neu laden, damit z. B. role und email aktuell sind
            laden(userId).getOrNull() ?: neu
        }
    }

    private fun merken(p: ProfileDto) {
        _profil.value = p
        settings.profilJson = json.encodeToString(ProfileDto.serializer(), p)
    }

    private fun gespeichertesProfil(): ProfileDto? = settings.profilJson?.let {
        runCatching { json.decodeFromString(ProfileDto.serializer(), it) }.getOrNull()
    }
}
