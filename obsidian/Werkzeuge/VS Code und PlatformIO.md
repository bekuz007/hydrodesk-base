---
tags:
  - typ/werkzeug
---

# VS Code und PlatformIO

Entwicklungsumgebung für die [[Firmware]]. Den Ordner `firmware/` in Visual Studio Code öffnen; `platformio.ini` baut `wokwi/sketch.ino` mit `HYDRO_CYD=1` und `HYDRO_BLE=1` und nutzt die Partition Huge APP.

Damit wurde die Firmware am 09.11.2026 auf das echte [[CYD ESP32-Display]] geladen. Auch die Hardware-Tests ([[COB-LED-Streifen]], [[Regensensor LM393]]) liefen über PlatformIO. Die iPhone-App kann man zusätzlich aus VS Code per Terminal bauen (`xcodebuild`), [[Xcode]] muss dafür trotzdem installiert sein.

Siehe auch: [[Wokwi]], [[Bautagebuch]], [[GitHub]].
