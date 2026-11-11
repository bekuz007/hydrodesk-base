// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE

import SwiftUI

/// Wasser-Farben (passend zu den LEDs des Geräts: blau = trinken, grün = Ziel) – wie in der Android-App.
enum Theme {
    static let wasserBlau = Color(red: 0x02 / 255, green: 0x77 / 255, blue: 0xBD / 255)
    static let wasserHell = Color(red: 0x4F / 255, green: 0xC3 / 255, blue: 0xF7 / 255)
    static let zielGruen = Color(red: 0x2E / 255, green: 0x7D / 255, blue: 0x32 / 255)
    static let warnOrange = Color(red: 0xEF / 255, green: 0x6C / 255, blue: 0x00 / 255)
}

/// Karte mit optionaler Überschrift – wird auf allen Bildschirmen verwendet.
struct Karte<Inhalt: View>: View {
    private let ueberschrift: String?
    private let inhalt: Inhalt

    init(_ ueberschrift: String? = nil, @ViewBuilder inhalt: () -> Inhalt) {
        self.ueberschrift = ueberschrift
        self.inhalt = inhalt()
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            if let ueberschrift {
                Text(ueberschrift).font(.headline)
            }
            inhalt
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(16)
        .background(Color(.secondarySystemGroupedBackground), in: RoundedRectangle(cornerRadius: 16))
    }
}

/// Grauer Hintergrund + Rand für scrollende Bildschirme.
struct BildschirmRahmen<Inhalt: View>: View {
    private let inhalt: Inhalt

    init(@ViewBuilder inhalt: () -> Inhalt) { self.inhalt = inhalt() }

    var body: some View {
        ScrollView {
            VStack(spacing: 16) { inhalt }
                .padding(16)
        }
        .background(Color(.systemGroupedBackground))
    }
}
