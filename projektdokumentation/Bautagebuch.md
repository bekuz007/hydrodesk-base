# Bautagebuch – HydroDesk Base

## 09.11.2026 – Test LED-Streifen ✅

**Ziel:** Prüfen, ob der BTF-LIGHTING COB-Streifen (WS2812B, 1 m, 160 LEDs) mit dem CYD funktioniert.

**Aufbau (provisorisch, ohne 5-V-Wandler):**

| LED-Streifen | CYD-Stecker CN1 |
|---|---|
| Rot (5 V) | Rot (3V3) |
| Weiß (GND) | Schwarz (GND) |
| Grün (DIN) | Gelb (IO27) |

**Software:** PlatformIO in VS Code, Bibliothek FastLED, Testcode in `tests/led_test/`. Farbwechsel Rot, Grün, Blau alle 0,5 s.

**Ablauf und Ergebnis:**
1. Test mit den ersten 10 LEDs, Helligkeit 30/255: alle 10 LEDs leuchten in allen drei Farben.
2. Test mit dem ganzen Streifen (160 LEDs), Helligkeit 10/255: der ganze Streifen leuchtet bis zum Ende.

**Hinweis:** Im Test lief der Streifen nur mit 3,3 V vom CYD, deshalb gedimmt. Im fertigen Gerät bekommt er 5 V über den Pololu-Wandler.
