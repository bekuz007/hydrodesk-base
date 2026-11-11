// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE

import SwiftUI

/// Admin-Bildschirm: alle Nutzer mit ihrer heutigen Trinkmenge (View `user_today` in Supabase).
/// Nur erreichbar für Profile mit `role = 'admin'` (per NavigationLink aus dem Profil). Selbst wenn jemand
/// ihn öffnen könnte: Supabase (Row Level Security) liefert Nicht-Admins nur die eigene Zeile.
/// Zustände: Laden, Fehler („Laden fehlgeschlagen: …“ mit „Erneut laden“), Liste.
struct AdminView: View {
    @Environment(AppContainer.self) private var container
    @State private var nutzer: [UserTodayDto] = []
    @State private var laedt = false
    @State private var fehler: String?

    var body: some View {
        BildschirmRahmen {
            Text("Alle Nutzer mit der heutigen Trinkmenge. Bearbeiten geht im Supabase-Dashboard.")
                .font(.footnote)
                .foregroundStyle(.secondary)
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.horizontal, 4)

            if let fehler, nutzer.isEmpty {
                Karte {
                    VStack(spacing: 12) {
                        Image(systemName: "exclamationmark.triangle")
                            .font(.title2)
                            .foregroundStyle(Theme.rotText)
                        Text(fehler)
                            .font(.footnote)
                            .foregroundStyle(Theme.rotText)
                            .multilineTextAlignment(.center)
                        Button("Erneut laden") { Task { await laden() } }
                            .buttonStyle(.hydro(.sekundaer))
                            .disabled(laedt)
                    }
                    .frame(maxWidth: .infinity)
                }
            } else if laedt && nutzer.isEmpty {
                Karte {
                    VStack(spacing: 12) {
                        ProgressView()
                        Text("Nutzer werden geladen …").font(.footnote).foregroundStyle(.secondary)
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 8)
                    .accessibilityElement(children: .combine)
                }
            } else {
                Karte {
                    VStack(spacing: 0) {
                        ForEach(Array(nutzer.enumerated()), id: \.element.id) { index, n in
                            if index > 0 { Divider() }
                            NutzerZeile(nutzer: n).padding(.vertical, 10)
                        }
                    }
                }
            }
        }
        .navigationTitle("Admin: Heute")
        .navigationBarTitleDisplayMode(.large)
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                Button { Task { await laden() } } label: { Image(systemName: "arrow.clockwise") }
                    .accessibilityLabel("Neu laden")
                    .disabled(laedt)
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
            let original = error.localizedDescription
            let text = AuthFehler.uebersetzen(original)
            fehler = "Laden fehlgeschlagen: " + (text.hasPrefix("Fehler: ") ? original : text)
        }
        laedt = false
    }
}

/// Zeile je Nutzer:in: Name (Admins mit „· Admin“), E-Mail klein darunter, „1.250 / 2.750 ml“ (grün mit Häkchen bei
/// erreichtem Ziel), Fortschrittsbalken.
private struct NutzerZeile: View {
    let nutzer: UserTodayDto

    var body: some View {
        let ziel = nutzer.dailyGoalMl ?? GoalCalculator.standardZielMl
        let erreicht = nutzer.heuteMl >= ziel
        let name = (nutzer.name?.isEmpty == false ? nutzer.name! : "(ohne Name)")

        VStack(alignment: .leading, spacing: 8) {
            HStack(alignment: .firstTextBaseline, spacing: 8) {
                VStack(alignment: .leading, spacing: 2) {
                    (Text(name).font(.headline)
                        + Text(nutzer.role == "admin" ? " · Admin" : "").font(.subheadline).foregroundStyle(.secondary))
                    Text(nutzer.email ?? "").font(.footnote).foregroundStyle(.secondary)
                }
                Spacer(minLength: 8)
                HStack(spacing: 4) {
                    Text("\(Format.ml(nutzer.heuteMl)) / \(Format.mlEinheit(ziel))")
                        .font(.subheadline.weight(.semibold))
                        .monospacedDigit()
                    if erreicht { Image(systemName: "checkmark.circle.fill").font(.footnote) }
                }
                .foregroundStyle(erreicht ? Theme.zielgruen : Color.primary)
            }
            FortschrittsBalken(getrunkenMl: nutzer.heuteMl, zielMl: ziel)
        }
        .accessibilityElement(children: .combine)
    }
}
