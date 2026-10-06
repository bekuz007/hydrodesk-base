package de.hydrodesk.app.ui.profile

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import de.hydrodesk.app.BuildConfig
import de.hydrodesk.app.data.repository.AuthZustand
import de.hydrodesk.app.domain.Format
import de.hydrodesk.app.ui.common.Abschnitt
import de.hydrodesk.app.ui.common.Titel
import de.hydrodesk.app.ui.common.appContainer
import java.util.Locale

/** Bildschirm "Profil / Einstellungen". */
@Composable
fun ProfilScreen(nutzer: AuthZustand.Angemeldet, onAdminOeffnen: () -> Unit) {
    val container = appContainer()
    val vm: ProfilViewModel = viewModel(key = "profil_${nutzer.userId}") { ProfilViewModel(nutzer.userId, container) }
    val profil by vm.profil.collectAsStateWithLifecycle()
    val demo by vm.demoModus.collectAsStateWithLifecycle()
    val offen by vm.offeneSyncs.collectAsStateWithLifecycle()
    var abmeldenFragen by remember { mutableStateOf(false) }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Titel("Profil")

        // ---------------- Körperdaten -> Tagesziel
        Abschnitt(ueberschrift = "Körperdaten") {
            OutlinedTextField(
                value = vm.name,
                onValueChange = { vm.name = it; vm.geaendert() },
                label = { Text("Name") },
                singleLine = true,
                modifier = Modifier.fillMaxWidth(),
            )
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.padding(top = 8.dp)) {
                OutlinedTextField(
                    value = vm.gewicht,
                    onValueChange = { vm.gewicht = it; vm.geaendert() },
                    label = { Text("Gewicht (kg)") },
                    singleLine = true,
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
                    modifier = Modifier.weight(1f),
                )
                OutlinedTextField(
                    value = vm.groesse,
                    onValueChange = { vm.groesse = it; vm.geaendert() },
                    label = { Text("Größe (cm)") },
                    singleLine = true,
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                    modifier = Modifier.weight(1f),
                )
            }

            val vorschau = vm.zielVorschau()
            Text(
                if (vorschau != null) {
                    "Tagesziel: ${Format.ml(vorschau.first)} ml " +
                        "(Körperoberfläche ${String.format(Locale.GERMANY, "%.2f", vorschau.second)} m² × 1.500 ml)"
                } else {
                    "Gewicht und Größe eingeben, dann wird das Tagesziel berechnet."
                },
                style = MaterialTheme.typography.titleSmall,
                modifier = Modifier.padding(top = 8.dp),
            )
            Text(
                "Formel nach Mosteller, gerundet auf 50 ml, 1.500–3.500 ml. Richtwert, keine medizinische Empfehlung.",
                style = MaterialTheme.typography.bodySmall,
            )
            Button(
                onClick = vm::speichern,
                enabled = !vm.speichert,
                modifier = Modifier.padding(top = 8.dp),
            ) { Text(if (vm.speichert) "Speichert …" else "Speichern") }
            vm.meldung?.let { Text(it, style = MaterialTheme.typography.bodyMedium, modifier = Modifier.padding(top = 4.dp)) }
        }

        // ---------------- Einstellungen
        Abschnitt(ueberschrift = "Einstellungen") {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Column(Modifier.weight(1f)) {
                    Text("Demo-Modus", style = MaterialTheme.typography.titleSmall)
                    Text(
                        "Simuliert den HydroDesk – zum Vorführen ohne Hardware.",
                        style = MaterialTheme.typography.bodySmall,
                    )
                }
                Switch(checked = demo, onCheckedChange = vm::setDemoModus)
            }
            if (!nutzer.offline) {
                Text(
                    if (offen == 0) "Synchronisierung: alles hochgeladen ✓"
                    else "Synchronisierung: $offen Einträge warten",
                    style = MaterialTheme.typography.bodyMedium,
                    modifier = Modifier.padding(top = 12.dp),
                )
                OutlinedButton(onClick = vm::jetztSynchronisieren, modifier = Modifier.padding(top = 4.dp)) {
                    Text("Jetzt synchronisieren")
                }
            }
        }

        // ---------------- Konto
        Abschnitt(ueberschrift = "Konto") {
            Text(nutzer.email, style = MaterialTheme.typography.bodyLarge)
            if (nutzer.offline) {
                Text(
                    "Offline-Modus: Daten werden nur auf diesem Handy gespeichert.",
                    style = MaterialTheme.typography.bodySmall,
                )
            } else {
                Text("Rolle: ${profil?.role ?: "user"}", style = MaterialTheme.typography.bodySmall)
            }
            if (profil?.istAdmin == true) {
                Button(onClick = onAdminOeffnen, modifier = Modifier.padding(top = 8.dp)) {
                    Text("Admin: alle Nutzer anzeigen")
                }
            }
            OutlinedButton(onClick = { abmeldenFragen = true }, modifier = Modifier.padding(top = 8.dp)) {
                Text(if (nutzer.offline) "Offline-Modus beenden" else "Abmelden")
            }
        }

        Text(
            "HydroDesk App ${BuildConfig.VERSION_NAME} · Schulprojekt FI-AE",
            style = MaterialTheme.typography.bodySmall,
        )
    }

    if (abmeldenFragen) {
        AlertDialog(
            onDismissRequest = { abmeldenFragen = false },
            title = { Text("Abmelden?") },
            text = {
                Text(
                    if (offen > 0 && !nutzer.offline)
                        "$offen Einträge sind noch nicht hochgeladen. Sie bleiben auf dem Handy und werden " +
                            "nach dem nächsten Login mit demselben Konto hochgeladen."
                    else "Deine Daten bleiben gespeichert."
                )
            },
            confirmButton = {
                TextButton(onClick = { abmeldenFragen = false; vm.abmelden() }) { Text("Abmelden") }
            },
            dismissButton = {
                TextButton(onClick = { abmeldenFragen = false }) { Text("Abbrechen") }
            },
        )
    }
}
