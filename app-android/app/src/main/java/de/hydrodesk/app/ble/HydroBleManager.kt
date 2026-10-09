// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE

package de.hydrodesk.app.ble

import android.annotation.SuppressLint
import android.bluetooth.BluetoothAdapter
import android.bluetooth.BluetoothDevice
import android.bluetooth.BluetoothGatt
import android.bluetooth.BluetoothGattCallback
import android.bluetooth.BluetoothGattCharacteristic
import android.bluetooth.BluetoothGattDescriptor
import android.bluetooth.BluetoothManager
import android.bluetooth.BluetoothProfile
import android.bluetooth.le.ScanCallback
import android.bluetooth.le.ScanFilter
import android.bluetooth.le.ScanResult
import android.bluetooth.le.ScanSettings
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.Build
import android.os.ParcelUuid
import android.util.Log
import androidx.core.content.ContextCompat
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.util.UUID

/**
 * Verbindung zum echten HydroDesk-Gerät über Bluetooth Low Energy (BLE).
 *
 * Ablauf:
 *  1. Scannen nach Geräten mit der HydroDesk-Dienst-UUID ODER dem Namen "HydroDesk"
 *  2. Verbinden (GATT), MTU erhöhen, Dienste suchen
 *  3. Benachrichtigungen (notify) der Werte-Characteristic einschalten
 *  4. Jeder empfangene Text ("1250/2750 ml") wird in einen DeviceReading übersetzt
 *  5. Bei Trennung: nach 3 s automatisch neu suchen (solange der Nutzer verbunden sein will)
 *
 * Die UUIDs müssen mit der Firmware übereinstimmen (wokwi/sketch.ino, BT_SERVICE_UUID / BT_WERTE_UUID).
 *
 * Hinweis: Alle Aufrufe prüfen vorher die Berechtigungen (siehe starten()).
 * Deshalb wird die Lint-Warnung "MissingPermission" hier unterdrückt.
 */
@SuppressLint("MissingPermission")
class HydroBleManager(
    private val context: Context,
    private val scope: CoroutineScope,
) : HydroGeraet {

    companion object {
        val SERVICE_UUID: UUID = UUID.fromString("4f9a0001-6c1e-4b8e-9d6a-2b7c1e0a4d10")
        val WERTE_UUID: UUID = UUID.fromString("4f9a0002-6c1e-4b8e-9d6a-2b7c1e0a4d10")
        /** Standard-Descriptor zum Einschalten von notify (Client Characteristic Configuration) */
        val CCCD_UUID: UUID = UUID.fromString("00002902-0000-1000-8000-00805f9b34fb")
        const val GERAETENAME = "HydroDesk"

        private const val SCAN_DAUER_MS = 30_000L        // so lange suchen ...
        private const val SCAN_PAUSE_MS = 15_000L        // ... dann Pause, dann wieder suchen
        private const val WIEDERVERBINDEN_MS = 3_000L    // Wartezeit nach einer Trennung
        private const val TAG = "HydroBle"
    }

    override val quelle = "HydroDesk"

    private val _status = MutableStateFlow(VerbindungsStatus.GETRENNT)
    override val status: StateFlow<VerbindungsStatus> = _status.asStateFlow()

    private val _messwerte = MutableSharedFlow<DeviceReading>(extraBufferCapacity = 16)
    override val messwerte: SharedFlow<DeviceReading> = _messwerte.asSharedFlow()

    private val _letzterMesswert = MutableStateFlow<DeviceReading?>(null)
    override val letzterMesswert: StateFlow<DeviceReading?> = _letzterMesswert.asStateFlow()

    private val adapter: BluetoothAdapter?
        get() = context.getSystemService(BluetoothManager::class.java)?.adapter

    @Volatile private var gatt: BluetoothGatt? = null
    @Volatile private var scanLaeuft = false
    /** Will der Nutzer verbunden sein? Nur dann wird automatisch neu verbunden. */
    @Volatile private var gewuenscht = false
    private var zeitJob: Job? = null   // Scan-Timeout bzw. Wartezeit bis zum nächsten Versuch

    init {
        // Wird Bluetooth eingeschaltet, während der Nutzer verbunden sein will -> automatisch weiter
        val empfaenger = object : BroadcastReceiver() {
            override fun onReceive(c: Context, intent: Intent) {
                when (intent.getIntExtra(BluetoothAdapter.EXTRA_STATE, -1)) {
                    BluetoothAdapter.STATE_ON -> if (gewuenscht) starten()
                    BluetoothAdapter.STATE_OFF -> {
                        verbindungSchliessen()
                        scanLaeuft = false
                        _status.value = VerbindungsStatus.BLUETOOTH_AUS
                    }
                }
            }
        }
        ContextCompat.registerReceiver(
            context, empfaenger,
            IntentFilter(BluetoothAdapter.ACTION_STATE_CHANGED),
            ContextCompat.RECEIVER_NOT_EXPORTED,
        )
    }

    /** Verbindung aufbauen (vom Nutzer per Taste "Verbinden" ausgelöst). */
    override fun starten() {
        gewuenscht = true
        zeitJob?.cancel()
        if (!BlePermissions.alleErteilt(context)) {
            _status.value = VerbindungsStatus.KEINE_BERECHTIGUNG
            return
        }
        val a = adapter
        if (a == null || !a.isEnabled) {
            _status.value = VerbindungsStatus.BLUETOOTH_AUS
            return
        }
        if (gatt != null || scanLaeuft) return   // läuft schon
        scanStarten()
    }

    /** Verbindung trennen und NICHT automatisch neu verbinden. */
    override fun stoppen() {
        gewuenscht = false
        zeitJob?.cancel()
        scanStoppen()
        verbindungSchliessen()
        _status.value = VerbindungsStatus.GETRENNT
    }

    // ------------------------------------------------------------------ Scannen

    private fun scanStarten() {
        val scanner = adapter?.bluetoothLeScanner
        if (scanner == null) {
            _status.value = VerbindungsStatus.BLUETOOTH_AUS
            return
        }
        // Zwei Filter = ODER: Dienst-UUID (im Werbepaket) oder Name (in der Scan-Antwort)
        val filter = listOf(
            ScanFilter.Builder().setServiceUuid(ParcelUuid(SERVICE_UUID)).build(),
            ScanFilter.Builder().setDeviceName(GERAETENAME).build(),
        )
        val einstellungen = ScanSettings.Builder()
            .setScanMode(ScanSettings.SCAN_MODE_LOW_LATENCY)
            .build()
        try {
            scanner.startScan(filter, einstellungen, scanCallback)
        } catch (e: SecurityException) {
            _status.value = VerbindungsStatus.KEINE_BERECHTIGUNG
            return
        }
        scanLaeuft = true
        _status.value = VerbindungsStatus.SUCHEN
        Log.i(TAG, "Suche nach HydroDesk gestartet")

        // Gerät sucht nur 2 min nach dem Einschalten -> nicht endlos scannen
        zeitJob = scope.launch {
            delay(SCAN_DAUER_MS)
            if (scanLaeuft) {
                Log.i(TAG, "Kein HydroDesk gefunden – neuer Versuch in ${SCAN_PAUSE_MS / 1000} s")
                scanStoppen()
                _status.value = VerbindungsStatus.GETRENNT
                spaeterNeuVersuchen(SCAN_PAUSE_MS)
            }
        }
    }

    private fun scanStoppen() {
        if (!scanLaeuft) return
        scanLaeuft = false
        try {
            adapter?.bluetoothLeScanner?.stopScan(scanCallback)
        } catch (e: Exception) {
            Log.w(TAG, "stopScan fehlgeschlagen", e)
        }
    }

    private val scanCallback = object : ScanCallback() {
        override fun onScanResult(callbackType: Int, result: ScanResult) {
            if (!scanLaeuft || gatt != null) return
            Log.i(TAG, "Gefunden: ${result.device.address} (RSSI ${result.rssi})")
            scanStoppen()
            zeitJob?.cancel()
            verbinden(result.device)
        }

        override fun onScanFailed(errorCode: Int) {
            Log.w(TAG, "Scan fehlgeschlagen, Code $errorCode")
            scanLaeuft = false
            _status.value = VerbindungsStatus.GETRENNT
            spaeterNeuVersuchen(SCAN_PAUSE_MS)
        }
    }

    // ------------------------------------------------------------------ Verbinden

    private fun verbinden(geraet: BluetoothDevice) {
        _status.value = VerbindungsStatus.VERBINDEN
        // Ab Android 17 gibt es eine neue Variante mit BluetoothGattConnectionSettings;
        // diese hier funktioniert auf ALLEN Versionen ab Android 8 weiterhin.
        @Suppress("DEPRECATION")
        gatt = geraet.connectGatt(context, false, gattCallback, BluetoothDevice.TRANSPORT_LE)
    }

    private fun verbindungSchliessen() {
        gatt?.let {
            it.disconnect()
            it.close()
        }
        gatt = null
    }

    private fun spaeterNeuVersuchen(warteMs: Long) {
        if (!gewuenscht) return
        zeitJob?.cancel()
        zeitJob = scope.launch {
            delay(warteMs)
            if (gewuenscht && gatt == null && !scanLaeuft) starten()
        }
    }

    private val gattCallback = object : BluetoothGattCallback() {

        override fun onConnectionStateChange(g: BluetoothGatt, status: Int, newState: Int) {
            if (newState == BluetoothProfile.STATE_CONNECTED && status == BluetoothGatt.GATT_SUCCESS) {
                Log.i(TAG, "GATT verbunden – MTU anfragen")
                // Größere MTU, damit auch längere Texte (z. B. JSON) in ein Paket passen
                if (!g.requestMtu(185)) g.discoverServices()
            } else {
                Log.i(TAG, "GATT getrennt (Status $status)")
                g.close()
                if (gatt == g) gatt = null
                _status.value = VerbindungsStatus.GETRENNT
                spaeterNeuVersuchen(WIEDERVERBINDEN_MS)
            }
        }

        override fun onMtuChanged(g: BluetoothGatt, mtu: Int, status: Int) {
            g.discoverServices()
        }

        override fun onServicesDiscovered(g: BluetoothGatt, status: Int) {
            val werte = g.getService(SERVICE_UUID)?.getCharacteristic(WERTE_UUID)
            if (werte == null) {
                Log.w(TAG, "HydroDesk-Dienst nicht gefunden – falsches Gerät?")
                g.disconnect()
                return
            }
            g.setCharacteristicNotification(werte, true)
            val cccd = werte.getDescriptor(CCCD_UUID)
            if (cccd == null) {
                _status.value = VerbindungsStatus.VERBUNDEN
                g.readCharacteristic(werte)
                return
            }
            descriptorSchreiben(g, cccd, BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE)
        }

        override fun onDescriptorWrite(g: BluetoothGatt, descriptor: BluetoothGattDescriptor, status: Int) {
            Log.i(TAG, "Notify eingeschaltet (Status $status)")
            _status.value = VerbindungsStatus.VERBUNDEN
            // Aktuellen Wert einmal lesen – das Gerät sendet sonst erst bei der nächsten Änderung
            g.getService(SERVICE_UUID)?.getCharacteristic(WERTE_UUID)?.let { g.readCharacteristic(it) }
        }

        // Android 13+ (API 33): Wert kommt direkt als ByteArray
        override fun onCharacteristicChanged(g: BluetoothGatt, c: BluetoothGattCharacteristic, value: ByteArray) {
            if (c.uuid == WERTE_UUID) verarbeiten(value)
        }

        // Android 8–12: alte Variante
        @Deprecated("Nur für Android < 13")
        override fun onCharacteristicChanged(g: BluetoothGatt, c: BluetoothGattCharacteristic) {
            @Suppress("DEPRECATION")
            if (c.uuid == WERTE_UUID) c.value?.let { verarbeiten(it) }
        }

        override fun onCharacteristicRead(g: BluetoothGatt, c: BluetoothGattCharacteristic, value: ByteArray, status: Int) {
            if (status == BluetoothGatt.GATT_SUCCESS && c.uuid == WERTE_UUID) verarbeiten(value)
        }

        @Deprecated("Nur für Android < 13")
        override fun onCharacteristicRead(g: BluetoothGatt, c: BluetoothGattCharacteristic, status: Int) {
            @Suppress("DEPRECATION")
            if (status == BluetoothGatt.GATT_SUCCESS && c.uuid == WERTE_UUID) c.value?.let { verarbeiten(it) }
        }
    }

    private fun descriptorSchreiben(g: BluetoothGatt, d: BluetoothGattDescriptor, wert: ByteArray) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            g.writeDescriptor(d, wert)
        } else {
            @Suppress("DEPRECATION")
            d.value = wert
            @Suppress("DEPRECATION")
            g.writeDescriptor(d)
        }
    }

    private fun verarbeiten(bytes: ByteArray) {
        val text = bytes.toString(Charsets.UTF_8)
        val wert = BlePayloadParser.parse(text)
        if (wert == null) {
            Log.w(TAG, "Unbekanntes Format: \"$text\"")
            return
        }
        _letzterMesswert.value = wert
        _messwerte.tryEmit(wert)
    }
}
