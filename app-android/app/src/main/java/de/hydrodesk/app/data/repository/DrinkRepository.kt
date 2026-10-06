package de.hydrodesk.app.data.repository

import android.util.Log
import de.hydrodesk.app.ble.DeviceReading
import de.hydrodesk.app.data.local.DailySummary
import de.hydrodesk.app.data.local.DrinkDao
import de.hydrodesk.app.data.local.DrinkEntry
import de.hydrodesk.app.data.remote.DrinkEntryDto
import de.hydrodesk.app.data.remote.zuDto
import de.hydrodesk.app.data.remote.zuEntity
import de.hydrodesk.app.data.settings.AppSettings
import de.hydrodesk.app.domain.Tage
import io.github.jan.supabase.SupabaseClient
import io.github.jan.supabase.auth.auth
import io.github.jan.supabase.postgrest.from
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import java.time.Instant
import java.time.LocalDate
import java.time.temporal.ChronoUnit

/**
 * Trink-Einträge: lokal speichern (Room) und mit Supabase synchronisieren.
 *
 * OFFLINE-FIRST: Jeder Schluck wird ZUERST auf dem Handy gespeichert (synced = false).
 * Danach lädt der SyncWorker alle offenen Einträge hoch, sobald Internet da ist.
 */
@OptIn(ExperimentalCoroutinesApi::class)
class DrinkRepository(
    private val dao: DrinkDao,
    private val settings: AppSettings,
    private val supabase: SupabaseClient?,
    private val syncAnstossen: () -> Unit,
) {
    private val sperre = Mutex()   // verhindert, dass zwei Messwerte gleichzeitig verarbeitet werden

    /** Liefert das aktuelle Datum und meldet sich nach Mitternacht mit dem neuen Tag. */
    private val tagFlow: Flow<LocalDate> = flow {
        while (true) {
            emit(Tage.heute())
            delay(30_000)
        }
    }.distinctUntilChanged()

    fun heuteSumme(userId: String): Flow<Int> = tagFlow.flatMapLatest { tag ->
        dao.summe(userId, Tage.startMillis(tag), Tage.endeMillis(tag))
    }

    fun heuteEintraege(userId: String): Flow<List<DrinkEntry>> = tagFlow.flatMapLatest { tag ->
        dao.eintraege(userId, Tage.startMillis(tag), Tage.endeMillis(tag))
    }

    fun letzterSchluck(userId: String): Flow<DrinkEntry?> = dao.letzterEintrag(userId)

    fun tagesSummen(userId: String, tage: Long = 30): Flow<List<DailySummary>> =
        dao.tagesSummen(userId, Tage.startMillis(Tage.heute().minusDays(tage - 1)))

    fun anzahlNichtSynchronisiert(userId: String): Flow<Int> = dao.anzahlNichtSynchronisiert(userId)

    suspend fun heuteSummeFuerQuelle(userId: String, quelle: String): Int {
        val tag = Tage.heute()
        return dao.summeFuerQuelle(userId, quelle, Tage.startMillis(tag), Tage.endeMillis(tag))
    }

    /**
     * SCHLUCK-ERKENNUNG
     * Das Gerät schickt immer den Tagesstand ("heute"). Jede ERHÖHUNG gegenüber dem
     * letzten Wert ist ein neuer Schluck: neu - alt = getrunkene Menge.
     *
     *  - Erster Wert des Tages (oder nach Neuinstallation): Vergleich mit der Summe,
     *    die für dieses Gerät heute schon gespeichert ist. So werden Schlucke, die
     *    ohne Verbindung getrunken wurden, beim Verbinden nachgetragen.
     *  - Wert wird KLEINER (Gerät wurde zurückgesetzt): nur neuer Ausgangswert, kein Eintrag.
     *
     * @return die erkannte Menge in ml oder null (kein neuer Schluck)
     */
    suspend fun geraetewertVerarbeiten(userId: String, wert: DeviceReading, quelle: String): Int? =
        sperre.withLock {
            val tag = Tage.heute().toString()
            val schluessel = "${userId}_$quelle"   // pro Nutzer und Gerät getrennt merken
            val letzter = settings.letzterGeraetewert(schluessel, tag)
            val vergleich = letzter ?: heuteSummeFuerQuelle(userId, quelle)
            settings.setLetzterGeraetewert(schluessel, tag, wert.heuteMl)

            val differenz = wert.heuteMl - vergleich
            if (differenz < MIN_SCHLUCK_ML) return@withLock null

            dao.einfuegen(
                DrinkEntry(
                    userId = userId,
                    timestamp = System.currentTimeMillis(),
                    ml = differenz,
                    device = quelle,
                )
            )
            Log.i(TAG, "Neuer Schluck: +$differenz ml ($quelle, Gerät meldet ${wert.heuteMl} ml)")
            syncAnstossen()
            differenz
        }

    /**
     * Abgleich mit Supabase (wird vom SyncWorker aufgerufen):
     *  1. offene lokale Einträge hochladen
     *  2. Einträge der letzten 30 Tage herunterladen (z. B. nach Handywechsel)
     * @return Anzahl hochgeladener Einträge
     */
    suspend fun synchronisieren(): Result<Int> = runCatching {
        val sb = supabase ?: return Result.success(0)          // kein Supabase -> nichts zu tun
        sb.auth.awaitInitialization()                          // gespeicherte Sitzung laden
        val user = sb.auth.currentUserOrNull() ?: return Result.success(0) // nicht angemeldet

        val offen = dao.nichtSynchronisiert(user.id)
        if (offen.isNotEmpty()) {
            // ignoreDuplicates: schon vorhandene ids werden übersprungen (kein Doppel-Eintrag)
            sb.from("drink_entries").upsert(offen.map { it.zuDto() }) {
                onConflict = "id"
                ignoreDuplicates = true
            }
            dao.alsSynchronisiertMarkieren(offen.map { it.id })
        }

        val seit = Instant.now().minus(30, ChronoUnit.DAYS).toString()
        val entfernt = sb.from("drink_entries").select {
            filter {
                eq("user_id", user.id)
                gte("ts", seit)
            }
        }.decodeList<DrinkEntryDto>()
        dao.einfuegenFallsNeu(entfernt.map { it.zuEntity() })

        Log.i(TAG, "Sync fertig: ${offen.size} hochgeladen, ${entfernt.size} aus Supabase geprüft")
        offen.size
    }

    companion object {
        private const val TAG = "DrinkRepository"
        const val MIN_SCHLUCK_ML = 5   // kleinere Änderungen ignorieren
    }
}
