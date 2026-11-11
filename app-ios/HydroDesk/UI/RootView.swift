// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE

import SwiftUI

/// Einstieg der Oberfläche: zeigt je nach Login-Zustand Ladekreis, Login-Bildschirm
/// oder die App mit der Tab-Leiste unten.
struct RootView: View {
    @Environment(AppContainer.self) private var container
    @Environment(\.scenePhase) private var szenenPhase

    var body: some View {
        Group {
            switch container.auth.zustand {
            case .laedt:
                ProgressView()
            case .abgemeldet:
                LoginView()
            case .angemeldet(let nutzer):
                HauptBereich(nutzer: nutzer)
            }
        }
        // Bei jedem Wechsel des Login-Zustands (und beim Start): Gerät/Demo passend starten oder stoppen
        .task(id: container.auth.zustand) {
            container.geraete.authGeaendert(container.auth.zustand)
        }
        .onChange(of: szenenPhase) { _, neu in
            if neu == .active {
                container.tagPruefen()
                container.drinks.syncAnstossen()
            }
        }
    }
}

/// Die drei Tabs der unteren Leiste (Admin erreicht man über „Profil“).
private struct HauptBereich: View {
    let nutzer: AngemeldeterNutzer
    @Environment(AppContainer.self) private var container

    var body: some View {
        TabView {
            NavigationStack {
                HeuteView(nutzer: nutzer, heute: container.heute)
                    .id(container.heute)   // nach Mitternacht neu aufbauen
                    .navigationTitle("Heute")
            }
            .tabItem { Label("Heute", systemImage: "drop.fill") }

            NavigationStack {
                VerlaufView(nutzer: nutzer, heute: container.heute)
                    .id(container.heute)
                    .navigationTitle("Verlauf")
            }
            .tabItem { Label("Verlauf", systemImage: "chart.bar.fill") }

            NavigationStack {
                ProfilView(nutzer: nutzer)
                    .navigationTitle("Profil")
            }
            .tabItem { Label("Profil", systemImage: "person.fill") }
        }
        // Nach dem Login: Profil laden und einmal synchronisieren
        .task(id: nutzer.userId) {
            _ = await container.profile.laden(userId: nutzer.userId)
            container.drinks.syncAnstossen()
        }
        // Solange die App offen ist: alle 30 s prüfen, ob ein neuer Tag begonnen hat; stündlich synchronisieren
        .task {
            var runden = 0
            while !Task.isCancelled {
                try? await Task.sleep(for: .seconds(30))
                container.tagPruefen()
                runden += 1
                if runden % 120 == 0 { container.drinks.syncAnstossen() }
            }
        }
    }
}
