// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE

package de.hydrodesk.app.ble

import de.hydrodesk.app.data.repository.AuthRepository
import de.hydrodesk.app.data.repository.AuthZustand
import de.hydrodesk.app.data.repository.DrinkRepository
import de.hydrodesk.app.data.settings.AppSettings
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

/**
 * Wählt je nach Demo-Schalter das echte Gerät (BLE) oder das Demo-Gerät aus und
 * gibt jeden empfangenen Wert an das DrinkRepository weiter (Schluck-Erkennung).
 * Läuft in der ganzen App (nicht nur auf einem Bildschirm).
 */
@OptIn(ExperimentalCoroutinesApi::class)
class GeraeteManager(
    private val ble: HydroBleManager,
    private val demo: DemoGeraet,
    settings: AppSettings,
    private val auth: AuthRepository,
    private val drinks: DrinkRepository,
    scope: CoroutineScope,
) {
    private fun waehlen(demoAn: Boolean): HydroGeraet = if (demoAn) demo else ble

    /** Das gerade aktive Gerät */
    val aktiv: StateFlow<HydroGeraet> = settings.demoModus
        .map { waehlen(it) }
        .stateIn(scope, SharingStarted.Eagerly, waehlen(settings.demoModus.value))

    val status: StateFlow<VerbindungsStatus> = aktiv
        .flatMapLatest { it.status }
        .stateIn(scope, SharingStarted.Eagerly, VerbindungsStatus.GETRENNT)

    val letzterMesswert: StateFlow<DeviceReading?> = aktiv
        .flatMapLatest { it.letzterMesswert }
        .stateIn(scope, SharingStarted.Eagerly, null)

    init {
        // Werte des aktiven Geräts verarbeiten
        scope.launch {
            aktiv.collectLatest { geraet ->
                geraet.messwerte.collect { wert ->
                    val z = auth.zustand.value
                    if (z is AuthZustand.Angemeldet) drinks.geraetewertVerarbeiten(z.userId, wert, geraet.quelle)
                }
            }
        }
        // Beim Umschalten Demo <-> echt: altes Gerät stoppen, Demo gleich starten (nur wenn angemeldet)
        scope.launch {
            var vorher: HydroGeraet? = null
            aktiv.collect { neu ->
                if (vorher != null && vorher !== neu) vorher?.stoppen()
                if (neu === demo && auth.zustand.value is AuthZustand.Angemeldet) demo.starten()
                vorher = neu
            }
        }
        // Abmelden -> Verbindung trennen; Anmelden -> Demo (falls eingeschaltet) starten
        scope.launch {
            auth.zustand.collect { z ->
                when (z) {
                    is AuthZustand.Abgemeldet -> aktiv.value.stoppen()
                    is AuthZustand.Angemeldet -> if (aktiv.value === demo) demo.starten()
                    AuthZustand.Laedt -> Unit
                }
            }
        }
    }

    fun verbinden() = aktiv.value.starten()
    fun trennen() = aktiv.value.stoppen()
    fun schluckSimulieren(ml: Int = 200) = demo.schluckSimulieren(ml)
}
