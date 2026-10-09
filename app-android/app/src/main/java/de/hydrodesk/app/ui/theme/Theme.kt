// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE

package de.hydrodesk.app.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

// Wasser-Farben (passend zu den LEDs des Geräts: blau = trinken, grün = Ziel)
val WasserBlau = Color(0xFF0277BD)
val WasserHell = Color(0xFF4FC3F7)
val ZielGruen = Color(0xFF2E7D32)
val WarnOrange = Color(0xFFEF6C00)

private val HellesSchema = lightColorScheme(
    primary = WasserBlau,
    secondary = Color(0xFF00838F),
    tertiary = ZielGruen,
    primaryContainer = Color(0xFFD6ECFF),
    onPrimaryContainer = Color(0xFF001D33),
)

private val DunklesSchema = darkColorScheme(
    primary = WasserHell,
    secondary = Color(0xFF4DD0E1),
    tertiary = Color(0xFF81C784),
    primaryContainer = Color(0xFF004A77),
    onPrimaryContainer = Color(0xFFD6ECFF),
)

@Composable
fun HydroDeskTheme(dunkel: Boolean = isSystemInDarkTheme(), inhalt: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = if (dunkel) DunklesSchema else HellesSchema,
        content = inhalt,
    )
}
