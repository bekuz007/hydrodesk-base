---
tags:
  - typ/hardware
---

# Regensensor LM393

Feuchtigkeitssensor mit LM393-Auswertung (digital und analog), bei Berrybase 1,80 €. Die Sensorplatte (FC-37 / YL-83) misst **40 × 54 mm**, das Auswertemodul **16 × 30 mm**.

Die Platte liegt in einer Mulde **links** neben der [[Wägezelle]] unter dem [[Flaschen-Pad]]. Überläuft Wasser über die Ablaufkerbe im Pad, tropft es durch den 3-mm-Schlitz im [[Deckel]] direkt auf den Sensor. Das Modul sitzt vorne im Mittelstreifen.

Bei Nässe schaltet die [[Firmware]] den LED-Strom über die [[FET-Platine]] ab und zeigt den Sperrbildschirm **„WASSER ERKANNT · STROM AUS“**. In der Simulation hebt sich die Sperre nach 5 s Trockenheit von selbst auf.

**Test am 09.11.2026:** Mit Wassertropfen auf der Platte meldet der ESP32 „NASS“ – Test bestanden. Im Test hing DO an GPIO27; im fertigen Gerät kommt DO an **GPIO19** (über den microSD-Slot, muss gelötet werden).

Siehe auch: [[Anleitung]], [[Bautagebuch]], [[COB-LED-Streifen]].
