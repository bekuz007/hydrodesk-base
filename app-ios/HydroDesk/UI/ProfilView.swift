// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE

import SwiftData
import SwiftUI

/// Bildschirm „Profil / Einstellungen“.
struct ProfilView: View {
    let nutzer: AngemeldeterNutzer
    @Environment(AppContainer.self) private var container

    @Query private var offene: [DrinkEntry]

    // Eingabefelder (als Text, damit auch halbe Eingaben wie „72,“ möglich sind)
    @State private var eingabe = Eingabe()
    /// Was zuletzt automatisch aus dem Profil eingetragen wurde (so merkt die App, ob der Nutzer etwas geändert hat)
    @State private var gefuellt = Eingabe()
    @State private var speichert = false
    @State private var meldung: String?
    @State private var abmeldenFragen = false

    init(nutzer: AngemeldeterNutzer) {
        self.nutzer = nutzer
        let uid = nutzer.userId
        _offene = Query(filter: #Predicate<DrinkEntry> { $0.userId == uid && $0.synced == false })
    }

    private struct Eingabe: Equatable {
        var name = ""
        var gewicht = ""
        var groesse = ""
    }

    private var profil: ProfileDto? { container.profile.profil }

    var body: some View {
        BildschirmRahmen {
            koerperdaten
            einstellungen
            konto
            Text("HydroDesk App \(HydroKonstanten.appVersion) · Schulprojekt FI-AE")
                .font(.footnote)
                .foregroundStyle(.secondary)
        }
        .onAppear(perform: felderFuellen)
        .onChange(of: container.profile.profil) { _, _ in felderFuellen() }
        .alert("Abmelden?", isPresented: $abmeldenFragen) {
            Button("Abmelden", role: .destructive) {
                Task { await container.auth.abmelden() }
            }
            Button("Abbrechen", role: .cancel) {}
        } message: {
            Text(!offene.isEmpty && !nutzer.offline
                ? "\(offene.count) Einträge sind noch nicht hochgeladen. Sie bleiben auf dem iPhone und werden nach dem nächsten Login mit demselben Konto hochgeladen."
                : "Deine Daten bleiben gespeichert.")
        }
    }

    // ---------------- Körperdaten → Tagesziel
    private var koerperdaten: some View {
        let vorschau = ProfilPruefung.zielVorschau(gewichtText: eingabe.gewicht, groesseText: eingabe.groesse)
        return Karte("Körperdaten") {
            TextField("Name", text: $eingabe.name)
                .textContentType(.name)
                .textFieldStyle(.roundedBorder)
            HStack {
                TextField("Gewicht (kg)", text: $eingabe.gewicht)
                    .keyboardType(.decimalPad)
                    .textFieldStyle(.roundedBorder)
                TextField("Größe (cm)", text: $eingabe.groesse)
                    .keyboardType(.numberPad)
                    .textFieldStyle(.roundedBorder)
            }
            if let vorschau {
                Text("Tagesziel: \(Format.ml(vorschau.zielMl)) ml (Körperoberfläche \(Format.dezimal(vorschau.kof, stellen: 2)) m² × 1.500 ml)")
                    .font(.subheadline.weight(.semibold))
            } else {
                Text("Gewicht und Größe eingeben, dann wird das Tagesziel berechnet.")
                    .font(.subheadline.weight(.semibold))
            }
            Text("Formel nach Mosteller, gerundet auf 50 ml, 1.500–3.500 ml. Richtwert, keine medizinische Empfehlung.")
                .font(.footnote)
                .foregroundStyle(.secondary)
            Button(speichert ? "Speichert …" : "Speichern", action: speichern)
                .buttonStyle(.borderedProminent)
                .disabled(speichert)
            if let meldung { Text(meldung).font(.callout) }
        }
    }

    // ---------------- Einstellungen
    private var einstellungen: some View {
        Karte("Einstellungen") {
            Toggle(isOn: Binding(
                get: { container.geraete.demoModus },
                set: { container.geraete.setDemoModus($0) }
            )) {
                VStack(alignment: .leading) {
                    Text("Demo-Modus").font(.subheadline.weight(.semibold))
                    Text("Simuliert den HydroDesk – zum Vorführen ohne Hardware.")
                        .font(.footnote).foregroundStyle(.secondary)
                }
            }
            if !nutzer.offline {
                Text(offene.isEmpty ? "Synchronisierung: alles hochgeladen ✓"
                                    : "Synchronisierung: \(offene.count) Einträge warten")
                    .padding(.top, 8)
                Button("Jetzt synchronisieren", action: jetztSynchronisieren)
                    .buttonStyle(.bordered)
                    .disabled(container.drinks.syncLaeuft)
            }
        }
    }

    // ---------------- Konto
    private var konto: some View {
        Karte("Konto") {
            Text(nutzer.email)
            if nutzer.offline {
                Text("Offline-Modus: Daten werden nur auf diesem iPhone gespeichert.")
                    .font(.footnote).foregroundStyle(.secondary)
            } else {
                Text("Rolle: \(profil?.role ?? "user")").font(.footnote).foregroundStyle(.secondary)
            }
            if profil?.istAdmin == true {
                NavigationLink {
                    AdminView()
                } label: {
                    Text("Admin: alle Nutzer anzeigen").frame(maxWidth: .infinity)
                }
                .buttonStyle(.borderedProminent)
                .padding(.top, 4)
            }
            Button(nutzer.offline ? "Offline-Modus beenden" : "Abmelden") { abmeldenFragen = true }
                .buttonStyle(.bordered)
                .padding(.top, 4)
        }
    }

    // MARK: - Aktionen

    /// Felder mit dem gespeicherten Profil füllen (solange der Nutzer noch nichts geändert hat).
    private func felderFuellen() {
        guard let p = profil, p.id == nutzer.userId, eingabe == gefuellt else { return }
        let neu = Eingabe(name: p.name ?? "",
                          gewicht: p.weightKg.map(kgText) ?? "",
                          groesse: p.heightCm.map(String.init) ?? "")
        eingabe = neu
        gefuellt = neu
    }

    private func kgText(_ kg: Double) -> String {
        kg.truncatingRemainder(dividingBy: 1) == 0 ? String(Int(kg)) : Format.dezimal(kg, stellen: 1)
    }

    private func speichern() {
        // Gleiche Grenzen wie in der Firmware (Serial-Befehle „gewicht“ / „groesse“)
        if let fehler = ProfilPruefung.fehler(name: eingabe.name, gewichtText: eingabe.gewicht, groesseText: eingabe.groesse) {
            meldung = fehler
            return
        }
        guard let kg = ProfilPruefung.gewicht(eingabe.gewicht), let cm = ProfilPruefung.groesse(eingabe.groesse) else { return }
        speichert = true
        Task {
            let ergebnis = await container.profile.speichern(
                userId: nutzer.userId, name: eingabe.name.trimmingCharacters(in: .whitespaces),
                gewichtKg: kg, groesseCm: cm)
            if let fehler = ergebnis.fehler {
                meldung = "Lokal gespeichert, aber nicht in Supabase: \(fehler)"
            } else {
                gefuellt = eingabe   // gespeicherter Stand gilt als „nicht geändert“
                meldung = "Gespeichert. Neues Tagesziel: \(ergebnis.ziel) ml"
            }
            speichert = false
        }
    }

    private func jetztSynchronisieren() {
        meldung = "Synchronisierung läuft …"
        Task {
            switch await container.drinks.synchronisieren() {
            case .success: meldung = "Synchronisierung abgeschlossen."
            case .failure(let f): meldung = "Synchronisierung fehlgeschlagen: \(f.text)"
            }
        }
    }
}
