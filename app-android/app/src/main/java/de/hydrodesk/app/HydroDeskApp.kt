// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE

package de.hydrodesk.app

import android.app.Application
import de.hydrodesk.app.sync.SyncWorker

/**
 * Application-Klasse: wird beim Start der App als Erstes erzeugt.
 * Hier entsteht der AppContainer (einfache "manuelle Dependency Injection").
 */
class HydroDeskApp : Application() {
    lateinit var container: AppContainer
        private set

    override fun onCreate() {
        super.onCreate()
        container = AppContainer(this)
        SyncWorker.periodischPlanen(this)   // stündlicher Abgleich mit Supabase
    }
}
