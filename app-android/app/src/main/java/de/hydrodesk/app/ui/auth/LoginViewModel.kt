// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE

package de.hydrodesk.app.ui.auth

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import de.hydrodesk.app.data.remote.SupabaseModul
import de.hydrodesk.app.data.repository.AuthRepository
import kotlinx.coroutines.launch

/** Logik des Login-/Registrieren-Bildschirms. */
class LoginViewModel(private val auth: AuthRepository) : ViewModel() {
    var registrieren by mutableStateOf(false)
    var name by mutableStateOf("")
    var email by mutableStateOf("")
    var passwort by mutableStateOf("")
    var laedt by mutableStateOf(false)
        private set
    var fehler by mutableStateOf<String?>(null)
        private set
    var info by mutableStateOf<String?>(null)
        private set

    val supabaseEingerichtet = SupabaseModul.istKonfiguriert

    fun absenden() {
        fehler = null
        info = null
        // Eingaben prüfen, bevor etwas an den Server geht
        when {
            registrieren && name.isBlank() -> { fehler = "Bitte einen Namen eingeben."; return }
            !email.contains("@") || !email.contains(".") -> { fehler = "Bitte eine gültige E-Mail-Adresse eingeben."; return }
            passwort.length < 6 -> { fehler = "Das Passwort braucht mindestens 6 Zeichen."; return }
        }
        laedt = true
        viewModelScope.launch {
            if (registrieren) {
                auth.registrieren(name, email, passwort)
                    .onSuccess { angemeldet ->
                        if (!angemeldet) {
                            info = "Konto angelegt. Bitte den Bestätigungslink in der E-Mail öffnen und dann anmelden."
                            registrieren = false
                        }
                        // angemeldet == true: die App wechselt automatisch zum Hauptbildschirm
                    }
                    .onFailure { fehler = it.message }
            } else {
                auth.anmelden(email, passwort).onFailure { fehler = it.message }
            }
            laedt = false
        }
    }

    fun offlineTesten() = auth.offlineStarten()
}
