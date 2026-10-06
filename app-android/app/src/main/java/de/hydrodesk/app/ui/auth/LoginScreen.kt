package de.hydrodesk.app.ui.auth

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawingPadding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.SegmentedButton
import androidx.compose.material3.SegmentedButtonDefaults
import androidx.compose.material3.SingleChoiceSegmentedButtonRow
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import de.hydrodesk.app.ui.common.appContainer

/** Bildschirm "Anmelden / Registrieren" (E-Mail + Passwort über Supabase Auth). */
@Composable
fun LoginScreen() {
    val container = appContainer()
    val vm: LoginViewModel = viewModel { LoginViewModel(container.authRepository) }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .safeDrawingPadding()
            .verticalScroll(rememberScrollState())
            .padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Spacer(Modifier.height(24.dp))
        Text("💧", style = MaterialTheme.typography.displayMedium)
        Text("HydroDesk", style = MaterialTheme.typography.headlineLarge)
        Text(
            "Dein Trink-Tracker für den Schreibtisch",
            style = MaterialTheme.typography.bodyMedium,
            textAlign = TextAlign.Center,
        )
        Spacer(Modifier.height(8.dp))

        if (!vm.supabaseEingerichtet) {
            Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.errorContainer)) {
                Text(
                    "Supabase ist noch nicht eingerichtet.\n" +
                        "SUPABASE_URL und SUPABASE_ANON_KEY in local.properties eintragen " +
                        "und die App neu bauen (siehe README). Bis dahin geht nur \"Ohne Konto testen\".",
                    modifier = Modifier.padding(16.dp),
                    color = MaterialTheme.colorScheme.onErrorContainer,
                )
            }
        }

        // Umschalter Anmelden / Registrieren
        SingleChoiceSegmentedButtonRow(Modifier.fillMaxWidth()) {
            SegmentedButton(
                selected = !vm.registrieren,
                onClick = { vm.registrieren = false },
                shape = SegmentedButtonDefaults.itemShape(index = 0, count = 2),
            ) { Text("Anmelden") }
            SegmentedButton(
                selected = vm.registrieren,
                onClick = { vm.registrieren = true },
                shape = SegmentedButtonDefaults.itemShape(index = 1, count = 2),
            ) { Text("Registrieren") }
        }

        if (vm.registrieren) {
            OutlinedTextField(
                value = vm.name,
                onValueChange = { vm.name = it },
                label = { Text("Name") },
                singleLine = true,
                modifier = Modifier.fillMaxWidth(),
            )
        }
        OutlinedTextField(
            value = vm.email,
            onValueChange = { vm.email = it },
            label = { Text("E-Mail") },
            singleLine = true,
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Email),
            modifier = Modifier.fillMaxWidth(),
        )
        OutlinedTextField(
            value = vm.passwort,
            onValueChange = { vm.passwort = it },
            label = { Text("Passwort (mind. 6 Zeichen)") },
            singleLine = true,
            visualTransformation = PasswordVisualTransformation(),
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password),
            modifier = Modifier.fillMaxWidth(),
        )

        vm.fehler?.let { Text(it, color = MaterialTheme.colorScheme.error) }
        vm.info?.let { Text(it, color = MaterialTheme.colorScheme.primary) }

        Button(
            onClick = vm::absenden,
            enabled = !vm.laedt && vm.supabaseEingerichtet,
            modifier = Modifier.fillMaxWidth(),
        ) {
            if (vm.laedt) {
                CircularProgressIndicator(Modifier.size(20.dp), strokeWidth = 2.dp)
            } else {
                Text(if (vm.registrieren) "Konto erstellen" else "Anmelden")
            }
        }

        TextButton(onClick = vm::offlineTesten) {
            Text("Ohne Konto testen (Daten bleiben nur auf dem Handy)")
        }
    }
}
