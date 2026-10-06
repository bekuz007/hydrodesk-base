/*
 * ============================================================================
 *  HydroDesk Base – Wokwi-Simulation (ESP32, Arduino)          Version 2
 * ============================================================================
 *  Schulprojekt FI-AE: Trink-Tracker für den Schreibtisch.
 *  Eine Flasche steht auf einem Pad über einer Wägezelle (HX711). Das Display
 *  zeigt Uhrzeit, Akku, heute getrunkene Menge, Tagesziel und Flascheninhalt.
 *  Es gibt KEINE Tasten: alles wird aus dem Gewicht abgeleitet.
 *  LEDs (WS2812) leuchten nur bei Ereignissen (Akku-Warnung: kurz rot blitzen).
 *  Ein Nässe-Sensor schaltet bei
 *  Wasser die Last ab.
 *
 *  Simulation (Wokwi)                      | Echte Hardware
 *  ----------------------------------------+---------------------------------
 *  ILI9341 + kapazitiver Touch FT6206 (I2C)| CYD ESP32-2432S028R:
 *                                          | ILI9341 + resistiver Touch XPT2046
 *  HX711-Schieberegler (0–5 kg)            | HX711 + 5-kg-Wägezelle
 *  Schiebeschalter "NÄSSE"                 | LM393-Regensensor, Ausgang DO
 *  Potentiometer "AKKU"                    | Akku über Spannungsteiler am ADC
 *  LED "LAST"                              | MOSFET, der die Last schaltet
 *  WLAN "Wokwi-GUEST" + NTP                | Heim-/Schul-WLAN (secrets.h) + NTP
 *  Telegram: nur Serial-Ausgabe (Stub)     | Telegram-Bot über WLAN
 *
 *  Versteckte Bedienung: 3 s irgendwo auf das Display drücken
 *  -> Service-Modus "Kalibrierung" (nur dort gibt es Tasten).
 *  Serieller Monitor (115200 Baud): "hilfe", "status", "reset",
 *  "gewicht 75", "groesse 180", "zeit 23:59"
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

#include <Arduino.h>
#include <SPI.h>
#include <WiFi.h>               // WLAN (im ESP32-Kern enthalten)
#include <time.h>               // Uhrzeit / Datum
#include <sys/time.h>           // settimeofday() für die Ersatzuhr
#include <esp_sntp.h>           // Meldung "NTP-Zeit empfangen"
#include <Preferences.h>        // Einstellungen dauerhaft im Flash (NVS)
#include <HX711.h>              // Wägezellen-Verstärker
#include <Adafruit_NeoPixel.h>  // LED-Streifen WS2812

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

// --- Erinnerung
const uint32_t ERINNERUNG_MS        = 30UL * 1000UL; // Demo: 30 s (echt z. B. 45UL*60UL*1000UL)

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
const uint32_t STABIL_MS            = 1500;   // so lange muss das Gewicht ruhig sein
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
const float    AKKU_LEER_V          = 3.0f;
const float    AKKU_VOLL_V          = 4.2f;
const int      AKKU_WARN_PROZENT    = 20;     // darunter: Hinweis + 2x rot blinken
const int      AKKU_KRITISCH_PROZENT = 10;    // darunter: Balken "Bitte laden" + 4x rot blinken
const int      AKKU_HYSTERESE_PROZENT = 2;    // erst bei Schwelle + 2 % gilt die Warnung als vorbei
const uint8_t  AKKU_BLINK_WARN      = 2;      // Anzahl Blitze unter 20 %
const uint8_t  AKKU_BLINK_KRITISCH  = 4;      // Anzahl Blitze unter 10 %
const uint32_t AKKU_BLINK_AN_MS     = 300;
const uint32_t AKKU_BLINK_AUS_MS    = 300;
const uint32_t AKKU_WIEDERHOLUNG_MS = 10UL * 60UL * 1000UL; // Blinkmuster alle 10 min wiederholen (0 = nie)
const uint32_t AKKU_HINWEIS_MS      = 5000;   // Hinweis "Akku unter 20 %" so lange im Statusfeld

// --- LED-Streifen: leuchtet NUR bei Ereignissen. Dauerlicht, nie blinkend -
//     EINZIGE Ausnahme: die kurze Akku-Warnung (2x bzw. 4x rot, dann aus)
const uint8_t  LED_ANZAHL           = 10;
const uint8_t  LED_HELLIGKEIT       = 60;     // 0..255 (mittel)
const uint32_t LED_GRUEN_MS         = 10000;  // "Ziel erreicht" 10 s grün
const uint32_t LED_ROT_MS           = 5000;   // Waagen-Fehler: 5 s rot

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
const int PIN_LED_DATA  = 23;  // WS2812 Daten
const int PIN_LAST      = 18;  // HIGH = Last/Strom an (MOSFET-Gate)

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
 *  ERINNERUNG     Seit ERINNERUNG_MS nichts getrunken, Ziel nicht erreicht.
 *                 LEDs dauerhaft blau, bis wieder getrunken wird.
 *  ZIEL_ERREICHT  Tagesziel erreicht. LEDs 10 s grün, dann aus.
 *                 Keine Erinnerungen mehr, es wird weiter gezählt.
 *  NAESSE_SPERRE  Nässe-Sensor meldet Wasser: Last sofort AUS, LEDs bernstein,
 *                 rote Vollbild-Warnung. Hebt sich AUTOMATISCH auf, wenn der
 *                 Sensor TROCKEN_FREIGABE_MS (5 s) lang trocken ist.
 *  KALIBRIERUNG   Versteckter Service-Modus (3 s aufs Display drücken):
 *                 Tara + 500-g-Referenz. Messung pausiert.
 *
 *  Übergänge (Priorität von oben nach unten):
 *    jeder Zustand   --Wasser erkannt-----------------> NAESSE_SPERRE
 *    NAESSE_SPERRE   --5 s ununterbrochen trocken-----> IDLE
 *    normale Zustände--3 s Display gedrückt-----------> KALIBRIERUNG
 *    KALIBRIERUNG    --Taste "Fertig"-----------------> IDLE
 *    sonst wird der passende Zustand jedes Mal neu bestimmt:
 *        getrunken >= Ziel                          -> ZIEL_ERREICHT
 *        Zeit seit letztem Schluck >= ERINNERUNG_MS -> ERINNERUNG
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

// Eine Taste (gibt es NUR im Service-Modus)
struct Taste {
  int16_t x, y, w, h;
  const char* beschriftung;
};

// Bildschirm-Bereiche, die einzeln neu gezeichnet werden (gegen Flackern)
enum Bereich : uint8_t {
  B_ZEIT, B_DATUM, B_AKKU, B_MENGE, B_VON, B_BALKEN, B_ZIELTEXT,
  B_FLASCHE, B_LEER, B_ZULETZT, B_NAECHSTE, B_STATUS, B_ANZAHL
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

// Trinken + Ziel
int      getrunkenHeute   = 0;              // ml
float    profilKg         = KOERPERGEWICHT_KG;
int      profilCm         = KOERPERGROESSE_CM;
int      tagesziel        = 2000;           // wird aus dem Profil berechnet
uint32_t letzterSchluckMs = 0;
bool     heuteGetrunken   = false;

// Sensoren
bool     nass             = false;
uint32_t trockenSeit      = 0;
uint8_t  akkuStufe        = 0;    // 0 = ok, 1 = unter 20 %, 2 = unter 10 %
uint32_t akkuWarnMs       = 0;    // Zeitpunkt der letzten Akku-Warnung (für die 10-min-Wiederholung)
uint32_t akkuHinweisBisMs = 0;    // bis dahin Hinweis "Akku unter 20 %" im Statusfeld
float    akkuVolt         = 4.2f;
int      akkuProzent      = 100;
bool     fehlerVorher     = false;

// Uhr
UhrQuelle uhrQuelle       = UHR_KEINE;
volatile bool ntpEmpfangen = false;
long     letzterTag       = -1;             // Jahr*1000 + Tag im Jahr
bool     wlanVerbunden    = false;

// LEDs
uint32_t gruenBisMs       = 0;
uint32_t rotBisMs         = 0;
uint32_t blinkStartMs     = 0;    // Akku-Blinkmuster: Start ...
uint8_t  blinkAnzahl      = 0;    // ... und Anzahl Blitze (0 = kein Blinken)

// Anzeige / Touch
bool     bildschirmNeu    = true;
uint8_t  kalSchritt       = 0;
uint32_t touchStartMs     = 0;
bool     touchGehalten    = false;
bool     langdruckErledigt = false;

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
  XPT2046_Touchscreen touch(33, 36);   // CYD-Touch: CS 33, IRQ 36
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

void anzeigeInit() {
  pinMode(PIN_TFT_LED, OUTPUT);
  digitalWrite(PIN_TFT_LED, HIGH);   // Hintergrundbeleuchtung an
#if HYDRO_CYD
  tft.init();
  tft.setRotation(0);                // Hochformat 240 x 320
  touchSpi.begin(25, 39, 32, 33);
  touch.begin(touchSpi);
  touch.setRotation(0);
  touchBereit = true;
#else
  tftSpi.begin(PIN_TFT_SCK, PIN_TFT_MISO, PIN_TFT_MOSI, -1);
  tft.begin();
  tft.setRotation(0);                // Hochformat 240 x 320
  tft.cp437(true);                   // richtige Zeichentabelle für Umlaute
  Wire.begin(PIN_TOUCH_SDA, PIN_TOUCH_SCL);
  touchBereit = touch.begin(40);
#endif
  tft.fillScreen(0x0000);
  logZeile("SYSTEM", touchBereit ? "Display + Touch bereit" : "Display bereit, Touch NICHT gefunden");
}

// Liefert true, SOLANGE das Display berührt wird, und die Position in
// Display-Pixeln (0..239, 0..319). Kurz-/Langdruck wertet touchAuswerten() aus.
bool readTouch(int16_t& x, int16_t& y) {
  if (!touchBereit) return false;
#if HYDRO_CYD
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

bool getroffen(const Taste& t, int16_t x, int16_t y) {
  return x >= t.x && x < t.x + t.w && y >= t.y && y < t.y + t.h;
}

void tasteZeichnen(const Taste& t, uint16_t fuellung, uint16_t schrift) {
  tft.fillRoundRect(t.x, t.y, t.w, t.h, 6, fuellung);
  tft.drawRoundRect(t.x, t.y, t.w, t.h, 6, WEISS);
  textMitte(t.x, t.w, t.y + (t.h - 16) / 2, t.beschriftung, 2, schrift, fuellung);
}

// Tasten NUR im Service-Modus "Kalibrierung"
const Taste TASTE_KAL_TARA    = { 10, 196, 220, 36, "1. Pad leer: Tara" };
const Taste TASTE_KAL_GEWICHT = { 10, 238, 220, 36, "2. 500 g liegt: OK" };
const Taste TASTE_KAL_FERTIG  = { 10, 280, 220, 36, "Fertig" };

// ============================================================================
//  UHR: WLAN + NTP, Ersatzuhr, Tageswechsel
// ============================================================================
void ntpCallback(struct timeval* tv) {
  (void)tv;
  ntpEmpfangen = true;   // wird im loop() ausgewertet (hier nur Merker setzen)
}

void uhrStarten() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WLAN_SSID, WLAN_PASS, WLAN_KANAL);
  sntp_set_time_sync_notification_cb(ntpCallback);
  configTzTime(ZEITZONE, NTP_SERVER);   // setzt Zeitzone + startet NTP im Hintergrund
  logZeile("UHR", String("Verbinde mit WLAN \"") + WLAN_SSID + "\" ...");
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
  if (ntpEmpfangen && uhrQuelle != UHR_NTP) {
    uhrQuelle = UHR_NTP;
    tagMerken();
    logZeile("UHR", "NTP-Zeit empfangen");
    bildschirmNeu = true;
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
  static uint32_t letzteMessung = 0;
  if (jetzt - letzteMessung < 100) return;   // 10 Messungen pro Sekunde
  letzteMessung = jetzt;

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
  if (!leergewichtGelernt || kandidat < leergewicht) {
    logZeile("LEER", "Leergewicht gelernt: " + String(kandidat, 0) + " g (Gewicht vor dem Nachfüllen" +
             (leergewichtGelernt ? ", kleiner als bisher " + String(leergewicht, 0) + " g)" : ")"));
    leergewicht = kandidat;
    leergewichtGelernt = true;
    leergewichtSpeichern();
  }
}

void leergewichtUntergrenze(float w) {
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
void trinkenAuswerten() {
  if (flascheSteht && gewicht < FLASCHE_WEG_G) {
    flascheSteht = false;
    padLeerSeit = millis();
    logZeile("WAAGE", "Flasche abgehoben – Änderungen werden ignoriert");
    return;
  }
  if (!gewichtRuhig) return;

  bool geradeAbgestellt = false;
  if (!flascheSteht && gewicht >= FLASCHE_DA_G) {
    flascheSteht = true;
    geradeAbgestellt = true;
    logZeile("WAAGE", "Flasche steht (" + String(gewicht, 0) + " g)");
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
    logZeile("TRINKEN", "+" + String(ml) + " ml getrunken (" + String(referenzGewicht, 0) + " g -> " +
                        String(gewicht, 0) + " g), heute " + String(getrunkenHeute) + " ml");
    referenzGewicht = gewicht;
    leergewichtUntergrenze(gewicht);
  } else if (-differenz >= MIN_NACHFUELL_G) {
    logZeile("TRINKEN", "Nachgefüllt (+" + String(-differenz, 0) + " g) – zählt nicht als Trinken");
    leergewichtKandidat(referenzGewicht);   // Regel 1
    referenzGewicht = gewicht;
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

void akkuLesen() {
  static uint32_t letzte = 0;
  if (millis() - letzte < 500) return;
  letzte = millis();
  int adc = analogRead(PIN_AKKU_ADC);   // 0..4095
  // SIMULATION: Poti 0..4095 direkt als 3,0..4,2 V.
  // ECHT: Spannungsteiler 100k/100k, akkuVolt = analogReadMilliVolts(PIN_AKKU_ADC) * 2 / 1000.0;
  akkuVolt = AKKU_LEER_V + (AKKU_VOLL_V - AKKU_LEER_V) * adc / 4095.0f;
  akkuProzent = constrain((int)lroundf((akkuVolt - AKKU_LEER_V) * 100.0f / (AKKU_VOLL_V - AKKU_LEER_V)), 0, 100);

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
  if (akkuStufe == 1) akkuHinweisBisMs = millis() + AKKU_HINWEIS_MS;
  logZeile("AKKU", String(akkuStufe == 2 ? "KRITISCH" : "NIEDRIG") + ": " + String(akkuVolt, 2) + " V (" +
                   String(akkuProzent) + " %) -> LEDs " + String(blinkAnzahl) + "x rot");
}

// Waage ohne Daten oder Tara falsch (negativ)
bool waageFehler() {
  return !waageOk || gewicht < NEGATIV_FEHLER_G;
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

  switch (neu) {   // beim BETRETEN
    case NAESSE_SPERRE:
      digitalWrite(PIN_LAST, LOW);   // MOSFET aus -> Strom aus
      logZeile("LAST", "AUS (WASSER ERKANNT · STROM AUS)");
      telegramSenden("HydroDesk: WASSER ERKANNT – Strom wurde abgeschaltet!");
      break;
    case ERINNERUNG:
      telegramSenden("HydroDesk: Zeit zu trinken! Heute " + String(getrunkenHeute) + " von " +
                     String(tagesziel) + " ml");
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
    digitalWrite(PIN_LAST, HIGH);
    logZeile("LAST", "wieder AN (5 s trocken)");
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
  } else if (millis() - letzterSchluckMs >= ERINNERUNG_MS) {
    zustandWechseln(ERINNERUNG, String(ERINNERUNG_MS / 1000) + " s nichts getrunken");
  } else if (flascheSteht) {
    zustandWechseln(MESSEN, zustand == ERINNERUNG ? "getrunken"
                          : (zustand == ZIEL_ERREICHT ? "Ziel höher / neuer Tag" : "Flasche steht"));
  } else {
    zustandWechseln(IDLE, "keine Flasche auf dem Pad");
  }
}

// ============================================================================
//  TOUCH (versteckt): 3 s Langdruck -> Kalibrierung; Tasten nur dort
// ============================================================================
void touchAuswerten() {
  int16_t x = 0, y = 0;
  bool gedrueckt = readTouch(x, y);
  bool neu = gedrueckt && !touchGehalten;
  if (neu) {
    touchStartMs = millis();
    langdruckErledigt = false;
    logZeile("TOUCH", "x=" + String(x) + " y=" + String(y));
  }
  touchGehalten = gedrueckt;

  if (zustand == NAESSE_SPERRE) return;           // Bedienung gesperrt

  if (zustand == KALIBRIERUNG) {
    if (!neu) return;
    if (getroffen(TASTE_KAL_TARA, x, y)) {
      taraSetzen();
      kalSchritt = 1;
      bildschirmNeu = true;
    } else if (getroffen(TASTE_KAL_GEWICHT, x, y) && kalSchritt >= 1) {
      float f = (rohMittel - tara) / KALIBRIER_GEWICHT_G;
      if (fabsf(f) > 0.01f) {
        faktor = f;
        speicher.putFloat("faktor", faktor);
        kalSchritt = 2;
        logZeile("KALIB", "neuer Faktor " + String(faktor, 4) + " Rohwert/g");
      } else {
        logZeile("KALIB", "kein Gewicht erkannt – Faktor nicht geändert");
      }
      bildschirmNeu = true;
    } else if (getroffen(TASTE_KAL_FERTIG, x, y)) {
      zustandWechseln(IDLE, "Kalibrierung beendet");
    }
    return;
  }

  // Normalbetrieb: keine Tasten, nur der versteckte Langdruck
  if (gedrueckt && !langdruckErledigt && millis() - touchStartMs >= LANGDRUCK_MS) {
    langdruckErledigt = true;
    zustandWechseln(KALIBRIERUNG, "3 s Langdruck");
  }
}

// ============================================================================
//  LED-STREIFEN: aus im Normalbetrieb, nur bei Ereignissen, Dauerlicht
//  (einzige Ausnahme: Akku-Warnung 2x bzw. 4x rot blitzen, dann aus)
//  Priorität: bernstein (Wasser) > rot (Akku-Blinken 2x/4x bzw. Fehler 5 s)
//             > blau (Erinnerung) > grün (Ziel erreicht, 10 s)
// ============================================================================
void ledsAktualisieren() {
  static uint32_t letzteFarbe = 0xFFFFFFFF;
  uint32_t jetzt = millis();
  uint32_t farbe = 0;   // aus
  // Akku-Blinkmuster: läuft im Hintergrund weiter, auch wenn bernstein Vorrang hat
  bool blinkAn = false;
  if (blinkAnzahl > 0) {
    uint32_t periode = AKKU_BLINK_AN_MS + AKKU_BLINK_AUS_MS;
    uint32_t t = jetzt - blinkStartMs;
    if (t >= periode * blinkAnzahl) blinkAnzahl = 0;   // fertig -> wieder aus
    else blinkAn = (t % periode) < AKKU_BLINK_AN_MS;
  }
  bool blinkLaeuft = blinkAnzahl > 0;

  if (zustand == NAESSE_SPERRE)                 farbe = leds.Color(255, 110, 0);  // bernstein
  else if (blinkLaeuft)                         farbe = blinkAn ? leds.Color(255, 0, 0) : 0; // Akku: rot / Pause
  else if ((int32_t)(rotBisMs - jetzt) > 0)     farbe = leds.Color(255, 0, 0);    // rot (Fehler)
  else if (zustand == ERINNERUNG)               farbe = leds.Color(0, 0, 255);    // blau
  else if ((int32_t)(gruenBisMs - jetzt) > 0)   farbe = leds.Color(0, 255, 0);    // grün

  if (farbe == letzteFarbe) return;   // nur senden, wenn sich etwas ändert
  letzteFarbe = farbe;
  for (uint8_t i = 0; i < LED_ANZAHL; i++) leds.setPixelColor(i, farbe);
  leds.show();
  logZeile("LED", farbe == 0 ? "aus" : "Farbe 0x" + String(farbe, HEX));
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

  // --- Oben rechts: Akku-Symbol + Prozent
  if (geaendert(B_AKKU, String(akkuProzent) + "/" + String(akkuStufe))) {
    // grün = ok, orange = unter 20 %, rot = unter 10 %
    uint16_t f = akkuStufe == 2 ? ROT : (akkuStufe == 1 ? ORANGE : GRUEN);
    tft.fillRect(176, 0, 64, 50, SCHWARZ);
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

  // --- Unten: Flasche, Leergewicht, zuletzt getrunken, nächste Erinnerung
  String fl = flascheSteht ? "Flasche: " + mitPunkt(flascheninhaltMl()) + " ml" : "Keine Flasche";
  if (geaendert(B_FLASCHE, fl)) {
    tft.fillRect(0, 204, BREITE, 22, SCHWARZ);
    tft.drawFastHLine(8, 203, BREITE - 16, DUNKELGRAU);
    text(10, 210, fl, 2, flascheSteht ? CYAN : GRAU, SCHWARZ);
  }
  String leer = "Leergewicht " + String((int)lroundf(leergewicht)) + " g " +
                (leergewichtGelernt ? "(gelernt)" : "(Schätzwert)");
  if (geaendert(B_LEER, leer)) {
    tft.fillRect(0, 230, BREITE, 10, SCHWARZ);
    text(10, 231, leer, 1, GRAU, SCHWARZ);
  }

  uint32_t seit = (millis() - letzterSchluckMs) / 1000;
  String zl = heuteGetrunken ? "Zuletzt getrunken: vor " + dauerText(seit) : "Heute noch nichts getrunken";
  if (geaendert(B_ZULETZT, zl)) {
    tft.fillRect(0, 246, BREITE, 10, SCHWARZ);
    text(10, 247, zl, 1, WEISS, SCHWARZ);
  }

  String ne;
  if (zielErreicht)               ne = "Ziel erreicht - keine Erinnerung";
  else if (zustand == ERINNERUNG) ne = "Erinnerung aktiv!";
  else {
    uint32_t rest = (ERINNERUNG_MS - min(ERINNERUNG_MS, millis() - letzterSchluckMs)) / 1000;
    if (rest < 120 || !uhrOk) {
      ne = "Nächste Erinnerung: in " + dauerText(rest);
    } else {
      time_t t = time(nullptr) + rest;
      struct tm e;
      localtime_r(&t, &e);
      ne = "Nächste Erinnerung: " + zweistellig(e.tm_hour) + ":" + zweistellig(e.tm_min);
    }
  }
  if (geaendert(B_NAECHSTE, ne)) {
    tft.fillRect(0, 262, BREITE, 10, SCHWARZ);
    text(10, 263, ne, 1, WEISS, SCHWARZ);
  }

  // --- Ganz unten: Statusfeld (Erinnerung / Warnung / Service-Hinweis)
  String st;
  uint16_t sf = SCHWARZ, sc = GRAU;
  if (touchGehalten && !langdruckErledigt && millis() - touchStartMs >= 1000) {
    st = "Service-Modus: noch " + String((LANGDRUCK_MS - min(LANGDRUCK_MS, millis() - touchStartMs) + 999) / 1000) + " s halten";
    sf = DUNKELGRAU; sc = WEISS;
  } else if (akkuStufe == 2) {
    st = "Bitte laden";                    sf = ROT;       sc = WEISS;   // bleibt, bis > 12 %
  } else if (!waageOk) {
    st = "Fehler: Waage antwortet nicht";  sf = DUNKELROT; sc = WEISS;
  } else if (gewicht < NEGATIV_FEHLER_G) {
    st = "Gewicht negativ: Kalibrierung!"; sf = DUNKELROT; sc = WEISS;
  } else if (zustand == ERINNERUNG) {
    st = "Zeit zu trinken!";               sf = BLAU;      sc = WEISS;
  } else if (akkuStufe == 1 && (int32_t)(akkuHinweisBisMs - millis()) > 0) {
    st = "Akku unter 20 %";                sf = ORANGE;    sc = SCHWARZ; // 5 s, dann normal
  } else {
    st = String(zustandName(zustand)) + "  |  WLAN " + (wlanVerbunden ? "ok" : "-") + "  |  " +
         (uhrQuelle == UHR_NTP ? "NTP" : (uhrQuelle == UHR_ERSATZ ? "Ersatzuhr" : "keine Zeit"));
  }
  if (geaendert(B_STATUS, st + String(sf))) {
    tft.fillRect(0, 282, BREITE, 38, SCHWARZ);
    bool gross = textBreite(st, 2) <= 224;
    if (sf != SCHWARZ) tft.fillRoundRect(6, 284, 228, 32, 6, sf);
    textMitte(6, 228, gross ? 293 : 297, st, gross ? 2 : 1, sc, sf);
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
    text(6, 7, "Service: Waage", 2, WEISS, DUNKELBLAU);
    text(8, 36,  "1. Alles vom Pad nehmen,", 1, WEISS, SCHWARZ);
    text(8, 48,  "   dann Taste 1 drücken.", 1, WEISS, SCHWARZ);
    text(8, 64,  "2. Genau 500 g auflegen", 1, WEISS, SCHWARZ);
    text(8, 76,  "   (Wokwi: Regler 0.5 kg),", 1, WEISS, SCHWARZ);
    text(8, 88,  "   dann Taste 2 drücken.", 1, WEISS, SCHWARZ);
    text(8, 104, "In Wokwi ist das NICHT nötig.", 1, GRAU, SCHWARZ);
    tasteZeichnen(TASTE_KAL_TARA, kalSchritt >= 1 ? DUNKELGRUEN : DUNKELBLAU, WEISS);
    tasteZeichnen(TASTE_KAL_GEWICHT, kalSchritt >= 2 ? DUNKELGRUEN : (kalSchritt >= 1 ? DUNKELBLAU : DUNKELGRAU), WEISS);
    tasteZeichnen(TASTE_KAL_FERTIG, DUNKELGRAU, WEISS);
  }
  String werte = String((long)rohMittel) + "|" + String((int)lroundf(gewicht)) + "|" + String(faktor, 4);
  if (geaendert(B_STATUS, werte)) {
    tft.fillRect(0, 122, BREITE, 64, SCHWARZ);
    text(8, 126, "Rohwert: " + String((long)rohMittel), 2, CYAN, SCHWARZ);
    text(8, 148, "Gewicht: " + String((int)lroundf(gewicht)) + " g", 2, WEISS, SCHWARZ);
    text(8, 170, "Faktor:  " + String(faktor, 4) + " /g", 1, GRAU, SCHWARZ);
  }
}

void drawUI() {
  static uint32_t letzte = 0;
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
}

void statusAusgeben() {
  struct tm lt;
  String uhr = zeitHolen(lt) ? zweistellig(lt.tm_mday) + "." + zweistellig(lt.tm_mon + 1) + ". " +
                               zweistellig(lt.tm_hour) + ":" + zweistellig(lt.tm_min)
                             : String("keine");
  logZeile("STATUS", String("Zustand=") + zustandName(zustand) +
           " | heute=" + String(getrunkenHeute) + "/" + String(tagesziel) + " ml" +
           " | Profil=" + String(profilKg, 1) + " kg/" + String(profilCm) + " cm" +
           " | Gewicht=" + String((int)lroundf(gewicht)) + " g" + (gewichtRuhig ? " (ruhig)" : " (unruhig)") +
           " | Flasche=" + String(flascheninhaltMl()) + " ml, leer=" + String(leergewicht, 0) + " g" +
           (leergewichtGelernt ? " (gelernt)" : " (Schätzwert)") +
           " | Akku=" + String(akkuVolt, 2) + " V, " + String(akkuProzent) + " %" +
           (akkuStufe == 2 ? " (unter 10 %)" : (akkuStufe == 1 ? " (unter 20 %)" : "")) +
           " | nass=" + String(nass ? "ja" : "nein") +
           " | Last=" + String(digitalRead(PIN_LAST) ? "AN" : "AUS") +
           " | Uhr=" + uhr + (uhrQuelle == UHR_NTP ? " (NTP)" : (uhrQuelle == UHR_ERSATZ ? " (Ersatz)" : "")));
}

void serielleBefehle() {
  static String zeile;
  while (Serial.available()) {
    char c = (char)Serial.read();
    if (c == '\r') continue;
    if (c != '\n') { if (zeile.length() < 40) zeile += c; continue; }
    zeile.trim();
    zeile.toLowerCase();
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
    } else if (zeile.length() > 0) {
      hilfeAusgeben();
    }
    zeile = "";
  }
}

// ============================================================================
//  SETUP + LOOP
// ============================================================================
void setup() {
  Serial.begin(115200);
  delay(200);
  Serial.println();
  Serial.println(F("=== HydroDesk Base – Wokwi-Simulation (V2) ==="));

  pinMode(PIN_NAESSE, INPUT_PULLUP);
  pinMode(PIN_LAST, OUTPUT);
  digitalWrite(PIN_LAST, HIGH);          // Last an
  pinMode(PIN_AKKU_ADC, INPUT);

  leds.begin();
  leds.setBrightness(LED_HELLIGKEIT);
  leds.clear();
  leds.show();                           // LEDs im Normalbetrieb AUS

  speicher.begin("hydrodesk", false);
  faktor             = speicher.getFloat("faktor", WOKWI_FAKTOR);
  profilKg           = speicher.getFloat("kg", KOERPERGEWICHT_KG);
  profilCm           = speicher.getInt("cm", KOERPERGROESSE_CM);
  leergewicht        = speicher.getFloat("leer", LEERGEWICHT_START_G);
  leergewichtGelernt = speicher.getBool("leerOk", false);
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
           (leergewichtGelernt ? "(gelernt)" : "(Startwert, wird beim Nachfüllen gelernt)"));

  uhrStarten();
  letzterSchluckMs = millis();
  naesseLesen();
  logZeile("SYSTEM", "Erinnerung nach " + String(ERINNERUNG_MS / 1000) + " s ohne Trinken");
  logZeile("ZUSTAND", "Start in IDLE");
  hilfeAusgeben();
}

void loop() {
  naesseLesen();          // 1. Sicherheit zuerst
  akkuLesen();
  waageLesen();
  uhrVerwalten();
  touchAuswerten();       // 2. versteckte Bedienung
  zustandAktualisieren(); // 3. Zustandsautomat
  ledsAktualisieren();    // 4. Ausgaben
  drawUI();
  serielleBefehle();
  delay(5);
}
