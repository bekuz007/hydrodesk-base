// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE

package de.hydrodesk.app

import android.content.Context
import de.hydrodesk.app.ble.DemoGeraet
import de.hydrodesk.app.ble.GeraeteManager
import de.hydrodesk.app.ble.HydroBleManager
import de.hydrodesk.app.data.local.AppDatabase
import de.hydrodesk.app.data.remote.SupabaseModul
import de.hydrodesk.app.data.repository.AdminRepository
import de.hydrodesk.app.data.repository.AuthRepository
import de.hydrodesk.app.data.repository.AuthZustand
import de.hydrodesk.app.data.repository.DrinkRepository
import de.hydrodesk.app.data.repository.ProfileRepository
import de.hydrodesk.app.data.settings.AppSettings
import de.hydrodesk.app.sync.SyncWorker
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob

/**
 * Hier werden alle "großen" Objekte der App GENAU EINMAL erzeugt und verbunden.
 * Die ViewModels holen sich ihre Repositories von hier.
 * (Das ersetzt ein DI-Framework wie Hilt – für ein Schulprojekt übersichtlicher.)
 */
class AppContainer(context: Context) {
    private val appContext = context.applicationContext

    /** Läuft so lange wie die App (für BLE und Hintergrund-Aufgaben). */
    val appScope = CoroutineScope(SupervisorJob() + Dispatchers.Default)

    val settings = AppSettings(appContext)
    val supabase = SupabaseModul.erstellen()          // null, wenn nicht eingerichtet
    private val datenbank = AppDatabase.erstellen(appContext)

    val authRepository = AuthRepository(supabase, settings, appScope)
    val profileRepository = ProfileRepository(supabase, settings)
    val adminRepository = AdminRepository(supabase)
    val drinkRepository = DrinkRepository(datenbank.drinkDao(), settings, supabase) {
        SyncWorker.jetztPlanen(appContext)
    }

    private val bleManager = HydroBleManager(appContext, appScope)
    private val demoGeraet = DemoGeraet(appScope) {
        val z = authRepository.zustand.value
        if (z is AuthZustand.Angemeldet) drinkRepository.heuteSummeFuerQuelle(z.userId, "Demo") else 0
    }
    val geraeteManager = GeraeteManager(bleManager, demoGeraet, settings, authRepository, drinkRepository, appScope)

    fun syncAnstossen() = SyncWorker.jetztPlanen(appContext)
}
