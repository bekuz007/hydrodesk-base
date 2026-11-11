// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE

import SwiftUI

/// Bildschirm „Anmelden / Registrieren“ (E-Mail + Passwort über Supabase Auth)
/// plus „Ohne Konto testen“ (nur lokal).
struct LoginView: View {
    @Environment(AppContainer.self) private var container

    @State private var registrieren = false
    @State private var name = ""
    @State private var email = ""
    @State private var passwort = ""
    @State private var laedt = false
    @State private var fehler: String?
    @State private var info: String?

    var body: some View {
        ScrollView {
            VStack(spacing: 14) {
                Spacer().frame(height: 24)
                Text("💧").font(.system(size: 60))
                Text("HydroDesk").font(.largeTitle.bold())
                Text("Dein Trink-Tracker für den Schreibtisch")
                    .font(.subheadline)
                    .multilineTextAlignment(.center)
                Spacer().frame(height: 8)

                if !container.auth.supabaseEingerichtet {
                    Text("Supabase ist noch nicht eingerichtet.\n"
                        + "SUPABASE_URL und SUPABASE_ANON_KEY in Config/Secrets.xcconfig eintragen "
                        + "und die App neu bauen (siehe README). Bis dahin geht nur „Ohne Konto testen“.")
                        .font(.callout)
                        .foregroundStyle(.red)
                        .padding(12)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .background(Color.red.opacity(0.1), in: RoundedRectangle(cornerRadius: 12))
                }

                Picker("Modus", selection: $registrieren) {
                    Text("Anmelden").tag(false)
                    Text("Registrieren").tag(true)
                }
                .pickerStyle(.segmented)

                if registrieren {
                    TextField("Name", text: $name)
                        .textContentType(.name)
                        .textFieldStyle(.roundedBorder)
                }
                TextField("E-Mail", text: $email)
                    .textContentType(.emailAddress)
                    .keyboardType(.emailAddress)
                    .textInputAutocapitalization(.never)
                    .autocorrectionDisabled()
                    .textFieldStyle(.roundedBorder)
                SecureField("Passwort (mind. 6 Zeichen)", text: $passwort)
                    .textContentType(registrieren ? .newPassword : .password)
                    .textFieldStyle(.roundedBorder)

                if let fehler { Text(fehler).foregroundStyle(.red).frame(maxWidth: .infinity, alignment: .leading) }
                if let info { Text(info).foregroundStyle(Theme.wasserBlau).frame(maxWidth: .infinity, alignment: .leading) }

                Button(action: absenden) {
                    if laedt {
                        ProgressView().frame(maxWidth: .infinity)
                    } else {
                        Text(registrieren ? "Konto erstellen" : "Anmelden").frame(maxWidth: .infinity)
                    }
                }
                .buttonStyle(.borderedProminent)
                .controlSize(.large)
                .disabled(laedt || !container.auth.supabaseEingerichtet)

                Button("Ohne Konto testen (Daten bleiben nur auf dem iPhone)") {
                    container.auth.offlineStarten()
                }
                .multilineTextAlignment(.center)
            }
            .padding(24)
        }
        .scrollDismissesKeyboard(.interactively)
    }

    private func absenden() {
        fehler = nil
        info = nil
        // Eingaben prüfen, bevor etwas an den Server geht (gleiche Regeln wie in der Android-App)
        if registrieren && name.trimmingCharacters(in: .whitespaces).isEmpty {
            fehler = "Bitte einen Namen eingeben."; return
        }
        if !email.contains("@") || !email.contains(".") {
            fehler = "Bitte eine gültige E-Mail-Adresse eingeben."; return
        }
        if passwort.count < 6 {
            fehler = "Das Passwort braucht mindestens 6 Zeichen."; return
        }
        laedt = true
        Task {
            if registrieren {
                switch await container.auth.registrieren(name: name, email: email, passwort: passwort) {
                case .success(.angemeldet):
                    break   // die App wechselt automatisch zum Hauptbildschirm
                case .success(.bestaetigungNoetig):
                    info = "Konto angelegt. Bitte den Bestätigungslink in der E-Mail öffnen und dann anmelden."
                    registrieren = false
                case .failure(let f):
                    fehler = f.text
                }
            } else {
                fehler = await container.auth.anmelden(email: email, passwort: passwort)
            }
            laedt = false
        }
    }
}
