// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE

package de.hydrodesk.app.ble

import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.StateFlow

/** Verbindungszustand, wie er in der App angezeigt wird. */
enum class VerbindungsStatus(val text: String) {
    KEINE_BERECHTIGUNG("Keine Berechtigung"),
    BLUETOOTH_AUS("Bluetooth ist aus"),
    GETRENNT("Getrennt"),
    SUCHEN("Suchen …"),
    VERBINDEN("Verbinden …"),
    VERBUNDEN("Verbunden"),
    DEMO("Verbunden (Demo)"),
}

/**
 * Gemeinsame Schnittstelle für das echte Gerät (BLE) und den Demo-Modus.
 * So muss der Rest der App nicht wissen, woher die Werte kommen.
 */
interface HydroGeraet {
    /** Name der Quelle, wird bei jedem Trink-Eintrag gespeichert. */
    val quelle: String
    val status: StateFlow<VerbindungsStatus>
    /** Jeder empfangene Wert (auch gleiche Werte mehrfach). */
    val messwerte: SharedFlow<DeviceReading>
    /** Der zuletzt empfangene Wert (für die Anzeige). */
    val letzterMesswert: StateFlow<DeviceReading?>
    fun starten()
    fun stoppen()
}
