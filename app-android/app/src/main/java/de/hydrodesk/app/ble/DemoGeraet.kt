// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE

package de.hydrodesk.app.ble

import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import kotlin.random.Random

/**
 * DEMO-MODUS: tut so, als wäre ein HydroDesk verbunden.
 * Erzeugt dieselben Texte wie die Firmware ("1250/2750 ml") und schickt sie durch
 * denselben Parser – damit wird die komplette App-Logik ohne Hardware getestet.
 *
 * Ab und zu (alle 15–40 s) wird zufällig ein Schluck von 50–300 ml simuliert.
 * Zusätzlich kann man per Taste einen Schluck auslösen ([schluckSimulieren]).
 *
 * @param startwert liefert, wie viel heute im Demo-Modus schon getrunken wurde
 */
class DemoGeraet(
    private val scope: CoroutineScope,
    private val startwert: suspend () -> Int,
) : HydroGeraet {

    override val quelle = "Demo"

    private val _status = MutableStateFlow(VerbindungsStatus.GETRENNT)
    override val status: StateFlow<VerbindungsStatus> = _status.asStateFlow()

    private val _messwerte = MutableSharedFlow<DeviceReading>(extraBufferCapacity = 16)
    override val messwerte: SharedFlow<DeviceReading> = _messwerte.asSharedFlow()

    private val _letzterMesswert = MutableStateFlow<DeviceReading?>(null)
    override val letzterMesswert: StateFlow<DeviceReading?> = _letzterMesswert.asStateFlow()

    private var heuteMl = 0
    private var job: Job? = null

    override fun starten() {
        if (job?.isActive == true) return
        job = scope.launch {
            _status.value = VerbindungsStatus.SUCHEN
            delay(1_000)                         // kurz "suchen", wie beim echten Gerät
            heuteMl = startwert()
            _status.value = VerbindungsStatus.DEMO
            senden()
            while (isActive) {
                delay(Random.nextLong(15_000, 40_000))
                heuteMl += Random.nextInt(1, 7) * 50   // 50 .. 300 ml
                senden()
            }
        }
    }

    override fun stoppen() {
        job?.cancel()
        job = null
        _status.value = VerbindungsStatus.GETRENNT
    }

    /** Für die Taste "Schluck simulieren". */
    fun schluckSimulieren(ml: Int = 200) {
        if (job?.isActive != true) return
        heuteMl += ml
        senden()
    }

    private fun senden() {
        val text = "$heuteMl/$DEMO_ZIEL_ML ml"     // gleiches Format wie die Firmware
        val wert = BlePayloadParser.parse(text) ?: return
        _letzterMesswert.value = wert
        _messwerte.tryEmit(wert)
    }

    private companion object {
        const val DEMO_ZIEL_ML = 2750
    }
}
