// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE

import SwiftUI

/// Farb-Tokens aus dem Design (Light und Dark). Die Markenfarben liegen als Color-Assets im
/// Asset-Katalog (je mit „Any“ und „Dark“); Systemfarben (Hintergründe, Label, Trennlinie)
/// kommen direkt von SwiftUI. Werte und Verwendung: siehe DESIGN_SPEC.md.
enum Theme {
    /// Hauptbuttons, App-Icon (weißer Text darauf)
    static let wasserblauFlaeche = Color("WasserblauFlaeche")
    /// Ring, Prozent, Mengen, aktiver Tab, Links (nur auf Karten)
    static let wasserblau = Color("WasserblauText")
    /// Lichtlinie, Akzent im Dark Mode
    static let wasserhell = Color("Wasserhell")
    /// Ziel erreicht, Verbunden, Häkchen, Ring/Linie bei Ziel
    static let zielgruen = Color("Zielgruen")
    /// Statuspunkt „Bluetooth aus“ / „Keine Berechtigung“
    static let warnorangePunkt = Color("WarnorangePunkt")
    /// Statustext der orangen Zustände
    static let warnorangeText = Color("WarnorangeText")
    /// Fehler, destruktiv, Fehlerrand
    static let rotText = Color("SystemrotText")
    /// Lichtlinie bei niedrigem Akku / Fehler
    static let rotLichtlinie = Color("SystemrotLichtlinie")
    /// Hintergrund des Abmelden-Buttons
    static let destruktivFlaeche = Color("DestruktivFlaeche")
    /// Statuspunkt „Getrennt“
    static let grauPunkt = Color("SystemgrauPunkt")
    /// Trennen, Jetzt synchronisieren
    static let sekundaerbutton = Color("Sekundaerbutton")
    /// leerer Teil von Ring und Balken
    static let spur = Color("Spur")
    /// Lichtlinie bei getrennt / Bluetooth aus / keine Berechtigung
    static let lichtlinieAus = Color("LichtlinieAus")

    // System-Hintergründe
    static let bildschirmHintergrund = Color(.systemGroupedBackground)
    static let karte = Color(.secondarySystemGroupedBackground)
    static let eingabeHintergrund = Color(.tertiarySystemGroupedBackground)

    // Abstände (pt)
    static let rand: CGFloat = 16
    static let kartenAbstand: CGFloat = 16
    static let kartenInnenabstand: CGFloat = 16
    static let tippflaeche: CGFloat = 44
    static let ringDurchmesser: CGFloat = 220
    static let lichtlinieBreite: CGFloat = 160

    // Radien (pt)
    static let radiusKarte: CGFloat = 16
    static let radiusButton: CGFloat = 12
    static let radiusFeld: CGFloat = 10
}

/// Karte mit optionaler Überschrift – Container auf `secondarySystemGroupedBackground`,
/// Radius 16, Innenabstand 16. Grundlage fast aller Inhalte.
struct Karte<Inhalt: View>: View {
    private let ueberschrift: String?
    private let inhalt: Inhalt

    init(_ ueberschrift: String? = nil, @ViewBuilder inhalt: () -> Inhalt) {
        self.ueberschrift = ueberschrift
        self.inhalt = inhalt()
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            if let ueberschrift {
                Text(ueberschrift).font(.headline).accessibilityAddTraits(.isHeader)
            }
            inhalt
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(Theme.kartenInnenabstand)
        .background(Theme.karte, in: RoundedRectangle(cornerRadius: Theme.radiusKarte))
    }
}

/// Grauer Hintergrund + Rand (16 pt) für scrollende Bildschirme, 16 pt Abstand zwischen den Karten.
struct BildschirmRahmen<Inhalt: View>: View {
    private let inhalt: Inhalt

    init(@ViewBuilder inhalt: () -> Inhalt) { self.inhalt = inhalt() }

    var body: some View {
        ScrollView {
            VStack(spacing: Theme.kartenAbstand) { inhalt }
                .padding(Theme.rand)
        }
        .background(Theme.bildschirmHintergrund)
    }
}
