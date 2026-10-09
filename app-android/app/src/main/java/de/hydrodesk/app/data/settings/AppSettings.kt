// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE

package de.hydrodesk.app.data.settings

import android.content.Context
import androidx.core.content.edit
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

/**
 * Kleine Einstellungen, die auf dem Handy gespeichert werden (SharedPreferences).
 * Für große Datenmengen ist Room da – hier nur einzelne Werte.
 */
class AppSettings(context: Context) {
    private val prefs = context.getSharedPreferences("hydrodesk_einstellungen", Context.MODE_PRIVATE)

    // --- Demo-Modus: simuliert das Gerät, damit die App ohne Hardware vorführbar ist
    private val _demoModus = MutableStateFlow(prefs.getBoolean(KEY_DEMO, false))
    val demoModus: StateFlow<Boolean> = _demoModus.asStateFlow()

    fun setDemoModus(an: Boolean) {
        prefs.edit { putBoolean(KEY_DEMO, an) }
        _demoModus.value = an
    }

    // --- Offline-Modus ohne Konto (wenn Supabase noch nicht eingerichtet ist)
    private val _offlineKonto = MutableStateFlow(prefs.getBoolean(KEY_OFFLINE, false))
    val offlineKonto: StateFlow<Boolean> = _offlineKonto.asStateFlow()

    fun setOfflineKonto(an: Boolean) {
        prefs.edit { putBoolean(KEY_OFFLINE, an) }
        _offlineKonto.value = an
    }

    // --- Profil als JSON zwischenspeichern (damit es auch ohne Internet angezeigt wird)
    var profilJson: String?
        get() = prefs.getString(KEY_PROFIL, null)
        set(wert) = prefs.edit { putString(KEY_PROFIL, wert) }

    // --- Letzter "heute"-Wert des Geräts pro Quelle und Tag (für die Schluck-Erkennung)
    fun letzterGeraetewert(quelle: String, tag: String): Int? =
        if (prefs.getString("geraet_tag_$quelle", null) == tag) prefs.getInt("geraet_wert_$quelle", 0) else null

    fun setLetzterGeraetewert(quelle: String, tag: String, wert: Int) {
        prefs.edit {
            putString("geraet_tag_$quelle", tag)
            putInt("geraet_wert_$quelle", wert)
        }
    }

    private companion object {
        const val KEY_DEMO = "demo_modus"
        const val KEY_OFFLINE = "offline_konto"
        const val KEY_PROFIL = "profil_json"
    }
}
