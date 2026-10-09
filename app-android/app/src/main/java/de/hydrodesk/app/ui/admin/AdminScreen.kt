// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE

package de.hydrodesk.app.ui.admin

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.lifecycle.viewmodel.compose.viewModel
import de.hydrodesk.app.data.remote.UserTodayDto
import de.hydrodesk.app.data.repository.AdminRepository
import de.hydrodesk.app.domain.Format
import de.hydrodesk.app.domain.GoalCalculator
import de.hydrodesk.app.ui.common.Abschnitt
import de.hydrodesk.app.ui.common.Titel
import de.hydrodesk.app.ui.common.appContainer
import de.hydrodesk.app.ui.theme.ZielGruen
import kotlinx.coroutines.launch

/** Lädt die Admin-Übersicht (View user_today in Supabase). */
class AdminViewModel(private val admin: AdminRepository) : ViewModel() {
    var nutzer by mutableStateOf<List<UserTodayDto>>(emptyList())
        private set
    var laedt by mutableStateOf(false)
        private set
    var fehler by mutableStateOf<String?>(null)
        private set

    fun laden() {
        laedt = true
        fehler = null
        viewModelScope.launch {
            admin.alleNutzerHeute()
                .onSuccess { nutzer = it }
                .onFailure { fehler = "Laden fehlgeschlagen: ${it.message}" }
            laedt = false
        }
    }
}

/**
 * Admin-Bildschirm: alle Nutzer mit ihrer heutigen Trinkmenge.
 * Nur sichtbar für Profile mit role = 'admin'. Selbst wenn jemand ihn öffnen
 * könnte: Supabase (Row Level Security) liefert Nicht-Admins nur die eigene Zeile.
 */
@Composable
fun AdminScreen(onZurueck: () -> Unit) {
    val container = appContainer()
    val vm: AdminViewModel = viewModel { AdminViewModel(container.adminRepository) }
    LaunchedEffect(Unit) { vm.laden() }

    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        item {
            Row(verticalAlignment = Alignment.CenterVertically) {
                IconButton(onClick = onZurueck) {
                    Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Zurück")
                }
                Titel("Admin: Heute", Modifier.weight(1f))
                IconButton(onClick = vm::laden) {
                    Icon(Icons.Filled.Refresh, contentDescription = "Neu laden")
                }
            }
            Text(
                "Alle Nutzer mit der heutigen Trinkmenge. Bearbeiten geht im Supabase-Dashboard (Table Editor).",
                style = MaterialTheme.typography.bodySmall,
            )
        }
        if (vm.laedt) item { CircularProgressIndicator() }
        vm.fehler?.let { f -> item { Text(f, color = MaterialTheme.colorScheme.error) } }
        items(vm.nutzer, key = { it.id }) { n -> NutzerZeile(n) }
    }
}

@Composable
private fun NutzerZeile(n: UserTodayDto) {
    val ziel = n.dailyGoalMl ?: GoalCalculator.STANDARD_ZIEL_ML
    val erreicht = n.heuteMl >= ziel
    Abschnitt {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f)) {
                Text(
                    (n.name?.takeIf { it.isNotBlank() } ?: "(ohne Name)") + if (n.role == "admin") " · Admin" else "",
                    style = MaterialTheme.typography.titleMedium,
                )
                Text(n.email ?: "", style = MaterialTheme.typography.bodySmall)
            }
            Text(
                "${Format.ml(n.heuteMl)} / ${Format.ml(ziel)} ml",
                color = if (erreicht) ZielGruen else MaterialTheme.colorScheme.onSurface,
            )
        }
        LinearProgressIndicator(
            progress = { (n.heuteMl.toFloat() / ziel).coerceIn(0f, 1f) },
            modifier = Modifier
                .fillMaxWidth()
                .padding(top = 8.dp),
            color = if (erreicht) ZielGruen else MaterialTheme.colorScheme.primary,
        )
    }
}
