package de.hydrodesk.app.data.local

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import kotlinx.coroutines.flow.Flow

/** Alle Datenbank-Zugriffe auf die Tabelle drink_entries. */
@Dao
interface DrinkDao {

    @Insert
    suspend fun einfuegen(eintrag: DrinkEntry)

    /** Einträge aus Supabase übernehmen; schon vorhandene ids werden übersprungen. */
    @Insert(onConflict = OnConflictStrategy.IGNORE)
    suspend fun einfuegenFallsNeu(eintraege: List<DrinkEntry>)

    @Query("SELECT COALESCE(SUM(ml), 0) FROM drink_entries WHERE userId = :userId AND timestamp >= :von AND timestamp < :bis")
    fun summe(userId: String, von: Long, bis: Long): Flow<Int>

    @Query("SELECT COALESCE(SUM(ml), 0) FROM drink_entries WHERE userId = :userId AND device = :quelle AND timestamp >= :von AND timestamp < :bis")
    suspend fun summeFuerQuelle(userId: String, quelle: String, von: Long, bis: Long): Int

    @Query("SELECT * FROM drink_entries WHERE userId = :userId ORDER BY timestamp DESC LIMIT 1")
    fun letzterEintrag(userId: String): Flow<DrinkEntry?>

    @Query("SELECT * FROM drink_entries WHERE userId = :userId AND timestamp >= :von AND timestamp < :bis ORDER BY timestamp DESC")
    fun eintraege(userId: String, von: Long, bis: Long): Flow<List<DrinkEntry>>

    /** Summe pro Kalendertag (Ortszeit des Handys), neuester Tag zuerst. */
    @Query(
        """
        SELECT date(timestamp / 1000, 'unixepoch', 'localtime') AS day,
               SUM(ml) AS totalMl,
               COUNT(*) AS drinks
        FROM drink_entries
        WHERE userId = :userId AND timestamp >= :von
        GROUP BY day
        ORDER BY day DESC
        """
    )
    fun tagesSummen(userId: String, von: Long): Flow<List<DailySummary>>

    @Query("SELECT * FROM drink_entries WHERE userId = :userId AND synced = 0")
    suspend fun nichtSynchronisiert(userId: String): List<DrinkEntry>

    @Query("SELECT COUNT(*) FROM drink_entries WHERE userId = :userId AND synced = 0")
    fun anzahlNichtSynchronisiert(userId: String): Flow<Int>

    @Query("UPDATE drink_entries SET synced = 1 WHERE id IN (:ids)")
    suspend fun alsSynchronisiertMarkieren(ids: List<String>)
}
