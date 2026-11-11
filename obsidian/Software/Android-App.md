---
tags:
  - typ/software
---

# Android-App

Begleit-App in `app-android/`: **Kotlin**, Jetpack Compose (Material 3), MVVM, Room, WorkManager und [[Supabase]]. Sie empfängt den Tagesstand per [[Bluetooth LE]] vom Gerät, erkennt Schlucke, zeigt Heute / Verlauf / Profil und synchronisiert offline-first in dieselben Tabellen wie die [[iPhone-App]].

Funktionen: Anmelden und Registrieren (oder „Ohne Konto testen“), Fortschrittsring, Bluetooth-Status, 7-Tage-Diagramm, 30-Tage-Liste, Tagesziel nach Mosteller (wie die [[Firmware]]), Demo-Modus und eine Admin-Ansicht (Rolle `admin`).

**Stand:** Version 1.0 baut (`assembleDebug`), die Unit-Tests sind grün, der Demo-Modus ist nutzbar. Die Verbindung mit dem echten Gerät ist noch [[Offen]] – siehe `app-android/README.md`. Entwicklung in [[Android Studio]]; das Schema liegt in `app-android/supabase/schema.sql`.

Siehe auch: [[HydroDesk Base]], [[GitHub]].
