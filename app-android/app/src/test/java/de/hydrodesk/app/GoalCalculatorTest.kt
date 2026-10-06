package de.hydrodesk.app

import de.hydrodesk.app.domain.GoalCalculator
import org.junit.Assert.assertEquals
import org.junit.Test

/** Unit-Tests: laufen auf dem PC mit ./gradlew test (kein Handy nötig). */
class GoalCalculatorTest {

    @Test
    fun beispielAusDerFirmware_70kg_175cm_ergibt_2750ml() {
        assertEquals(2750, GoalCalculator.tageszielMl(70.0, 175.0))
    }

    @Test
    fun koerperoberflaeche_nachMosteller() {
        assertEquals(1.845, GoalCalculator.koerperoberflaeche(70.0, 175.0), 0.001)
    }

    @Test
    fun untereGrenze_1500ml() {
        assertEquals(1500, GoalCalculator.tageszielMl(30.0, 120.0))
    }

    @Test
    fun obereGrenze_3500ml() {
        assertEquals(3500, GoalCalculator.tageszielMl(250.0, 230.0))
    }

    @Test
    fun ergebnisIstImmerAuf50Gerundet() {
        for (kg in 40..120 step 7) for (cm in 150..200 step 9) {
            assertEquals(0, GoalCalculator.tageszielMl(kg.toDouble(), cm.toDouble()) % 50)
        }
    }
}
