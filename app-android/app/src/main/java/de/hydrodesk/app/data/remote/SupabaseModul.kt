package de.hydrodesk.app.data.remote

import de.hydrodesk.app.BuildConfig
import io.github.jan.supabase.SupabaseClient
import io.github.jan.supabase.auth.Auth
import io.github.jan.supabase.createSupabaseClient
import io.github.jan.supabase.postgrest.Postgrest

/**
 * Erstellt den Supabase-Client.
 * URL und Schlüssel kommen aus local.properties -> BuildConfig (siehe app/build.gradle.kts).
 */
object SupabaseModul {

    /** true, wenn in local.properties echte Werte eingetragen sind. */
    val istKonfiguriert: Boolean
        get() = BuildConfig.SUPABASE_URL.startsWith("https://") &&
            !BuildConfig.SUPABASE_URL.contains("DEIN-PROJEKT") &&
            BuildConfig.SUPABASE_ANON_KEY.length > 20

    /** Liefert null, wenn Supabase nicht eingerichtet ist (dann geht nur der Offline-Modus). */
    fun erstellen(): SupabaseClient? {
        if (!istKonfiguriert) return null
        return createSupabaseClient(
            supabaseUrl = BuildConfig.SUPABASE_URL,
            supabaseKey = BuildConfig.SUPABASE_ANON_KEY,
        ) {
            install(Auth)      // Login; die Sitzung wird automatisch auf dem Handy gespeichert
            install(Postgrest) // Datenbank-Zugriff (Tabellen profiles, drink_entries)
        }
    }
}
