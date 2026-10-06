package de.hydrodesk.app.ui.today

import android.annotation.SuppressLint
import android.bluetooth.BluetoothAdapter
import android.content.Intent
import android.net.Uri
import android.provider.Settings
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import de.hydrodesk.app.ble.BlePermissions
import de.hydrodesk.app.ble.VerbindungsStatus
import de.hydrodesk.app.data.repository.AuthZustand
import de.hydrodesk.app.domain.Format
import de.hydrodesk.app.ui.common.Abschnitt
import de.hydrodesk.app.ui.common.Titel
import de.hydrodesk.app.ui.common.appContainer
import de.hydrodesk.app.ui.theme.WarnOrange
import de.hydrodesk.app.ui.theme.ZielGruen

/** Bildschirm "Heute": Menge, Ziel, Fortschritt, Bluetooth-Status, letzter Schluck. */
@SuppressLint("MissingPermission") // ACTION_REQUEST_ENABLE wird erst nach erteilter Berechtigung gestartet
@Composable
fun HeuteScreen(nutzer: AuthZustand.Angemeldet) {
    val container = appContainer()
    val vm: HeuteViewModel = viewModel(key = "heute_${nutzer.userId}") { HeuteViewModel(nutzer.userId, container) }
    val ui by vm.ui.collectAsStateWithLifecycle()
    val context = LocalContext.current
    var berechtigungAbgelehnt by remember { mutableStateOf(false) }

    // Bluetooth einschalten lassen (Systemdialog)
    val btEinschalten = rememberLauncherForActivityResult(ActivityResultContracts.StartActivityForResult()) {
        vm.verbinden()
    }
    // Laufzeit-Berechtigungen anfragen (Android 12+: Scan/Connect, älter: Standort)
    val berechtigungen = rememberLauncherForActivityResult(ActivityResultContracts.RequestMultiplePermissions()) { ergebnis ->
        berechtigungAbgelehnt = !ergebnis.values.all { it }
        if (!berechtigungAbgelehnt) vm.verbinden()
    }

    fun verbindenGeklickt() {
        when {
            ui.demoModus -> vm.verbinden()
            !BlePermissions.alleErteilt(context) -> berechtigungen.launch(BlePermissions.benoetigt())
            ui.status == VerbindungsStatus.BLUETOOTH_AUS ->
                btEinschalten.launch(Intent(BluetoothAdapter.ACTION_REQUEST_ENABLE))
            else -> vm.verbinden()
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Titel("Heute")

        // ---------------- Große Anzeige: getrunken / Ziel
        Abschnitt {
            Box(
                Modifier
                    .fillMaxWidth()
                    .padding(vertical = 8.dp),
                contentAlignment = Alignment.Center,
            ) {
                CircularProgressIndicator(
                    progress = { ui.fortschritt.coerceIn(0f, 1f) },
                    modifier = Modifier.size(220.dp),
                    strokeWidth = 16.dp,
                    strokeCap = StrokeCap.Round,
                    color = if (ui.zielErreicht) ZielGruen else MaterialTheme.colorScheme.primary,
                    trackColor = MaterialTheme.colorScheme.surfaceVariant,
                )
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text("heute getrunken", style = MaterialTheme.typography.labelLarge)
                    Text(
                        "${Format.ml(ui.heuteMl)} ml",
                        style = MaterialTheme.typography.displaySmall,
                        fontWeight = FontWeight.Bold,
                    )
                    Text("von ${Format.ml(ui.zielMl)} ml", style = MaterialTheme.typography.titleMedium)
                    Text("${(ui.fortschritt * 100).toInt()} %", style = MaterialTheme.typography.bodyLarge)
                }
            }
            Text(
                if (ui.zielErreicht) "Ziel erreicht ✓"
                else "noch ${Format.ml(ui.zielMl - ui.heuteMl)} ml",
                style = MaterialTheme.typography.titleMedium,
                color = if (ui.zielErreicht) ZielGruen else MaterialTheme.colorScheme.onSurface,
                modifier = Modifier.align(Alignment.CenterHorizontally),
            )
            Text(
                "Tagesziel ${ui.zielHerkunft}",
                style = MaterialTheme.typography.bodySmall,
                modifier = Modifier.align(Alignment.CenterHorizontally),
            )
        }

        // ---------------- Bluetooth / Gerät
        Abschnitt(ueberschrift = if (ui.demoModus) "HydroDesk (Demo-Modus)" else "HydroDesk") {
            Row(verticalAlignment = Alignment.CenterVertically) {
                StatusPunkt(ui.status)
                Spacer(Modifier.width(8.dp))
                Text(ui.status.text, style = MaterialTheme.typography.titleMedium)
            }
            ui.messwert?.let {
                Text(
                    "Gerät meldet: ${it.rohtext}" + (it.akkuProzent?.let { a -> " · Akku $a %" } ?: ""),
                    style = MaterialTheme.typography.bodySmall,
                    modifier = Modifier.padding(top = 4.dp),
                )
            }
            if (ui.status == VerbindungsStatus.SUCHEN && !ui.demoModus) {
                Text(
                    "Tipp: Der HydroDesk ist nur 2 Minuten nach dem Einschalten sichtbar. " +
                        "Notfalls Gerät kurz aus- und einschalten.",
                    style = MaterialTheme.typography.bodySmall,
                    modifier = Modifier.padding(top = 4.dp),
                )
            }
            if (berechtigungAbgelehnt || ui.status == VerbindungsStatus.KEINE_BERECHTIGUNG) {
                Text(
                    "Ohne Bluetooth-Berechtigung kann die App das Gerät nicht finden.",
                    color = MaterialTheme.colorScheme.error,
                    style = MaterialTheme.typography.bodySmall,
                    modifier = Modifier.padding(top = 4.dp),
                )
                OutlinedButton(onClick = {
                    // App-Einstellungen öffnen, falls "Nicht mehr fragen" gewählt wurde
                    context.startActivity(
                        Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS, Uri.fromParts("package", context.packageName, null))
                    )
                }) { Text("App-Einstellungen öffnen") }
            }

            Row(
                Modifier.padding(top = 8.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                val verbunden = ui.status in listOf(
                    VerbindungsStatus.VERBUNDEN, VerbindungsStatus.DEMO,
                    VerbindungsStatus.SUCHEN, VerbindungsStatus.VERBINDEN,
                )
                if (verbunden) {
                    OutlinedButton(onClick = vm::trennen) { Text("Trennen") }
                } else {
                    Button(onClick = { verbindenGeklickt() }) {
                        Text(if (ui.status == VerbindungsStatus.BLUETOOTH_AUS && !ui.demoModus) "Bluetooth einschalten" else "Verbinden")
                    }
                }
                if (ui.demoModus && ui.status == VerbindungsStatus.DEMO) {
                    Button(onClick = vm::schluckSimulieren) { Text("Schluck simulieren (+200 ml)") }
                }
            }
        }

        // ---------------- Letzter Schluck + heutige Einträge
        Abschnitt(ueberschrift = "Heutige Schlucke") {
            val letzter = ui.letzter
            if (letzter == null) {
                Text("Heute noch nichts getrunken.")
            } else {
                Text(
                    "Zuletzt: +${Format.ml(letzter.ml)} ml um ${Format.uhrzeit(letzter.timestamp)} Uhr",
                    style = MaterialTheme.typography.titleMedium,
                )
                Spacer(Modifier.size(8.dp))
                ui.eintraege.take(8).forEach { e ->
                    HorizontalDivider()
                    Row(Modifier.fillMaxWidth().padding(vertical = 6.dp)) {
                        Text("${Format.uhrzeit(e.timestamp)} Uhr", Modifier.weight(1f))
                        Text(e.device, Modifier.weight(1f), style = MaterialTheme.typography.bodySmall)
                        Text("+${Format.ml(e.ml)} ml" + if (e.synced || nutzer.offline) "" else " ⟳")
                    }
                }
                if (ui.eintraege.size > 8) Text("… und ${ui.eintraege.size - 8} weitere", style = MaterialTheme.typography.bodySmall)
            }
        }

        // ---------------- Sync-Hinweis
        Text(
            when {
                nutzer.offline -> "Offline-Modus: Einträge werden nur auf diesem Handy gespeichert."
                ui.offeneSyncs == 0 -> "✓ Alle Einträge sind in Supabase gespeichert."
                else -> "⟳ ${ui.offeneSyncs} Einträge werden hochgeladen, sobald Internet da ist."
            },
            style = MaterialTheme.typography.bodySmall,
        )
    }
}

/** Farbiger Punkt: grün = verbunden, blau = suchen, orange = Problem, grau = getrennt. */
@Composable
private fun StatusPunkt(status: VerbindungsStatus) {
    val farbe = when (status) {
        VerbindungsStatus.VERBUNDEN, VerbindungsStatus.DEMO -> ZielGruen
        VerbindungsStatus.SUCHEN, VerbindungsStatus.VERBINDEN -> MaterialTheme.colorScheme.primary
        VerbindungsStatus.KEINE_BERECHTIGUNG, VerbindungsStatus.BLUETOOTH_AUS -> WarnOrange
        VerbindungsStatus.GETRENNT -> Color.Gray
    }
    Box(
        Modifier
            .size(14.dp)
            .background(farbe, CircleShape)
    )
}
