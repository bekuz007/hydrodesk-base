// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE

package de.hydrodesk.app.ui.today

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import de.hydrodesk.app.AppContainer
import de.hydrodesk.app.ble.DeviceReading
import de.hydrodesk.app.ble.VerbindungsStatus
import de.hydrodesk.app.data.local.DrinkEntry
import de.hydrodesk.app.domain.GoalCalculator
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn

/** Alles, was der Heute-Bildschirm anzeigt. */
data class HeuteUiState(
    val heuteMl: Int = 0,
    val zielMl: Int = GoalCalculator.STANDARD_ZIEL_ML,
    val zielHerkunft: String = "",
    val eintraege: List<DrinkEntry> = emptyList(),
    val status: VerbindungsStatus = VerbindungsStatus.GETRENNT,
    val messwert: DeviceReading? = null,
    val offeneSyncs: Int = 0,
    val demoModus: Boolean = false,
) {
    val fortschritt: Float get() = if (zielMl > 0) heuteMl.toFloat() / zielMl else 0f
    val zielErreicht: Boolean get() = heuteMl >= zielMl
    val letzter: DrinkEntry? get() = eintraege.firstOrNull()
}

class HeuteViewModel(userId: String, private val container: AppContainer) : ViewModel() {
    private val geraete = container.geraeteManager
    private val drinks = container.drinkRepository

    val ui: StateFlow<HeuteUiState> = combine(
        drinks.heuteSumme(userId),
        drinks.heuteEintraege(userId),
        container.profileRepository.profil,
        geraete.status,
        geraete.letzterMesswert,
    ) { summe, eintraege, profil, status, messwert ->
        // Tagesziel: 1. aus dem Profil, 2. vom Gerät, 3. Standardwert
        val (ziel, herkunft) = when {
            profil?.dailyGoalMl != null -> profil.dailyGoalMl to "aus deinem Profil"
            messwert?.zielMl != null -> messwert.zielMl to "vom HydroDesk"
            else -> GoalCalculator.STANDARD_ZIEL_ML to "Standardwert – bitte Profil ausfüllen"
        }
        HeuteUiState(summe, ziel, herkunft, eintraege, status, messwert)
    }.combine(drinks.anzahlNichtSynchronisiert(userId)) { zustand, offen ->
        zustand.copy(offeneSyncs = offen)
    }.combine(container.settings.demoModus) { zustand, demo ->
        zustand.copy(demoModus = demo)
    }.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), HeuteUiState())

    fun verbinden() = geraete.verbinden()
    fun trennen() = geraete.trennen()
    fun schluckSimulieren() = geraete.schluckSimulieren(200)
}
