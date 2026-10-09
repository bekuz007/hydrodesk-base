// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE

package de.hydrodesk.app.domain

import java.time.Instant
import java.time.LocalDate
import java.time.ZoneId
import java.time.format.DateTimeFormatter
import java.util.Locale

/** Kleine Hilfsfunktionen für deutsche Zahlen- und Datumsanzeige. */
object Format {
    private val uhrzeit = DateTimeFormatter.ofPattern("HH:mm", Locale.GERMANY)
    private val datumLang = DateTimeFormatter.ofPattern("EEEE, d. MMMM", Locale.GERMANY)
    private val wochentagKurz = DateTimeFormatter.ofPattern("EE", Locale.GERMANY)

    /** 1250 -> "1.250" (deutscher Tausenderpunkt, wie auf dem Display des Geräts) */
    fun ml(wert: Int): String = String.format(Locale.GERMANY, "%,d", wert)

    /** Zeitstempel (Millisekunden) -> "14:32" */
    fun uhrzeit(millis: Long): String =
        uhrzeit.format(Instant.ofEpochMilli(millis).atZone(ZoneId.systemDefault()))

    /** 2026-10-06 -> "Dienstag, 6. Oktober" */
    fun datumLang(tag: LocalDate): String = datumLang.format(tag)

    /** 2026-10-06 -> "Di" */
    fun wochentagKurz(tag: LocalDate): String = wochentagKurz.format(tag).removeSuffix(".")
}

/** Tagesgrenzen in der Zeitzone des Handys (für Datenbank-Abfragen). */
object Tage {
    fun heute(): LocalDate = LocalDate.now()

    fun startMillis(tag: LocalDate): Long =
        tag.atStartOfDay(ZoneId.systemDefault()).toInstant().toEpochMilli()

    fun endeMillis(tag: LocalDate): Long = startMillis(tag.plusDays(1))
}
