// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE

package de.hydrodesk.app.ble

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.os.Build
import androidx.core.content.ContextCompat

/** Welche Laufzeit-Berechtigungen braucht BLE auf diesem Android? */
object BlePermissions {
    /**
     * Android 12+ (API 31): BLUETOOTH_SCAN + BLUETOOTH_CONNECT
     * Android 8–11:        Standort (FINE_LOCATION) – ohne ihn liefert der Scan nichts
     */
    fun benoetigt(): Array<String> =
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            arrayOf(Manifest.permission.BLUETOOTH_SCAN, Manifest.permission.BLUETOOTH_CONNECT)
        } else {
            arrayOf(Manifest.permission.ACCESS_FINE_LOCATION)
        }

    fun alleErteilt(context: Context): Boolean = benoetigt().all {
        ContextCompat.checkSelfPermission(context, it) == PackageManager.PERMISSION_GRANTED
    }
}
