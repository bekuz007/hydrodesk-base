// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE

package de.hydrodesk.app.data.local

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase

/** Die lokale SQLite-Datenbank der App (Room). */
@Database(entities = [DrinkEntry::class], version = 1, exportSchema = true)
abstract class AppDatabase : RoomDatabase() {
    abstract fun drinkDao(): DrinkDao

    companion object {
        fun erstellen(context: Context): AppDatabase =
            Room.databaseBuilder(context, AppDatabase::class.java, "hydrodesk.db").build()
    }
}
