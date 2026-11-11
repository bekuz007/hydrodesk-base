---
tags:
  - typ/software
---

# Supabase

Gemeinsame Cloud-Datenbank von [[Android-App]] und [[iPhone-App]]. Das Schema steht in `app-android/supabase/schema.sql` und darf mehrfach ausgeführt werden.

**Tabellen**

- `profiles`: Name, E-Mail, Gewicht, Größe, Tagesziel, Rolle (`user` oder `admin`)
- `drink_entries`: ein Schluck = eine Zeile (UUID, Zeitpunkt, ml, Gerät)

**Sichten:** `daily_totals` (Summe pro Tag, Grenze in Europe/Berlin) und `user_today` (Admin-Übersicht).

**Sicherheit (RLS):** Jeder liest und ändert nur die eigenen Zeilen; eine Administratorin oder ein Administrator darf alle Zeilen lesen, aber nicht die Einträge anderer Leute ändern. Die Rolle schützt der Trigger `profiles_schuetzen` (nur Admin oder Dashboard darf sie setzen). Hilfsfunktion `is_admin()` ist `security definer`, damit die Richtlinien nicht in eine Endlosschleife laufen. Bei der Registrierung legt `handle_new_user()` automatisch ein Profil an.

URL und anon-Key gehören in gitignorierte Dateien, **niemals** der `service_role`-Schlüssel in eine App.

Siehe auch: [[Design-Spezifikation]], [[Lizenz]].
