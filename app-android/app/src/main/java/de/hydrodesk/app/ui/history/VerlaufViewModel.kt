package de.hydrodesk.app.ui.history

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import de.hydrodesk.app.AppContainer
import de.hydrodesk.app.data.local.DailySummary
import de.hydrodesk.app.domain.GoalCalculator
import de.hydrodesk.app.domain.Tage
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn
import java.time.LocalDate

/** Ein Balken im Diagramm. */
data class TagesBalken(val tag: LocalDate, val ml: Int)

data class VerlaufUiState(
    val woche: List<TagesBalken> = emptyList(),   // genau 7 Tage, ältester zuerst
    val tage: List<DailySummary> = emptyList(),   // alle Tage mit Einträgen (30 Tage)
    val zielMl: Int = GoalCalculator.STANDARD_ZIEL_ML,
)

class VerlaufViewModel(userId: String, container: AppContainer) : ViewModel() {
    val ui: StateFlow<VerlaufUiState> = combine(
        container.drinkRepository.tagesSummen(userId, 30),
        container.profileRepository.profil,
    ) { summen, profil ->
        val proTag = summen.associate { it.day to it.totalMl }
        val heute = Tage.heute()
        // Die letzten 7 Tage – auch Tage ohne Eintrag (dann 0 ml)
        val woche = (6 downTo 0).map { vor ->
            val tag = heute.minusDays(vor.toLong())
            TagesBalken(tag, proTag[tag.toString()] ?: 0)
        }
        VerlaufUiState(woche, summen, profil?.dailyGoalMl ?: GoalCalculator.STANDARD_ZIEL_ML)
    }.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), VerlaufUiState())
}
