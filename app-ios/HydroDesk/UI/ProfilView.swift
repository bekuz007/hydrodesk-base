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
    @State private var meldung: ProfilMeldung?
    @State private var abmeldenFragen = false
    /// Welches Feld gerade die Tastatur hat (Ziffernblock hat keine Return-Taste → „Fertig“-Knopf nötig)
    @FocusState private var tastaturAktiv: Bool

    init(nutzer: AngemeldeterNutzer) {
        self.nutzer = nutzer
        let uid = nutzer.userId
        _offene = Query(filter: #Predicate<DrinkEntry> { $0.userId == uid && $0.synced == false })
    }

    /// Rückmeldung unter dem Speichern-Button bzw. bei „Jetzt synchronisieren“
    private struct ProfilMeldung: Equatable {
        var art: Rueckmeldung.Art?   // nil = neutrale Info
        var text: String
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
                .font(.caption)
                .foregroundStyle(.secondary)
                .frame(maxWidth: .infinity)
        }
        .scrollDismissesKeyboard(.interactively)
        .toolbar {
            ToolbarItemGroup(placement: .keyboard) {
                Spacer()
                Button("Fertig") { tastaturAktiv = false }
                    .fontWeight(.semibold)
            }
        }
        .onAppear(perform: felderFuellen)
        .onChange(of: container.profile.profil) { _, _ in felderFuellen() }
        .alert("Abmelden?", isPresented: $abmeldenFragen) {
            Button("Abmelden", role: .destructive) {
                Task { await container.auth.abmelden() }
            }
            Button("Abbrechen", role: .cancel) {}
        } message: {
            Text(SyncZustand.abmeldeText(offene: offene.count, offlineKonto: nutzer.offline))
        }
    }

    // ---------------- Körperdaten → Tagesziel
    private var koerperdaten: some View {
        let vorschau = ProfilPruefung.zielVorschau(gewichtText: eingabe.gewicht, groesseText: eingabe.groesse)
        return Karte("Körperdaten") {
            eingabeZeile("Name", einheit: nil, breite: 180) {
                TextField("Name", text: $eingabe.name)
                    .textContentType(.name)
                    .submitLabel(.done)
                    .multilineTextAlignment(.trailing)
            }
            eingabeZeile("Gewicht", einheit: "kg") {
                TextField("0", text: $eingabe.gewicht)
                    .keyboardType(.decimalPad)
                    .multilineTextAlignment(.trailing)
            }
            eingabeZeile("Größe", einheit: "cm") {
                TextField("0", text: $eingabe.groesse)
                    .keyboardType(.numberPad)
                    .multilineTextAlignment(.trailing)
            }

            // Live-Vorschau des Tagesziels
            Group {
                if let vorschau {
                    Text("Tagesziel: \(Format.mlEinheit(vorschau.zielMl)) (Körperoberfläche \(Format.dezimal(vorschau.kof, stellen: 2)) m² × 1.500 ml)")
                } else {
                    Text("Gewicht und Größe eingeben, dann wird das Tagesziel berechnet.")
                }
            }
            .font(vorschau != nil ? .subheadline.weight(.semibold) : .subheadline)
            .foregroundStyle(vorschau != nil ? Color.primary : Color.secondary)
            .padding(12)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(Theme.eingabeHintergrund, in: RoundedRectangle(cornerRadius: Theme.radiusFeld))

            Text("Formel nach Mosteller, gerundet auf 50 ml, 1.500–3.500 ml. Richtwert, keine medizinische Empfehlung.")
                .font(.footnote)
                .foregroundStyle(.secondary)

            Button(action: speichern) {
                KnopfText(text: speichert ? "Speichert …" : "Speichern", laedt: speichert)
            }
            .buttonStyle(.hydro(.haupt))
            .disabled(speichert)

            if let meldung { meldungsZeile(meldung) }
        }
    }

    /// Zeile „Beschriftung links, Eingabefeld rechts“ (Feld mit Tertiär-Hintergrund, Radius 10, ggf. Einheit dahinter).
    private func eingabeZeile<Feld: View>(_ titel: String, einheit: String?, breite: CGFloat = 100,
                                          @ViewBuilder feld: () -> Feld) -> some View {
        HStack(spacing: 8) {
            Text(titel).font(.body)
            Spacer(minLength: 8)
            feld()
                .font(.body)
                .focused($tastaturAktiv)
                .padding(.horizontal, 12)
                .frame(width: breite, height: Theme.tippflaeche)
                .background(Theme.eingabeHintergrund, in: RoundedRectangle(cornerRadius: Theme.radiusFeld))
            if let einheit {
                Text(einheit).font(.footnote).foregroundStyle(.secondary).frame(width: 24, alignment: .leading)
            }
        }
        .frame(minHeight: Theme.tippflaeche)
    }

    @ViewBuilder
    private func meldungsZeile(_ m: ProfilMeldung) -> some View {
        if let art = m.art {
            Rueckmeldung(art: art, text: m.text, schrift: .caption)
        } else {
            Text(m.text).font(.caption).foregroundStyle(.secondary)
        }
    }

    // ---------------- Einstellungen
    private var einstellungen: some View {
        let sync = SyncZustand.bestimmen(offlineKonto: nutzer.offline, offene: offene.count)
        return Karte("Einstellungen") {
            Toggle(isOn: Binding(
                get: { container.geraete.demoModus },
                set: { container.geraete.setDemoModus($0) }
            )) {
                VStack(alignment: .leading, spacing: 2) {
                    Text("Demo-Modus").font(.body)
                    Text("Simuliert den HydroDesk – zum Vorführen ohne Hardware.")
                        .font(.footnote).foregroundStyle(.secondary)
                }
            }
            .frame(minHeight: Theme.tippflaeche)

            Divider()

            HStack {
                Text("Synchronisierung").font(.body)
                Spacer(minLength: 8)
                Text(sync.kurzText).font(.subheadline).foregroundStyle(.secondary)
            }
            .frame(minHeight: Theme.tippflaeche)
            .accessibilityElement(children: .combine)

            Button(action: jetztSynchronisieren) {
                KnopfText(text: "Jetzt synchronisieren")
            }
            .buttonStyle(.hydro(.sekundaer))
            .disabled(container.drinks.syncLaeuft || nutzer.offline)
        }
    }

    // ---------------- Konto
    private var konto: some View {
        Karte("Konto") {
            zeileMitWert("E-Mail", nutzer.offline ? "Ohne Konto – nur dieses iPhone" : nutzer.email)
            Divider()
            zeileMitWert("Rolle", nutzer.offline ? "user" : (profil?.role ?? "user"))

            if profil?.istAdmin == true && !nutzer.offline {
                NavigationLink {
                    AdminView()
                } label: {
                    HStack(spacing: 6) {
                        Text("Admin: alle Nutzer anzeigen")
                        Image(systemName: "chevron.right").imageScale(.small)
                    }
                }
                .buttonStyle(.hydro(.sekundaer))
            }

            Button(nutzer.offline ? "Offline-Modus beenden" : "Abmelden") { abmeldenFragen = true }
                .buttonStyle(.hydro(.destruktiv))
        }
    }

    private func zeileMitWert(_ titel: String, _ wert: String) -> some View {
        HStack(alignment: .firstTextBaseline) {
            Text(titel).font(.body)
            Spacer(minLength: 12)
            Text(wert)
                .font(.body)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.trailing)
        }
        .frame(minHeight: Theme.tippflaeche)
        .accessibilityElement(children: .combine)
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
        tastaturAktiv = false   // Tastatur ausblenden
        // Gleiche Grenzen wie in der Firmware (Serial-Befehle „gewicht“ / „groesse“)
        if let fehler = ProfilPruefung.fehler(name: eingabe.name, gewichtText: eingabe.gewicht, groesseText: eingabe.groesse) {
            meldung = ProfilMeldung(art: .fehler, text: fehler)
            return
        }
        guard let kg = ProfilPruefung.gewicht(eingabe.gewicht), let cm = ProfilPruefung.groesse(eingabe.groesse) else { return }
        speichert = true
        Task {
            let ergebnis = await container.profile.speichern(
                userId: nutzer.userId, name: eingabe.name.trimmingCharacters(in: .whitespaces),
                gewichtKg: kg, groesseCm: cm)
            if let fehler = ergebnis.fehler {
                meldung = ProfilMeldung(art: .fehler, text: "Lokal gespeichert, aber nicht in Supabase: \(fehler)")
            } else {
                gefuellt = eingabe   // gespeicherter Stand gilt als „nicht geändert“
                meldung = ProfilMeldung(art: .erfolg, text: "Gespeichert. Neues Tagesziel: \(Format.mlEinheit(ergebnis.ziel))")
            }
            speichert = false
        }
    }

    private func jetztSynchronisieren() {
        meldung = ProfilMeldung(art: nil, text: "Synchronisierung läuft …")
        Task {
            switch await container.drinks.synchronisieren() {
            case .success: meldung = ProfilMeldung(art: .erfolg, text: "Synchronisierung abgeschlossen.")
            case .failure(let f): meldung = ProfilMeldung(art: .fehler, text: "Synchronisierung fehlgeschlagen: \(f.text)")
            }
        }
    }
}
