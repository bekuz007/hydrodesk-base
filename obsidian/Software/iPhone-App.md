---
tags:
  - typ/software
---

# iPhone-App

Begleit-App in `app-ios/`: **Swift / SwiftUI** (iOS 17+), SwiftData, Swift Charts, CoreBluetooth, supabase-swift 2.55.6. Gleicher Funktionsumfang und dieselben [[Supabase]]-Tabellen wie die [[Android-App]]. Wer sich auf beiden Systemen mit demselben Konto anmeldet, sieht dieselben Daten.

Bildschirme: Anmelden / Registrieren (oder „Ohne Konto testen“), **Heute** (Ring, Lichtlinie, Gerätekarte mit sieben Zuständen), **Verlauf** (7-Tage-Diagramm, 30-Tage-Liste) mit **Tagesseite** aller Einträge eines Tages, **Profil** und **Admin**. Das Aussehen folgt der [[Design-Spezifikation]].

**Stand:** 57 Unit-Tests grün. Mit Xcode für das iPhone gebaut und installiert. Mit der kostenlosen Apple-ID läuft die Installation **7 Tage**, danach muss die App neu aufgespielt werden. [[Bluetooth LE]] mit dem echten [[CYD ESP32-Display]] ist noch [[Offen]].

Gebaut wird mit [[Xcode]] (`HydroDesk.xcodeproj`); aus VS Code geht das Bauen über das Terminal (`xcodebuild`, `xcrun devicectl`). Zugangsdaten stehen in der gitignorierten `Config/Secrets.xcconfig`, niemals den `service_role`-Schlüssel eintragen.

Siehe auch: [[HydroDesk Base]], [[Bautagebuch]].
