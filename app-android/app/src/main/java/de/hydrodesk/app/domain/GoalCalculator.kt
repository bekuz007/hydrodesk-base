// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE

package de.hydrodesk.app.domain

import kotlin.math.roundToInt
import kotlin.math.sqrt

/**
 * Berechnet das Tagesziel aus Körpergewicht und Körpergröße.
 *
 * GENAU dieselbe Formel wie in der ESP32-Firmware (zielBerechnen() in sketch.ino):
 *  1. Körperoberfläche (KOF) nach Mosteller:  KOF [m²] = Wurzel(cm * kg / 3600)
 *  2. Tagesziel = KOF * 1500 ml pro m²
 *  3. auf 50 ml runden, Grenzen 1500 ... 3500 ml
 *
 * Beispiel: 70 kg, 175 cm -> KOF 1,845 m² -> 2767 ml -> 2750 ml
 *
 * RICHTWERT, KEINE MEDIZINISCHE EMPFEHLUNG!
 */
object GoalCalculator {
    const val ML_PRO_M2 = 1500.0
    const val ZIEL_MIN_ML = 1500
    const val ZIEL_MAX_ML = 3500
    const val STANDARD_ZIEL_ML = 2000   // wenn noch kein Profil ausgefüllt ist

    /** Körperoberfläche in m² (Formel nach Mosteller). */
    fun koerperoberflaeche(gewichtKg: Double, groesseCm: Double): Double =
        sqrt(groesseCm * gewichtKg / 3600.0)

    /** Tagesziel in ml, auf 50 ml gerundet und auf 1500..3500 ml begrenzt. */
    fun tageszielMl(gewichtKg: Double, groesseCm: Double): Int {
        val kof = koerperoberflaeche(gewichtKg, groesseCm)
        val ml = (kof * ML_PRO_M2 / 50.0).roundToInt() * 50
        return ml.coerceIn(ZIEL_MIN_ML, ZIEL_MAX_ML)
    }
}
