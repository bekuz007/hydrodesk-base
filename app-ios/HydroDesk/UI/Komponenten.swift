// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE

import SwiftUI

// Wiederverwendbare Bausteine aus dem Design (DESIGN_SPEC.md, Abschnitt „Komponenten“).
// Nur SF Symbols, keine Emojis, keine eigenen Fonts.

// MARK: - Farben für Lichtlinie und Status

extension LichtlinienFarbe {
    var farbe: Color {
        switch self {
        case .blau: return Theme.wasserhell
        case .gruen: return Theme.zielgruen
        case .rot: return Theme.rotLichtlinie
        case .aus: return Theme.lichtlinieAus
        }
    }
}

extension StatusFarbe {
    /// Farbe des Punkts
    var punkt: Color {
        switch self {
        case .blau: return Theme.wasserblau
        case .gruen: return Theme.zielgruen
        case .orange: return Theme.warnorangePunkt
        case .grau: return Theme.grauPunkt
        }
    }

    /// Farbe des Statustexts (orange hat einen eigenen, dunkleren Ton für den Kontrast)
    var text: Color {
        switch self {
        case .blau: return Theme.wasserblau
        case .gruen: return Theme.zielgruen
        case .orange: return Theme.warnorangeText
        case .grau: return Color.secondary
        }
    }
}

// MARK: - Lichtlinie

/// Waagerechte Linie (3 pt, Radius 2) mit weichem Glow – wie die LED-Linie am Gerät.
/// `breite == nil` → volle Breite (Statusleiste oben in der Gerätekarte). Grau („aus“) ohne Glow.
struct Lichtlinie: View {
    let farbe: LichtlinienFarbe
    var breite: CGFloat? = Theme.lichtlinieBreite

    var body: some View {
        let c = farbe.farbe
        RoundedRectangle(cornerRadius: 2)
            .fill(c)
            .frame(width: breite, height: 3)
            .frame(maxWidth: breite == nil ? .infinity : nil)
            .shadow(color: farbe == .aus ? .clear : c.opacity(0.75), radius: 5)
            .accessibilityHidden(true)
    }
}

// MARK: - App-Marke

/// App-Icon aus dem Design: blaue Fläche, weißer Tropfen, Lichtlinie darunter.
struct AppMarke: View {
    var groesse: CGFloat = 96

    var body: some View {
        ZStack {
            RoundedRectangle(cornerRadius: groesse * 22 / 96)
                .fill(Theme.wasserblauFlaeche)
            VStack(spacing: groesse * 0.07) {
                Image(systemName: "drop.fill")
                    .font(.system(size: groesse * 0.4, weight: .semibold))
                    .foregroundStyle(.white)
                RoundedRectangle(cornerRadius: 2)
                    .fill(Theme.wasserhell)
                    .frame(width: groesse * 0.4, height: max(2, groesse * 0.03))
                    .shadow(color: Theme.wasserhell.opacity(0.8), radius: groesse * 0.05)
            }
        }
        .frame(width: groesse, height: groesse)
        .shadow(color: Theme.wasserblauFlaeche.opacity(0.35), radius: groesse * 0.14)
        .accessibilityHidden(true)
    }
}

// MARK: - Buttons

enum KnopfArt { case haupt, sekundaer, destruktiv }

/// Buttons: Höhe 44 pt (Anmelden 50 pt), Radius 12, `.headline`.
/// Haupt = Wasserblau mit weißem Text, sekundär = Sekundärbutton-Fläche, destruktiv = rote Schrift auf rosa Fläche.
/// Deaktiviert = reduzierte Deckkraft.
struct HydroKnopfStil: ButtonStyle {
    var art: KnopfArt
    var hoehe: CGFloat = Theme.tippflaeche

    func makeBody(configuration: Configuration) -> some View {
        KnopfInhalt(label: configuration.label, gedrueckt: configuration.isPressed, art: art, hoehe: hoehe)
    }

    private struct KnopfInhalt<Label: View>: View {
        let label: Label
        let gedrueckt: Bool
        let art: KnopfArt
        let hoehe: CGFloat
        @Environment(\.isEnabled) private var aktiv

        var body: some View {
            label
                .font(.headline)
                .multilineTextAlignment(.center)
                .foregroundStyle(vordergrund)
                .padding(.horizontal, 12)
                .frame(maxWidth: .infinity, minHeight: hoehe)
                .background(hintergrund, in: RoundedRectangle(cornerRadius: Theme.radiusButton))
                .contentShape(RoundedRectangle(cornerRadius: Theme.radiusButton))
                .opacity(aktiv ? (gedrueckt ? 0.75 : 1) : 0.45)
        }

        private var vordergrund: Color {
            switch art {
            case .haupt: return .white
            case .sekundaer: return .primary
            case .destruktiv: return Theme.rotText
            }
        }

        private var hintergrund: Color {
            switch art {
            case .haupt: return Theme.wasserblauFlaeche
            case .sekundaer: return Theme.sekundaerbutton
            case .destruktiv: return Theme.destruktivFlaeche
            }
        }
    }
}

extension ButtonStyle where Self == HydroKnopfStil {
    static func hydro(_ art: KnopfArt, hoehe: CGFloat = Theme.tippflaeche) -> HydroKnopfStil {
        HydroKnopfStil(art: art, hoehe: hoehe)
    }
}

/// Inhalt eines Buttons mit Ladezustand: Spinner + geänderter Text („Speichert …“).
struct KnopfText: View {
    let text: String
    var laedt = false

    var body: some View {
        HStack(spacing: 8) {
            if laedt { ProgressView().tint(.white) }
            Text(text)
        }
    }
}

// MARK: - Status

/// Statuspunkt (10 pt) oder kleiner Spinner (Suchen/Verbinden) plus Statustext (`.subheadline`, semibold).
/// Nie nur Farbe: der Text steht immer dabei.
struct StatusChip: View {
    let modell: GeraeteKarteModell

    var body: some View {
        HStack(spacing: 6) {
            if modell.zeigtSpinner {
                ProgressView().controlSize(.small).tint(modell.statusFarbe.text)
            } else {
                Circle().fill(modell.statusFarbe.punkt).frame(width: 10, height: 10)
            }
            Text(modell.statusText)
                .font(.subheadline.weight(.semibold))
                .foregroundStyle(modell.statusFarbe.text)
        }
        .accessibilityElement(children: .combine)
    }
}

/// Akku-Symbol (Rahmen mit Füllung) und Prozent als Text daneben.
struct AkkuAnzeige: View {
    let prozent: Int

    var body: some View {
        HStack(spacing: 4) {
            Image(systemName: GeraeteKarteModell.akkuSymbol(prozent))
            Text("Akku \(Format.prozent(prozent))")
        }
        .accessibilityElement(children: .combine)
    }
}

// MARK: - Fortschritt

/// Fortschrittsring: 220 pt, Strichstärke 18, runde Enden. Spur in Spur-Farbe, Fortschritt in Wasserblau,
/// bei erreichtem Ziel in Zielgrün. In der Mitte: große Zahl (SF Pro Rounded, 60 pt), „/ 2.750 ml“ und Prozent.
struct FortschrittsRing: View {
    let getrunkenMl: Int
    let zielMl: Int

    @ScaledMetric(relativeTo: .largeTitle) private var zahlGroesse: CGFloat = 60

    var body: some View {
        let erreicht = getrunkenMl >= zielMl
        let farbe = erreicht ? Theme.zielgruen : Theme.wasserblau
        let anteil = Fortschritt.anteil(getrunkenMl: getrunkenMl, zielMl: zielMl)
        let prozent = Fortschritt.prozent(getrunkenMl: getrunkenMl, zielMl: zielMl)

        ZStack {
            Circle().stroke(Theme.spur, lineWidth: 18)
            Circle()
                .trim(from: 0, to: max(anteil, 0.001))   // bei 0 ml bleibt ein kleiner Punkt als Start
                .stroke(farbe, style: StrokeStyle(lineWidth: 18, lineCap: .round))
                .rotationEffect(.degrees(-90))
                .animation(.easeOut(duration: 0.4), value: anteil)
            VStack(spacing: 2) {
                Text(Format.ml(getrunkenMl))
                    .font(.system(size: zahlGroesse, weight: .bold, design: .rounded))
                    .monospacedDigit()
                    .lineLimit(1)
                    .minimumScaleFactor(0.5)
                Text("/ \(Format.mlEinheit(zielMl))")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                    .monospacedDigit()
                Text(Format.prozent(prozent))
                    .font(.subheadline.weight(.semibold))
                    .foregroundStyle(farbe)
                    .monospacedDigit()
            }
            .padding(.horizontal, 28)
        }
        .frame(width: Theme.ringDurchmesser, height: Theme.ringDurchmesser)
        .accessibilityElement(children: .ignore)
        .accessibilityLabel("Getrunken heute")
        .accessibilityValue("\(Format.mlEinheit(getrunkenMl)) von \(Format.mlEinheit(zielMl)), \(Format.prozent(prozent))")
    }
}

/// Schmaler Fortschrittsbalken (4 pt, Radius 2): Spur in Spur-Farbe, Füllung blau bzw. grün bei Ziel.
struct FortschrittsBalken: View {
    let getrunkenMl: Int
    let zielMl: Int

    var body: some View {
        let erreicht = getrunkenMl >= zielMl
        let anteil = Fortschritt.anteil(getrunkenMl: getrunkenMl, zielMl: zielMl)
        GeometryReader { g in
            ZStack(alignment: .leading) {
                RoundedRectangle(cornerRadius: 2).fill(Theme.spur)
                RoundedRectangle(cornerRadius: 2)
                    .fill(erreicht ? Theme.zielgruen : Theme.wasserblau)
                    .frame(width: g.size.width * anteil)
            }
        }
        .frame(height: 4)
        .accessibilityHidden(true)
    }
}

// MARK: - Zeilen und Hinweise

/// Leerzustand: SF Symbol in secondaryLabel, darunter Text (`.subheadline`), zentriert.
struct LeerZustand: View {
    let symbol: String
    let text: String

    var body: some View {
        VStack(spacing: 10) {
            Image(systemName: symbol).font(.title2).foregroundStyle(.secondary)
            Text(text)
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 8)
        .accessibilityElement(children: .combine)
    }
}

/// Kleine graue Zeile (`.caption`), optional mit Sync-Symbol – z. B. die Sync-Zeile unten auf „Heute“.
struct SyncZeile: View {
    let zustand: SyncZustand
    var textUeberschreiben: String?

    var body: some View {
        HStack(alignment: .firstTextBaseline, spacing: 6) {
            if zustand.zeigtSymbol && textUeberschreiben == nil {
                Image(systemName: "arrow.triangle.2.circlepath")
            }
            Text(textUeberschreiben ?? zustand.zeilenText)
        }
        .font(.caption)
        .foregroundStyle(.secondary)
        .frame(maxWidth: .infinity, alignment: .leading)
        .accessibilityElement(children: .combine)
    }
}

/// Rückmeldung mit Symbol und Text (nie nur Farbe): Erfolg grün, Fehler rot, Info blau.
struct Rueckmeldung: View {
    enum Art { case erfolg, fehler, info }
    let art: Art
    let text: String
    var schrift: Font = .footnote

    var body: some View {
        HStack(alignment: .firstTextBaseline, spacing: 6) {
            Image(systemName: symbol)
            Text(text).fixedSize(horizontal: false, vertical: true)
        }
        .font(schrift)
        .foregroundStyle(farbe)
        .frame(maxWidth: .infinity, alignment: .leading)
        .accessibilityElement(children: .combine)
    }

    private var symbol: String {
        switch art {
        case .erfolg: return "checkmark.circle.fill"
        case .fehler: return "exclamationmark.circle.fill"
        case .info: return "info.circle"
        }
    }

    private var farbe: Color {
        switch art {
        case .erfolg: return Theme.zielgruen
        case .fehler: return Theme.rotText
        case .info: return Theme.wasserblau
        }
    }
}

// MARK: - Schluck-Zeile (Heute und Tagesseite)

/// Eine Zeile der Schluckliste: Uhrzeit, Quelle, Menge (+ Sync-Symbol, solange nicht hochgeladen). Mind. 40 pt hoch.
struct SchluckZeile: View {
    let eintrag: DrinkEntry
    let nochNichtHochgeladen: Bool

    var body: some View {
        HStack(spacing: 12) {
            Text(Format.uhrzeitUhr(eintrag.timestamp))
                .font(.body)
                .monospacedDigit()
            Text(eintrag.device)
                .font(.subheadline)
                .foregroundStyle(.secondary)
            Spacer(minLength: 8)
            if nochNichtHochgeladen {
                Image(systemName: "arrow.triangle.2.circlepath")
                    .font(.footnote)
                    .foregroundStyle(.secondary)
                    .accessibilityLabel("noch nicht hochgeladen")
            }
            Text("+\(Format.mlEinheit(eintrag.ml))")
                .font(.body.weight(.semibold))
                .foregroundStyle(Theme.wasserblau)
                .monospacedDigit()
        }
        .frame(minHeight: 40)
        .accessibilityElement(children: .combine)
    }
}
