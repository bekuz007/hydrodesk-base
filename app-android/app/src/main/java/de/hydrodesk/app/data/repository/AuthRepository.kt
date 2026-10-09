// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE

package de.hydrodesk.app.data.repository

import de.hydrodesk.app.data.settings.AppSettings
import io.github.jan.supabase.SupabaseClient
import io.github.jan.supabase.auth.auth
import io.github.jan.supabase.auth.providers.builtin.Email
import io.github.jan.supabase.auth.status.SessionStatus
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.flow.stateIn
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put

/** Ist jemand angemeldet? */
sealed interface AuthZustand {
    data object Laedt : AuthZustand
    data object Abgemeldet : AuthZustand
    data class Angemeldet(val userId: String, val email: String, val offline: Boolean) : AuthZustand
}

/**
 * Login, Registrierung und Logout über Supabase Auth.
 * Die Sitzung speichert supabase-kt selbst auf dem Handy -> nach dem
 * Neustart der App ist man weiter angemeldet.
 */
class AuthRepository(
    private val supabase: SupabaseClient?,
    private val settings: AppSettings,
    scope: CoroutineScope,
) {
    val zustand: StateFlow<AuthZustand> = combine(
        supabase?.auth?.sessionStatus ?: flowOf(SessionStatus.NotAuthenticated(isSignOut = false)),
        settings.offlineKonto,
    ) { status, offline ->
        if (offline) {
            AuthZustand.Angemeldet(OFFLINE_USER_ID, "Offline (ohne Konto)", offline = true)
        } else {
            when (status) {
                is SessionStatus.Authenticated -> {
                    val user = status.session.user
                    if (user != null) AuthZustand.Angemeldet(user.id, user.email ?: "", offline = false)
                    else AuthZustand.Abgemeldet
                }
                is SessionStatus.Initializing -> AuthZustand.Laedt
                // Token konnte nicht erneuert werden (z. B. kein Internet):
                // trotzdem angemeldet bleiben, damit die App offline weiter funktioniert.
                is SessionStatus.RefreshFailure -> {
                    val user = supabase?.auth?.currentUserOrNull()
                    if (user != null) AuthZustand.Angemeldet(user.id, user.email ?: "", offline = false)
                    else AuthZustand.Abgemeldet
                }
                is SessionStatus.NotAuthenticated -> AuthZustand.Abgemeldet
            }
        }
    }.stateIn(scope, SharingStarted.Eagerly, AuthZustand.Laedt)

    suspend fun anmelden(email: String, passwort: String): Result<Unit> = runCatching {
        val sb = supabase ?: error(NICHT_KONFIGURIERT)
        sb.auth.signInWith(Email) {
            this.email = email.trim()
            this.password = passwort
        }
    }.uebersetzen()

    /**
     * Registriert ein neues Konto. Der Name wird als "user metadata" mitgeschickt;
     * der Trigger in schema.sql legt damit automatisch die Zeile in profiles an.
     * @return true = sofort angemeldet, false = erst E-Mail bestätigen
     */
    suspend fun registrieren(name: String, email: String, passwort: String): Result<Boolean> = runCatching {
        val sb = supabase ?: error(NICHT_KONFIGURIERT)
        sb.auth.signUpWith(Email) {
            this.email = email.trim()
            this.password = passwort
            data = buildJsonObject { put("name", name.trim()) }
        }
        sb.auth.currentSessionOrNull() != null
    }.uebersetzen()

    suspend fun abmelden() {
        if (settings.offlineKonto.value) {
            settings.setOfflineKonto(false)
            return
        }
        val sb = supabase ?: return
        // Ohne Internet schlägt signOut fehl -> dann die Sitzung nur lokal löschen
        runCatching { sb.auth.signOut() }.onFailure { runCatching { sb.auth.clearSession() } }
    }

    /** Ohne Konto weitermachen: Daten bleiben nur auf dem Handy. */
    fun offlineStarten() = settings.setOfflineKonto(true)

    /** Fehlermeldungen von Supabase (englisch) in verständliches Deutsch übersetzen. */
    private fun <T> Result<T>.uebersetzen(): Result<T> = recoverCatching { fehler ->
        val text = (fehler.message ?: "").lowercase()
        val meldung = when {
            text.contains(NICHT_KONFIGURIERT.lowercase()) -> NICHT_KONFIGURIERT
            text.contains("invalid login credentials") -> "E-Mail oder Passwort ist falsch."
            text.contains("email not confirmed") -> "Die E-Mail-Adresse ist noch nicht bestätigt. Bitte den Link in der E-Mail öffnen."
            text.contains("already registered") || text.contains("already exists") -> "Für diese E-Mail gibt es schon ein Konto. Bitte anmelden."
            text.contains("password") && text.contains("at least") -> "Das Passwort ist zu kurz (mindestens 6 Zeichen)."
            text.contains("invalid") && text.contains("email") -> "Die E-Mail-Adresse ist ungültig."
            text.contains("rate limit") -> "Zu viele Versuche. Bitte kurz warten."
            text.contains("unable to resolve host") || text.contains("timeout") ||
                text.contains("failed to connect") || text.contains("network") ->
                "Keine Verbindung zum Server. Bitte Internet prüfen."
            else -> "Fehler: ${fehler.message}"
        }
        throw IllegalStateException(meldung, fehler)
    }

    companion object {
        const val OFFLINE_USER_ID = "offline"
        const val NICHT_KONFIGURIERT = "Supabase ist nicht eingerichtet (local.properties)."
    }
}
