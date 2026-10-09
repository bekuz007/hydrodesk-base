// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE

package de.hydrodesk.app.ui.profile

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import de.hydrodesk.app.AppContainer
import de.hydrodesk.app.data.remote.ProfileDto
import de.hydrodesk.app.domain.GoalCalculator
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import java.util.Locale

/** Logik für Profil + Einstellungen. */
class ProfilViewModel(
    private val userId: String,
    private val container: AppContainer,
) : ViewModel() {
    private val profile = container.profileRepository

    // Eingabefelder (als Text, damit auch halbe Eingaben wie "72," möglich sind)
    var name by mutableStateOf("")
    var gewicht by mutableStateOf("")
    var groesse by mutableStateOf("")
    var speichert by mutableStateOf(false)
        private set
    var meldung by mutableStateOf<String?>(null)
        private set
    private var bearbeitet = false

    val profil: StateFlow<ProfileDto?> = profile.profil
    val demoModus: StateFlow<Boolean> = container.settings.demoModus
    val offeneSyncs: StateFlow<Int> = container.drinkRepository.anzahlNichtSynchronisiert(userId)
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), 0)

    init {
        // Felder mit dem gespeicherten Profil füllen (solange der Nutzer noch nichts geändert hat)
        viewModelScope.launch {
            profile.profil.collect { p -> if (p != null && p.id == userId && !bearbeitet) felderFuellen(p) }
        }
    }

    private fun felderFuellen(p: ProfileDto) {
        name = p.name ?: ""
        gewicht = p.weightKg?.let { formatKg(it) } ?: ""
        groesse = p.heightCm?.toString() ?: ""
    }

    fun geaendert() { bearbeitet = true }

    private fun gewichtZahl(): Double? = gewicht.replace(',', '.').toDoubleOrNull()
    private fun groesseZahl(): Int? = groesse.trim().toIntOrNull()

    /** Live-Vorschau des Tagesziels während der Eingabe (null = Eingabe unvollständig). */
    fun zielVorschau(): Pair<Int, Double>? {
        val kg = gewichtZahl() ?: return null
        val cm = groesseZahl() ?: return null
        if (kg !in 30.0..250.0 || cm !in 120..230) return null
        return GoalCalculator.tageszielMl(kg, cm.toDouble()) to GoalCalculator.koerperoberflaeche(kg, cm.toDouble())
    }

    fun speichern() {
        val kg = gewichtZahl()
        val cm = groesseZahl()
        // Gleiche Grenzen wie in der Firmware (Serial-Befehle "gewicht" / "groesse")
        meldung = when {
            name.isBlank() -> "Bitte einen Namen eingeben."
            kg == null || kg !in 30.0..250.0 -> "Gewicht bitte zwischen 30 und 250 kg angeben."
            cm == null || cm !in 120..230 -> "Größe bitte zwischen 120 und 230 cm angeben."
            else -> null
        }
        if (meldung != null || kg == null || cm == null) return
        speichert = true
        viewModelScope.launch {
            profile.speichern(userId, name.trim(), kg, cm)
                .onSuccess {
                    bearbeitet = false
                    meldung = "Gespeichert. Neues Tagesziel: ${it.dailyGoalMl} ml"
                }
                .onFailure { meldung = "Lokal gespeichert, aber nicht in Supabase: ${it.message}" }
            speichert = false
        }
    }

    fun setDemoModus(an: Boolean) = container.settings.setDemoModus(an)

    fun jetztSynchronisieren() {
        container.syncAnstossen()
        meldung = "Synchronisierung gestartet (läuft, sobald Internet da ist)."
    }

    fun abmelden() {
        viewModelScope.launch { container.authRepository.abmelden() }
    }

    private fun formatKg(kg: Double): String =
        if (kg % 1.0 == 0.0) kg.toInt().toString() else String.format(Locale.GERMANY, "%.1f", kg)
}
