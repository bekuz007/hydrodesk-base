---
tags:
  - typ/software
---

# Bluetooth LE

Die [[Firmware]] bewirbt das Gerät unter dem Namen **HydroDesk** (Bibliothek NimBLE-Arduino, nicht das eingebaute Bluedroid – das ist zu groß).

- Dienst: `4f9a0001-6c1e-4b8e-9d6a-2b7c1e0a4d10`
- Characteristic: `4f9a0002-6c1e-4b8e-9d6a-2b7c1e0a4d10` (lesen und Notify), Text wie `1250/2750 ml`

Version 4 sendet nur in **Fenstern**: 2 min nach dem Start, 2 min nach Antippen des Bluetooth-Symbols, 60 s still nach erkanntem Trinken oder Nachfüllen. Danach wird der Stack beendet und beim nächsten Fenster neu aufgebaut. Die [[Android-App]] und die [[iPhone-App]] sollen verbinden, den Wert lesen und wieder trennen.

Auf dem Display: Status-Symbol neben dem [[Akku]]; der [[COB-LED-Streifen]] blinkt beim Suchen weiß und bei Verbindung zweimal lila.

**Noch offen:** Verbindung mit dem Handy (nRF Connect oder die Apps) am echten [[CYD ESP32-Display]]. Siehe [[Offen]].

Siehe auch: [[Wokwi]], [[Stromsparmodus]].
