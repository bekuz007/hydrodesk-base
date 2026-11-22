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
    /// V5: Info-Seite „HydroDesk“ offen?
    @State private var infoOffen = false

    var body: some View {
        let geraete = container.geraete
        let messwert = geraete.letzterMesswert
        let geraetStatus = geraete.geraeteStatus
        let modell = GeraeteKarteModell(
            status: geraete.status, demoModus: geraete.demoModus,
            akkuProzent: geraetStatus?.akkuProzent ?? messwert?.akkuProzent, zielErreicht: zielErreicht)

        VStack(spacing: 0) {
            Lichtlinie(farbe: modell.lichtlinie, breite: nil)
            VStack(alignment: .leading, spacing: 12) {
                kopf(modell)

                if modell.status == .verbunden, let messwert {
                    HStack(spacing: 6) {
                        Text(GeraeteKarteModell.meldetText(messwert))
                        if geraetStatus == nil, let akku = messwert.akkuProzent {
                            Text("·")
                            AkkuAnzeige(prozent: akku)
                        }
                    }
                    .font(.footnote)
                    .foregroundStyle(.secondary)
                    .monospacedDigit()
                }
                // V5: Flascheninhalt und Akku direkt auf der Karte
                if modell.status == .verbunden, let geraetStatus {
                    Text(geraetStatus.kurzText)
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
                    // V5: Firmware liefert Status → Info-Seite (von dort auch „einstellen“)
                    if geraete.steuerbar {
                        Button("Details") { infoOffen = true }
                            .buttonStyle(.hydro(.haupt))
                    }
                }
            }
            .padding(Theme.kartenInnenabstand)
        }
        .frame(maxWidth: .infinity)
        .background(Theme.karte)
        .clipShape(RoundedRectangle(cornerRadius: Theme.radiusKarte))
        // Ganze Karte antippbar, sobald das Gerät verbunden ist (Knöpfe haben Vorrang)
        .contentShape(RoundedRectangle(cornerRadius: Theme.radiusKarte))
        .onTapGesture { if geraete.steuerbar { infoOffen = true } }
        .accessibilityElement(children: .contain)
        .sheet(isPresented: $infoOffen) {
            GeraetInfoView()
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

// MARK: - V5: Info-Seite „HydroDesk“

/// Info-Seite zum verbundenen Gerät (Karte auf „Heute“ antippen): Flascheninhalt, Gewicht, Zustand,
/// Tagesstand Gerät/App, Akku, Waage, Nässe, Profil. Nur Anzeige – Einstellungen über
/// „Waage & Flasche einstellen“ (`GeraetSteuerungView`).
struct GeraetInfoView: View {
    @Environment(AppContainer.self) private var container
    @Environment(\.dismiss) private var dismiss
    @State private var steuerungOffen = false

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

                if let s {
                    if s.nass {
                        Section { Rueckmeldung(art: .fehler, text: "Wasser erkannt – das Gerät ist gesperrt und die LEDs sind aus.") }
                    }
                    if !s.waageOk {
                        Section { Rueckmeldung(art: .fehler, text: "Waage antwortet nicht – Kabel am HX711 prüfen.") }
                    }

                    // 1. Flasche
                    Section {
                        HStack(alignment: .firstTextBaseline) {
                            Text(s.flascheSteht ? "In der Flasche" : "Flasche")
                            Spacer()
                            Text(s.flascheSteht ? s.flascheText : "nicht auf dem Pad")
                                .font(s.flascheSteht ? .title2.bold() : .body)
                                .foregroundStyle(s.flascheSteht ? Color.primary : Color.secondary)
                                .monospacedDigit()
                        }
                        if let anteil = s.fuellstand {
                            ProgressView(value: anteil) {
                                Text("\(Format.prozent(Int((anteil * 100).rounded()))) von \(Format.mlEinheit(s.kapazitaetMl))")
                                    .font(.footnote)
                                    .foregroundStyle(.secondary)
                            }
                            .tint(Theme.wasserblau)
                        }
                        HStack {
                            Text("Auf dem Pad")
                            Spacer()
                            Text("\(Format.ml(s.gewichtG)) g").foregroundStyle(.secondary).monospacedDigit()
                            Text(s.ruhig ? "ruhig" : "…")
                                .font(.caption)
                                .foregroundStyle(s.ruhig ? Theme.zielgruen : Color.secondary)
                        }
                        zeile("Zustand", s.zustandText)
                    } header: {
                        Text("Flasche")
                    } footer: {
                        if s.flascheSteht && !s.flascheKalibriert {
                            Text("Flasche noch nicht angelernt – der Inhalt ist nur geschätzt. Unter „Waage & Flasche einstellen“ leere und volle Flasche übernehmen.")
                        }
                    }

                    // 2. Heute
                    Section {
                        zeile("Gerät", "\(Format.ml(s.heuteMl)) / \(Format.mlEinheit(s.zielMl))")
                        if let app = appHeuteMl {
                            zeile("App", Format.mlEinheit(app))
                            if app == s.heuteMl {
                                Rueckmeldung(art: .erfolg, text: "Gerät und App zeigen denselben Stand.")
                            } else {
                                Rueckmeldung(art: .info, text: "Wird abgeglichen – das Gerät übernimmt den Stand der App.")
                            }
                        }
                    } header: {
                        Text("Heute getrunken")
                    }

                    // 3. Gerät
                    Section {
                        HStack {
                            Text("Akku")
                            Spacer()
                            if let akku = s.akkuProzent {
                                AkkuAnzeige(prozent: akku)
                            } else {
                                Text(s.akkuText).foregroundStyle(.secondary)
                            }
                        }
                        zeile("Bluetooth", geraete.status.text)
                        zeile("Waage", s.waageOk ? "OK" : "Fehler")
                        zeile("Nässe-Sensor", s.nass ? "Wasser erkannt" : "trocken")
                        zeile("Profil", "\(Format.dezimal(s.profilKg, stellen: 1)) kg · \(s.profilCm) cm")
                    } header: {
                        Text("Gerät")
                    }
                } else {
                    Section {
                        Text("Warte auf Daten vom Gerät …").foregroundStyle(.secondary)
                    }
                }

                Section {
                    Button("Waage & Flasche einstellen") { steuerungOffen = true }
                        .disabled(!geraete.steuerbar)
                } footer: {
                    Text("Tara, Eichen, leere/volle Flasche anlernen, Profil übertragen.")
                }
            }
            .navigationTitle("HydroDesk")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Fertig") { dismiss() }
                }
            }
            .sheet(isPresented: $steuerungOffen) {
                GeraetSteuerungView()
                    .environment(container)
            }
        }
    }

    /// Summe aller heutigen Einträge in der App (wie auf „Heute“)
    private var appHeuteMl: Int? {
        guard let nutzer = container.auth.zustand.nutzer else { return nil }
        return container.drinks.heuteSumme(userId: nutzer.userId)
    }

    private func zeile(_ titel: String, _ wert: String) -> some View {
        HStack {
            Text(titel)
            Spacer()
            Text(wert).foregroundStyle(.secondary).monospacedDigit()
        }
    }
}

// MARK: - V5: Gerät steuern

/// Bildschirm „Gerät steuern“: Live-Gewicht, Flasche anlernen (Leer/Voll), Waage nullen/eichen,
/// Profil übertragen. Erreichbar über die Info-Seite „HydroDesk“. Schickt Text-Befehle per Bluetooth
/// (`GeraeteBefehl`) – dieselben wie im Seriellen Monitor der Firmware.
struct GeraetSteuerungView: View {
    @Environment(AppContainer.self) private var container
    @Environment(\.dismiss) private var dismiss

    @State private var eichGramm = "203"
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
                    Text("Das Gerät zeigt automatisch denselben Stand wie die App. Falsche Einträge in der App löschen – das Gerät übernimmt die Korrektur.")
                        .foregroundStyle(.secondary)
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
