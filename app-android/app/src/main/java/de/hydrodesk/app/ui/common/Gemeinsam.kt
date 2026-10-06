package de.hydrodesk.app.ui.common

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import de.hydrodesk.app.AppContainer
import de.hydrodesk.app.HydroDeskApp

/** Holt den AppContainer (alle Repositories) aus der Application. */
@Composable
fun appContainer(): AppContainer =
    (LocalContext.current.applicationContext as HydroDeskApp).container

/** Überschrift oben auf jedem Bildschirm. */
@Composable
fun Titel(text: String, modifier: Modifier = Modifier) {
    Text(
        text = text,
        style = MaterialTheme.typography.headlineMedium,
        modifier = modifier.padding(bottom = 8.dp),
    )
}

/** Karte mit optionaler Überschrift – wird auf allen Bildschirmen verwendet. */
@Composable
fun Abschnitt(
    modifier: Modifier = Modifier,
    ueberschrift: String? = null,
    inhalt: @Composable ColumnScope.() -> Unit,
) {
    Card(modifier = modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp)) {
            if (ueberschrift != null) {
                Text(
                    ueberschrift,
                    style = MaterialTheme.typography.titleMedium,
                    modifier = Modifier.padding(bottom = 8.dp),
                )
            }
            inhalt()
        }
    }
}
