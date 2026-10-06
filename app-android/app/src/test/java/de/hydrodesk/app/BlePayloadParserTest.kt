package de.hydrodesk.app

import de.hydrodesk.app.ble.BlePayloadParser
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class BlePayloadParserTest {

    @Test
    fun textFormatDerFirmware() {
        val wert = BlePayloadParser.parse("1250/2750 ml")!!
        assertEquals(1250, wert.heuteMl)
        assertEquals(2750, wert.zielMl)
        assertNull(wert.akkuProzent)
    }

    @Test
    fun textOhneLeerzeichenUndOhneMl() {
        val wert = BlePayloadParser.parse("0/2000")!!
        assertEquals(0, wert.heuteMl)
        assertEquals(2000, wert.zielMl)
    }

    @Test
    fun jsonFormat() {
        val wert = BlePayloadParser.parse("""{"heute":1250,"ziel":2750,"akku":88}""")!!
        assertEquals(1250, wert.heuteMl)
        assertEquals(2750, wert.zielMl)
        assertEquals(88, wert.akkuProzent)
    }

    @Test
    fun ungueltigeTexteWerdenIgnoriert() {
        assertNull(BlePayloadParser.parse(""))
        assertNull(BlePayloadParser.parse("hallo"))
        assertNull(BlePayloadParser.parse("{kaputt"))
        assertNull(BlePayloadParser.parse("""{"ziel":2750}"""))
    }
}
