---
tags:
  - typ/software
---

# WLAN und NTP

Die [[Firmware]] nutzt WLAN nicht dauerhaft, sondern nur zum Uhr-Abgleich: beim Start, danach alle **6 Stunden**, außerdem auf den Befehl `sync` (Timeout 20 s). Zeitserver: `pool.ntp.org`. Anschließend geht das WLAN wieder aus ([[Stromsparmodus]]). Ohne gültige Uhrzeit gibt es eine Ersatzuhr (im Test gelb).

Die Zugangsdaten stehen in der gitignorierten `secrets.h`. In der [[Wokwi]]-Simulation dient das Gast-WLAN „Wokwi-GUEST“.

**Test am 09.11.2026:** Das [[CYD ESP32-Display]] hat sich mit dem WLAN verbunden und die Uhrzeit geholt. Beim ersten Abgleich nach dem Start kam innerhalb von 10 s keine NTP-Antwort; mit dem Befehl `sync` klappte es sofort.

Siehe auch: [[Bautagebuch]], [[VS Code und PlatformIO]].
