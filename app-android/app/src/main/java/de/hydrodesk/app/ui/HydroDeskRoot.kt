// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE

package de.hydrodesk.app.ui

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.DateRange
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Person
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import de.hydrodesk.app.data.repository.AuthZustand
import de.hydrodesk.app.ui.admin.AdminScreen
import de.hydrodesk.app.ui.auth.LoginScreen
import de.hydrodesk.app.ui.common.appContainer
import de.hydrodesk.app.ui.history.VerlaufScreen
import de.hydrodesk.app.ui.profile.ProfilScreen
import de.hydrodesk.app.ui.today.HeuteScreen

/** Die drei Tabs der unteren Leiste. */
private enum class Tab(val route: String, val titel: String, val icon: ImageVector) {
    HEUTE("heute", "Heute", Icons.Filled.Home),
    VERLAUF("verlauf", "Verlauf", Icons.Filled.DateRange),
    PROFIL("profil", "Profil", Icons.Filled.Person),
}

private const val ROUTE_ADMIN = "admin"

/**
 * Einstieg der Oberfläche: zeigt je nach Login-Zustand
 * Ladekreis, Login-Bildschirm oder die App mit unterer Navigationsleiste.
 */
@Composable
fun HydroDeskRoot() {
    val container = appContainer()
    val zustand by container.authRepository.zustand.collectAsStateWithLifecycle()

    when (val z = zustand) {
        AuthZustand.Laedt -> Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
            CircularProgressIndicator()
        }
        AuthZustand.Abgemeldet -> LoginScreen()
        is AuthZustand.Angemeldet -> {
            // Nach dem Login: Profil laden und einmal synchronisieren
            LaunchedEffect(z.userId) {
                container.profileRepository.laden(z.userId)
                container.syncAnstossen()
            }
            HauptBereich(z)
        }
    }
}

@Composable
private fun HauptBereich(nutzer: AuthZustand.Angemeldet) {
    val nav = rememberNavController()
    val aktuellerEintrag by nav.currentBackStackEntryAsState()
    val aktuelleRoute = aktuellerEintrag?.destination?.route

    Scaffold(
        bottomBar = {
            NavigationBar {
                Tab.entries.forEach { tab ->
                    NavigationBarItem(
                        selected = aktuelleRoute == tab.route,
                        onClick = {
                            nav.navigate(tab.route) {
                                popUpTo(nav.graph.findStartDestination().id) { saveState = true }
                                launchSingleTop = true
                                restoreState = true
                            }
                        },
                        icon = { Icon(tab.icon, contentDescription = null) },
                        label = { Text(tab.titel) },
                    )
                }
            }
        },
    ) { innenAbstand ->
        NavHost(
            navController = nav,
            startDestination = Tab.HEUTE.route,
            modifier = Modifier.padding(innenAbstand),
        ) {
            composable(Tab.HEUTE.route) { HeuteScreen(nutzer) }
            composable(Tab.VERLAUF.route) { VerlaufScreen(nutzer) }
            composable(Tab.PROFIL.route) {
                ProfilScreen(nutzer, onAdminOeffnen = { nav.navigate(ROUTE_ADMIN) })
            }
            composable(ROUTE_ADMIN) { AdminScreen(onZurueck = { nav.popBackStack() }) }
        }
    }
}
