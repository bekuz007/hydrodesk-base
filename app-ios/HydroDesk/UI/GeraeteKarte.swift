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
                }
            }
            .padding(Theme.kartenInnenabstand)
        }
        .frame(maxWidth: .infinity)
        .background(Theme.karte)
        .clipShape(RoundedRectangle(cornerRadius: Theme.radiusKarte))
        .accessibilityElement(children: .contain)
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
