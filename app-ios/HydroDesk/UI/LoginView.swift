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

    private enum Feld { case name, email, passwort }

    @State private var fehlerFeld: Feld?
    @FocusState private var fokus: Feld?

    var body: some View {
        ScrollView {
            VStack(spacing: 16) {
                // Marke oben
                VStack(spacing: 8) {
                    AppMarke(groesse: 96)
                        .padding(.bottom, 8)
                    Text("HydroDesk").font(.title.bold())
                    Text("Dein Trink-Tracker für den Schreibtisch")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                        .multilineTextAlignment(.center)
                }
                .padding(.top, 24)
                .padding(.bottom, 8)
                .accessibilityElement(children: .combine)

                Picker("Modus", selection: $registrieren) {
                    Text("Anmelden").tag(false)
                    Text("Registrieren").tag(true)
                }
                .pickerStyle(.segmented)
                .onChange(of: registrieren) { _, _ in
                    fehler = nil
                    fehlerFeld = nil
                }

                // Felder als Zeilen in einer Karte (je 50 pt)
                VStack(spacing: 0) {
                    if registrieren {
                        zeile(.name) {
                            TextField("Name", text: $name)
                                .textContentType(.name)
                        }
                        Divider()
                    }
                    zeile(.email) {
                        TextField("E-Mail", text: $email)
                            .textContentType(.emailAddress)
                            .keyboardType(.emailAddress)
                            .textInputAutocapitalization(.never)
                            .autocorrectionDisabled()
                    }
                    Divider()
                    zeile(.passwort) {
                        SecureField("Passwort (mind. 6 Zeichen)", text: $passwort)
                            .textContentType(registrieren ? .newPassword : .password)
                    }
                }
                .background(Theme.karte, in: RoundedRectangle(cornerRadius: Theme.radiusFeld))
                .clipShape(RoundedRectangle(cornerRadius: Theme.radiusFeld))

                if let fehler { Rueckmeldung(art: .fehler, text: fehler) }
                if let info { Rueckmeldung(art: .info, text: info) }

                if !container.auth.supabaseEingerichtet {
                    HStack(alignment: .firstTextBaseline, spacing: 8) {
                        Image(systemName: "exclamationmark.triangle.fill").foregroundStyle(Theme.warnorangePunkt)
                        Text("Cloud noch nicht eingerichtet – nur ‚Ohne Konto testen‘ möglich")
                            .foregroundStyle(.secondary)
                    }
                    .font(.footnote)
                    .padding(12)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .background(Theme.eingabeHintergrund, in: RoundedRectangle(cornerRadius: Theme.radiusFeld))
                    .accessibilityElement(children: .combine)
                }

                Button(action: absenden) {
                    KnopfText(text: laedt ? (registrieren ? "Konto erstellen …" : "Anmelden …")
                                          : (registrieren ? "Konto erstellen" : "Anmelden"),
                              laedt: laedt)
                }
                .buttonStyle(.hydro(.haupt, hoehe: 50))
                .disabled(laedt || !container.auth.supabaseEingerichtet)

                VStack(spacing: 8) {
                    Button("Ohne Konto testen") { container.auth.offlineStarten() }
                        .buttonStyle(.hydro(.sekundaer))
                        .disabled(laedt)
                    Text("Daten bleiben nur auf dem iPhone")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
            .padding(Theme.rand)
        }
        .background(Theme.bildschirmHintergrund)
        .scrollDismissesKeyboard(.interactively)
    }

    /// Eine Eingabezeile (50 pt). Bei einem Fehler: roter Rand (1,5 pt).
    private func zeile<Inhalt: View>(_ feld: Feld, @ViewBuilder inhalt: () -> Inhalt) -> some View {
        inhalt()
            .focused($fokus, equals: feld)
            .padding(.horizontal, 16)
            .frame(minHeight: 50)
            .overlay {
                if fehlerFeld == feld {
                    Rectangle().strokeBorder(Theme.rotText, lineWidth: 1.5)
                }
            }
    }

    private func absenden() {
        fehler = nil
        fehlerFeld = nil
        info = nil
        // Eingaben prüfen, bevor etwas an den Server geht (gleiche Regeln wie in der Android-App)
        if registrieren && name.trimmingCharacters(in: .whitespaces).isEmpty {
            fehler = "Bitte einen Namen eingeben."; fehlerFeld = .name; return
        }
        if !email.contains("@") || !email.contains(".") {
            fehler = "Bitte eine gültige E-Mail-Adresse eingeben."; fehlerFeld = .email; return
        }
        if passwort.count < 6 {
            fehler = "Das Passwort braucht mindestens 6 Zeichen."; fehlerFeld = .passwort; return
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
