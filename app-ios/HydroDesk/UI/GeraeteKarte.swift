// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE

import SwiftUI
import UIKit

/// Gerätekarte auf „Heute“: Lichtlinie oben als Statusleiste, Titel, Statuspunkt/Spinner + Statustext,
/// optional Akku, Hinweis und Aktionsbutton(s). Die sieben Zustände stehen in `GeraeteKarteModell`
/// (und in DESIGN_SPEC.md); hier wird nur gezeichnet.
struct GeraeteKarte: View {
    /// Heute schon so viel getrunken wie das Tagesziel? (→ grüne Lichtlinie)
    let zielErreicht: Bool

    @Environment(AppContainer.self) private var container
    @Environment(\.openURL) private var openURL
    /// V5: Bildschirm „Gerät steuern“ offen?
    @State private var steuerungOffen = false

    var body: some View {
        let geraete = container.geraete
        let messwert = geraete.letzterMesswert
        let modell = GeraeteKarteModell(
            status: geraete.status, demoModus: geraete.demoModus,
            akkuProzent: messwert?.akkuProzent, zielErreicht: zielErreicht)

        VStack(spacing: 0) {
            Lichtlinie(farbe: modell.lichtlinie, breite: nil)
            VStack(alignment: .leading, spacing: 12) {
                kopf(modell)

                if modell.status == .verbunden, let messwert {
                    HStack(spacing: 6) {
                        Text(GeraeteKarteModell.meldetText(messwert))
                        if let akku = messwert.akkuProzent {
                            Text("·")
                            AkkuAnzeige(prozent: akku)
                        }
                    }
                    .font(.footnote)
                    .foregroundStyle(.secondary)
                    .monospacedDigit()
                }
                if let hinweis = modell.hinweis {
                    Text(hinweis).font(.footnote).foregroundStyle(.secondary)
                }
                if let akkuHinweis = modell.akkuHinweis {
                    Rueckmeldung(art: .fehler, text: akkuHinweis)
                }

                HStack(spacing: 12) {
                    ForEach(modell.aktionen, id: \.self) { aktion in
                        knopf(aktion)
                    }
                    // V5: Firmware kann gesteuert werden → eigener Bildschirm
                    if geraete.steuerbar {
                        Button("Gerät steuern") { steuerungOffen = true }
                            .buttonStyle(.hydro(.haupt))
                    }
                }
            }
            .padding(Theme.kartenInnenabstand)
        }
        .frame(maxWidth: .infinity)
        .background(Theme.karte)
        .clipShape(RoundedRectangle(cornerRadius: Theme.radiusKarte))
        .accessibilityElement(children: .contain)
        .sheet(isPresented: $steuerungOffen) {
            GeraetSteuerungView()
                .environment(container)
        }
    }

    @ViewBuilder
    private func kopf(_ modell: GeraeteKarteModell) -> some View {
        if modell.demoModus {
            VStack(alignment: .leading, spacing: 8) {
                Text(modell.titel).font(.headline)
                StatusChip(modell: modell)
            }
        } else {
            ViewThatFits(in: .horizontal) {
                HStack {
                    Text(modell.titel).font(.headline)
                    Spacer(minLength: 8)
                    StatusChip(modell: modell)
                }
                VStack(alignment: .leading, spacing: 8) {
                    Text(modell.titel).font(.headline)
                    StatusChip(modell: modell)
                }
            }
        }
    }

    @ViewBuilder
    private func knopf(_ aktion: GeraeteAktion) -> some View {
        switch aktion {
        case .trennen:
            Button("Trennen") { container.geraete.trennen() }
                .buttonStyle(.hydro(.sekundaer))
        case .verbinden:
            Button("Verbinden") { container.geraete.verbinden() }
                .buttonStyle(.hydro(.haupt))
        case .erneutVersuchen:
            Button("Erneut versuchen") { container.geraete.verbinden() }
                .buttonStyle(.hydro(.haupt))
        case .einstellungenOeffnen:
            Button("iPhone-Einstellungen öffnen") {
                if let url = URL(string: UIApplication.openSettingsURLString) { openURL(url) }
            }
            .buttonStyle(.hydro(.haupt))
        case .schluckSimulieren:
            Button("Schluck simulieren (+200 ml)") { container.geraete.schluckSimulieren() }
                .buttonStyle(.hydro(.haupt))
        }
    }
}

// MARK: - V5: Gerät steuern

/// Bildschirm „Gerät steuern“: Live-Gewicht, Flasche anlernen (Leer/Voll), Waage nullen/eichen,
/// Profil übertragen und Tageszähler zurücksetzen. Schickt Text-Befehle per Bluetooth
/// (`GeraeteBefehl`) – dieselben wie im Seriellen Monitor der Firmware.
struct GeraetSteuerungView: View {
    @Environment(AppContainer.self) private var container
    @Environment(\.dismiss) private var dismiss

    @State private var eichGramm = "203"
    @State private var resetFragen = false
    /// Nummer der Antwort, die beim Öffnen schon da war (alte Antworten nicht anzeigen)
    @State private var startAntwort = 0

    var body: some View {
        let geraete = container.geraete
        let s = geraete.geraeteStatus

        NavigationStack {
            Form {
                if !geraete.steuerbar {
                    Section {
                        Rueckmeldung(art: .fehler, text: "Verbindung zum HydroDesk ist weg. Bitte auf „Heute“ neu verbinden.")
                    }
                }

                if let antwort = geraete.letzteAntwort, antwort.nummer > startAntwort {
                    Section("Rückmeldung vom Gerät") {
                        Text(antwort.text).font(.callout)
                    }
                }

                Section {
                    if let s {
                        HStack {
                            Text("Auf dem Pad")
                            Spacer()
                            Text("\(Format.ml(s.gewichtG)) g").monospacedDigit().bold()
                            Text(s.ruhig ? "ruhig" : "…")
                                .font(.caption)
                                .foregroundStyle(s.ruhig ? Theme.zielgruen : Color.secondary)
                        }
                        if !s.waageOk {
                            Rueckmeldung(art: .fehler, text: "Waage antwortet nicht – Kabel am HX711 prüfen.")
                        }
                        if s.nass {
                            Rueckmeldung(art: .fehler, text: "Wasser erkannt – Gerät ist gesperrt.")
                        }
                    } else {
                        Text("Warte auf Daten vom Gerät …").foregroundStyle(.secondary)
                    }
                } header: {
                    Text("Waage")
                }

                Section {
                    if let s {
                        zeile("Leere Flasche", s.flascheKalibriert ? "\(Format.ml(s.leerG)) g" : "–")
                        zeile("Volle Flasche", s.vollG > 0 ? "\(Format.ml(s.vollG)) g" : "–")
                        zeile("Passt hinein", s.kapazitaetMl > 0 ? Format.mlEinheit(s.kapazitaetMl) : "–")
                        zeile("Jetzt drin (ca.)", Format.mlEinheit(s.flascheMl))
                    }
                    Button("Leere Flasche übernehmen") { _ = geraete.senden(.flascheLeer) }
                        .disabled(!bereit(s))
                    Button("Volle Flasche übernehmen") { _ = geraete.senden(.flascheVoll) }
                        .disabled(!bereit(s) || !(s?.flascheKalibriert ?? false))
                } header: {
                    Text("Flasche anlernen")
                } footer: {
                    Text("Erst die leere, dann die volle Flasche aufs Pad stellen, loslassen und warten, bis „ruhig“ erscheint.")
                }

                Section {
                    Button("Nullpunkt setzen (Tara)") { _ = geraete.senden(.tara) }
                        .disabled(!geraete.steuerbar)
                    HStack {
                        TextField("Gramm", text: $eichGramm)
                            .keyboardType(.numberPad)
                            .frame(maxWidth: 90)
                        Text("g")
                        Spacer()
                        Button("Eichen") {
                            if let g = Int(eichGramm), g > 0 { _ = geraete.senden(.eichen(gramm: g)) }
                        }
                        .disabled(!bereit(s) || (Int(eichGramm) ?? 0) <= 0)
                    }
                } header: {
                    Text("Waage einstellen")
                } footer: {
                    Text("Tara: Pad leer lassen. Eichen: etwas mit bekanntem Gewicht auflegen (z. B. iPhone 13 Pro ohne Hülle = 203 g) und das Gewicht eintragen.")
                }

                Section {
                    if let s {
                        zeile("Auf dem Gerät", "\(Format.dezimal(s.profilKg, stellen: 1)) kg · \(s.profilCm) cm")
                        zeile("Tagesziel Gerät", Format.mlEinheit(s.zielMl))
                    }
                    if let p = container.profile.profil, let kg = p.weightKg, let cm = p.heightCm {
                        zeile("In der App", "\(Format.dezimal(kg, stellen: 1)) kg · \(cm) cm")
                        if let s, s.profilPasst(gewichtKg: kg, groesseCm: cm) {
                            Rueckmeldung(art: .erfolg, text: "Profil ist auf dem Gerät aktuell.")
                        } else {
                            Button("Profil aufs Gerät übertragen") { _ = geraete.profilSenden() }
                                .disabled(!geraete.steuerbar)
                        }
                    } else {
                        Text("Im Profil Gewicht und Größe eintragen – dann wird beides automatisch übertragen.")
                            .foregroundStyle(.secondary)
                    }
                } header: {
                    Text("Profil")
                }

                Section {
                    if let s { zeile("Heute getrunken (Gerät)", Format.mlEinheit(s.heuteMl)) }
                    Button("Tageszähler auf 0 setzen", role: .destructive) { resetFragen = true }
                        .disabled(!geraete.steuerbar)
                } header: {
                    Text("Heute")
                }
            }
            .navigationTitle("Gerät steuern")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Fertig") { dismiss() }
                }
            }
            .confirmationDialog("Tageszähler auf dem Gerät auf 0 setzen?", isPresented: $resetFragen,
                                titleVisibility: .visible) {
                Button("Auf 0 setzen", role: .destructive) { _ = geraete.senden(.tagZuruecksetzen) }
                Button("Abbrechen", role: .cancel) {}
            }
            .onAppear { startAntwort = geraete.letzteAntwort?.nummer ?? 0 }
        }
    }

    /// Befehle, die ein ruhiges Gewicht brauchen, nur anbieten, wenn verbunden und die Waage läuft.
    private func bereit(_ s: GeraeteStatus?) -> Bool {
        container.geraete.steuerbar && (s?.waageOk ?? false)
    }

    private func zeile(_ titel: String, _ wert: String) -> some View {
        HStack {
            Text(titel)
            Spacer()
            Text(wert).foregroundStyle(.secondary).monospacedDigit()
        }
    }
}
