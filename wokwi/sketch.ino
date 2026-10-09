/*
 * ============================================================================
 *  HydroDesk Base – Wokwi-Simulation (ESP32, Arduino)          Version 4
 * ============================================================================
 *  Schulprojekt FI-AE: Trink-Tracker für den Schreibtisch.
 *  Eine Flasche steht auf einem Pad über einer Wägezelle (HX711). Das Display
 *  zeigt Uhrzeit, Akku, heute getrunkene Menge, Tagesziel und Flascheninhalt.
 *  Touch-Tasten „Leer“ und „Voll“ auf dem Hauptbildschirm (Flaschen-Kalibrierung);
 *  Trinken/Nachfüllen wird weiter aus dem Gewicht abgeleitet.
 *  LED-Linie (COB-Streifen WS2812B, 26 LEDs hinter einer Diffusor-Leiste)
 *  leuchtet nur bei Ereignissen (Dauerlicht). Blinken NUR bei:
 *  Akku-Warnung (rot), Bluetooth sucht (weiß), Handy verbunden (2x lila).
 *  Oben rechts: Bluetooth-Symbol links neben dem Akku (neu in V3).
 *  Antippen des Symbols macht das Gerät 2 min für das Handy sichtbar (neu in V4).
 *  Ein Nässe-Sensor schaltet bei Wasser den Strom des LED-Streifens ab.
 *
 *  NEU IN V4 – STROMSPAREN (README Kapitel 18):
 *   - Display: hell -> nach 30 s gedimmt -> nach 2 min aus (RUHE), nachts nach 15 s aus
 *   - WLAN nur zum Uhr-Abgleich (Start, alle 6 h, Befehl "sync"), danach aus
 *   - Bluetooth nur in Fenstern (Start 2 min, Symbol antippen 2 min, 60 s nach dem Trinken)
 *   - CPU 80 MHz, auf dem echten CYD Light-Sleep in RUHE (Wecken alle 100 ms + Touch + Nässe)
 *   - LED-Streifen bekommt nur Strom, wenn er leuchtet (FET an GPIO18)
 *   - Akku-Prozent per LiPo-Tabelle, Schutzabschaltung bei leerem Akku
 *   - "stromsparen 0" = Verhalten wie Version 3 (zum Vergleichen)
 *
 *  Simulation (Wokwi)                      | Echte Hardware
 *  ----------------------------------------+---------------------------------
 *  ILI9341 + kapazitiver Touch FT6206 (I2C)| CYD ESP32-2432S028R:
 *                                          | ILI9341 + resistiver Touch XPT2046
 *  HX711-Schieberegler (0–5 kg)            | HX711 + 5-kg-Wägezelle
 *  Schiebeschalter "NÄSSE"                 | LM393-Regensensor, Ausgang DO
 *  Potentiometer "AKKU"                    | Akku über Spannungsteiler am ADC
 *  LED "LAST"                              | LED-Strom: P-MOSFET AO3401A (High-Side)
 *  LED "LICHT" an GPIO21 (PWM)             | Hintergrundlicht des Displays (PWM)
 *  LED-Streifen 26 Pixel                   | BTF-LIGHTING WS2812B FCOB, 26 LEDs
 *  WLAN "Wokwi-GUEST" + NTP                | Heim-/Schul-WLAN (secrets.h) + NTP
 *  Telegram: nur Serial-Ausgabe (Stub)     | Telegram-Bot über WLAN
 *  Bluetooth: per Serial-Befehl simuliert   | BLE (NimBLE), HYDRO_BLE 1
 *
 *  Sichtbare Touch-Tasten „Leer“ / „Voll“ (Haupt- und Kalibrier-Bildschirm).
 *  Optional: 3 s Langdruck oder Serial „kalib“ öffnet den Kalibrier-Bildschirm.
 *  Serieller Monitor (115200 Baud): "hilfe", "status", "reset",
 *  "gewicht 75", "groesse 180", "zeit 23:59",
 *  "kalib", "leer", "voll",
 *  "bt suchen", "bt verbunden", "bt getrennt", "bt aus",
 *  "sync" (Uhr-Abgleich per WLAN), "stromsparen 0" / "stromsparen 1"
 * ============================================================================
 */

// ----------------------------------------------------------------------------
//  HARDWARE-AUSWAHL
//  0 = Wokwi-Simulation (ILI9341 + FT6206, Adafruit-Bibliotheken)  <- Standard
//  1 = echtes CYD ESP32-2432S028R (TFT_eSPI + XPT2046_Touchscreen)
// ----------------------------------------------------------------------------
#ifndef HYDRO_CYD
  #define HYDRO_CYD 0
#endif

// ----------------------------------------------------------------------------
//  BLUETOOTH-AUSWAHL
//  0 = Bluetooth nur simuliert (Serial-Befehle "bt ...")  <- Standard für Wokwi
//      (Wokwi kann kein Bluetooth simulieren)
//  1 = echtes BLE mit der Bibliothek NimBLE-Arduino (Gerät heißt "HydroDesk")
//      Echtes Gerät: HYDRO_CYD 1 UND HYDRO_BLE 1. Speicher: siehe README Kapitel 16
//      Ab V4 Partition "Huge APP (3MB No OTA/1MB SPIFFS)" PFLICHT (Default 1,25 MB ist zu klein).
// ----------------------------------------------------------------------------
#ifndef HYDRO_BLE
  #define HYDRO_BLE 0
#endif

// ----------------------------------------------------------------------------
//  STROMSPAREN (neu in V4, README Kapitel 18, Stromsparplan)
//  1 = Energie-Automat AKTIV -> GEDIMMT -> RUHE, WLAN nur zum Uhr-Abgleich,
//      Bluetooth nur in Fenstern, CPU 80 MHz, Sparblau, LED-Strom nur bei Bedarf  <- Standard
//  0 = Verhalten wie Version 3 (zum Vergleichen und für die Fehlersuche).
//      Umschalten geht auch zur Laufzeit: Serial "stromsparen 0" / "stromsparen 1".
// ----------------------------------------------------------------------------
#ifndef STROMSPAREN
  #define STROMSPAREN 1
#endif
// Echter Light-Sleep nur auf dem echten CYD. Wokwi simuliert Light-Sleep und
// GPIO-Wecken nicht verlässlich -> dort läuft derselbe Energie-Automat ohne Schlaf.
#ifndef HYDRO_LIGHTSLEEP
  #define HYDRO_LIGHTSLEEP HYDRO_CYD
#endif
#if HYDRO_LIGHTSLEEP && !HYDRO_CYD
  #error "HYDRO_LIGHTSLEEP 1 geht nur zusammen mit HYDRO_CYD 1"
#endif

#include <Arduino.h>
#include <SPI.h>
#include <WiFi.h>               // WLAN (im ESP32-Kern enthalten)
#include <time.h>               // Uhrzeit / Datum
#include <sys/time.h>           // settimeofday() für die Ersatzuhr
#include <esp_sntp.h>           // Meldung "NTP-Zeit empfangen"
#include <Preferences.h>        // Einstellungen dauerhaft im Flash (NVS)
#include <HX711.h>              // Wägezellen-Verstärker
#include <Adafruit_NeoPixel.h>  // LED-Streifen WS2812
#include <esp_sleep.h>          // Light-Sleep / Deep-Sleep (im ESP32-Kern enthalten)
#include <driver/gpio.h>        // gpio_hold_en(): Pin-Pegel im Schlaf festhalten

#if HYDRO_BLE
  #include <NimBLEDevice.h>        // Bibliothek "NimBLE-Arduino" (h2zero), nur für echtes BLE
#endif

#if HYDRO_CYD
  #include <TFT_eSPI.h>            // Display-Pins stehen in User_Setup.h der Bibliothek
  #include <XPT2046_Touchscreen.h> // resistiver Touch des CYD
#else
  #include <Wire.h>
  #include <Adafruit_GFX.h>
  #include <Adafruit_ILI9341.h>
  #include <Adafruit_FT6206.h>
#endif

// ============================================================================
//  EINSTELLUNGEN (hier dürfen die Azubis Werte ändern)
// ============================================================================
// --- Profil für das Tagesziel (auch per Serial: "gewicht 75", "groesse 180")
const float    KOERPERGEWICHT_KG    = 70.0f;
const int      KOERPERGROESSE_CM    = 175;
const float    ML_PRO_M2            = 1500.0f; // Trinkmenge pro m² Körperoberfläche
const int      ZIEL_MIN_ML          = 1500;
const int      ZIEL_MAX_ML          = 3500;

// --- Erinnerung (Trink-Plan + Pause nach echtem Schluck)
// WOKWI_DEMO_ERINNERUNG 1 = kurze Zeiten für die Simulation (README).
// Auf dem echten Gerät: #define WOKWI_DEMO_ERINNERUNG 0 (oder vor dem Compile setzen).
#ifndef WOKWI_DEMO_ERINNERUNG
  #define WOKWI_DEMO_ERINNERUNG 1
#endif
#if WOKWI_DEMO_ERINNERUNG
  const uint32_t ERINNERUNG_PAUSE_MS       = 90UL * 1000UL;          // Demo: 90 s Pause nach ≥100 ml
  const uint32_t ERINNERUNG_MIN_ABSTAND_MS = 60UL * 1000UL;          // Demo: frühestens alle 60 s
  const uint32_t TRUNK_FENSTER_MS          = 20UL * 1000UL;          // Demo: 20 s für ≥100 ml-Fenster
#else
  const uint32_t ERINNERUNG_PAUSE_MS       = 75UL * 60UL * 1000UL;   // 75 min Pause nach ≥100 ml
  const uint32_t ERINNERUNG_MIN_ABSTAND_MS = 90UL * 60UL * 1000UL;   // frühestens alle 90 min
  const uint32_t TRUNK_FENSTER_MS          = 10UL * 60UL * 1000UL;   // ~10 min Trinkfenster
#endif
const float    TRUNK_RESET_MIN_ML         = 100.0f;  // ab so viel im Fenster: Pause starten
const float    SCHLUCK_OHNE_PAUSE_ML      = 40.0f;   // darunter: zählt, setzt Pause NICHT
const uint8_t  ERINNERUNG_MAX_PRO_TAG     = 6;       // höchstens so viele Erinnerungen/Tag
const int      RUHE_START_STUNDE          = 22;      // Ruhezeit 22:00 ...
const int      RUHE_ENDE_STUNDE           = 7;       // ... bis 07:00 (keine Erinnerungen)
// Zeitplan (Soll-Anteil am Tagesziel): 12:00 → 40 %, 16:00 → 70 %, 20:00 → 100 %
// (20:00 = ca. 2 h vor Ruhezeit). Erinnerung nur, wenn hinter diesem Plan.

// --- WLAN + Uhrzeit
// Wokwi: offenes Gast-WLAN "Wokwi-GUEST" auf Kanal 6 (ohne Passwort).
// Echtes Gerät: Zugangsdaten NICHT hier eintragen, sondern in eine Datei
// secrets.h auslagern (die nicht ins Git kommt), z. B.
//   #define WLAN_SSID_GEHEIM "MeinWLAN"
//   #define WLAN_PASS_GEHEIM "geheim"
const char*    WLAN_SSID            = "Wokwi-GUEST";
const char*    WLAN_PASS            = "";
const int      WLAN_KANAL           = 6;
const char*    ZEITZONE             = "CET-1CEST,M3.5.0,M10.5.0/3"; // Deutschland inkl. Sommerzeit
const char*    NTP_SERVER           = "pool.ntp.org";
const uint32_t NTP_WARTEZEIT_MS     = 10000;  // danach Ersatzuhr ab 12:00

// --- Waage (1 g Wasser ~ 1 ml)
const float    WOKWI_FAKTOR         = 0.42f;  // Rohwert pro Gramm im Wokwi-HX711 "5kg" (5 kg = 2100)
const float    KALIBRIER_GEWICHT_G  = 500.0f; // Referenzgewicht für die Kalibrierung
const float    FLASCHE_DA_G         = 40.0f;  // ab hier gilt "Flasche steht auf dem Pad"
const float    FLASCHE_WEG_G        = 25.0f;  // darunter gilt "Flasche abgehoben" (Hysterese)
const float    STABIL_TOLERANZ_G    = 6.0f;   // so viel darf das Gewicht schwanken und gilt trotzdem als ruhig
const uint32_t STABIL_MS            = 1500;   // so lange muss das Gewicht ruhig sein (Trinken)
const uint32_t KALIB_STABIL_MS      = 1000;   // Kalibrierung: ~1 s ruhiges Gewicht vor Übernahme
const float    MIN_SCHLUCK_G        = 15.0f;  // kleinere Abnahmen werden ignoriert (Rauschen)
const float    MIN_NACHFUELL_G      = 20.0f;  // ab dieser Zunahme gilt "nachgefüllt"
const float    NEGATIV_FEHLER_G     = -30.0f; // deutlich negatives Gewicht = Tara falsch

// --- Leergewicht der Flasche (wird automatisch gelernt, siehe leergewichtLernen())
const float    LEERGEWICHT_START_G  = 150.0f; // Startwert; übliche Flaschen wiegen leer 100–400 g
const uint32_t PAD_LEER_RESET_MS    = 60000;  // Pad so lange leer + deutlich anderes Gewicht ...
const float    ANDERE_FLASCHE_G     = 250.0f; // ... (mind. so viel Unterschied) = andere Flasche

// --- Nässe
const uint32_t TROCKEN_FREIGABE_MS  = 5000;   // so lange trocken -> Sperre hebt sich selbst auf

// --- Akku (in Wokwi: Potentiometer). Simulation: 0..4095 -> 3,0..4,2 V
const float    AKKU_LEER_V          = 3.0f;   // nur Wokwi: Poti ganz links
const float    AKKU_VOLL_V          = 4.2f;   // nur Wokwi: Poti ganz rechts
const float    AKKU_TEILER          = 2.0f;   // echt: Spannungsteiler 2 x 10 kΩ -> ADC sieht die halbe Akkuspannung
// Akku-Prozent aus der Spannung (neu in V4, statt linear 3,0..4,2 V):
// TYPISCHE Ruhespannungs-Kurve einer LiPo-Zelle (Literaturwert, Quelle: README Kapitel 18),
// NICHT am eigenen Akku gemessen. Nach dem Entladetest (Stromsparplan, Test H5) ersetzen.
const float    AKKU_TABELLE_V[]     = { 3.27f, 3.61f, 3.69f, 3.71f, 3.73f, 3.75f, 3.77f, 3.79f, 3.80f, 3.82f, 3.84f,
                                        3.85f, 3.87f, 3.91f, 3.95f, 3.98f, 4.02f, 4.08f, 4.11f, 4.15f, 4.20f };
const uint8_t  AKKU_TABELLE_P[]     = { 0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50,
                                        55, 60, 65, 70, 75, 80, 85, 90, 95, 100 };
const uint8_t  AKKU_TABELLE_N       = sizeof(AKKU_TABELLE_P) / sizeof(AKKU_TABELLE_P[0]);
static_assert(sizeof(AKKU_TABELLE_V) / sizeof(AKKU_TABELLE_V[0]) == sizeof(AKKU_TABELLE_P), "Akku-Tabelle: gleich viele Werte");
// Schutz bei leerem Akku: so lange unter AKKU_ABSCHALT_V -> Meldung, dann Tiefschlaf mit Timer
const float    AKKU_ABSCHALT_V      = 3.30f;  // Schätzwert, nach der Entlademessung anpassen
const uint32_t AKKU_ABSCHALT_MS     = 60000;  // 60 s lang darunter (kurze Einbrüche zählen nicht)
const uint32_t AKKU_LEER_MELDUNG_MS = 10000;  // "Akku leer - bitte laden" so lange zeigen
const uint32_t AKKU_LEER_SCHLAF_MIN = 15;     // im Tiefschlaf alle 15 min prüfen, ob geladen wird
const float    AKKU_WIEDERANLAUF_V  = 3.60f;  // erst ab dieser Spannung wieder normal starten (Erholung im Leerlauf)
const int      AKKU_WARN_PROZENT    = 20;     // darunter: Hinweis + 2x rot blinken
const int      AKKU_KRITISCH_PROZENT = 10;    // darunter: Balken "Bitte laden" + 4x rot blinken
const int      AKKU_HYSTERESE_PROZENT = 2;    // erst bei Schwelle + 2 % gilt die Warnung als vorbei
const uint8_t  AKKU_BLINK_WARN      = 2;      // Anzahl Blitze unter 20 %
const uint8_t  AKKU_BLINK_KRITISCH  = 4;      // Anzahl Blitze unter 10 %
const uint32_t AKKU_BLINK_AN_MS     = 300;    // Warnung <20 %: kurz blitzen
const uint32_t AKKU_BLINK_AUS_MS    = 300;
const uint32_t AKKU_BLINK_KRITISCH_AN_MS  = 650; // kritisch <10 %: normaler Takt (langsamer)
const uint32_t AKKU_BLINK_KRITISCH_AUS_MS = 650;
const uint32_t AKKU_WIEDERHOLUNG_MS = 10UL * 60UL * 1000UL; // Blinkmuster alle 10 min wiederholen (0 = nie)
const uint32_t AKKU_HINWEIS_MS      = 5000;   // Hinweis "Akku unter 20 %" so lange im Statusfeld

// --- LED-Streifen: leuchtet NUR bei Ereignissen, sonst Dauerlicht.
//     Blinken gibt es NUR bei: Akku-Warnung (rot), Bluetooth sucht (weiß),
//     Handy verbunden (2x lila). Alles andere leuchtet ruhig.
// --- Echte Hardware: BTF-LIGHTING WS2812B FCOB (COB-Streifen), 5 V, 160 LED/m, 5 mm breit,
//     jede LED mit eigenem IC, teilbar alle 12,5 mm (2 LEDs). Verbaut: 13 Segmente = 162,5 mm
//     = 26 LEDs hinter der Diffusor-Leiste vorne -> die ganze Frontlinie leuchtet gleichmäßig.
const uint8_t  LED_ANZAHL           = 26;
// Strombudget (5-V-Wandler Pololu S13V10F5, max. 1 A):
//   26 LEDs voll weiß (255)           ca. 0,49 A  (ungünstigster Fall, kommt im Programm nicht vor)
//   mit LED_HELLIGKEIT 60 (= 60/255)  höchstens ca. 0,12 A
//   + CYD (Display + ESP32 + WLAN/BLE) ca. 0,25–0,35 A  -> zusammen unter 0,5 A, genug Reserve.
//   LED_HELLIGKEIT darum höchstens 80 einstellen (ca. 0,15 A für die LEDs).
const uint8_t  LED_HELLIGKEIT       = 60;     // 0..255 (mittel), höchstens 80 (Strombudget, siehe oben)
static_assert(LED_HELLIGKEIT <= 80, "LED_HELLIGKEIT höchstens 80 (Strombudget 5-V-Wandler)");
const uint32_t LED_GRUEN_MS         = 10000;  // "Ziel erreicht" 10 s grün
const uint32_t LED_ROT_MS           = 5000;   // Waagen-Fehler: 5 s rot
// Erinnerung (V4): erst LED_ERINNERUNG_HELL_MS voll blau, danach ruhiges "Sparblau" (Dauerlicht)
const uint32_t LED_ERINNERUNG_HELL_MS = 2UL * 60UL * 1000UL;
const uint8_t  LED_HELLIGKEIT_SPAR  = 15;     // wirksame Helligkeit 0..255 für Sparblau
static_assert(LED_HELLIGKEIT_SPAR <= LED_HELLIGKEIT, "Sparblau darf nicht heller sein als normal");
// Blau-Wert für Sparblau: LED_HELLIGKEIT wird zusätzlich angewendet -> 255 * 15 / 60 = 64
const uint8_t  LED_SPARBLAU_WERT    = (uint8_t)((255U * LED_HELLIGKEIT_SPAR + LED_HELLIGKEIT / 2) / LED_HELLIGKEIT);
// LED-Strom (FET an GPIO18): nach dem Einschalten kurz warten, bevor Daten gesendet werden
const uint32_t LED_STROM_EINSCHWING_MS = 10;

// --- Bluetooth (Symbol oben rechts + LED-Status)
const bool     BT_START_SUCHEN      = true;   // beim Einschalten gleich nach dem Handy suchen (Demo)
const uint32_t BT_SUCH_TIMEOUT_MS   = 2UL * 60UL * 1000UL; // Start + Symbol antippen: so lange suchen, dann "nicht verbunden"
const uint32_t BT_SYNC_FENSTER_MS   = 60UL * 1000UL;       // V4: nach jedem Trinken/Nachfüllen still sichtbar (ohne Blinken)
const uint32_t BT_WEISS_AN_MS       = 500;    // Suchen: weiß blinken 500 ms an ...
const uint32_t BT_WEISS_AUS_MS      = 500;    // ... 500 ms aus
const uint8_t  BT_WEISS_WERT        = 90;     // gedimmtes Weiß: 0..255 je Farbkanal (zusätzlich LED_HELLIGKEIT)
const uint8_t  BT_LILA_ANZAHL       = 2;      // verbunden: genau 2x lila blinken, dann normal
const uint32_t BT_LILA_AN_MS        = 300;
const uint32_t BT_LILA_AUS_MS       = 300;
const uint32_t BT_NOTIFY_MS         = 1000;   // nur echtes BLE: Werte höchstens 1x pro Sekunde senden
const char*    BT_NAME              = "HydroDesk"; // so heißt das Gerät in der Bluetooth-Liste des Handys
// Eigene 128-Bit-UUIDs (zufällig erzeugt) für den HydroDesk-Dienst
const char*    BT_SERVICE_UUID      = "4f9a0001-6c1e-4b8e-9d6a-2b7c1e0a4d10";
const char*    BT_WERTE_UUID        = "4f9a0002-6c1e-4b8e-9d6a-2b7c1e0a4d10"; // lesen + notify: "1250/2750 ml"

// --- Stromsparen (V4). Nur wirksam mit STROMSPAREN 1 bzw. nach "stromsparen 1"
const uint32_t ANZEIGE_DIMMEN_NACH_MS    = 30UL * 1000UL;   // 30 s ohne Aktivität -> GEDIMMT
const uint32_t ANZEIGE_AUS_NACH_MS       = 2UL * 60UL * 1000UL; // 2 min ohne Aktivität -> RUHE (Display aus)
const uint32_t ANZEIGE_AUS_NACH_MS_NACHT = 15UL * 1000UL;   // in der Ruhezeit 22-7 Uhr schon nach 15 s aus
const uint8_t  LCD_HELL             = 255;    // PWM-Wert Hintergrundlicht 0..255 (AKTIV)
const uint8_t  LCD_GEDIMMT          = 40;     // ca. 16 % (GEDIMMT)
const uint32_t LCD_PWM_FREQ_HZ      = 5000;   // LEDC an GPIO21
const uint8_t  LCD_PWM_BITS         = 8;
const uint32_t RUHE_WECKTAKT_MS     = 100;    // Light-Sleep: Wecken passend zu 10 Waagen-Messungen pro Sekunde
const uint32_t CPU_MHZ              = 80;     // statt 240 MHz (offizielle Option "80MHz (WiFi/BT)")
const uint32_t WLAN_ABGLEICH_ALLE_MS     = 6UL * 60UL * 60UL * 1000UL; // Uhr-Abgleich alle 6 h
const uint32_t WLAN_ABGLEICH_OHNE_NTP_MS = 30UL * 60UL * 1000UL;       // noch nie NTP: alle 30 min versuchen
const uint32_t WLAN_ABGLEICH_TIMEOUT_MS  = 20UL * 1000UL;  // so lange WLAN + NTP versuchen, dann aufgeben
const bool     RUHE_PINS_HALTEN     = true;   // Light-Sleep: Pegel von GPIO18/21/22/23 festhalten (Test H8)
const bool     TOUCH_IRQ_NUTZEN     = true;   // CYD: PENIRQ (GPIO36) als Hinweis + Weckquelle

// --- Versteckter Service-Modus
const uint32_t LANGDRUCK_MS         = 3000;   // 3 s drücken -> Kalibrierung

// ============================================================================
//  PINS  (Tabelle mit CYD-Vorschlag: README.md)
// ============================================================================
const int PIN_TFT_SCK   = 14;
const int PIN_TFT_MISO  = 12;
const int PIN_TFT_MOSI  = 13;
const int PIN_TFT_CS    = 15;
const int PIN_TFT_DC    = 2;
const int PIN_TFT_RST   = 4;   // CYD: RST hängt an EN -> dort -1
const int PIN_TFT_LED   = 21;  // Hintergrundbeleuchtung (CYD: GPIO21)
const int PIN_TOUCH_SDA = 32;  // nur Wokwi: FT6206 über I2C
const int PIN_TOUCH_SCL = 33;
const int PIN_HX711_DT  = 27;  // CYD: Stecker CN1
const int PIN_HX711_SCK = 22;  // CYD: Stecker CN1 / P3
const int PIN_AKKU_ADC  = 35;  // nur Eingang, ADC1 (funktioniert auch mit WLAN)
const int PIN_NAESSE    = 19;  // LOW = nass (wie LM393-Modul DO)
const int PIN_LED_DATA  = 23;  // WS2812B Daten (DIN); echt: 330–470 Ω in Reihe direkt am Streifen-DIN
const int PIN_LAST      = 18;  // HIGH = Strom für den LED-Streifen an (NPN BC547B -> P-MOSFET AO3401A, High-Side)
const int PIN_TOUCH_IRQ = 36;  // nur CYD: XPT2046 PENIRQ (LOW = berührt), nur Eingang

// ============================================================================
//  ZUSTANDSAUTOMAT
// ============================================================================
/*
 *  Das Gerät ist immer in GENAU EINEM der folgenden Zustände:
 *
 *  IDLE           Keine Flasche auf dem Pad (oder gerade abgehoben).
 *                 Gewichtsänderungen werden ignoriert.
 *  MESSEN         Flasche steht auf dem Pad, Gewicht wird überwacht.
 *                 Wird die Flasche nach dem Abheben LEICHTER zurückgestellt
 *                 und ist das Gewicht wieder ruhig, zählt die Differenz als
 *                 "getrunken". Wird sie SCHWERER, war es Nachfüllen
 *                 (zählt NICHT negativ, dient aber zum Lernen des Leergewichts).
 *  ERINNERUNG     Hinter dem Trink-Plan, Pause vorbei, Abstand eingehalten,
 *                 unter Max/Tag, außerhalb Ruhezeit, Ziel nicht erreicht.
 *                 LEDs dauerhaft blau, bis wieder getrunken wird.
 *  ZIEL_ERREICHT  Tagesziel erreicht. LEDs 10 s grün, dann aus.
 *                 Keine Erinnerungen mehr, es wird weiter gezählt.
 *  NAESSE_SPERRE  Nässe-Sensor meldet Wasser: LED-Strom sofort AUS (Streifen dunkel,
 *                 V4: kein Bernstein mehr, weil der Streifen dann keinen Strom hat),
 *                 rote Vollbild-Warnung. Hebt sich AUTOMATISCH auf, wenn der
 *                 Sensor TROCKEN_FREIGABE_MS (5 s) lang trocken ist.
 *  KALIBRIERUNG   Kalibrier-Bildschirm (3 s / Serial "kalib"); Tasten Leer/Voll
 *                 auch auf dem Hauptbildschirm. Messung pausiert.
 *
 *  Übergänge (Priorität von oben nach unten):
 *    jeder Zustand   --Wasser erkannt-----------------> NAESSE_SPERRE
 *    NAESSE_SPERRE   --5 s ununterbrochen trocken-----> IDLE
 *    normale Zustände--3 s Display / "kalib"----------> KALIBRIERUNG
 *    KALIBRIERUNG    --Taste "Fertig"-----------------> IDLE
 *    sonst wird der passende Zustand jedes Mal neu bestimmt:
 *        getrunken >= Ziel                          -> ZIEL_ERREICHT
 *        erinnerungMoeglich()                       -> ERINNERUNG
 *        Flasche steht                              -> MESSEN
 *        sonst                                      -> IDLE
 *
 *  Akku-Warnung (unter 20 % / unter 10 %) und Fehler sind KEINE eigenen Zustände, sondern eine
 *  Zusatzanzeige, weil das Gerät trotzdem weiter misst.
 */
enum Zustand : uint8_t {
  IDLE,
  MESSEN,
  ERINNERUNG,
  ZIEL_ERREICHT,
  NAESSE_SPERRE,
  KALIBRIERUNG
};

// Woher kommt die Uhrzeit?
enum UhrQuelle : uint8_t { UHR_KEINE, UHR_ERSATZ, UHR_NTP };

/*
 *  Bluetooth-Zustand (eigener kleiner Automat, unabhängig vom Haupt-Zustand):
 *    BT_AUS              Bluetooth ausgeschaltet         Symbol: nicht gezeichnet  LEDs: -
 *    BT_SUCHEN           sichtbar, wartet auf das Handy  Symbol: blinkt weiß/blau  LEDs: weiß blinken
 *                        (V4: stilles Sync-Fenster)      Symbol: fest blau         LEDs: -
 *    BT_VERBUNDEN        Handy verbunden                 Symbol: blau + Punkte     LEDs: 2x lila, dann normal
 *    BT_NICHT_VERBUNDEN  Fenster vorbei                  Symbol: grau              LEDs: -
 *  Übergänge:  "bt suchen" / Start / Symbol antippen --> BT_SUCHEN laut, 2 min
 *              Trinken/Nachfüllen erkannt (V4) --------> BT_SUCHEN still, 60 s
 *              BT_SUCHEN --Handy verbindet---> BT_VERBUNDEN
 *              BT_SUCHEN --Zeit um-----------> BT_NICHT_VERBUNDEN (V4: BLE-Stack aus)
 *              BT_VERBUNDEN --Handy weg------> BT_SUCHEN (gleiche Art wie vorher: laut 2 min / still 60 s)
 *              jeder Zustand --"bt aus"------> BT_AUS
 */
enum BtZustand : uint8_t { BT_AUS, BT_SUCHEN, BT_VERBUNDEN, BT_NICHT_VERBUNDEN };

// Wer bestimmt gerade die LED-Farbe? (nur für das Protokoll im Seriellen Monitor)
enum LedQuelle : uint8_t { L_AUS, L_GESPERRT, L_AKKU, L_LILA, L_WEISS, L_ROT, L_BLAU, L_SPARBLAU, L_GRUEN };

/*
 *  Energie-Zustand (V4, eigener kleiner Automat, unabhängig vom Haupt-Zustand):
 *    E_AKTIV    Licht LCD_HELL, Display wird gezeichnet
 *    E_GEDIMMT  Licht LCD_GEDIMMT, Display wird gezeichnet
 *    E_RUHE     Licht 0, kein Zeichnen (CYD: Display-Schlaf + Light-Sleep, wenn erlaubt)
 *  Übergänge:  30 s ohne Aktivität -> GEDIMMT, 2 min (nachts 15 s) -> RUHE,
 *              jede Aktivität (Touch, Flasche, Trinken, Erinnerung, Nässe, ...) -> AKTIV
 */
enum Energie : uint8_t { E_AKTIV, E_GEDIMMT, E_RUHE };

// WLAN (V4): aus, kurzer Uhr-Abgleich oder dauerhaft an (nur "stromsparen 0" = wie V3)
enum WlanModus : uint8_t { WLAN_AUS, WLAN_ABGLEICH, WLAN_DAUER };

// Touch-Taste (sichtbar: Leer / Voll auf Haupt- und Kalibrier-Bildschirm)
struct Taste {
  int16_t x, y, w, h;
  const char* beschriftung;
};

// Bildschirm-Bereiche, die einzeln neu gezeichnet werden (gegen Flackern)
enum Bereich : uint8_t {
  B_ZEIT, B_DATUM, B_AKKU, B_MENGE, B_VON, B_BALKEN, B_ZIELTEXT,
  B_FLASCHE, B_LEER, B_ZULETZT, B_NAECHSTE, B_TASTEN, B_STATUS, B_BT, B_ANZAHL
};

const char* zustandName(Zustand z) {
  switch (z) {
    case IDLE:          return "IDLE";
    case MESSEN:        return "MESSEN";
    case ERINNERUNG:    return "ERINNERUNG";
    case ZIEL_ERREICHT: return "ZIEL_ERREICHT";
    case NAESSE_SPERRE: return "NAESSE_SPERRE";
    case KALIBRIERUNG:  return "KALIBRIERUNG";
  }
  return "?";
}

const char* energieName(Energie e) {
  switch (e) {
    case E_AKTIV:   return "AKTIV";
    case E_GEDIMMT: return "GEDIMMT";
    case E_RUHE:    return "RUHE";
  }
  return "?";
}

const char* btName(BtZustand b) {
  switch (b) {
    case BT_AUS:             return "aus";
    case BT_SUCHEN:          return "suchen";
    case BT_VERBUNDEN:       return "verbunden";
    case BT_NICHT_VERBUNDEN: return "nicht verbunden";
  }
  return "?";
}

// ============================================================================
//  GLOBALE VARIABLEN
// ============================================================================
HX711             waage;
Adafruit_NeoPixel leds(LED_ANZAHL, PIN_LED_DATA, NEO_GRB + NEO_KHZ800);
Preferences       speicher;

Zustand  zustand          = IDLE;

// Waage
float    tara             = 0;              // Rohwert bei leerem Pad
float    faktor           = WOKWI_FAKTOR;   // Rohwert pro Gramm
float    rohMittel        = 0;              // geglätteter Rohwert
float    gewicht          = 0;              // aktuelles Gewicht in g
bool     waageOk          = false;
uint32_t letzteWaageMs    = 0;
float    ruheStartGewicht = 0;
uint32_t ruheSeit         = 0;
bool     gewichtRuhig     = false;
bool     flascheSteht     = false;
uint32_t padLeerSeit      = 0;              // seit wann das Pad leer ist
bool     referenzGueltig  = false;
float    referenzGewicht  = 0;              // letztes ruhiges Gewicht mit Flasche
float    leergewicht      = LEERGEWICHT_START_G;
bool     leergewichtGelernt = false;
bool     flascheKalibriert = false;         // Leergewicht aus Kalibrierung (bevorzugt)
float    vollgewicht      = 0;              // g bei "volle Flasche"
int      flaschenKapazitaetMl = 0;          // max(0, voll - leer), 1 g ≈ 1 ml
bool     kapazitaetKalibriert = false;

// Trinken + Ziel
int      getrunkenHeute   = 0;              // ml
float    profilKg         = KOERPERGEWICHT_KG;
int      profilCm         = KOERPERGROESSE_CM;
int      tagesziel        = 2000;           // wird aus dem Profil berechnet
uint32_t letzterSchluckMs = 0;
bool     heuteGetrunken   = false;
uint32_t erinnerungPauseBisMs = 0;          // Pause nach ≥100 ml (keine Erinnerung)
uint32_t letzteErinnerungMs   = 0;          // für Mindestabstand
uint8_t  erinnerungenHeute    = 0;
uint32_t trunkFensterStartMs  = 0;
float    trunkFensterMl       = 0;          // Summe im ~10-min-Fenster (≥40-ml-Schlucke)

// Sensoren
bool     nass             = false;
uint32_t trockenSeit      = 0;
uint8_t  akkuStufe        = 0;    // 0 = ok, 1 = unter 20 %, 2 = unter 10 %
uint32_t akkuWarnMs       = 0;    // Zeitpunkt der letzten Akku-Warnung (für die 10-min-Wiederholung)
uint32_t akkuHinweisBisMs = 0;    // bis dahin Hinweis "Akku unter 20 %" im Statusfeld
float    akkuVolt         = 4.2f;
int      akkuProzent      = 100;
uint32_t akkuLeerSeitMs   = 0;    // V4: seit wann unter AKKU_ABSCHALT_V (0 = nicht)
bool     fehlerVorher     = false;
// Bleibt im Tiefschlaf erhalten (RTC-Speicher): "wir schlafen, weil der Akku leer war"
RTC_DATA_ATTR bool akkuLeerSchlaf = false;

// Uhr
UhrQuelle uhrQuelle       = UHR_KEINE;
volatile bool ntpEmpfangen = false;
long     letzterTag       = -1;             // Jahr*1000 + Tag im Jahr
bool     wlanVerbunden    = false;
// WLAN-Abgleich (V4)
WlanModus wlanModus       = WLAN_AUS;
uint32_t wlanStartMs      = 0;              // Beginn des laufenden Abgleichs (Timeout)
uint32_t letzterAbgleichMs = 0;             // Beginn des letzten Abgleichs (Abstand 6 h)
bool     ntpAngefragt     = false;          // NTP in diesem Abgleich schon angefragt?
bool     driftMessbar     = false;          // Uhr war vorher per NTP gestellt -> Abweichung sinnvoll
int64_t  driftVorherUs    = 0;              // Systemzeit beim Anfragen ...
uint32_t driftVorherMs    = 0;              // ... und millis() dazu
uint32_t letzterNtpMs     = 0;              // millis() beim letzten NTP-Empfang
long     letzteAbweichungMs = 0;            // gemessene Abweichung beim letzten Abgleich (Protokoll/Status)

// LEDs
uint32_t gruenBisMs       = 0;
uint32_t rotBisMs         = 0;
uint32_t blinkStartMs     = 0;    // Akku-Blinkmuster: Start ...
uint8_t  blinkAnzahl      = 0;    // ... und Anzahl Blitze (0 = kein Blinken)
uint32_t blinkAnMs        = AKKU_BLINK_AN_MS;   // aktiver An-Takt (Warnung oder kritisch)
uint32_t blinkAusMs       = AKKU_BLINK_AUS_MS;  // aktiver Aus-Takt
bool     ledStromAn       = false;  // V4: FET an GPIO18 leitet (Streifen hat 5 V)

// Bluetooth
BtZustand btZustand       = BT_AUS;
uint32_t btSuchStartMs    = 0;    // Beginn der Suche (für den Blinktakt)
uint32_t btFensterEndeMs  = 0;    // V4: Ende des Sichtbarkeits-Fensters
bool     btStill          = false; // V4: stilles Sync-Fenster (nach dem Trinken, ohne Blinken)
bool     lilaAusstehend   = false; // 2x lila wartet, bis das Akku-Blinken fertig ist
bool     lilaLaeuft       = false;
uint32_t lilaStartMs      = 0;

// Anzeige / Touch
bool     bildschirmNeu    = true;
uint8_t  kalSchritt       = 0;              // 0=warte Leer, 1=warte Voll, 2=fertig
uint32_t touchStartMs     = 0;
bool     touchGehalten    = false;
bool     langdruckErledigt = false;
String   kalibMeldung     = "";             // deutsche Feedback-/Fehlermeldung auf dem Display
uint32_t kalibMeldungBisMs = 0;             // Anzeige bis zu diesem millis()-Zeitpunkt

// Energie (V4)
bool     stromsparen      = STROMSPAREN;    // Hauptschalter, per Serial umschaltbar
Energie  energie          = E_AKTIV;
uint32_t letzteAktivitaetMs = 0;
uint8_t  lichtWert        = 0;              // aktueller PWM-Wert des Hintergrundlichts
bool     weckBeruehrung   = false;          // diese Berührung hat nur geweckt (zählt nicht als Taste)
uint32_t waageLetzteMessungMs = 0;          // für den Wecktakt im Light-Sleep
uint32_t schlafZyklen     = 0;              // Anzahl Light-Sleep-Zyklen (Status)

// ============================================================================
//  HILFSFUNKTIONEN: LOG, TELEGRAM-STUB, ZAHLEN
// ============================================================================
// Zeitstempel für den Seriellen Monitor: Uhrzeit, falls bekannt, sonst Laufzeit
String zeitstempel() {
  char buf[16];
  if (uhrQuelle != UHR_KEINE) {
    time_t t = time(nullptr);
    struct tm lt;
    localtime_r(&t, &lt);
    snprintf(buf, sizeof(buf), "%02d:%02d:%02d", lt.tm_hour, lt.tm_min, lt.tm_sec);
  } else {
    uint32_t s = millis() / 1000;
    snprintf(buf, sizeof(buf), "+%02lu:%02lu", (unsigned long)(s / 60), (unsigned long)(s % 60));
  }
  return String(buf);
}

void logZeile(const char* kategorie, const String& text) {
  Serial.print('[');
  Serial.print(zeitstempel());
  Serial.print("] [");
  Serial.print(kategorie);
  Serial.print("] ");
  Serial.println(text);
}

// Telegram wird NICHT simuliert. Später hier den Bot-Aufruf einbauen.
void telegramSenden(const String& nachricht) {
  logZeile("TELEGRAM-STUB", "würde senden: \"" + nachricht + "\"");
}

// 1250 -> "1.250" (deutscher Tausenderpunkt)
String mitPunkt(long wert) {
  bool negativ = wert < 0;
  unsigned long v = negativ ? -wert : wert;
  String s = String(v % 1000);
  if (v >= 1000) {
    while (s.length() < 3) s = "0" + s;
    s = String(v / 1000) + "." + s;
  }
  return negativ ? "-" + s : s;
}

// ============================================================================
//  TAGESZIEL AUS KÖRPERGEWICHT UND GRÖSSE
// ============================================================================
/*
 *  RICHTWERT, KEINE MEDIZINISCHE EMPFEHLUNG!
 *  1. Körperoberfläche nach Mosteller:  KOF [m²] = Wurzel(cm * kg / 3600)
 *  2. Tagesziel = KOF * 1500 ml/m²
 *  3. auf 50 ml runden, Grenzen 1500 ... 3500 ml
 *  Beispiel 70 kg, 175 cm: Wurzel(175*70/3600) = 1,845 m² -> 2767 ml -> 2750 ml
 */
int zielBerechnen(float kg, int cm) {
  float kof = sqrtf(cm * kg / 3600.0f);
  int ml = (int)lroundf(kof * ML_PRO_M2 / 50.0f) * 50;
  return constrain(ml, ZIEL_MIN_ML, ZIEL_MAX_ML);
}

void zielAktualisieren(bool loggen) {
  tagesziel = zielBerechnen(profilKg, profilCm);
  if (loggen) {
    float kof = sqrtf(profilCm * profilKg / 3600.0f);
    logZeile("ZIEL", "Profil " + String(profilKg, 1) + " kg, " + String(profilCm) + " cm -> KOF " +
             String(kof, 3) + " m² -> Tagesziel " + String(tagesziel) + " ml (Richtwert)");
  }
}

// ============================================================================
//  HARDWARE-ABSTRAKTION DISPLAY + TOUCH
//  Nur dieser Block unterscheidet sich zwischen Wokwi und CYD.
//  Der Rest benutzt nur anzeigeInit(), readTouch() und tft.xxx()-Funktionen,
//  die Adafruit_GFX UND TFT_eSPI beide kennen.
// ============================================================================
const int16_t BREITE = 240;   // Hochformat (Display links im Gehäuse)
const int16_t HOEHE  = 320;

#if HYDRO_CYD
  TFT_eSPI tft;
  SPIClass touchSpi(VSPI);
  // CYD-Touch: CS 33. IRQ (GPIO36) liest der Sketch selbst (V4): kein Interrupt der Bibliothek,
  // damit GPIO36 im Light-Sleep als Weckquelle dienen kann (Errata: LOW ist nur ein Hinweis).
  XPT2046_Touchscreen touch(33);
  // Rohwerte -> Pixel. Am echten Gerät kalibrieren (Ecken antippen).
  const int TOUCH_X_MIN = 200, TOUCH_X_MAX = 3700;
  const int TOUCH_Y_MIN = 240, TOUCH_Y_MAX = 3800;
#else
  const bool      TOUCH_SPIEGELN = true;  // FT6206 zählt gespiegelt zur Rotation 0
  SPIClass        tftSpi(HSPI);
  Adafruit_ILI9341 tft(&tftSpi, PIN_TFT_DC, PIN_TFT_CS, PIN_TFT_RST);
  Adafruit_FT6206 touch;
#endif

bool touchBereit = false;

// Hintergrundlicht per PWM (V4, M1). In Wokwi zeigt die Hilfs-LED "LICHT" an GPIO21 den Wert.
void hintergrundlichtSetzen(uint8_t wert) {
  lichtWert = wert;
  ledcWrite(PIN_TFT_LED, wert);
}

void anzeigeInit() {
#if HYDRO_CYD
  tft.init();                        // (TFT_eSPI schaltet ggf. TFT_BL ein -> LEDC erst danach)
  tft.setRotation(0);                // Hochformat 240 x 320
  touchSpi.begin(25, 39, 32, 33);
  touch.begin(touchSpi);
  touch.setRotation(0);
  pinMode(PIN_TOUCH_IRQ, INPUT);     // PENIRQ (GPIO36 hat keine internen Pull-Widerstände)
  touchBereit = true;
#else
  tftSpi.begin(PIN_TFT_SCK, PIN_TFT_MISO, PIN_TFT_MOSI, -1);
  tft.begin();
  tft.setRotation(0);                // Hochformat 240 x 320
  tft.cp437(true);                   // richtige Zeichentabelle für Umlaute
  Wire.begin(PIN_TOUCH_SDA, PIN_TOUCH_SCL);
  touchBereit = touch.begin(40);
#endif
  ledcAttach(PIN_TFT_LED, LCD_PWM_FREQ_HZ, LCD_PWM_BITS);   // Kern 3.x: Pin, Frequenz, Auflösung
  hintergrundlichtSetzen(LCD_HELL);
  tft.fillScreen(0x0000);
  logZeile("SYSTEM", touchBereit ? "Display + Touch bereit" : "Display bereit, Touch NICHT gefunden");
}

// Liefert true, SOLANGE das Display berührt wird, und die Position in
// Display-Pixeln (0..239, 0..319). Kurz-/Langdruck wertet touchAuswerten() aus.
bool readTouch(int16_t& x, int16_t& y) {
  if (!touchBereit) return false;
#if HYDRO_CYD
  // PENIRQ HIGH = sicher nicht berührt (spart die SPI-Abfrage). LOW ist nur ein Hinweis
  // (Errata GPIO36: kurze Störimpulse) -> erst die Druckmessung entscheidet.
  if (TOUCH_IRQ_NUTZEN && digitalRead(PIN_TOUCH_IRQ) == HIGH) return false;
  if (!touch.touched()) return false;
  TS_Point p = touch.getPoint();
  x = constrain(map(p.x, TOUCH_X_MIN, TOUCH_X_MAX, 0, BREITE - 1), 0, BREITE - 1);
  y = constrain(map(p.y, TOUCH_Y_MIN, TOUCH_Y_MAX, 0, HOEHE - 1), 0, HOEHE - 1);
#else
  if (touch.touched() == 0) return false;
  TS_Point p = touch.getPoint();
  x = TOUCH_SPIEGELN ? BREITE - 1 - p.x : p.x;
  y = TOUCH_SPIEGELN ? HOEHE - 1 - p.y : p.y;
  x = constrain(x, 0, BREITE - 1);
  y = constrain(y, 0, HOEHE - 1);
#endif
  return true;
}

// Display schlafen legen / wecken (V4, M3). Wokwi: Licht wird nicht simuliert -> schwarz zeichnen.
void anzeigeSchlafen() {
#if HYDRO_CYD
  tft.writecommand(0x28);            // DISPOFF
  tft.writecommand(0x10);            // SLPIN (ILI9341: danach 5 ms bis zum nächsten Befehl)
  delay(5);
#else
  tft.fillScreen(0x0000);
#endif
}

void anzeigeWecken() {
#if HYDRO_CYD
  tft.writecommand(0x11);            // SLPOUT
  delay(120);                        // ILI9341: 120 ms warten
  tft.writecommand(0x29);            // DISPON
#endif
}

// ============================================================================
//  ZEICHEN-HILFEN (unabhängig von der Hardware)
// ============================================================================
const uint16_t SCHWARZ     = 0x0000;
const uint16_t WEISS       = 0xFFFF;
const uint16_t GRAU        = 0x8410;
const uint16_t HELLGRAU    = 0xBDF7;
const uint16_t DUNKELGRAU  = 0x2945;
const uint16_t ROT         = 0xF800;
const uint16_t DUNKELROT   = 0x8000;
const uint16_t GRUEN       = 0x07E0;
const uint16_t DUNKELGRUEN = 0x03E0;
const uint16_t BLAU        = 0x041F;
const uint16_t DUNKELBLAU  = 0x0010;
const uint16_t CYAN        = 0x07FF;
const uint16_t GELB        = 0xFFE0;
const uint16_t ORANGE      = 0xFD20;

// Wandelt deutsche Umlaute (UTF-8 im Quelltext) in die Zeichentabelle des
// Display-Fonts (CP437) um. Andere Sonderzeichen werden weggelassen.
String fuerDisplay(const String& s) {
  String r;
  for (unsigned int i = 0; i < s.length(); i++) {
    uint8_t c = (uint8_t)s[i];
    if (c == 0xC3 && i + 1 < s.length()) {
      uint8_t d = (uint8_t)s[++i];
      switch (d) {
        case 0xA4: r += (char)0x84; break; // ä
        case 0xB6: r += (char)0x94; break; // ö
        case 0xBC: r += (char)0x81; break; // ü
        case 0x84: r += (char)0x8E; break; // Ä
        case 0x96: r += (char)0x99; break; // Ö
        case 0x9C: r += (char)0x9A; break; // Ü
        case 0x9F: r += (char)0xE1; break; // ß
        default:   r += '?';
      }
    } else if (c < 0x80) {
      r += (char)c;
    }
  }
  return r;
}

int16_t textBreite(const String& s, uint8_t groesse) {
  return fuerDisplay(s).length() * 6 * groesse;
}

void text(int16_t x, int16_t y, const String& s, uint8_t groesse, uint16_t farbe, uint16_t hinter) {
  tft.setTextSize(groesse);
  tft.setTextColor(farbe, hinter);
  tft.setCursor(x, y);
  tft.print(fuerDisplay(s));
}

void textMitte(int16_t x0, int16_t breite, int16_t y, const String& s, uint8_t groesse,
               uint16_t farbe, uint16_t hinter) {
  text(x0 + (breite - textBreite(s, groesse)) / 2, y, s, groesse, farbe, hinter);
}

// Haken (✓) aus Linien, weil der Standard-Font keinen hat
void haken(int16_t x, int16_t y, uint16_t farbe) {
  for (int8_t d = 0; d < 3; d++) {
    tft.drawLine(x, y + 6 + d, x + 4, y + 10 + d, farbe);
    tft.drawLine(x + 4, y + 10 + d, x + 12, y + d, farbe);
  }
}

// Bluetooth-Rune aus Linien. cx = senkrechter Strich (2 px breit), y0 = oben,
// 19 px hoch, von cx-5 bis cx+5 breit. Die Schrägen sind 1 px breit (wirkt sauberer).
void btSymbol(int16_t cx, int16_t y0, uint16_t farbe) {
  const int16_t h = 18, r = 5;
  const int16_t y1 = y0 + h;
  tft.drawLine(cx, y0, cx, y1, farbe);                   // senkrechter Strich ...
  tft.drawLine(cx + 1, y0, cx + 1, y1, farbe);           // ... doppelt
  tft.drawLine(cx, y0, cx + r, y0 + r, farbe);           // oben nach rechts
  tft.drawLine(cx + r, y0 + r, cx - r, y1 - r, farbe);   // Diagonale nach links unten
  tft.drawLine(cx, y1, cx + r, y1 - r, farbe);           // unten nach rechts
  tft.drawLine(cx + r, y1 - r, cx - r, y0 + r, farbe);   // Diagonale nach links oben
}

bool getroffen(const Taste& t, int16_t x, int16_t y) {
  return x >= t.x && x < t.x + t.w && y >= t.y && y < t.y + t.h;
}

void tasteZeichnen(const Taste& t, uint16_t fuellung, uint16_t schrift) {
  tft.fillRoundRect(t.x, t.y, t.w, t.h, 8, fuellung);
  tft.drawRoundRect(t.x, t.y, t.w, t.h, 8, WEISS);
  // Große Tasten: Schriftgröße 3 (besser treffbar in Wokwi / mit Finger)
  uint8_t g = (t.h >= 46) ? 3 : 2;
  int16_t th = 8 * g;
  textMitte(t.x, t.w, t.y + (t.h - th) / 2, t.beschriftung, g, schrift, fuellung);
}

// Große Touch-Tasten „Leer“ / „Voll“ (Hauptbildschirm + Kalibrierung).
// Treffflächen bewusst groß für FT6206 / Wokwi-Simulated-Touch (Display 240×320).
const Taste TASTE_LEER       = { 6,   230, 110, 52, "Leer" };   // groß für Wokwi-Touch
const Taste TASTE_VOLL       = { 124, 230, 110, 52, "Voll" };
const Taste TASTE_KAL_FERTIG = { 6,   288, 228, 28, "Fertig" };  // nur Kalibrier-Bildschirm
// Bluetooth-Symbol oben rechts (gezeichnet bei x 168..191 / y 2..25): Antippen = 2 min sichtbar (V4)
const Taste FLAECHE_BT_SYMBOL = { 162, 0, 32, 30, "" };

// ============================================================================
//  ENERGIE-AUTOMAT (V4): AKTIV -> GEDIMMT -> RUHE
// ============================================================================
void energieSetzen(Energie neu, const String& grund) {
  if (neu == energie) return;
  logZeile("ENERGIE", String(energieName(energie)) + " -> " + energieName(neu) + "  (" + grund + ")");
  Energie alt = energie;
  energie = neu;
  if (alt == E_RUHE) {
    anzeigeWecken();                 // CYD: Display aus dem Schlaf holen
    bildschirmNeu = true;            // alles neu zeichnen
  }
  if (neu == E_AKTIV)        hintergrundlichtSetzen(LCD_HELL);
  else if (neu == E_GEDIMMT) hintergrundlichtSetzen(LCD_GEDIMMT);
  else {
    hintergrundlichtSetzen(0);
    anzeigeSchlafen();
  }
}

// Jede Aktivität (Touch, Flasche, Trinken, Erinnerung, Nässe, Handy, Akku-Warnung, Serial)
void aktivitaet(const char* grund) {
  letzteAktivitaetMs = millis();
  if (energie != E_AKTIV) energieSetzen(E_AKTIV, grund);
}

bool inRuhezeit();   // steht weiter unten (Erinnerungs-Logik)

void energieVerwalten() {
  if (!stromsparen) return;          // wie V3: Display immer hell
  uint32_t jetzt = millis();
  // Display bleibt hell: Nässe (Sicherheit), Kalibrierung, Finger liegt noch auf
  if (zustand == NAESSE_SPERRE || zustand == KALIBRIERUNG || touchGehalten) {
    letzteAktivitaetMs = jetzt;
    if (energie != E_AKTIV) energieSetzen(E_AKTIV, zustand == NAESSE_SPERRE ? "Nässe-Sperre" :
                                                   (zustand == KALIBRIERUNG ? "Kalibrierung" : "Finger liegt auf"));
    return;
  }
  bool nacht = inRuhezeit();
  uint32_t ausNach  = nacht ? ANZEIGE_AUS_NACH_MS_NACHT : ANZEIGE_AUS_NACH_MS;
  uint32_t dimmNach = min(ANZEIGE_DIMMEN_NACH_MS, ausNach);
  uint32_t still = jetzt - letzteAktivitaetMs;
  if (still >= ausNach) {
    if (energie != E_RUHE) energieSetzen(E_RUHE, String(ausNach / 1000) + " s ohne Aktivität" + (nacht ? " (Nacht)" : ""));
  } else if (still >= dimmNach && dimmNach < ausNach) {
    if (energie == E_AKTIV) energieSetzen(E_GEDIMMT, String(dimmNach / 1000) + " s ohne Aktivität");
  }
}

// ============================================================================
//  UHR: WLAN + NTP, Ersatzuhr, Tageswechsel
// ============================================================================
void ntpCallback(struct timeval* tv) {
  (void)tv;
  ntpEmpfangen = true;   // wird im loop() ausgewertet (hier nur Merker setzen)
}

int64_t systemzeitUs() {
  struct timeval tv;
  gettimeofday(&tv, nullptr);
  return (int64_t)tv.tv_sec * 1000000LL + tv.tv_usec;
}

void wlanEinschalten() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WLAN_SSID, WLAN_PASS, WLAN_KANAL);
  ntpAngefragt = false;
  logZeile("UHR", String("Verbinde mit WLAN \"") + WLAN_SSID + "\" ...");
}

void wlanAusschalten(const String& grund) {
  esp_sntp_stop();                   // NTP-Dienst anhalten (startet beim nächsten Abgleich neu)
  WiFi.disconnect(true);             // trennen + Funk aus
  WiFi.mode(WIFI_OFF);
  wlanModus = WLAN_AUS;
  logZeile("UHR", "WLAN aus (" + grund + ")");
}

// Uhr-Abgleich (V4, M2): WLAN an, NTP holen, WLAN wieder aus (Timeout 20 s)
void wlanAbgleichStarten(const String& grund) {
  if (wlanModus == WLAN_DAUER) {
    Serial.println(F("WLAN ist dauerhaft an (Stromsparen aus) - NTP gleicht selbst ab."));
    return;
  }
  if (wlanModus == WLAN_ABGLEICH) {
    Serial.println(F("Abgleich läuft schon."));
    return;
  }
  wlanModus = WLAN_ABGLEICH;
  wlanStartMs = millis();
  letzterAbgleichMs = millis();
  logZeile("UHR", "Abgleich: WLAN an (" + grund + "), höchstens " + String(WLAN_ABGLEICH_TIMEOUT_MS / 1000) + " s");
  wlanEinschalten();
}

void uhrStarten() {
  setenv("TZ", ZEITZONE, 1);         // Zeitzone gleich setzen (auch für die Ersatzuhr)
  tzset();
  sntp_set_time_sync_notification_cb(ntpCallback);
  if (stromsparen) {
    wlanAbgleichStarten("Start");
  } else {
    wlanModus = WLAN_DAUER;          // wie V3: WLAN bleibt an
    wlanEinschalten();
  }
}

void wlanVerwalten() {
  uint32_t jetzt = millis();
  if (wlanModus == WLAN_AUS) {
    uint32_t abstand = uhrQuelle == UHR_NTP ? WLAN_ABGLEICH_ALLE_MS : WLAN_ABGLEICH_OHNE_NTP_MS;
    if (stromsparen && jetzt - letzterAbgleichMs >= abstand) {
      wlanAbgleichStarten(uhrQuelle == UHR_NTP ? "planmäßig alle 6 h" : "noch keine NTP-Zeit, alle 30 min");
    }
    return;
  }
  if (!ntpAngefragt && WiFi.status() == WL_CONNECTED) {
    ntpAngefragt = true;
    driftMessbar = uhrQuelle == UHR_NTP;      // nur dann ist die Abweichung aussagekräftig
    driftVorherUs = systemzeitUs();
    driftVorherMs = jetzt;
    ntpEmpfangen = false;
    configTzTime(ZEITZONE, NTP_SERVER);       // Zeitzone + NTP-Anfrage (startet SNTP neu)
    logZeile("UHR", "NTP-Anfrage an " + String(NTP_SERVER));
  }
  if (wlanModus == WLAN_ABGLEICH && jetzt - wlanStartMs >= WLAN_ABGLEICH_TIMEOUT_MS) {
    wlanAusschalten(String(WLAN_ABGLEICH_TIMEOUT_MS / 1000) + " s ohne NTP-Zeit, nächster Versuch in " +
                    (uhrQuelle == UHR_NTP ? "6 h" : "30 min"));
  }
}

// NTP ist angekommen: Abweichung der eigenen Uhr protokollieren (M2b), dann WLAN aus
void ntpVerarbeiten() {
  uint32_t jetzt = millis();
  if (driftMessbar && ntpAngefragt) {
    // erwartete Systemzeit ohne Korrektur = Zeit beim Anfragen + seitdem vergangene millis()
    int64_t erwartetUs = driftVorherUs + (int64_t)(jetzt - driftVorherMs) * 1000LL;
    letzteAbweichungMs = (long)((systemzeitUs() - erwartetUs) / 1000LL);
    float stunden = (jetzt - letzterNtpMs) / 3600000.0f;
    logZeile("UHR", "Abgleich: Abweichung " + String(letzteAbweichungMs / 1000.0f, 1) + " s in " +
             String(stunden, 1) + " h (" + (letzteAbweichungMs > 0 ? "Uhr ging nach" :
                                           (letzteAbweichungMs < 0 ? "Uhr ging vor" : "genau")) + ")");
  }
  driftMessbar = false;
  letzterNtpMs = jetzt;
  if (wlanModus == WLAN_ABGLEICH) wlanAusschalten("Uhr abgeglichen");
}

bool zeitHolen(struct tm& lt) {
  if (uhrQuelle == UHR_KEINE) return false;
  time_t t = time(nullptr);
  localtime_r(&t, &lt);
  return true;
}

long tagSchluessel(const struct tm& lt) {
  return (long)(lt.tm_year + 1900) * 1000L + lt.tm_yday;
}

// Datum, an dem der Sketch kompiliert wurde (z. B. "Oct  6 2026") -> Ersatzuhr
void ersatzuhrSetzen(int stunde, int minute) {
  struct tm lt = {};
  if (uhrQuelle != UHR_KEINE) {
    time_t t = time(nullptr);
    localtime_r(&t, &lt);          // heutiges Datum behalten
  } else {
    const char* monate = "JanFebMarAprMayJunJulAugSepOctNovDec";
    char mon[4] = { __DATE__[0], __DATE__[1], __DATE__[2], 0 };
    const char* p = strstr(monate, mon);
    lt.tm_mon  = p ? (int)(p - monate) / 3 : 0;
    lt.tm_mday = atoi(__DATE__ + 4);
    lt.tm_year = atoi(__DATE__ + 7) - 1900;
  }
  lt.tm_hour = stunde;
  lt.tm_min = minute;
  lt.tm_sec = 0;
  lt.tm_isdst = -1;
  struct timeval tv = { mktime(&lt), 0 };
  settimeofday(&tv, nullptr);
}

void tageszaehlerSpeichern() {
  speicher.putInt("heuteMl", getrunkenHeute);
  speicher.putLong("heuteTag", letzterTag);
}

void tageswechsel(const char* grund) {
  getrunkenHeute = 0;
  heuteGetrunken = false;
  letzterSchluckMs = millis();
  erinnerungenHeute = 0;
  letzteErinnerungMs = 0;
  trunkFensterMl = 0;
  trunkFensterStartMs = 0;
  tageszaehlerSpeichern();
  logZeile("TRINKEN", String("Tageszähler auf 0 (") + grund + ")");
}

// Wird bei JEDER neuen Zeitquelle aufgerufen: Tag merken, OHNE zurückzusetzen
void tagMerken() {
  struct tm lt;
  if (!zeitHolen(lt)) return;
  long tag = tagSchluessel(lt);
  if (letzterTag < 0 && speicher.getLong("heuteTag", -1) == tag) {
    getrunkenHeute = speicher.getInt("heuteMl", 0);   // nach Neustart am selben Tag weiterzählen
    heuteGetrunken = getrunkenHeute > 0;
    logZeile("TRINKEN", "heutiger Stand aus Speicher: " + String(getrunkenHeute) + " ml");
  }
  letzterTag = tag;
}

void uhrVerwalten() {
  bool w = WiFi.status() == WL_CONNECTED;
  if (w != wlanVerbunden) {
    wlanVerbunden = w;
    logZeile("UHR", w ? "WLAN verbunden" : "WLAN getrennt");
  }
  if (ntpEmpfangen) {
    ntpEmpfangen = false;
    if (uhrQuelle != UHR_NTP) {
      uhrQuelle = UHR_NTP;
      tagMerken();
      logZeile("UHR", "NTP-Zeit empfangen");
      bildschirmNeu = true;
    }
    ntpVerarbeiten();
  }
  if (uhrQuelle == UHR_KEINE && millis() >= NTP_WARTEZEIT_MS) {
    ersatzuhrSetzen(12, 0);
    uhrQuelle = UHR_ERSATZ;
    tagMerken();
    logZeile("UHR", "keine NTP-Zeit nach 10 s -> Ersatzuhr ab 12:00 (Anzeige gelb)");
  }
  // Mitternacht: neuer Tag -> Tageszähler automatisch zurücksetzen
  struct tm lt;
  if (zeitHolen(lt) && letzterTag >= 0) {
    long tag = tagSchluessel(lt);
    if (tag != letzterTag) {
      letzterTag = tag;
      tageswechsel("neuer Tag");
    }
  }
}

// ============================================================================
//  WAAGE
// ============================================================================
void waageInit() {
  waage.begin(PIN_HX711_DT, PIN_HX711_SCK);
  uint32_t start = millis();
  int n = 0;
  float summe = 0;
  while (millis() - start < 1000 && n < 5) {
    if (waage.is_ready()) {
      summe += (long)waage.read();
      n++;
    }
    delay(10);
  }
  if (n > 0) {
    rohMittel = summe / n;
    waageOk = true;
    letzteWaageMs = millis();
  }
  logZeile("WAAGE", n > 0 ? "HX711 gefunden, Rohwert " + String(rohMittel, 0)
                          : "HX711 antwortet nicht!");
}

void taraSetzen() {
  tara = rohMittel;
  referenzGueltig = false;
  speicher.putFloat("tara", tara);
  logZeile("WAAGE", "Tara gesetzt (Rohwert " + String(tara, 1) + ")");
}

// Liest den HX711 (nicht blockierend), glättet und prüft, ob das Gewicht ruhig ist.
void waageLesen() {
  uint32_t jetzt = millis();
  if (!waage.is_ready()) {
    if (waageOk && jetzt - letzteWaageMs > 2000) {
      waageOk = false;
      logZeile("FEHLER", "HX711 liefert keine Daten mehr");
    }
    return;
  }
  if (jetzt - waageLetzteMessungMs < RUHE_WECKTAKT_MS) return;   // 10 Messungen pro Sekunde
  waageLetzteMessungMs = jetzt;

  long roh = (long)waage.read();
  if (!waageOk) logZeile("WAAGE", "HX711 liefert wieder Daten");
  waageOk = true;
  letzteWaageMs = jetzt;

  rohMittel = rohMittel * 0.75f + roh * 0.25f;                       // glätten
  if (fabsf(roh - rohMittel) > 100.0f * faktor) rohMittel = roh;     // große Sprünge sofort
  gewicht = (rohMittel - tara) / faktor;

  if (fabsf(gewicht - ruheStartGewicht) > STABIL_TOLERANZ_G) {
    ruheStartGewicht = gewicht;
    ruheSeit = jetzt;
    gewichtRuhig = false;
  } else if (jetzt - ruheSeit >= STABIL_MS) {
    gewichtRuhig = true;
  }
}

void leergewichtSpeichern() {
  speicher.putFloat("leer", leergewicht);
  speicher.putBool("leerOk", leergewichtGelernt);
  speicher.putBool("flKalib", flascheKalibriert);
  speicher.putFloat("voll", vollgewicht);
  speicher.putInt("kapMl", flaschenKapazitaetMl);
  speicher.putBool("kapOk", kapazitaetKalibriert);
}

void flascheKalibSpeichern() {
  leergewichtSpeichern();
}

/*
 *  LEERGEWICHT DER FLASCHE AUTOMATISCH LERNEN
 *  ------------------------------------------
 *  Flascheninhalt [ml] = ruhiges Gewicht - Leergewicht der Flasche (1 g = 1 ml).
 *  Das Leergewicht kennt das Gerät am Anfang nicht -> Startwert 150 g.
 *
 *  Regel 1 (Nachfüllen): Wird die Flasche nach dem Abheben deutlich SCHWERER
 *     zurückgestellt, wurde nachgefüllt. Vorher war sie vermutlich (fast) leer.
 *     Das ruhige Gewicht VOR dem Nachfüllen ist ein Kandidat. Wir merken uns
 *     den KLEINSTEN Kandidaten als Leergewicht.
 *  Regel 2 (Untergrenze): Die Flasche kann nie leichter sein als leer.
 *     Ist ein ruhiges Gewicht mit Flasche kleiner als das Leergewicht,
 *     wird das Leergewicht auf diesen Wert gesenkt.
 *  Regel 3 (andere Flasche): War das Pad länger als 60 s leer und erscheint
 *     danach ein deutlich anderes Gewicht (>= 250 g Unterschied oder leichter
 *     als das Leergewicht), ist es vermutlich eine andere Flasche:
 *     Leergewicht zurück auf den Startwert, neu lernen.
 */
void leergewichtKandidat(float kandidat) {
  if (flascheKalibriert) return;   // kalibriertes Leergewicht hat Vorrang
  if (!leergewichtGelernt || kandidat < leergewicht) {
    logZeile("LEER", "Leergewicht gelernt: " + String(kandidat, 0) + " g (Gewicht vor dem Nachfüllen" +
             (leergewichtGelernt ? ", kleiner als bisher " + String(leergewicht, 0) + " g)" : ")"));
    leergewicht = kandidat;
    leergewichtGelernt = true;
    leergewichtSpeichern();
  }
}

void leergewichtUntergrenze(float w) {
  if (flascheKalibriert) return;   // kalibriertes Leergewicht hat Vorrang
  if (w < leergewicht - 0.5f) {
    logZeile("LEER", "Flasche leichter als Leergewicht -> Leergewicht = " + String(w, 0) + " g");
    leergewicht = w;
    leergewichtGelernt = true;
    leergewichtSpeichern();
  }
}

int flascheninhaltMl() {
  if (!flascheSteht) return 0;
  float basis = referenzGueltig ? referenzGewicht : gewicht;   // ruhiger Wert
  return max(0, (int)lroundf(basis - leergewicht));
}

// Wertet das Gewicht aus: Abheben, Abstellen, Trinken, Nachfüllen, Leergewicht.
void btSyncFenster(const String& grund);   // steht im Bluetooth-Teil

void trinkenAuswerten() {
  if (flascheSteht && gewicht < FLASCHE_WEG_G) {
    flascheSteht = false;
    padLeerSeit = millis();
    logZeile("WAAGE", "Flasche abgehoben – Änderungen werden ignoriert");
    aktivitaet("Flasche abgehoben");
    return;
  }
  if (!gewichtRuhig) return;

  bool geradeAbgestellt = false;
  if (!flascheSteht && gewicht >= FLASCHE_DA_G) {
    flascheSteht = true;
    geradeAbgestellt = true;
    logZeile("WAAGE", "Flasche steht (" + String(gewicht, 0) + " g)");
    aktivitaet("Flasche abgestellt");
  }
  if (!flascheSteht) return;

  // Regel 3: andere Flasche?
  if (geradeAbgestellt && referenzGueltig && millis() - padLeerSeit > PAD_LEER_RESET_MS &&
      (fabsf(gewicht - referenzGewicht) >= ANDERE_FLASCHE_G || gewicht < leergewicht - 30.0f)) {
    logZeile("LEER", "Pad war " + String((millis() - padLeerSeit) / 1000) + " s leer und Gewicht deutlich anders (" +
             String(referenzGewicht, 0) + " g -> " + String(gewicht, 0) +
             " g): andere Flasche, Leergewicht zurück auf " + String(LEERGEWICHT_START_G, 0) + " g");
    leergewicht = LEERGEWICHT_START_G;
    leergewichtGelernt = false;
    flascheKalibriert = false;
    kapazitaetKalibriert = false;
    vollgewicht = 0;
    flaschenKapazitaetMl = 0;
    leergewichtSpeichern();
    referenzGewicht = gewicht;          // neue Flasche: nichts zählen
    leergewichtUntergrenze(gewicht);
    return;
  }

  if (!referenzGueltig) {
    referenzGewicht = gewicht;
    referenzGueltig = true;
    logZeile("WAAGE", "Referenz gesetzt: " + String(referenzGewicht, 0) + " g");
    leergewichtUntergrenze(gewicht);
    return;
  }

  float differenz = referenzGewicht - gewicht;  // positiv = leichter = getrunken
  if (differenz >= MIN_SCHLUCK_G) {
    int ml = (int)lroundf(differenz);
    getrunkenHeute += ml;
    heuteGetrunken = true;
    letzterSchluckMs = millis();
    tageszaehlerSpeichern();
    // Pause nur nach ≥100 ml im Trinkfenster; Schlucke < 40 ml zählen, setzen Pause nicht
    if (ml >= (int)SCHLUCK_OHNE_PAUSE_ML) {
      uint32_t jetzt = millis();
      if (trunkFensterStartMs == 0 || jetzt - trunkFensterStartMs > TRUNK_FENSTER_MS) {
        trunkFensterStartMs = jetzt;
        trunkFensterMl = 0;
      }
      trunkFensterMl += ml;
      if (trunkFensterMl >= TRUNK_RESET_MIN_ML) {
        erinnerungPauseBisMs = jetzt + ERINNERUNG_PAUSE_MS;
        trunkFensterMl = 0;
        trunkFensterStartMs = jetzt;
        logZeile("ERINNERUNG", "Pause " + String(ERINNERUNG_PAUSE_MS / 1000) +
                 " s nach ≥" + String((int)TRUNK_RESET_MIN_ML) + " ml im Fenster");
      }
    } else {
      logZeile("ERINNERUNG", "Schluck " + String(ml) + " ml < " +
               String((int)SCHLUCK_OHNE_PAUSE_ML) + " ml – zählt, Pause unverändert");
    }
    logZeile("TRINKEN", "+" + String(ml) + " ml getrunken (" + String(referenzGewicht, 0) + " g -> " +
                        String(gewicht, 0) + " g), heute " + String(getrunkenHeute) + " ml");
    referenzGewicht = gewicht;
    leergewichtUntergrenze(gewicht);
    aktivitaet("Trinken erkannt");
    btSyncFenster("Trinken erkannt");       // V4: App kann den neuen Stand abholen
  } else if (-differenz >= MIN_NACHFUELL_G) {
    logZeile("TRINKEN", "Nachgefüllt (+" + String(-differenz, 0) + " g) – zählt nicht als Trinken");
    leergewichtKandidat(referenzGewicht);   // Regel 1
    referenzGewicht = gewicht;
    aktivitaet("Nachfüllen erkannt");
    btSyncFenster("Nachfüllen erkannt");
  }
}

// ============================================================================
//  SENSOREN: NÄSSE UND AKKU
// ============================================================================
void naesseLesen() {
  static bool roh = false;
  static uint32_t wechselSeit = 0;
  bool jetztNass = digitalRead(PIN_NAESSE) == LOW;  // LM393-DO: LOW = nass
  if (jetztNass != roh) {
    roh = jetztNass;
    wechselSeit = millis();
  }
  if (roh != nass && millis() - wechselSeit >= 100) {   // entprellen
    nass = roh;
    if (!nass) trockenSeit = millis();
    logZeile("NAESSE", nass ? "Sensor meldet WASSER" : "Sensor wieder trocken – Freigabe in 5 s");
  }
}

// Akkuspannung in Volt. SIMULATION: Poti 0..4095 direkt als 3,0..4,2 V.
// ECHT (CYD): Teiler 2 x 10 kΩ an GPIO35, 8 Messungen gemittelt (ADC-Kalibrierung aus dem eFuse).
float akkuSpannungMessen() {
#if HYDRO_CYD
  uint32_t summe = 0;
  for (uint8_t i = 0; i < 8; i++) summe += analogReadMilliVolts(PIN_AKKU_ADC);
  return summe / 8.0f / 1000.0f * AKKU_TEILER;
#else
  int adc = analogRead(PIN_AKKU_ADC);   // 0..4095
  return AKKU_LEER_V + (AKKU_VOLL_V - AKKU_LEER_V) * adc / 4095.0f;
#endif
}

// Prozent aus der LiPo-Tabelle (lineare Interpolation zwischen den Stützstellen, V4 / M9)
int akkuProzentAusSpannung(float v) {
  if (v <= AKKU_TABELLE_V[0]) return 0;
  for (uint8_t i = 1; i < AKKU_TABELLE_N; i++) {
    if (v < AKKU_TABELLE_V[i]) {
      float anteil = (v - AKKU_TABELLE_V[i - 1]) / (AKKU_TABELLE_V[i] - AKKU_TABELLE_V[i - 1]);
      return (int)lroundf(AKKU_TABELLE_P[i - 1] + anteil * (AKKU_TABELLE_P[i] - AKKU_TABELLE_P[i - 1]));
    }
  }
  return 100;
}

void tiefschlafStarten();     // steht unten bei SETUP
void ledStromSetzen(bool an, const String& grund);
void wlanAusschalten(const String& grund);
void bleStoppen();

// Akku leer: Meldung, alles aus, Tiefschlaf mit Timer (V4, Stromsparplan Kap. 5.6)
void akkuLeerAbschalten() {
  logZeile("AKKU", "LEER: " + String(akkuVolt, 2) + " V seit " + String(AKKU_ABSCHALT_MS / 1000) +
           " s unter " + String(AKKU_ABSCHALT_V, 2) + " V -> Meldung, dann Tiefschlaf (Prüfung alle " +
           String(AKKU_LEER_SCHLAF_MIN) + " min)");
  telegramSenden("HydroDesk: Akku leer – Gerät schaltet ab. Bitte laden.");
  ledStromSetzen(false, "Akku leer");
  if (wlanModus != WLAN_AUS) wlanAusschalten("Akku leer");
  bleStoppen();
  energieSetzen(E_AKTIV, "Akku leer - Meldung");
  hintergrundlichtSetzen(LCD_HELL);
  tft.fillScreen(0x0000);
  textMitte(0, BREITE, 110, "Akku leer", 3, ROT, SCHWARZ);
  textMitte(0, BREITE, 150, "bitte laden", 2, WEISS, SCHWARZ);
  textMitte(0, BREITE, 190, "Gerät schaltet ab.", 1, GRAU, SCHWARZ);
  delay(AKKU_LEER_MELDUNG_MS);
  hintergrundlichtSetzen(0);
  anzeigeSchlafen();
  akkuLeerSchlaf = true;
  tiefschlafStarten();
}

void akkuSchutzPruefen() {
  if (akkuVolt >= AKKU_ABSCHALT_V) {
    if (akkuLeerSeitMs != 0) logZeile("AKKU", "wieder über " + String(AKKU_ABSCHALT_V, 2) + " V - keine Abschaltung");
    akkuLeerSeitMs = 0;
    return;
  }
  if (akkuLeerSeitMs == 0) {
    akkuLeerSeitMs = millis() | 1;   // 0 heißt "nicht"
    logZeile("AKKU", "unter " + String(AKKU_ABSCHALT_V, 2) + " V (" + String(akkuVolt, 2) +
             " V): Abschaltung in " + String(AKKU_ABSCHALT_MS / 1000) + " s, wenn es so bleibt");
    return;
  }
  if (millis() - akkuLeerSeitMs >= AKKU_ABSCHALT_MS) akkuLeerAbschalten();
}

void akkuLesen() {
  static uint32_t letzte = 0;
  if (millis() - letzte < 500) return;
  letzte = millis();
  float v = akkuSpannungMessen();
#if HYDRO_CYD
  static bool erste = true;            // echt: leicht glätten (WLAN-/LED-Lastspitzen)
  akkuVolt = erste ? v : akkuVolt * 0.8f + v * 0.2f;
  erste = false;
#else
  akkuVolt = v;                        // Wokwi: Poti-Wert direkt (Tests reagieren sofort)
#endif
  akkuProzent = akkuProzentAusSpannung(akkuVolt);
  akkuSchutzPruefen();

  // Stufe mit Hysterese bestimmen: runter sofort, rauf erst bei Schwelle + 2 %
  uint8_t neu = akkuStufe;
  if (akkuProzent < AKKU_KRITISCH_PROZENT) neu = 2;
  else if (akkuProzent < AKKU_WARN_PROZENT) neu = (akkuStufe == 2 && akkuProzent < AKKU_KRITISCH_PROZENT + AKKU_HYSTERESE_PROZENT) ? 2 : 1;
  else if (akkuStufe >= 1 && akkuProzent < AKKU_WARN_PROZENT + AKKU_HYSTERESE_PROZENT) neu = 1;
  else neu = 0;

  if (neu > akkuStufe) {
    // Schwelle nach unten überschritten -> EINMAL warnen
    akkuStufe = neu;
    akkuWarnen();
    aktivitaet("Akku-Warnung");      // nur die erste Warnung weckt (Wiederholungen nur per LED)
    telegramSenden("HydroDesk: Akku unter " + String(neu == 2 ? AKKU_KRITISCH_PROZENT : AKKU_WARN_PROZENT) +
                   " % (" + String(akkuProzent) + " %)");
  } else if (neu < akkuStufe) {
    akkuStufe = neu;   // wieder über Schwelle + Hysterese (geladen): keine Warnung
    logZeile("AKKU", neu == 0 ? "wieder ok: " + String(akkuProzent) + " %"
                              : "wieder über " + String(AKKU_KRITISCH_PROZENT + AKKU_HYSTERESE_PROZENT) + " %: \"Bitte laden\" aus");
  } else if (akkuStufe > 0 && AKKU_WIEDERHOLUNG_MS > 0 && millis() - akkuWarnMs >= AKKU_WIEDERHOLUNG_MS) {
    akkuWarnen();      // noch immer unter der Schwelle: Muster alle 10 min wiederholen
  }
}

// Blinkmuster starten (2x unter 20 %, 4x unter 10 %) + Hinweis auf dem Display
void akkuWarnen() {
  akkuWarnMs = millis();
  blinkStartMs = millis();
  blinkAnzahl = akkuStufe == 2 ? AKKU_BLINK_KRITISCH : AKKU_BLINK_WARN;
  // <10 %: langsamer/normaler Takt; <20 %: weiterhin kurzes Blitzen
  blinkAnMs  = akkuStufe == 2 ? AKKU_BLINK_KRITISCH_AN_MS  : AKKU_BLINK_AN_MS;
  blinkAusMs = akkuStufe == 2 ? AKKU_BLINK_KRITISCH_AUS_MS : AKKU_BLINK_AUS_MS;
  if (akkuStufe == 1) akkuHinweisBisMs = millis() + AKKU_HINWEIS_MS;
  logZeile("AKKU", String(akkuStufe == 2 ? "KRITISCH" : "NIEDRIG") + ": " + String(akkuVolt, 2) + " V (" +
                   String(akkuProzent) + " %) -> LEDs " + String(blinkAnzahl) + "x rot (" +
                   String(blinkAnMs) + "/" + String(blinkAusMs) + " ms)");
}

// Waage ohne Daten oder Tara falsch (negativ)
bool waageFehler() {
  return !waageOk || gewicht < NEGATIV_FEHLER_G;
}

// ============================================================================
//  ERINNERUNGS-LOGIK (Plan, Pause, Ruhezeit, Abstand, Max/Tag)
// ============================================================================
bool inRuhezeit() {
  struct tm lt;
  if (!zeitHolen(lt)) return false;   // ohne Uhr: Erinnerungen erlaubt (Demo)
  return lt.tm_hour >= RUHE_START_STUNDE || lt.tm_hour < RUHE_ENDE_STUNDE;
}

// Soll-Menge nach Tageszeit: 07:00=0 %, 12:00=40 %, 16:00=70 %, 20:00=100 %
int sollGetrunkenMl() {
  struct tm lt;
  if (!zeitHolen(lt)) return 0;
  float stunde = lt.tm_hour + lt.tm_min / 60.0f;
  float anteil;
  if (stunde <= (float)RUHE_ENDE_STUNDE) anteil = 0.0f;
  else if (stunde <= 12.0f) anteil = 0.40f * (stunde - (float)RUHE_ENDE_STUNDE) / (12.0f - (float)RUHE_ENDE_STUNDE);
  else if (stunde <= 16.0f) anteil = 0.40f + 0.30f * (stunde - 12.0f) / 4.0f;
  else if (stunde <= 20.0f) anteil = 0.70f + 0.30f * (stunde - 16.0f) / 4.0f;
  else anteil = 1.0f;
  return (int)lroundf(anteil * (float)tagesziel);
}

bool hinterPlan() {
  return getrunkenHeute < sollGetrunkenMl();
}

bool erinnerungPauseAktiv() {
  return (int32_t)(erinnerungPauseBisMs - millis()) > 0;
}

bool erinnerungMoeglich() {
  if (getrunkenHeute >= tagesziel) return false;
  if (erinnerungenHeute >= ERINNERUNG_MAX_PRO_TAG) return false;
  if (inRuhezeit()) return false;
  if (erinnerungPauseAktiv()) return false;
  if (letzteErinnerungMs != 0 && millis() - letzteErinnerungMs < ERINNERUNG_MIN_ABSTAND_MS) return false;
  if (!hinterPlan()) return false;
  return true;
}

// Sekunden bis zur nächsten möglichen Erinnerung (Anzeige); 0 = jetzt / aktiv
uint32_t erinnerungRestSekunden() {
  if (getrunkenHeute >= tagesziel) return 0;
  if (erinnerungenHeute >= ERINNERUNG_MAX_PRO_TAG) return 0;
  uint32_t jetzt = millis();
  uint32_t rest = 0;
  if (erinnerungPauseAktiv()) rest = max(rest, (erinnerungPauseBisMs - jetzt + 999) / 1000);
  if (letzteErinnerungMs != 0 && jetzt - letzteErinnerungMs < ERINNERUNG_MIN_ABSTAND_MS) {
    rest = max(rest, (ERINNERUNG_MIN_ABSTAND_MS - (jetzt - letzteErinnerungMs) + 999) / 1000);
  }
  return rest;
}

// ============================================================================
//  ZUSTANDSWECHSEL
// ============================================================================
void zustandWechseln(Zustand neu, const String& grund) {
  if (neu == zustand) return;
  logZeile("ZUSTAND", String(zustandName(zustand)) + " -> " + zustandName(neu) + "  (" + grund + ")");
  Zustand alt = zustand;
  zustand = neu;
  bildschirmNeu = true;

  if (neu == ERINNERUNG || neu == ZIEL_ERREICHT || neu == NAESSE_SPERRE || neu == KALIBRIERUNG) {
    aktivitaet(zustandName(neu));    // V4: weckt das Display
  }
  switch (neu) {   // beim BETRETEN
    case NAESSE_SPERRE:
      ledStromSetzen(false, "WASSER ERKANNT");   // FET aus -> Streifen ohne Strom
      logZeile("LAST", "AUS (WASSER ERKANNT · STROM AUS)");
      telegramSenden("HydroDesk: WASSER ERKANNT – Strom wurde abgeschaltet!");
      break;
    case ERINNERUNG:
      erinnerungenHeute++;
      letzteErinnerungMs = millis();
      telegramSenden("HydroDesk: Zeit zu trinken! Heute " + String(getrunkenHeute) + " von " +
                     String(tagesziel) + " ml (Erinnerung " + String(erinnerungenHeute) + "/" +
                     String(ERINNERUNG_MAX_PRO_TAG) + ")");
      logZeile("ERINNERUNG", "ausgelöst (" + String(erinnerungenHeute) + "/" +
               String(ERINNERUNG_MAX_PRO_TAG) + "), Soll " + String(sollGetrunkenMl()) +
               " ml, Ist " + String(getrunkenHeute) + " ml");
      break;
    case ZIEL_ERREICHT:
      gruenBisMs = millis() + LED_GRUEN_MS;   // 10 s grün
      telegramSenden("HydroDesk: Tagesziel erreicht (" + String(getrunkenHeute) + " ml)");
      break;
    case KALIBRIERUNG:
      kalSchritt = 0;
      break;
    default:
      break;
  }
  if (alt == NAESSE_SPERRE) {    // beim VERLASSEN
    if (!stromsparen) ledStromSetzen(true, "5 s trocken");   // wie V3: Last sofort wieder an
    logZeile("LAST", stromsparen ? "wieder freigegeben (5 s trocken) - Strom nur, wenn die LEDs leuchten"
                                 : "wieder AN (5 s trocken)");
  }
  if (alt == NAESSE_SPERRE || alt == KALIBRIERUNG) {
    referenzGueltig = false;     // Gewicht kann sich verändert haben -> neu referenzieren
    flascheSteht = false;
    padLeerSeit = millis();
  }
}

void zustandAktualisieren() {
  // 1. Höchste Priorität: Wasser
  if (nass && zustand != NAESSE_SPERRE) {
    zustandWechseln(NAESSE_SPERRE, "Nässe-Sensor LOW");
    return;
  }
  if (zustand == NAESSE_SPERRE) {
    if (!nass && millis() - trockenSeit >= TROCKEN_FREIGABE_MS) {
      zustandWechseln(IDLE, "5 s trocken -> automatisch freigegeben");
    }
    return;
  }
  if (zustand == KALIBRIERUNG) return;   // verlässt man nur per "Fertig"

  // 2. Fehler-Beginn -> LEDs 5 s rot
  bool f = waageFehler();
  if (f && !fehlerVorher) rotBisMs = millis() + LED_ROT_MS;
  fehlerVorher = f;

  // 3. Messen + Auswerten, dann Zustand neu bestimmen
  trinkenAuswerten();

  if (getrunkenHeute >= tagesziel) {
    zustandWechseln(ZIEL_ERREICHT, String(getrunkenHeute) + " >= " + String(tagesziel) + " ml");
  } else if (zustand == ERINNERUNG) {
    // Bleibt aktiv, bis nach der Erinnerung wieder getrunken wurde
    if (letzterSchluckMs > letzteErinnerungMs) {
      if (flascheSteht) zustandWechseln(MESSEN, "getrunken");
      else zustandWechseln(IDLE, "getrunken, keine Flasche");
    }
  } else if (erinnerungMoeglich()) {
    zustandWechseln(ERINNERUNG, "hinter Plan (Soll " + String(sollGetrunkenMl()) +
                    " / Ist " + String(getrunkenHeute) + " ml)");
  } else if (flascheSteht) {
    zustandWechseln(MESSEN, zustand == ZIEL_ERREICHT ? "Ziel höher / neuer Tag" : "Flasche steht");
  } else {
    zustandWechseln(IDLE, "keine Flasche auf dem Pad");
  }
}

// ============================================================================
//  FLASCHEN-KALIBRIERUNG (leer / voll) – Touch-Tasten + Serial
// ============================================================================
void kalibMeldungSetzen(const String& msg, bool alsFehler) {
  kalibMeldung = msg;
  kalibMeldungBisMs = millis() + (alsFehler ? 4500UL : 3000UL);
  logZeile(alsFehler ? "KALIB" : "KALIB", msg);
}

bool gewichtKalibStabil() {
  // ~1 s ruhig (eigene Schwelle; Trink-Logik bleibt bei STABIL_MS)
  return (millis() - ruheSeit >= KALIB_STABIL_MS) &&
         (fabsf(gewicht - ruheStartGewicht) <= STABIL_TOLERANZ_G);
}

bool flascheGewichtNehmen(float& g, const char* was) {
  if (gewicht < FLASCHE_DA_G) {
    kalibMeldungSetzen(String("Keine Flasche – bitte ") + was + " aufstellen", true);
    return false;
  }
  if (!gewichtKalibStabil()) {
    kalibMeldungSetzen("Gewicht unruhig – ca. 1 s warten", true);
    return false;
  }
  g = gewicht;
  return true;
}

void kalibLeerBestaetigen() {
  float g = 0;
  if (!flascheGewichtNehmen(g, "leere Flasche")) return;
  leergewicht = g;
  leergewichtGelernt = true;
  flascheKalibriert = true;
  // Kapazität erst nach "voll" gültig; alten Wert verwerfen
  kapazitaetKalibriert = false;
  vollgewicht = 0;
  flaschenKapazitaetMl = 0;
  flascheKalibSpeichern();
  kalSchritt = 1;
  bildschirmNeu = true;
  kalibMeldungSetzen("Leer gespeichert: " + String((int)lroundf(leergewicht)) + " g", false);
}

void kalibVollBestaetigen() {
  if (!flascheKalibriert) {
    kalibMeldungSetzen("Zuerst Leer kalibrieren", true);
    return;
  }
  float g = 0;
  if (!flascheGewichtNehmen(g, "volle Flasche")) return;
  if (g <= leergewicht) {
    kalibMeldungSetzen("Voll muss größer als Leer sein", true);
    return;
  }
  vollgewicht = g;
  flaschenKapazitaetMl = max(0, (int)lroundf(vollgewicht - leergewicht));
  kapazitaetKalibriert = true;
  flascheKalibriert = true;
  flascheKalibSpeichern();
  kalSchritt = 2;
  bildschirmNeu = true;
  kalibMeldungSetzen("Kapazität: " + String(flaschenKapazitaetMl) + " ml", false);
}

// ============================================================================
//  TOUCH: Tasten Leer/Voll (Haupt + Kalib); optional 3 s -> Kalibrier-Bildschirm
// ============================================================================
void btSuchenStarten(const String& grund);   // steht im Bluetooth-Teil

void touchAuswerten() {
  int16_t x = 0, y = 0;
  bool gedrueckt = readTouch(x, y);
  bool neu = gedrueckt && !touchGehalten;
  if (neu) {
    touchStartMs = millis();
    langdruckErledigt = false;
    weckBeruehrung = stromsparen && energie != E_AKTIV;   // V4 (M8): gedimmt/aus -> nur wecken
    logZeile("TOUCH", "x=" + String(x) + " y=" + String(y) + (weckBeruehrung ? " (nur Wecken)" : ""));
    aktivitaet(weckBeruehrung ? "Touch weckt" : "Touch");
  }
  touchGehalten = gedrueckt;

  // Weck-Berührung: zählt weder als Taste noch als Langdruck, bis der Finger wieder weg ist
  if (weckBeruehrung) {
    if (!gedrueckt) weckBeruehrung = false;
    return;
  }

  if (zustand == NAESSE_SPERRE) return;           // Bedienung gesperrt

  // V4: Bluetooth-Symbol antippen -> 2 min sichtbar (auch ohne Laptop wieder verbinden)
  if (neu && zustand != KALIBRIERUNG && getroffen(FLAECHE_BT_SYMBOL, x, y)) {
    langdruckErledigt = true;
    btSuchenStarten("Bluetooth-Symbol angetippt");
    return;
  }

  // Sichtbare Tasten Leer / Voll – auf Haupt- und Kalibrier-Bildschirm
  if (zustand == KALIBRIERUNG || zustand == IDLE || zustand == MESSEN ||
      zustand == ERINNERUNG || zustand == ZIEL_ERREICHT) {
    if (neu) {
      if (getroffen(TASTE_LEER, x, y)) {
        langdruckErledigt = true;                 // kein Langdruck nach Tastendruck
        kalibLeerBestaetigen();
        return;
      }
      if (getroffen(TASTE_VOLL, x, y)) {
        langdruckErledigt = true;
        kalibVollBestaetigen();
        return;
      }
      if (zustand == KALIBRIERUNG && getroffen(TASTE_KAL_FERTIG, x, y)) {
        langdruckErledigt = true;
        zustandWechseln(IDLE, kalSchritt >= 2 ? "Kalibrierung beendet" : "Kalibrierung abgebrochen");
        return;
      }
    }
  }

  if (zustand == KALIBRIERUNG) {
    // Langdruck im Kalibrier-Bildschirm: aktuellen Schritt bestätigen
    if (gedrueckt && !langdruckErledigt && millis() - touchStartMs >= LANGDRUCK_MS) {
      langdruckErledigt = true;
      if (kalSchritt == 0) kalibLeerBestaetigen();
      else if (kalSchritt == 1) kalibVollBestaetigen();
      else zustandWechseln(IDLE, "Kalibrierung beendet");
    }
    return;
  }

  // Normalbetrieb: 3 s irgendwo (außer auf den Tasten) -> Kalibrier-Bildschirm
  if (gedrueckt && !langdruckErledigt && millis() - touchStartMs >= LANGDRUCK_MS) {
    langdruckErledigt = true;
    zustandWechseln(KALIBRIERUNG, "3 s Langdruck");
  }
}

// ============================================================================
//  BLUETOOTH
//  HYDRO_BLE 1: echtes BLE (NimBLE). Die Callbacks laufen in einer eigenen
//               BLE-Task -> dort nur Merker setzen, ausgewertet wird im loop().
//  HYDRO_BLE 0: Wokwi kann kein Bluetooth -> Zustand per Serial-Befehl "bt ...".
// ============================================================================
#if HYDRO_BLE
NimBLEServer*         bleServer   = nullptr;
NimBLECharacteristic* bleWerte    = nullptr;
volatile bool         bleVerbunden = false;   // von den Callbacks gesetzt
volatile uint16_t     bleTrennGrund = 0;
bool                  bleLaeuft    = false;   // V4: BLE-Stack eingeschaltet?

class HydroServerCallbacks : public NimBLEServerCallbacks {
  void onConnect(NimBLEServer* server, NimBLEConnInfo& info) override {
    (void)server; (void)info;
    bleVerbunden = true;
  }
  void onDisconnect(NimBLEServer* server, NimBLEConnInfo& info, int grund) override {
    (void)info;
    bleTrennGrund = (uint16_t)grund;
    bleVerbunden = server->getConnectedCount() > 0;
  }
};
HydroServerCallbacks bleCallbacks;

String bleWerteText() {
  return String(getrunkenHeute) + "/" + String(tagesziel) + " ml";
}

// BLE-Stack einschalten und Dienst anlegen. V4: bei jedem Fenster neu (nach deinit(true)).
void bleStarten() {
  if (bleLaeuft) return;
  bleVerbunden = false;
  NimBLEDevice::init(BT_NAME);
  bleServer = NimBLEDevice::createServer();
  bleServer->setCallbacks(&bleCallbacks, false);
  bleServer->advertiseOnDisconnect(false);      // Suchen steuert der Sketch selbst (Timeout!)
  NimBLEService* dienst = bleServer->createService(BT_SERVICE_UUID);
  bleWerte = dienst->createCharacteristic(BT_WERTE_UUID, NIMBLE_PROPERTY::READ | NIMBLE_PROPERTY::NOTIFY);
  bleWerte->setValue(bleWerteText().c_str());
  bleServer->start();

  // Werbepaket: Flags + Dienst-UUID; Name in der Scan-Antwort (zusammen > 31 Byte)
  NimBLEAdvertising* werbung = NimBLEDevice::getAdvertising();
  NimBLEAdvertisementData daten;
  daten.setFlags(BLE_HS_ADV_F_DISC_GEN | BLE_HS_ADV_F_BREDR_UNSUP);
  daten.addServiceUUID(BT_SERVICE_UUID);
  NimBLEAdvertisementData antwort;
  antwort.setName(BT_NAME);
  werbung->setAdvertisementData(daten);
  werbung->setScanResponseData(antwort);
  werbung->enableScanResponse(true);
  bleLaeuft = true;
  logZeile("BT", String("BLE-Stack an (NimBLE), Name \"") + BT_NAME + "\"");
}
#endif

// BLE-Stack ganz aus (V4, M6): Voraussetzung für den Light-Sleep. deinit(true) löscht Server,
// Dienst und Werbung -> bleStarten() legt beim nächsten Fenster alles neu an.
void bleStoppen() {
#if HYDRO_BLE
  if (!bleLaeuft) return;
  NimBLEDevice::stopAdvertising();
  NimBLEDevice::deinit(true);
  bleServer = nullptr;
  bleWerte = nullptr;
  bleVerbunden = false;
  bleLaeuft = false;
  logZeile("BT", "BLE-Stack aus (deinit)");
#endif
}

void btSetzen(BtZustand neu, const String& grund) {
  if (neu == btZustand) return;
  logZeile("BT", String(btName(btZustand)) + " -> " + btName(neu) + "  (" + grund + ")");
  BtZustand alt = btZustand;
  btZustand = neu;
  if (neu == BT_VERBUNDEN) {
    lilaAusstehend = true;          // 2x lila (startet nach einem laufenden Akku-Blinken)
    lilaLaeuft = false;
    aktivitaet("Handy verbunden");
  } else if (alt == BT_VERBUNDEN) {
    lilaAusstehend = false;         // getrennt, bevor lila fertig war -> abbrechen
    lilaLaeuft = false;
    aktivitaet("Handy getrennt");
  }
}

// Sichtbar werden und auf das Handy warten.
//   laut (still = false): Start, "bt suchen", Symbol antippen -> weiß blinken, BT_SUCH_TIMEOUT_MS
//   still (V4):           nach dem Trinken -> ohne Blinken, BT_SYNC_FENSTER_MS
void btFensterOeffnen(const String& grund, bool still, uint32_t dauerMs) {
  uint32_t jetzt = millis();
  bool lief = btZustand == BT_SUCHEN;
  if (still && lief) {              // läuft schon ein Fenster: höchstens verlängern, Art bleibt
    if ((int32_t)(jetzt + dauerMs - btFensterEndeMs) > 0) btFensterEndeMs = jetzt + dauerMs;
    logZeile("BT", "Fenster läuft schon -> noch " + String((btFensterEndeMs - jetzt) / 1000) + " s (" + grund + ")");
    return;
  }
  btFensterEndeMs = jetzt + dauerMs; // auch bei erneutem "bt suchen": Zeit neu starten
  btSuchStartMs = jetzt;            // Blinktakt ab Beginn
  btStill = still;
#if HYDRO_BLE
  bleStarten();
  if (bleServer && bleServer->getConnectedCount() > 0) {
    btSetzen(BT_VERBUNDEN, "Handy ist schon verbunden");
    return;
  }
  NimBLEDevice::startAdvertising();
#endif
  if (lief) logZeile("BT", "Suche neu gestartet (" + grund + ")");
  btSetzen(BT_SUCHEN, grund + ", max. " + String(dauerMs / 1000) + " s" + (still ? ", still (ohne Blinken)" : ""));
}

void btSuchenStarten(const String& grund) {
  btFensterOeffnen(grund, false, BT_SUCH_TIMEOUT_MS);
}

// V4 (Option A): nach jedem Trinken/Nachfüllen 60 s still sichtbar, damit die App den Stand abholt
void btSyncFenster(const String& grund) {
  if (!stromsparen) return;                       // wie V3: keine Fenster nach dem Trinken
  if (btZustand == BT_AUS || btZustand == BT_VERBUNDEN) return;
  btFensterOeffnen(grund, true, BT_SYNC_FENSTER_MS);
}

// Verbindung weg: wieder ein Fenster derselben Art (laut 2 min / still 60 s)
void btNachTrennung(const String& grund) {
  btFensterOeffnen(grund, btStill, btStill ? BT_SYNC_FENSTER_MS : BT_SUCH_TIMEOUT_MS);
}

void btAusschalten() {
#if HYDRO_BLE
  NimBLEDevice::stopAdvertising();
  if (bleServer) {
    for (uint16_t h : bleServer->getPeerDevices()) bleServer->disconnect(h);
  }
  if (stromsparen) bleStoppen();
#endif
  btSetzen(BT_AUS, "Befehl bt aus");
}

void btVerwalten() {
#if HYDRO_BLE
  bool v = bleVerbunden;
  if (v && btZustand != BT_VERBUNDEN && btZustand != BT_AUS) {
    btSetzen(BT_VERBUNDEN, "Handy hat sich verbunden");
  } else if (!v && btZustand == BT_VERBUNDEN) {
    btNachTrennung("Handy getrennt, Grund " + String(bleTrennGrund));
  }
  // Werte aktuell halten (lesen) und bei Änderung an das Handy schicken (notify)
  static String letzterWert;
  static uint32_t letzteNotify = 0;
  String wert = bleWerteText();
  if (bleLaeuft && bleWerte && wert != letzterWert && millis() - letzteNotify >= BT_NOTIFY_MS) {
    letzterWert = wert;
    letzteNotify = millis();
    bleWerte->setValue(wert.c_str());
    if (btZustand == BT_VERBUNDEN) bleWerte->notify();
  }
#endif
  if (btZustand == BT_SUCHEN && (int32_t)(millis() - btFensterEndeMs) >= 0) {
#if HYDRO_BLE
    NimBLEDevice::stopAdvertising();
#endif
    btSetzen(BT_NICHT_VERBUNDEN, btStill ? String(BT_SYNC_FENSTER_MS / 1000) + " s Sync-Fenster vorbei"
                                         : String(BT_SUCH_TIMEOUT_MS / 1000) + " s kein Handy -> Suche beendet");
  }
#if HYDRO_BLE
  // V4: ohne Fenster und ohne Verbindung den ganzen BLE-Stack ausschalten (erst dann Light-Sleep)
  if (stromsparen && bleLaeuft && (btZustand == BT_NICHT_VERBUNDEN || btZustand == BT_AUS)) bleStoppen();
#endif
}

// ============================================================================
//  LED-STREIFEN: aus im Normalbetrieb, nur bei Ereignissen, Dauerlicht.
//  Blinken NUR bei Akku-Warnung (rot), Bluetooth sucht (weiß), verbunden (2x lila).
//  Priorität: Nässe (Streifen ohne Strom, dunkel) > Akku rot blitzen (2x/4x) > lila 2x (Handy verbunden)
//             > weiß blinken (Bluetooth sucht) > rot (Fehler 5 s)
//             > blau (Erinnerung, V4: nach 2 min Sparblau) > grün (Ziel erreicht, 10 s)
//  In der Pause eines Blinkmusters sind die LEDs aus (keine Mischfarben).
//  V4 (H1): Der Streifen bekommt nur Strom (FET an GPIO18), solange eine Quelle aktiv ist.
//  Ausschalten: erst schwarz senden (DIN danach LOW), dann FET aus. Einschalten: FET an,
//  LED_STROM_EINSCHWING_MS warten, Farbe neu senden.
// ============================================================================
// LED-Strom über den FET schalten (V4, H1)
void ledStromSetzen(bool an, const String& grund) {
  if (an == ledStromAn) return;
  if (an) {
    digitalWrite(PIN_LAST, HIGH);       // NPN leitet -> Gate des P-MOSFET auf GND -> Streifen hat 5 V
    delay(LED_STROM_EINSCHWING_MS);     // Versorgung und LED-Chips einschwingen lassen
  } else {
    leds.clear();                       // erst alle LEDs schwarz ...
    leds.show();                        // ... (danach liegt DIN auf LOW)
    digitalWrite(PIN_LAST, LOW);        // ... dann 5 V wegschalten
  }
  ledStromAn = an;
  logZeile("LAST", String("LED-Strom ") + (an ? "AN" : "AUS") + " (" + grund + ")");
}

const char* ledQuelleName(LedQuelle q) {
  switch (q) {
    case L_AUS:       return "aus";
    case L_GESPERRT:  return "aus (Nässe: LED-Strom gesperrt)";
    case L_AKKU:      return "rot blitzen (Akku)";
    case L_LILA:      return "lila 2x blinken (Handy verbunden)";
    case L_WEISS:     return "weiß blinken (Bluetooth sucht)";
    case L_ROT:       return "rot (Fehler)";
    case L_BLAU:      return "blau (Erinnerung)";
    case L_SPARBLAU:  return "Sparblau (Erinnerung länger als 2 min)";
    case L_GRUEN:     return "grün (Ziel erreicht)";
  }
  return "?";
}

void ledsAktualisieren() {
  static uint32_t letzteFarbe = 0xFFFFFFFF;
  static LedQuelle letzteQuelle = L_AUS;
  uint32_t jetzt = millis();
  uint32_t farbe = 0;   // aus
  LedQuelle quelle = L_AUS;
  // Akku-Blinkmuster: läuft im Hintergrund weiter, auch während der Nässe-Sperre
  bool blinkAn = false;
  if (blinkAnzahl > 0) {
    uint32_t periode = blinkAnMs + blinkAusMs;
    uint32_t t = jetzt - blinkStartMs;
    if (t >= periode * blinkAnzahl) blinkAnzahl = 0;   // fertig -> wieder aus
    else blinkAn = (t % periode) < blinkAnMs;
  }
  bool blinkLaeuft = blinkAnzahl > 0;

  // 2x lila nach dem Verbinden: wartet, bis das Akku-Blinken fertig ist
  if (lilaAusstehend && !blinkLaeuft) {
    lilaAusstehend = false;
    lilaLaeuft = true;
    lilaStartMs = jetzt;
  }
  bool lilaAn = false;
  if (lilaLaeuft) {
    uint32_t periode = BT_LILA_AN_MS + BT_LILA_AUS_MS;
    uint32_t t = jetzt - lilaStartMs;
    if (t >= periode * BT_LILA_ANZAHL) lilaLaeuft = false;
    else lilaAn = (t % periode) < BT_LILA_AN_MS;
  }
  // weiß blinken, solange Bluetooth laut sucht (Takt ab Suchbeginn); stilles Fenster: kein Blinken
  bool weissAn = btZustand == BT_SUCHEN && !btStill &&
                 (jetzt - btSuchStartMs) % (BT_WEISS_AN_MS + BT_WEISS_AUS_MS) < BT_WEISS_AN_MS;

  if (zustand == NAESSE_SPERRE)               { quelle = L_GESPERRT; farbe = 0; }
  else if (blinkLaeuft)                       { quelle = L_AKKU;  farbe = blinkAn ? leds.Color(255, 0, 0) : 0; }
  else if (lilaLaeuft)                        { quelle = L_LILA;  farbe = lilaAn ? leds.Color(150, 0, 255) : 0; }
  else if (btZustand == BT_SUCHEN && !btStill) { quelle = L_WEISS; farbe = weissAn ? leds.Color(BT_WEISS_WERT, BT_WEISS_WERT, BT_WEISS_WERT) : 0; }
  else if ((int32_t)(rotBisMs - jetzt) > 0)   { quelle = L_ROT;   farbe = leds.Color(255, 0, 0); }
  else if (zustand == ERINNERUNG) {
    bool spar = stromsparen && jetzt - letzteErinnerungMs >= LED_ERINNERUNG_HELL_MS;
    quelle = spar ? L_SPARBLAU : L_BLAU;
    farbe  = leds.Color(0, 0, spar ? LED_SPARBLAU_WERT : 255);
  }
  else if ((int32_t)(gruenBisMs - jetzt) > 0) { quelle = L_GRUEN; farbe = leds.Color(0, 255, 0); }

  // Protokoll nur, wenn sich die QUELLE ändert (nicht bei jedem Blinken)
  if (quelle != letzteQuelle) {
    letzteQuelle = quelle;
    logZeile("LED", ledQuelleName(quelle));
  }
  // V4: Strom nur, solange eine Quelle aktiv ist (auch in den Blink-Pausen, kein Flackern).
  // Stromsparen aus = wie V3: Strom immer an, außer in der Nässe-Sperre.
  bool stromNoetig = zustand != NAESSE_SPERRE && (!stromsparen || quelle != L_AUS);
  if (!stromNoetig) {
    if (ledStromAn) ledStromSetzen(false, ledQuelleName(quelle));   // sendet vorher schwarz
    letzteFarbe = 0;
    return;
  }
  if (!ledStromAn) {
    ledStromSetzen(true, ledQuelleName(quelle));
    letzteFarbe = 0xFFFFFFFF;           // nach dem Einschalten Farbe neu senden
  }
  if (farbe == letzteFarbe) return;   // nur senden, wenn sich etwas ändert
  letzteFarbe = farbe;
  for (uint8_t i = 0; i < LED_ANZAHL; i++) leds.setPixelColor(i, farbe);
  leds.show();
}

// ============================================================================
//  BILDSCHIRME (drawUI)
// ============================================================================
String zuletzt[B_ANZAHL];

bool geaendert(Bereich b, const String& inhalt) {
  if (!bildschirmNeu && zuletzt[b] == inhalt) return false;
  zuletzt[b] = inhalt;
  return true;
}

const char* WOCHENTAG[] = { "So", "Mo", "Di", "Mi", "Do", "Fr", "Sa" };

String zweistellig(int v) {
  return v < 10 ? "0" + String(v) : String(v);
}

String dauerText(uint32_t s) {
  if (s < 60)  return String(s) + " s";
  if (s < 7200) return String(s / 60) + " min";
  return String(s / 3600) + " h";
}

void hauptbildschirmZeichnen() {
  struct tm lt;
  bool uhrOk = zeitHolen(lt);

  // --- Oben links: Uhrzeit groß, Datum darunter
  String zeit = uhrOk ? zweistellig(lt.tm_hour) + ":" + zweistellig(lt.tm_min) : "--:--";
  uint16_t zf = uhrQuelle == UHR_NTP ? WEISS : (uhrQuelle == UHR_ERSATZ ? GELB : GRAU);
  if (geaendert(B_ZEIT, zeit + String(zf))) {
    text(6, 6, zeit, 4, zf, SCHWARZ);
  }
  String datum;
  if (uhrOk) {
    datum = String(WOCHENTAG[lt.tm_wday]) + ", " + zweistellig(lt.tm_mday) + "." +
            zweistellig(lt.tm_mon + 1) + "." + String(lt.tm_year + 1900);
    if (uhrQuelle == UHR_ERSATZ) datum += " (ohne NTP)";
  } else {
    datum = "Zeit wird geholt ...";
  }
  if (geaendert(B_DATUM, datum)) {
    tft.fillRect(0, 42, 176, 10, SCHWARZ);
    text(8, 43, datum, 1, uhrQuelle == UHR_NTP ? HELLGRAU : GELB, SCHWARZ);
  }

  // --- Oben rechts: [Bluetooth] [Akku-Symbol], darunter Akku-Prozent
  //     Bereiche: Bluetooth x 168..191 / y 2..25, Akku-Symbol x 194..239 / y 0..25,
  //     Prozent x 184..239 / y 26..45. Uhrzeit endet bei x 126, Datum spätestens bei x 158.
  uint16_t btFarbe = SCHWARZ;   // SCHWARZ = nicht zeichnen (aus)
  bool btPunkte = false;
  bool btFest = false;
  if (btZustand == BT_SUCHEN && btStill) {
    btFarbe = BLAU; btFest = true;                        // V4: stilles Sync-Fenster, fest blau ohne Punkte
  } else if (btZustand == BT_SUCHEN) {
    bool hell = (millis() - btSuchStartMs) % (BT_WEISS_AN_MS + BT_WEISS_AUS_MS) < BT_WEISS_AN_MS;
    btFarbe = hell ? WEISS : BLAU;                        // pulsiert im LED-Takt
  } else if (btZustand == BT_VERBUNDEN) {
    btFarbe = BLAU; btPunkte = true;                      // fest blau + Punkte links/rechts
  } else if (btZustand == BT_NICHT_VERBUNDEN) {
    btFarbe = GRAU;                                       // Suche abgelaufen
  }
  if (geaendert(B_BT, String(btFarbe) + (btPunkte ? "p" : "") + (btFest ? "s" : ""))) {
    tft.fillRect(168, 2, 24, 24, SCHWARZ);
    if (btFarbe != SCHWARZ) {
      btSymbol(179, 6, btFarbe);
      if (btPunkte) {
        tft.fillRect(169, 14, 3, 3, btFarbe);
        tft.fillRect(188, 14, 3, 3, btFarbe);
      }
    }
  }

  if (geaendert(B_AKKU, String(akkuProzent) + "/" + String(akkuStufe))) {
    // grün = ok, orange = unter 20 %, rot = unter 10 %
    uint16_t f = akkuStufe == 2 ? ROT : (akkuStufe == 1 ? ORANGE : GRUEN);
    tft.fillRect(194, 0, 46, 26, SCHWARZ);
    tft.fillRect(184, 26, 56, 20, SCHWARZ);
    tft.drawRect(196, 8, 32, 15, WEISS);
    tft.fillRect(228, 12, 3, 7, WEISS);
    tft.fillRect(198, 10, 28 * akkuProzent / 100, 11, f);
    String p = String(akkuProzent) + "%";
    text(234 - textBreite(p, 2), 28, p, 2, akkuStufe > 0 ? f : WEISS, SCHWARZ);
  }

  // --- Mitte: heute getrunken (größtes Element)
  if (geaendert(B_MENGE, String(getrunkenHeute))) {
    tft.fillRect(0, 58, BREITE, 64, SCHWARZ);
    tft.drawFastHLine(8, 56, BREITE - 16, DUNKELGRAU);
    textMitte(0, BREITE, 62, "heute getrunken", 1, GRAU, SCHWARZ);
    String zahl = mitPunkt(getrunkenHeute);
    int16_t w = textBreite(zahl, 5) + 6 + textBreite("ml", 2);
    int16_t x0 = (BREITE - w) / 2;
    text(x0, 76, zahl, 5, WEISS, SCHWARZ);
    text(x0 + textBreite(zahl, 5) + 6, 100, "ml", 2, WEISS, SCHWARZ);
  }
  if (geaendert(B_VON, String(tagesziel))) {
    tft.fillRect(0, 124, BREITE, 18, SCHWARZ);
    textMitte(0, BREITE, 125, "von " + mitPunkt(tagesziel) + " ml", 2, HELLGRAU, SCHWARZ);
  }

  int prozent = (int)((long)getrunkenHeute * 100L / max(tagesziel, 1));
  if (geaendert(B_BALKEN, String(prozent))) {
    const int16_t bx = 12, by = 148, bw = 216, bh = 24;
    bool ziel = prozent >= 100;
    uint16_t f = ziel ? GRUEN : BLAU;
    int16_t voll = bw * min(prozent, 100) / 100;
    tft.fillRect(bx, by, bw, bh, DUNKELGRAU);
    tft.fillRect(bx, by, voll, bh, f);
    tft.drawRect(bx, by, bw, bh, WEISS);
    tft.setTextSize(2);
    tft.setTextColor(ziel ? SCHWARZ : WEISS);        // ohne Hintergrund (Balken zweifarbig)
    String pt = String(prozent) + " %";
    tft.setCursor(bx + (bw - textBreite(pt, 2)) / 2, by + 5);
    tft.print(pt);
  }

  bool zielErreicht = getrunkenHeute >= tagesziel;
  String zt = zielErreicht ? "Ziel erreicht" : "noch " + mitPunkt(tagesziel - getrunkenHeute) + " ml";
  if (geaendert(B_ZIELTEXT, zt)) {
    tft.fillRect(0, 178, BREITE, 22, SCHWARZ);
    if (zielErreicht) {
      int16_t w = textBreite(zt, 2) + 18;
      int16_t x0 = (BREITE - w) / 2;
      text(x0, 182, zt, 2, GRUEN, SCHWARZ);
      haken(x0 + w - 13, 182, GRUEN);
    } else {
      textMitte(0, BREITE, 184, zt, 1, GRAU, SCHWARZ);
    }
  }

  // --- Unten: Flasche x/y ml, Leer-Info, große Touch-Tasten Leer/Voll, Status
  String fl;
  if (!flascheSteht) {
    fl = "Keine Flasche";
  } else if (kapazitaetKalibriert) {
    fl = "Flasche: " + mitPunkt(flascheninhaltMl()) + "/" + mitPunkt(flaschenKapazitaetMl) + " ml";
  } else {
    fl = "Flasche: " + mitPunkt(flascheninhaltMl()) + " ml";
  }
  if (geaendert(B_FLASCHE, fl)) {
    tft.fillRect(0, 198, BREITE, 20, SCHWARZ);
    tft.drawFastHLine(8, 197, BREITE - 16, DUNKELGRAU);
    uint8_t fg = textBreite(fl, 2) <= (BREITE - 20) ? 2 : 1;
    text(10, fg == 2 ? 202 : 206, fl, fg, flascheSteht ? CYAN : GRAU, SCHWARZ);
  }
  String leer = "Leer " + String((int)lroundf(leergewicht)) + " g " +
                (flascheKalibriert ? "(kalibriert)" :
                 (leergewichtGelernt ? "(gelernt)" : "(Schätzwert)"));
  if (kapazitaetKalibriert) leer += " | Kap. " + String(flaschenKapazitaetMl) + " ml";
  if (geaendert(B_LEER, leer)) {
    tft.fillRect(0, 218, BREITE, 10, SCHWARZ);
    text(10, 219, leer, 1, GRAU, SCHWARZ);
  }

  // Erinnerungs-Hinweis (Logik unverändert) – eine Zeile über den Tasten entfällt;
  // Kurzinfo wandert bei Bedarf in das Statusfeld (siehe unten).
  uint32_t seit = (millis() - letzterSchluckMs) / 1000;
  String zl = heuteGetrunken ? "Zuletzt: vor " + dauerText(seit) : "Heute noch nichts";
  String ne;
  if (zielErreicht)               ne = "Ziel ok";
  else if (erinnerungenHeute >= ERINNERUNG_MAX_PRO_TAG)
                                  ne = "Max. Erinnerungen";
  else if (zustand == ERINNERUNG) ne = "Erinnerung!";
  else if (inRuhezeit())          ne = "Ruhezeit";
  else if (!hinterPlan() && uhrOk) ne = "Im Plan";
  else {
    uint32_t rest = erinnerungRestSekunden();
    if (rest == 0 && erinnerungMoeglich()) ne = "Erinnerung bald";
    else if (rest < 120 || !uhrOk)         ne = "in " + dauerText(rest > 0 ? rest : 1);
    else {
      time_t t = time(nullptr) + rest;
      struct tm e;
      localtime_r(&t, &e);
      ne = zweistellig(e.tm_hour) + ":" + zweistellig(e.tm_min);
    }
  }
  // B_ZULETZT / B_NAECHSTE weiter befüllen (Cache), Anzeige steckt in Status/Tasten-Bereich
  geaendert(B_ZULETZT, zl);
  geaendert(B_NAECHSTE, ne);

  // Große Touch-Tasten Leer | Voll (immer sichtbar auf dem Hauptbildschirm)
  String tk = String(kalSchritt) + "|" + String(flascheKalibriert ? 1 : 0) + "|" +
              String(kapazitaetKalibriert ? 1 : 0) + "|" +
              (gewichtKalibStabil() ? "1" : "0") + "|" + kalibMeldung;
  if (bildschirmNeu || geaendert(B_TASTEN, tk)) {
    tft.fillRect(0, 228, BREITE, 56, SCHWARZ);
    uint16_t leerFarbe = flascheKalibriert ? DUNKELGRUEN : DUNKELBLAU;
    uint16_t vollFarbe = (!flascheKalibriert) ? DUNKELGRAU :
                         (kapazitaetKalibriert ? DUNKELGRUEN : DUNKELBLAU);
    tasteZeichnen(TASTE_LEER, leerFarbe, WEISS);
    tasteZeichnen(TASTE_VOLL, vollFarbe, WEISS);
  }

  // --- Ganz unten: Statusfeld (Kalib-Meldung / Erinnerung / Warnung)
  String st;
  uint16_t sf = SCHWARZ, sc = GRAU;
  bool meldungAktiv = kalibMeldung.length() > 0 && (int32_t)(kalibMeldungBisMs - millis()) > 0;
  if (meldungAktiv) {
    st = kalibMeldung;
    bool fehler = kalibMeldung.indexOf("muss") >= 0 || kalibMeldung.indexOf("Zuerst") >= 0 ||
                  kalibMeldung.indexOf("Keine") >= 0 || kalibMeldung.indexOf("unruhig") >= 0;
    sf = fehler ? DUNKELROT : DUNKELGRUEN;
    sc = WEISS;
  } else if (touchGehalten && !langdruckErledigt && millis() - touchStartMs >= 1000) {
    st = "Kalib-Screen: noch " + String((LANGDRUCK_MS - min(LANGDRUCK_MS, millis() - touchStartMs) + 999) / 1000) + " s";
    sf = DUNKELGRAU; sc = WEISS;
  } else if (akkuStufe == 2) {
    st = "Bitte laden";                    sf = ROT;       sc = WEISS;
  } else if (!waageOk) {
    st = "Fehler: Waage antwortet nicht";  sf = DUNKELROT; sc = WEISS;
  } else if (gewicht < NEGATIV_FEHLER_G) {
    st = "Gewicht negativ: Kalibrierung!"; sf = DUNKELROT; sc = WEISS;
  } else if (zustand == ERINNERUNG) {
    st = "Zeit zu trinken!";               sf = BLAU;      sc = WEISS;
  } else if (akkuStufe == 1 && (int32_t)(akkuHinweisBisMs - millis()) > 0) {
    st = "Akku unter 20 %";                sf = ORANGE;    sc = SCHWARZ;
  } else {
    st = zl + " | Err. " + ne;
  }
  if (geaendert(B_STATUS, st + String(sf))) {
    tft.fillRect(0, 284, BREITE, 36, SCHWARZ);
    bool gross = textBreite(st, 2) <= 224;
    if (sf != SCHWARZ) tft.fillRoundRect(6, 286, 228, 30, 6, sf);
    textMitte(6, 228, gross ? 294 : 297, st, gross ? 2 : 1, sc, sf);
  }
}

void naessebildschirmZeichnen() {
  uint32_t rest = 0;
  if (!nass) rest = (TROCKEN_FREIGABE_MS - min(TROCKEN_FREIGABE_MS, millis() - trockenSeit) + 999) / 1000;
  String inhalt = nass ? "nass" : "trocken" + String(rest);
  if (!geaendert(B_STATUS, inhalt)) return;
  if (bildschirmNeu) {
    tft.fillScreen(ROT);
    textMitte(0, BREITE, 40, "WASSER", 4, WEISS, ROT);
    textMitte(0, BREITE, 80, "ERKANNT", 4, WEISS, ROT);
    tft.fillRect(20, 124, 200, 3, WEISS);
    textMitte(0, BREITE, 140, "STROM AUS", 3, GELB, ROT);
  }
  tft.fillRect(0, 190, BREITE, 90, ROT);
  textMitte(0, BREITE, 200, nass ? "Sensor: NASS" : "Sensor: trocken", 2, WEISS, ROT);
  textMitte(0, BREITE, 228, nass ? "Gerät abtrocknen." : "Freigabe in " + String(rest) + " s ...", 2, WEISS, ROT);
  textMitte(0, BREITE, 258, "Sperre endet automatisch,", 1, WEISS, ROT);
  textMitte(0, BREITE, 270, "wenn 5 s lang trocken.", 1, WEISS, ROT);
}

void kalibrierbildschirmZeichnen() {
  if (bildschirmNeu) {
    tft.fillScreen(SCHWARZ);
    tft.fillRect(0, 0, BREITE, 28, DUNKELBLAU);
    text(6, 7, "Kalibrierung", 2, WEISS, DUNKELBLAU);
    text(8, 36, "Leere Flasche → Taste Leer", 1, CYAN, SCHWARZ);
    text(8, 50, "Volle Flasche → Taste Voll", 1, CYAN, SCHWARZ);
    text(8, 66, "1 g = 1 ml  |  Serial: leer/voll", 1, GRAU, SCHWARZ);
  }

  String werte = String(kalSchritt) + "|" + String((int)lroundf(gewicht)) + "|" +
                 String((int)lroundf(leergewicht)) + "|" + String(flaschenKapazitaetMl) + "|" +
                 (gewichtKalibStabil() ? "1" : "0") + "|" + kalibMeldung + "|" +
                 String(flascheKalibriert ? 1 : 0) + "|" + String(kapazitaetKalibriert ? 1 : 0);
  if (bildschirmNeu || geaendert(B_STATUS, werte)) {
    tft.fillRect(0, 84, BREITE, 140, SCHWARZ);
    text(8, 88, "Gewicht: " + String((int)lroundf(gewicht)) + " g" +
                (gewichtKalibStabil() ? " (ruhig)" : " ..."), 2, WEISS, SCHWARZ);
    text(8, 112, "Leer: " + String((int)lroundf(leergewicht)) + " g" +
                 (flascheKalibriert ? " ok" : " – Taste Leer"), 1, GRAU, SCHWARZ);
    if (kapazitaetKalibriert) {
      text(8, 126, "Kapazität: " + String(flaschenKapazitaetMl) + " ml", 1, CYAN, SCHWARZ);
    } else {
      text(8, 126, "Kapazität: noch offen – Taste Voll", 1, GRAU, SCHWARZ);
    }
    if (flascheSteht) {
      text(8, 142, "Inhalt jetzt: " + String(flascheninhaltMl()) + " ml", 1, HELLGRAU, SCHWARZ);
    }

    bool meldungAktiv = kalibMeldung.length() > 0 && (int32_t)(kalibMeldungBisMs - millis()) > 0;
    if (meldungAktiv) {
      bool fehler = kalibMeldung.indexOf("muss") >= 0 || kalibMeldung.indexOf("Zuerst") >= 0 ||
                    kalibMeldung.indexOf("Keine") >= 0 || kalibMeldung.indexOf("unruhig") >= 0;
      uint16_t mf = fehler ? DUNKELROT : DUNKELGRUEN;
      tft.fillRoundRect(6, 160, 228, 28, 6, mf);
      uint8_t mg = textBreite(kalibMeldung, 2) <= 220 ? 2 : 1;
      textMitte(6, 228, mg == 2 ? 168 : 170, kalibMeldung, mg, WEISS, mf);
    } else if (kalSchritt == 0) {
      text(8, 168, "Schritt 1: leere Flasche, dann Leer", 1, HELLGRAU, SCHWARZ);
    } else if (kalSchritt == 1) {
      text(8, 168, "Schritt 2: volle Flasche, dann Voll", 1, HELLGRAU, SCHWARZ);
    } else {
      text(8, 168, "Fertig – Taste Fertig oder warten", 1, GRUEN, SCHWARZ);
    }

    uint16_t leerFarbe = (kalSchritt == 0) ? DUNKELBLAU : (flascheKalibriert ? DUNKELGRUEN : DUNKELBLAU);
    uint16_t vollFarbe = (kalSchritt == 1) ? DUNKELBLAU :
                         (kapazitaetKalibriert ? DUNKELGRUEN :
                          (flascheKalibriert ? DUNKELBLAU : DUNKELGRAU));
    tasteZeichnen(TASTE_LEER, leerFarbe, WEISS);
    tasteZeichnen(TASTE_VOLL, vollFarbe, WEISS);
    tasteZeichnen(TASTE_KAL_FERTIG, kalSchritt >= 2 ? DUNKELBLAU : DUNKELGRAU, WEISS);
  }
}


void drawUI() {
  static uint32_t letzte = 0;
  if (kalibMeldung.length() > 0 && (int32_t)(kalibMeldungBisMs - millis()) <= 0) {
    kalibMeldung = "";
  }
  if (stromsparen && energie == E_RUHE) return;            // V4: Display aus -> nicht zeichnen
  if (!bildschirmNeu && millis() - letzte < 200) return;   // max. 5x pro Sekunde
  letzte = millis();
  if (bildschirmNeu) {
    for (uint8_t i = 0; i < B_ANZAHL; i++) zuletzt[i] = "";
    if (zustand != NAESSE_SPERRE && zustand != KALIBRIERUNG) tft.fillScreen(SCHWARZ);
  }
  if (zustand == NAESSE_SPERRE)     naessebildschirmZeichnen();
  else if (zustand == KALIBRIERUNG) kalibrierbildschirmZeichnen();
  else                              hauptbildschirmZeichnen();
  bildschirmNeu = false;
}

// ============================================================================
//  SERIELLE BEFEHLE
// ============================================================================
void hilfeAusgeben() {
  Serial.println(F("Befehle: status | reset | gewicht <kg> | groesse <cm> | zeit <HH:MM> | hilfe"));
  Serial.println(F("Flasche:  kalib | leer | voll"));
  Serial.println(F("Energie:  stromsparen 0 | stromsparen 1 | sync (Uhr per WLAN abgleichen)"));
#if HYDRO_BLE
  Serial.println(F("Bluetooth (echtes BLE): bt suchen | bt aus   (verbunden/getrennt meldet das Handy)"));
#else
  Serial.println(F("Bluetooth (simuliert):  bt suchen | bt verbunden | bt getrennt | bt aus"));
#endif
}

String btText() {
  String t = btName(btZustand);
  if (btZustand == BT_SUCHEN) {
    int32_t rest = (int32_t)(btFensterEndeMs - millis());
    t += " (noch " + String((long)(max(rest, (int32_t)0) / 1000)) + " s" + (btStill ? ", still" : "") + ")";
  }
  return t + (HYDRO_BLE ? " [BLE]" : " [simuliert]");
}

// Befehle "bt suchen | verbunden | getrennt | aus"
void btBefehl(const String& wert) {
  if (wert == "suchen") {
    btSuchenStarten("Befehl bt suchen");
  } else if (wert == "aus") {
    btAusschalten();
  } else if (wert == "verbunden" || wert == "getrennt") {
#if HYDRO_BLE
    Serial.println(F("Mit echtem BLE meldet das Handy selbst verbunden/getrennt (nur in der Simulation per Befehl)."));
#else
    if (wert == "verbunden") {
      if (btZustand == BT_SUCHEN) btSetzen(BT_VERBUNDEN, "Befehl bt verbunden (simuliert)");
      else if (btZustand == BT_VERBUNDEN) Serial.println(F("Schon verbunden."));
      else Serial.println(F("Nicht sichtbar - erst \"bt suchen\", dann \"bt verbunden\"."));
    } else {
      if (btZustand == BT_VERBUNDEN) btNachTrennung("Befehl bt getrennt (simuliert)");
      else Serial.println(F("Kein Handy verbunden."));
    }
#endif
  } else {
    Serial.println(F("bt suchen | bt verbunden | bt getrennt | bt aus"));
  }
}

void statusAusgeben() {
  struct tm lt;
  String uhr = zeitHolen(lt) ? zweistellig(lt.tm_mday) + "." + zweistellig(lt.tm_mon + 1) + ". " +
                               zweistellig(lt.tm_hour) + ":" + zweistellig(lt.tm_min)
                             : String("keine");
  logZeile("STATUS", String("Zustand=") + zustandName(zustand) +
           " | heute=" + String(getrunkenHeute) + "/" + String(tagesziel) + " ml" +
           " | Soll=" + String(sollGetrunkenMl()) + " ml" +
           " | Erinnerungen=" + String(erinnerungenHeute) + "/" + String(ERINNERUNG_MAX_PRO_TAG) +
           (erinnerungPauseAktiv() ? " Pause" : "") +
           " | Profil=" + String(profilKg, 1) + " kg/" + String(profilCm) + " cm" +
           " | Gewicht=" + String((int)lroundf(gewicht)) + " g" + (gewichtRuhig ? " (ruhig)" : " (unruhig)") +
           " | Flasche=" + String(flascheninhaltMl()) + " ml" +
           ", leer=" + String(leergewicht, 0) + " g" +
           (flascheKalibriert ? " (kalibriert)" : (leergewichtGelernt ? " (gelernt)" : " (Schätzwert)")) +
           ", voll=" + String(vollgewicht, 0) + " g" +
           ", Kapazität=" + String(flaschenKapazitaetMl) + " ml" +
           (kapazitaetKalibriert ? " (kalibriert)" : "") +
           " | Akku=" + String(akkuVolt, 2) + " V, " + String(akkuProzent) + " %" +
           (akkuStufe == 2 ? " (unter 10 %)" : (akkuStufe == 1 ? " (unter 20 %)" : "")) +
           " | nass=" + String(nass ? "ja" : "nein") +
           " | LED-Strom=" + String(digitalRead(PIN_LAST) ? "AN" : "AUS") +
           " | Uhr=" + uhr + (uhrQuelle == UHR_NTP ? " (NTP)" : (uhrQuelle == UHR_ERSATZ ? " (Ersatz)" : "")) +
           " | BT=" + btText() +
           " | Energie=" + energieName(energie) + " (Licht " + String(lichtWert) + ")" +
           " | Stromsparen=" + String(stromsparen ? "an" : "aus") +
           " | WLAN=" + String(wlanModus == WLAN_AUS ? "aus" : (wlanModus == WLAN_ABGLEICH ? "Abgleich" : "dauerhaft")) +
           " | CPU=" + String(getCpuFrequencyMhz()) + " MHz" +
           (HYDRO_LIGHTSLEEP ? " | Schlafzyklen=" + String(schlafZyklen) : String("")));
}

// "stromsparen 0" = Verhalten wie V3, "stromsparen 1" = V4 (zur Laufzeit, nicht gespeichert)
void stromsparenSetzen(bool an) {
  if (an == stromsparen) {
    Serial.println(an ? F("Stromsparen ist schon an.") : F("Stromsparen ist schon aus."));
    return;
  }
  stromsparen = an;
  setCpuFrequencyMhz(an ? CPU_MHZ : 240);
  logZeile("ENERGIE", an ? "Stromsparen AN (CPU " + String(CPU_MHZ) + " MHz)"
                         : String("Stromsparen AUS -> Verhalten wie Version 3 (CPU 240 MHz)"));
  letzteAktivitaetMs = millis();
  if (!an) {
    energieSetzen(E_AKTIV, "Stromsparen aus");
    hintergrundlichtSetzen(LCD_HELL);
    if (wlanModus == WLAN_AUS) wlanEinschalten();
    wlanModus = WLAN_DAUER;
#if HYDRO_BLE
    bleStarten();                     // wie V3: Stack bleibt an
#endif
    if (zustand != NAESSE_SPERRE) ledStromSetzen(true, "Stromsparen aus");
  } else {
    letzterAbgleichMs = millis();
    if (wlanModus == WLAN_DAUER) {
      if (uhrQuelle == UHR_NTP) wlanAusschalten("Stromsparen an");
      else { wlanModus = WLAN_ABGLEICH; wlanStartMs = millis(); }
    }
    // BLE-Stack und LED-Strom schalten btVerwalten() / ledsAktualisieren() selbst ab
  }
}

void serielleBefehle() {
  static String zeile;
  while (Serial.available()) {
    char c = (char)Serial.read();
    if (c == '\r') continue;
    if (c != '\n') { if (zeile.length() < 40) zeile += c; continue; }
    zeile.trim();
    zeile.toLowerCase();
    if (zeile.length() > 0) aktivitaet("Serieller Befehl");
    int leer = zeile.indexOf(' ');
    String befehl = leer < 0 ? zeile : zeile.substring(0, leer);
    String wert = leer < 0 ? String("") : zeile.substring(leer + 1);
    wert.trim();
    wert.replace(',', '.');

    if (befehl == "status") {
      statusAusgeben();
    } else if (befehl == "reset") {
      tageswechsel("Befehl reset");
    } else if (befehl == "gewicht") {
      float kg = wert.toFloat();
      if (kg >= 30 && kg <= 250) {
        profilKg = kg;
        speicher.putFloat("kg", profilKg);
        zielAktualisieren(true);
      } else {
        Serial.println(F("Bitte Körpergewicht 30..250 kg angeben, z. B. \"gewicht 75\""));
      }
    } else if (befehl == "groesse") {
      int cm = wert.toInt();
      if (cm >= 120 && cm <= 230) {
        profilCm = cm;
        speicher.putInt("cm", profilCm);
        zielAktualisieren(true);
      } else {
        Serial.println(F("Bitte Körpergröße 120..230 cm angeben, z. B. \"groesse 180\""));
      }
    } else if (befehl == "zeit") {
      int dp = wert.indexOf(':');
      int h = dp > 0 ? wert.substring(0, dp).toInt() : -1;
      int m = dp > 0 ? wert.substring(dp + 1).toInt() : -1;
      if (h >= 0 && h < 24 && m >= 0 && m < 60) {
        ersatzuhrSetzen(h, m);
        uhrQuelle = UHR_ERSATZ;          // Uhr von Hand gestellt
        ntpEmpfangen = false;            // erst die NÄCHSTE NTP-Meldung stellt wieder um
        if (letzterTag < 0) tagMerken(); // erste Uhrzeit überhaupt: Tag merken, nicht zurücksetzen
        bildschirmNeu = true;
        logZeile("UHR", "Uhr von Hand gestellt (NTP kann sie später wieder korrigieren)");
      } else {
        Serial.println(F("Format: zeit HH:MM, z. B. \"zeit 23:59\""));
      }
    } else if (befehl == "kalib" || befehl == "kalibrierung") {
      if (zustand == NAESSE_SPERRE) {
        Serial.println(F("Während Nässe-Sperre keine Kalibrierung."));
      } else if (zustand != KALIBRIERUNG) {
        zustandWechseln(KALIBRIERUNG, "Befehl kalib");
      } else {
        Serial.println(F("Schon in Kalibrierung. Schritte: leer → voll → Fertig"));
      }
    } else if (befehl == "leer") {
      if (zustand != KALIBRIERUNG) zustandWechseln(KALIBRIERUNG, "Befehl leer");
      kalSchritt = 0;
      kalibLeerBestaetigen();
    } else if (befehl == "voll") {
      if (zustand != KALIBRIERUNG) zustandWechseln(KALIBRIERUNG, "Befehl voll");
      kalibVollBestaetigen();
    } else if (befehl == "bt") {
      btBefehl(wert);
    } else if (befehl == "sync") {
      wlanAbgleichStarten("Befehl sync");
    } else if (befehl == "stromsparen") {
      if (wert == "0" || wert == "1") stromsparenSetzen(wert == "1");
      else Serial.println(F("stromsparen 0 (wie V3) | stromsparen 1 (V4)"));
    } else if (zeile.length() > 0) {
      hilfeAusgeben();
    }
    zeile = "";
  }
}

// ============================================================================
//  SCHLAF (V4): Light-Sleep in RUHE (nur echtes CYD), Tiefschlaf bei leerem Akku
// ============================================================================
// Darf das Gerät jetzt kurz schlafen? (Gründe dagegen: Stromsparplan Kap. 3.2)
bool schlafErlaubt() {
  if (!stromsparen || energie != E_RUHE) return false;
  if (zustand == NAESSE_SPERRE || zustand == KALIBRIERUNG || nass) return false;
  if (touchGehalten) return false;                                    // Finger liegt noch auf
  if (blinkAnzahl > 0 || lilaLaeuft || lilaAusstehend) return false;  // Blinkmuster laufen in loop()
  if (btZustand == BT_SUCHEN || btZustand == BT_VERBUNDEN) return false;  // BLE-Fenster / Verbindung
#if HYDRO_BLE
  if (bleLaeuft) return false;                                        // Stack noch nicht aus
#endif
  if (wlanModus != WLAN_AUS) return false;                            // Uhr-Abgleich läuft
  if (Serial.available()) return false;
  return true;
}

#if HYDRO_LIGHTSLEEP
const gpio_num_t HALTE_PINS[] = { (gpio_num_t)PIN_LAST, (gpio_num_t)PIN_TFT_LED,
                                  (gpio_num_t)PIN_HX711_SCK, (gpio_num_t)PIN_LED_DATA };

// Bis zur nächsten Waagen-Messung schlafen (höchstens RUHE_WECKTAKT_MS). Wecken: Timer,
// Nässe (GPIO19 LOW) und Touch (GPIO36 LOW). millis() läuft im Light-Sleep weiter.
void leichtSchlafen() {
  uint32_t seit = millis() - waageLetzteMessungMs;
  if (seit >= RUHE_WECKTAKT_MS) return;           // Waage ist dran -> erst messen
  uint32_t dauer = RUHE_WECKTAKT_MS - seit;
  if (dauer < 5) return;                          // lohnt sich nicht
  if (digitalRead(PIN_NAESSE) == LOW) return;     // nass -> wach bleiben (Sperre folgt)
  bool touchWecken = TOUCH_IRQ_NUTZEN && digitalRead(PIN_TOUCH_IRQ) == HIGH;  // nur wenn gerade nicht LOW
  Serial.flush();
  if (RUHE_PINS_HALTEN) for (gpio_num_t p : HALTE_PINS) gpio_hold_en(p);   // Pegel festhalten (FET, Licht, HX711-SCK, DIN)
  esp_sleep_enable_timer_wakeup((uint64_t)dauer * 1000ULL);
  gpio_wakeup_enable((gpio_num_t)PIN_NAESSE, GPIO_INTR_LOW_LEVEL);
  if (touchWecken) gpio_wakeup_enable((gpio_num_t)PIN_TOUCH_IRQ, GPIO_INTR_LOW_LEVEL);
  esp_sleep_enable_gpio_wakeup();
  esp_light_sleep_start();
  gpio_wakeup_disable((gpio_num_t)PIN_NAESSE);
  if (touchWecken) gpio_wakeup_disable((gpio_num_t)PIN_TOUCH_IRQ);
  esp_sleep_disable_wakeup_source(ESP_SLEEP_WAKEUP_GPIO);
  esp_sleep_disable_wakeup_source(ESP_SLEEP_WAKEUP_TIMER);
  if (RUHE_PINS_HALTEN) for (gpio_num_t p : HALTE_PINS) gpio_hold_dis(p);
  schlafZyklen++;
}
#endif

// Tiefschlaf mit Timer (nur Akku-Schutz). FET-Pin und Licht-Pin werden LOW gehalten.
void tiefschlafStarten() {
  ledcDetach(PIN_TFT_LED);
  pinMode(PIN_TFT_LED, OUTPUT);
  digitalWrite(PIN_TFT_LED, LOW);
  digitalWrite(PIN_LAST, LOW);                    // Streifen ohne Strom
  pinMode(PIN_LED_DATA, OUTPUT);
  digitalWrite(PIN_LED_DATA, LOW);                // keine Fehlspeisung über DIN
  gpio_hold_en((gpio_num_t)PIN_TFT_LED);
  gpio_hold_en((gpio_num_t)PIN_LAST);
  gpio_hold_en((gpio_num_t)PIN_LED_DATA);
  gpio_deep_sleep_hold_en();
  Serial.flush();
  esp_sleep_enable_timer_wakeup((uint64_t)AKKU_LEER_SCHLAF_MIN * 60ULL * 1000000ULL);
  esp_deep_sleep_start();                         // kommt nicht zurück (Neustart nach dem Timer)
}

// ============================================================================
//  SETUP + LOOP
// ============================================================================
void setup() {
  // Zuerst: LED-Strom AUS (FET-Pin LOW), Pin-Halten aus einem Tiefschlaf lösen
  gpio_deep_sleep_hold_dis();
  gpio_hold_dis((gpio_num_t)PIN_TFT_LED);
  gpio_hold_dis((gpio_num_t)PIN_LAST);
  gpio_hold_dis((gpio_num_t)PIN_LED_DATA);
  pinMode(PIN_LAST, OUTPUT);
  digitalWrite(PIN_LAST, LOW);
  Serial.begin(115200);
  delay(200);
  Serial.println();
  Serial.println(F("=== HydroDesk Base – Wokwi-Simulation (V4) ==="));

  pinMode(PIN_NAESSE, INPUT_PULLUP);
  pinMode(PIN_AKKU_ADC, INPUT);

  // Akku-Schutz: aus dem Tiefschlaf aufgewacht? Erst bei genug Spannung normal starten.
  if (akkuLeerSchlaf) {
    float v = akkuSpannungMessen();
    if (v < AKKU_WIEDERANLAUF_V) {
      logZeile("AKKU", "noch leer (" + String(v, 2) + " V < " + String(AKKU_WIEDERANLAUF_V, 2) +
               " V) -> weiter schlafen");
      tiefschlafStarten();
      return;                              // (nur für den PC-Test; echt kommt der Tiefschlaf nicht zurück)
    }
    akkuLeerSchlaf = false;
    logZeile("AKKU", "Spannung wieder " + String(v, 2) + " V -> normaler Start");
  }

  if (stromsparen) setCpuFrequencyMhz(CPU_MHZ);   // M4: 80 MHz statt 240 MHz

  leds.begin();                          // DIN = Ausgang LOW
  leds.setBrightness(LED_HELLIGKEIT);
  leds.clear();
  if (!stromsparen) {                    // wie V3: Strom an, LEDs schwarz
    ledStromSetzen(true, "Start (Stromsparen aus)");
    leds.show();
  }                                      // V4: Streifen bleibt ohne Strom, bis er leuchten soll

  speicher.begin("hydrodesk", false);
  faktor             = speicher.getFloat("faktor", WOKWI_FAKTOR);
  profilKg           = speicher.getFloat("kg", KOERPERGEWICHT_KG);
  profilCm           = speicher.getInt("cm", KOERPERGROESSE_CM);
  leergewicht          = speicher.getFloat("leer", LEERGEWICHT_START_G);
  leergewichtGelernt   = speicher.getBool("leerOk", false);
  flascheKalibriert    = speicher.getBool("flKalib", false);
  vollgewicht          = speicher.getFloat("voll", 0);
  flaschenKapazitaetMl = speicher.getInt("kapMl", 0);
  kapazitaetKalibriert = speicher.getBool("kapOk", false);
  zielAktualisieren(true);

  anzeigeInit();
  waageInit();
  if (speicher.isKey("tara")) {
    tara = speicher.getFloat("tara", 0);
    logZeile("WAAGE", "Tara aus Speicher: " + String(tara, 1));
  } else {
    taraSetzen();                        // erster Start: Pad muss leer sein
  }
  logZeile("LEER", "Leergewicht " + String(leergewicht, 0) + " g " +
           (flascheKalibriert ? "(kalibriert)" :
            (leergewichtGelernt ? "(gelernt)" : "(Startwert, wird beim Nachfüllen gelernt)")));
  if (kapazitaetKalibriert) {
    logZeile("LEER", "Kapazität " + String(flaschenKapazitaetMl) + " ml (voll " +
             String(vollgewicht, 0) + " g)");
  }

  uhrStarten();
#if HYDRO_BLE
  if (!stromsparen) bleStarten();        // wie V3: Stack immer an. V4: erst im Fenster
#else
  logZeile("BT", "Bluetooth wird nur simuliert (Befehle: bt suchen | bt verbunden | bt getrennt | bt aus)");
#endif
  if (BT_START_SUCHEN) btSuchenStarten("Start");
  else btSetzen(BT_NICHT_VERBUNDEN, "Start ohne Suche");
  letzterSchluckMs = millis();
  naesseLesen();
  logZeile("SYSTEM", String("Erinnerung: Pause ") + String(ERINNERUNG_PAUSE_MS / 1000) +
           " s nach ≥100 ml, Abstand " + String(ERINNERUNG_MIN_ABSTAND_MS / 1000) +
           " s, max " + String(ERINNERUNG_MAX_PRO_TAG) + "/Tag, Ruhe " +
           String(RUHE_START_STUNDE) + ":00-" + String(RUHE_ENDE_STUNDE) + ":00" +
           (WOKWI_DEMO_ERINNERUNG ? " [WOKWI-DEMO]" : " [Gerät]"));
  logZeile("ZUSTAND", "Start in IDLE");
  logZeile("ENERGIE", stromsparen ? "Stromsparen an: CPU " + String(getCpuFrequencyMhz()) +
                                    " MHz, dimmen nach 30 s, Display aus nach 2 min (nachts 15 s)" +
                                    (HYDRO_LIGHTSLEEP ? ", Light-Sleep in RUHE" : ", Wokwi: ohne echten Schlaf")
                                  : String("Stromsparen aus (wie Version 3)"));
  letzteAktivitaetMs = millis();
  hilfeAusgeben();
}

void loop() {
  naesseLesen();          // 1. Sicherheit zuerst
  akkuLesen();
  waageLesen();
  uhrVerwalten();
  btVerwalten();
  touchAuswerten();       // 2. versteckte Bedienung
  zustandAktualisieren(); // 3. Zustandsautomat
  energieVerwalten();     //    V4: Display hell / gedimmt / aus
  ledsAktualisieren();    // 4. Ausgaben
  drawUI();
  serielleBefehle();
  wlanVerwalten();        //    V4: Uhr-Abgleich per WLAN
#if HYDRO_LIGHTSLEEP
  if (schlafErlaubt()) {  // V4: in RUHE bis zur nächsten Waagen-Messung schlafen
    leichtSchlafen();
    return;
  }
#endif
  delay(5);
}
