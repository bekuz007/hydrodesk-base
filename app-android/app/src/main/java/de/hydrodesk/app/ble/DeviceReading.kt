package de.hydrodesk.app.ble

import kotlinx.serialization.json.Json
import kotlinx.serialization.json.intOrNull
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive

/**
 * Ein Messwert vom HydroDesk-Gerät.
 * @param heuteMl    heute getrunken (ml), zählt das Gerät selbst
 * @param zielMl     Tagesziel, das auf dem Gerät eingestellt ist
 * @param akkuProzent Akkustand (nur, falls die Firmware ihn mitschickt)
 */
data class DeviceReading(
    val heuteMl: Int,
    val zielMl: Int? = null,
    val akkuProzent: Int? = null,
    val rohtext: String = "",
)

/**
 * Übersetzt den Text der BLE-Characteristic in einen [DeviceReading].
 *
 * Unterstützte Formate:
 *  - aktuelle Firmware (Version 3):  "1250/2750 ml"
 *  - mögliche spätere Firmware (JSON): {"heute":1250,"ziel":2750,"akku":88}
 */
object BlePayloadParser {
    private val textFormat = Regex("""^\s*(\d+)\s*/\s*(\d+)\s*(ml)?\s*$""", RegexOption.IGNORE_CASE)

    fun parse(rohtext: String): DeviceReading? {
        val text = rohtext.trim().trimEnd('\u0000')
        if (text.startsWith("{")) return parseJson(text)
        val treffer = textFormat.matchEntire(text) ?: return null
        val heute = treffer.groupValues[1].toIntOrNull() ?: return null
        val ziel = treffer.groupValues[2].toIntOrNull()
        return DeviceReading(heuteMl = heute, zielMl = ziel, rohtext = text)
    }

    private fun parseJson(text: String): DeviceReading? = try {
        val objekt = Json.parseToJsonElement(text).jsonObject
        val heute = objekt["heute"]?.jsonPrimitive?.intOrNull
        heute?.let {
            DeviceReading(
                heuteMl = it,
                zielMl = objekt["ziel"]?.jsonPrimitive?.intOrNull,
                akkuProzent = objekt["akku"]?.jsonPrimitive?.intOrNull,
                rohtext = text,
            )
        }
    } catch (e: Exception) {
        null   // kein gültiges JSON -> ignorieren
    }
}
