package de.hydrodesk.app.data.repository

import de.hydrodesk.app.data.remote.UserTodayDto
import io.github.jan.supabase.SupabaseClient
import io.github.jan.supabase.postgrest.from
import io.github.jan.supabase.postgrest.query.Order

/**
 * Admin-Übersicht: alle Nutzer mit ihrer heutigen Trinkmenge (View user_today).
 * Die Row Level Security in Supabase sorgt dafür, dass nur Admins ALLE Zeilen
 * sehen – normale Nutzer bekommen nur ihre eigene Zeile.
 */
class AdminRepository(private val supabase: SupabaseClient?) {
    suspend fun alleNutzerHeute(): Result<List<UserTodayDto>> = runCatching {
        val sb = supabase ?: error(AuthRepository.NICHT_KONFIGURIERT)
        sb.from("user_today")
            .select { order("name", Order.ASCENDING) }
            .decodeList<UserTodayDto>()
    }
}
