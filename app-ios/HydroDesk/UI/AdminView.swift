// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE

import SwiftUI

/// Admin-Bildschirm: alle Nutzer mit ihrer heutigen Trinkmenge (View `user_today` in Supabase).
/// Nur erreichbar für Profile mit `role = 'admin'`. Selbst wenn jemand ihn öffnen könnte:
/// Supabase (Row Level Security) liefert Nicht-Admins nur die eigene Zeile.
struct AdminView: View {
    @Environment(AppContainer.self) private var container
    @State private var nutzer: [UserTodayDto] = []
    @State private var laedt = false
    @State private var fehler: String?

    var body: some View {
        BildschirmRahmen {
            Text("Alle Nutzer mit der heutigen Trinkmenge. Bearbeiten geht im Supabase-Dashboard (Table Editor).")
                .font(.footnote)
                .foregroundStyle(.secondary)
                .frame(maxWidth: .infinity, alignment: .leading)
            if laedt { ProgressView() }
            if let fehler { Text(fehler).foregroundStyle(.red).frame(maxWidth: .infinity, alignment: .leading) }
            ForEach(nutzer) { n in
                NutzerZeile(nutzer: n)
            }
        }
        .navigationTitle("Admin: Heute")
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                Button { Task { await laden() } } label: { Image(systemName: "arrow.clockwise") }
                    .accessibilityLabel("Neu laden")
            }
        }
        .task { await laden() }
    }

    private func laden() async {
        guard let remote = container.remote else {
            fehler = HydroKonstanten.nichtKonfiguriert
            return
        }
        laedt = true
        fehler = nil
        do {
            nutzer = try await remote.alleNutzerHeute()
        } catch {
            fehler = "Laden fehlgeschlagen: \(error.localizedDescription)"
        }
        laedt = false
    }
}

private struct NutzerZeile: View {
    let nutzer: UserTodayDto

    var body: some View {
        let ziel = nutzer.dailyGoalMl ?? GoalCalculator.standardZielMl
        let erreicht = nutzer.heuteMl >= ziel
        Karte {
            HStack {
                VStack(alignment: .leading) {
                    let name = (nutzer.name?.isEmpty == false ? nutzer.name! : "(ohne Name)")
                    Text(name + (nutzer.role == "admin" ? " · Admin" : "")).font(.headline)
                    Text(nutzer.email ?? "").font(.footnote).foregroundStyle(.secondary)
                }
                Spacer()
                Text("\(Format.ml(nutzer.heuteMl)) / \(Format.ml(ziel)) ml")
                    .foregroundStyle(erreicht ? Theme.zielGruen : Color.primary)
            }
            ProgressView(value: min(Double(nutzer.heuteMl) / Double(max(ziel, 1)), 1))
                .tint(erreicht ? Theme.zielGruen : Theme.wasserBlau)
        }
    }
}
