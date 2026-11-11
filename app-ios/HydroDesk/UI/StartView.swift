// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE

import SwiftUI

/// Start: schlichte Ladeanzeige, zentriert – App-Icon mit Lichtlinie, „HydroDesk“, kleiner Spinner,
/// „Sitzung wird geprüft …“ (solange die gespeicherte Sitzung geprüft wird).
struct StartView: View {
    var body: some View {
        VStack(spacing: 16) {
            AppMarke(groesse: 96)
            Text("HydroDesk").font(.title.bold())
            ProgressView().padding(.top, 16)
            Text("Sitzung wird geprüft …")
                .font(.footnote)
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Theme.bildschirmHintergrund)
        .accessibilityElement(children: .combine)
    }
}
