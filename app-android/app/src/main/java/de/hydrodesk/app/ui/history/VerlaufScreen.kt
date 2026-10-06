package de.hydrodesk.app.ui.history

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.PathEffect
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import de.hydrodesk.app.data.local.DailySummary
import de.hydrodesk.app.data.repository.AuthZustand
import de.hydrodesk.app.domain.Format
import de.hydrodesk.app.ui.common.Abschnitt
import de.hydrodesk.app.ui.common.Titel
import de.hydrodesk.app.ui.common.appContainer
import de.hydrodesk.app.ui.theme.ZielGruen
import java.time.LocalDate
import java.util.Locale

/** Bildschirm "Verlauf": Balkendiagramm der letzten 7 Tage + Liste pro Tag. */
@Composable
fun VerlaufScreen(nutzer: AuthZustand.Angemeldet) {
    val container = appContainer()
    val vm: VerlaufViewModel = viewModel(key = "verlauf_${nutzer.userId}") { VerlaufViewModel(nutzer.userId, container) }
    val ui by vm.ui.collectAsStateWithLifecycle()

    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = androidx.compose.foundation.layout.PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        item { Titel("Verlauf") }
        item {
            Abschnitt(ueberschrift = "Letzte 7 Tage") {
                WochenDiagramm(ui.woche, ui.zielMl)
                Text(
                    "Gestrichelte Linie = Tagesziel (${Format.ml(ui.zielMl)} ml), grün = Ziel erreicht",
                    style = MaterialTheme.typography.bodySmall,
                    modifier = Modifier.padding(top = 8.dp),
                )
            }
        }
        if (ui.tage.isEmpty()) {
            item { Text("Noch keine Einträge. Verbinde den HydroDesk oder schalte den Demo-Modus ein.") }
        }
        items(ui.tage, key = { it.day }) { tag -> TagesZeile(tag, ui.zielMl) }
    }
}

/**
 * Einfaches Balkendiagramm, selbst gezeichnet mit Compose Canvas
 * (keine zusätzliche Diagramm-Bibliothek nötig).
 */
@Composable
fun WochenDiagramm(woche: List<TagesBalken>, zielMl: Int) {
    if (woche.isEmpty()) return
    val balkenFarbe = MaterialTheme.colorScheme.primary
    val zielFarbe = ZielGruen
    // Höchster Wert bestimmt die Skala (mindestens das Ziel, plus 10 % Luft nach oben)
    val maxWert = maxOf(zielMl, woche.maxOf { it.ml }).coerceAtLeast(1) * 1.1f

    Column {
        Canvas(
            Modifier
                .fillMaxWidth()
                .height(180.dp)
        ) {
            val platzProTag = size.width / woche.size
            val balkenBreite = platzProTag * 0.6f
            woche.forEachIndexed { i, balken ->
                val hoehe = size.height * balken.ml / maxWert
                drawRoundRect(
                    color = if (balken.ml >= zielMl) zielFarbe else balkenFarbe,
                    topLeft = Offset(i * platzProTag + (platzProTag - balkenBreite) / 2, size.height - hoehe),
                    size = Size(balkenBreite, hoehe),
                    cornerRadius = CornerRadius(6.dp.toPx()),
                )
            }
            // Ziel-Linie (gestrichelt)
            val zielY = size.height - size.height * zielMl / maxWert
            drawLine(
                color = zielFarbe,
                start = Offset(0f, zielY),
                end = Offset(size.width, zielY),
                strokeWidth = 2.dp.toPx(),
                pathEffect = PathEffect.dashPathEffect(floatArrayOf(16f, 10f)),
            )
        }
        // Beschriftung unter den Balken: Wochentag + Liter
        Row(Modifier.fillMaxWidth()) {
            woche.forEach { balken ->
                Column(Modifier.weight(1f), horizontalAlignment = Alignment.CenterHorizontally) {
                    Text(Format.wochentagKurz(balken.tag), style = MaterialTheme.typography.labelMedium)
                    Text(
                        String.format(Locale.GERMANY, "%.1f l", balken.ml / 1000.0),
                        style = MaterialTheme.typography.labelSmall,
                    )
                }
            }
        }
    }
}

@Composable
private fun TagesZeile(tag: DailySummary, zielMl: Int) {
    val datum = LocalDate.parse(tag.day)
    val erreicht = tag.totalMl >= zielMl
    Abschnitt {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f)) {
                Text(Format.datumLang(datum), style = MaterialTheme.typography.titleMedium)
                Text("${tag.drinks} Schlucke", style = MaterialTheme.typography.bodySmall)
            }
            Text(
                "${Format.ml(tag.totalMl)} ml" + if (erreicht) " ✓" else "",
                style = MaterialTheme.typography.titleMedium,
                color = if (erreicht) ZielGruen else MaterialTheme.colorScheme.onSurface,
            )
        }
        LinearProgressIndicator(
            progress = { (tag.totalMl.toFloat() / zielMl).coerceIn(0f, 1f) },
            modifier = Modifier
                .fillMaxWidth()
                .padding(top = 8.dp),
            color = if (erreicht) ZielGruen else MaterialTheme.colorScheme.primary,
        )
    }
}
