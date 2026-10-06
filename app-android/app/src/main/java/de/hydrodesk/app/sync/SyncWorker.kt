package de.hydrodesk.app.sync

import android.content.Context
import androidx.work.BackoffPolicy
import androidx.work.Constraints
import androidx.work.CoroutineWorker
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.ExistingWorkPolicy
import androidx.work.NetworkType
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.WorkerParameters
import de.hydrodesk.app.HydroDeskApp
import java.util.concurrent.TimeUnit

/**
 * Hintergrund-Aufgabe (WorkManager): lädt offene Trink-Einträge zu Supabase hoch.
 * WorkManager startet sie erst, wenn Internet da ist, und wiederholt sie bei Fehlern.
 */
class SyncWorker(context: Context, params: WorkerParameters) : CoroutineWorker(context, params) {

    override suspend fun doWork(): Result {
        val container = (applicationContext as HydroDeskApp).container
        return container.drinkRepository.synchronisieren().fold(
            onSuccess = { Result.success() },
            onFailure = { if (runAttemptCount < 5) Result.retry() else Result.failure() },
        )
    }

    companion object {
        private const val NAME_SOFORT = "hydrodesk-sync"
        private const val NAME_PERIODISCH = "hydrodesk-sync-periodisch"

        private val nurMitInternet = Constraints.Builder()
            .setRequiredNetworkType(NetworkType.CONNECTED)
            .build()

        /** Einmalig so bald wie möglich synchronisieren (z. B. nach einem neuen Schluck). */
        fun jetztPlanen(context: Context) {
            val auftrag = OneTimeWorkRequestBuilder<SyncWorker>()
                .setConstraints(nurMitInternet)
                .setBackoffCriteria(BackoffPolicy.EXPONENTIAL, 30, TimeUnit.SECONDS)
                .build()
            WorkManager.getInstance(context)
                .enqueueUniqueWork(NAME_SOFORT, ExistingWorkPolicy.APPEND_OR_REPLACE, auftrag)
        }

        /** Zusätzlich jede Stunde einmal abgleichen (falls etwas liegen geblieben ist). */
        fun periodischPlanen(context: Context) {
            val auftrag = PeriodicWorkRequestBuilder<SyncWorker>(1, TimeUnit.HOURS)
                .setConstraints(nurMitInternet)
                .build()
            WorkManager.getInstance(context)
                .enqueueUniquePeriodicWork(NAME_PERIODISCH, ExistingPeriodicWorkPolicy.KEEP, auftrag)
        }
    }
}
