/*
 * ============================================================================
 *  HydroDesk Base – Wokwi-Simulation (ESP32, Arduino)
 * ============================================================================
 *  Schulprojekt FI-AE: Trink-Tracker für den Schreibtisch.
 *  Eine Flasche steht auf einem Pad über einer Wägezelle (HX711). Das Display
 *  zeigt, wie viel heute getrunken wurde. Ein LED-Streifen (WS2812) zeigt den
 *  Zustand farbig an. Ein Nässe-Sensor schaltet bei Wasser die Last ab.
 *
 *  Simulation (Wokwi)                      | Echte Hardware
 *  ----------------------------------------+---------------------------------
 *  ILI9341 + kapazitiver Touch FT6206 (I2C)| CYD ESP32-2432S028R:
 *                                          | ILI9341 + resistiver Touch XPT2046
 *  HX711-Schieberegler (0–5 kg)            | HX711 + 5-kg-Wägezelle
 *  Schiebeschalter "NÄSSE"                 | LM393-Regensensor, Ausgang DO
 *  Potentiometer "AKKU"                    | Akku über Spannungsteiler am ADC
 *  LED "LAST"                              | MOSFET, der die Last schaltet
 *  Telegram: nur Serial-Ausgabe (Stub)     | Telegram-Bot über WLAN
 *
 *  Bedienung in Wokwi: siehe README.md
 *  Serieller Monitor (115200 Baud): Befehle "hilfe", "status", "reset"
 * ============================================================================
 */

// ----------------------------------------------------------------------------
//  HARDWARE-AUSWAHL
//  0 = Wokwi-Simulation (ILI9341 + FT6206, Adafruit-Bibliotheken)  <- Standard
//  1 = echtes CYD ESP32-2432S028R (TFT_eSPI + XPT2046_Touchscreen)
//      -> siehe README, Abschnitt "Umstieg auf das CYD"
// ----------------------------------------------------------------------------
#ifndef HYDRO_CYD
  #define HYDRO_CYD 0
#endif

#include <Arduino.h>
#include <SPI.h>
#include <Preferences.h>        // Einstellungen dauerhaft im Flash (NVS) speichern
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
const uint32_t ERINNERUNG_MS        = 30UL * 1000UL; // Demo: 30 s (echt z. B. 45 min = 45UL*60UL*1000UL)
const int      ZIEL_START_ML        = 2000;          // Tagesziel beim ersten Start
const int      ZIEL_SCHRITT_ML      = 250;           // Schrittweite der +/- Tasten
const int      ZIEL_MIN_ML          = 500;
const int      ZIEL_MAX_ML          = 5000;

// Waage (1 g Wasser ~ 1 ml)
const float    WOKWI_FAKTOR         = 0.42f;  // Rohwert pro Gramm im Wokwi-HX711 "5kg" (5 kg = 2100)
const float    KALIBRIER_GEWICHT_G  = 500.0f; // Referenzgewicht für die Kalibrierung
const float    FLASCHE_DA_G         = 40.0f;  // ab hier gilt "Flasche steht auf dem Pad"
const float    FLASCHE_WEG_G        = 25.0f;  // darunter gilt "Flasche abgehoben" (Hysterese)
const float    STABIL_TOLERANZ_G    = 6.0f;   // so viel darf das Gewicht schwanken und gilt trotzdem als ruhig
const uint32_t STABIL_MS            = 1500;   // so lange muss das Gewicht ruhig sein
const float    MIN_SCHLUCK_G        = 15.0f;  // kleinere Abnahmen werden ignoriert (Rauschen)
const float    MIN_NACHFUELL_G      = 20.0f;  // ab dieser Zunahme gilt "nachgefüllt"
const float    NEGATIV_FEHLER_G     = -30.0f; // deutlich negatives Gewicht = Tara falsch

// Akku (in Wokwi: Potentiometer). Simulation: 0..4095 -> 3,0..4,2 V
const float    AKKU_LEER_V          = 3.0f;
const float    AKKU_VOLL_V          = 4.2f;
const float    AKKU_NIEDRIG_V       = 3.4f;   // darunter: Fehler/Akku niedrig (rot)
const float    AKKU_OK_V            = 3.5f;   // darüber wieder ok (Hysterese)

// LED-Streifen
const uint8_t  LED_ANZAHL           = 10;
const uint8_t  LED_HELLIGKEIT       = 80;     // 0..255

// ============================================================================
//  PINS  (Tabelle mit CYD-Vorschlag: README.md)
// ============================================================================
// Display ILI9341 (SPI, gleiche Pins wie das Display im CYD)
const int PIN_TFT_SCK   = 14;
const int PIN_TFT_MISO  = 12;
const int PIN_TFT_MOSI  = 13;
const int PIN_TFT_CS    = 15;
const int PIN_TFT_DC    = 2;
const int PIN_TFT_RST   = 4;   // CYD: RST hängt an EN -> dort -1
const int PIN_TFT_LED   = 21;  // Hintergrundbeleuchtung (CYD: GPIO21)
// Touch (nur Wokwi): FT6206 über I2C
const int PIN_TOUCH_SDA = 32;
const int PIN_TOUCH_SCL = 33;
// Peripherie (in Wokwi und am CYD gleich)
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
 *  IDLE           Bereit, aber keine Flasche auf dem Pad (oder gerade
 *                 abgehoben). Gewichtsänderungen werden ignoriert.
 *  MESSEN         Flasche steht auf dem Pad. Das Gewicht wird überwacht.
 *                 Wird die Flasche nach dem Abheben leichter zurückgestellt
 *                 und ist das Gewicht wieder ruhig, wird die Differenz als
 *                 "getrunken" gezählt. Wird sie schwerer, war es Nachfüllen
 *                 (zählt NICHT negativ).
 *  ERINNERUNG     Seit ERINNERUNG_MS wurde nichts getrunken und das Ziel ist
 *                 noch nicht erreicht. LEDs blau, Hinweis auf dem Display.
 *                 Wird weiter gemessen; nach dem nächsten Schluck -> MESSEN.
 *  ZIEL_ERREICHT  Tagesziel erreicht. LEDs grün, keine Erinnerungen mehr.
 *                 Es wird weiter gezählt.
 *  NAESSE_SPERRE  Der Nässe-Sensor meldet Wasser: Last sofort AUS, LEDs
 *                 bernstein, rote Vollbild-Warnung, Bedienung gesperrt.
 *                 Verlassen NUR, wenn der Sensor wieder trocken ist UND
 *                 jemand "Quittieren" drückt.
 *  KALIBRIERUNG   Waage einstellen: Pad leer -> Tara, dann 500 g auflegen
 *                 -> Faktor berechnen. Messung pausiert.
 *
 *  Übergänge (Priorität von oben nach unten):
 *    jeder Zustand  --Wasser erkannt-------------------> NAESSE_SPERRE
 *    NAESSE_SPERRE  --trocken + "Quittieren"-----------> IDLE
 *    IDLE/MESSEN/.. --Taste "Kal."---------------------> KALIBRIERUNG
 *    KALIBRIERUNG   --Taste "Fertig"-------------------> IDLE
 *    sonst wird der passende Zustand jedes Mal neu bestimmt:
 *        getrunken >= Ziel            -> ZIEL_ERREICHT
 *        Zeit seit letztem Schluck >= ERINNERUNG_MS -> ERINNERUNG
 *        Flasche steht               -> MESSEN
 *        sonst                       -> IDLE
 *
 *  "Fehler / Akku niedrig" ist KEIN eigener Zustand, sondern eine
 *  Zusatzanzeige (LEDs rot, Hinweis), weil das Gerät trotzdem weiter misst.
 */
enum Zustand : uint8_t {
  IDLE,
  MESSEN,
  ERINNERUNG,
  ZIEL_ERREICHT,
  NAESSE_SPERRE,
  KALIBRIERUNG
};

// ----------------------------------------------------------------------------
//  Weitere Datentypen (stehen hier oben, damit die Arduino-IDE sie kennt,
//  bevor die erste Funktion kommt)
// ----------------------------------------------------------------------------
// Eine Taste auf dem Touch-Display: Position, Größe, Beschriftung
struct Taste {
  int16_t x, y, w, h;
  const char* beschriftung;
};
// Bildschirm-Bereiche, die einzeln neu gezeichnet werden
enum Bereich : uint8_t { B_KOPF, B_STATUS, B_MENGE, B_BALKEN, B_INFO, B_HINWEIS, B_ZIEL, B_TASTEN, B_ANZAHL };

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
uint32_t zustandSeit      = 0;

// Waage
float    tara             = 0;              // Rohwert bei leerem Pad
float    faktor           = WOKWI_FAKTOR;   // Rohwert pro Gramm
float    rohMittel        = 0;              // gleitender Mittelwert der Rohwerte
float    gewicht          = 0;              // aktuelles Gewicht in g
bool     waageOk          = false;
uint32_t letzteWaageMs    = 0;
float    ruheStartGewicht = 0;
uint32_t ruheSeit         = 0;
bool     gewichtRuhig     = false;
bool     flascheSteht     = false;
bool     referenzGueltig  = false;
float    referenzGewicht  = 0;              // letztes ruhiges Gewicht mit Flasche

// Trinken
int      getrunkenHeute   = 0;              // ml
int      tagesziel        = ZIEL_START_ML;  // ml
int      flascheMl        = 500;            // gewählte Flaschengröße
float    vollGewicht      = 0;              // gespeichertes Gewicht der vollen Flasche (0 = unbekannt)
uint32_t letzterSchluckMs = 0;
int      letzterSchluckMl = 0;

// Sensoren
bool     nass             = false;
bool     akkuNiedrig      = false;
float    akkuVolt         = 4.2f;
int      akkuProzent      = 100;

// Anzeige
String   hinweisText      = "";            // kurzer Hinweis nach Tastendruck
uint32_t hinweisBisMs     = 0;
bool     bildschirmNeu    = true;          // true = komplett neu zeichnen
uint8_t  kalSchritt       = 0;             // 0 = Tara fehlt, 1 = Gewicht fehlt, 2 = fertig

// ============================================================================
//  HILFSFUNKTIONEN: LOG + TELEGRAM-STUB
// ============================================================================
// Zeitstempel mm:ss seit Start für den Seriellen Monitor
String zeitstempel() {
  uint32_t s = millis() / 1000;
  char buf[12];
  snprintf(buf, sizeof(buf), "%02lu:%02lu", (unsigned long)(s / 60), (unsigned long)(s % 60));
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

// Telegram wird NICHT simuliert. Später hier den Bot-Aufruf einbauen
// (WLAN + z. B. Bibliothek "UniversalTelegramBot").
void telegramSenden(const String& nachricht) {
  logZeile("TELEGRAM-STUB", "würde senden: \"" + nachricht + "\"");
}

// ============================================================================
//  HARDWARE-ABSTRAKTION DISPLAY + TOUCH
//  Nur dieser Block unterscheidet sich zwischen Wokwi und CYD.
//  Der Rest des Programms benutzt nur: anzeigeInit(), readTouch(), tft.xxx()
//  mit Funktionen, die Adafruit_GFX UND TFT_eSPI beide kennen
//  (fillScreen, fillRect, drawRect, fillRoundRect, drawRoundRect,
//   setCursor, setTextSize, setTextColor, print).
// ============================================================================
const int16_t BREITE = 240;   // Hochformat (Display links im Gehäuse)
const int16_t HOEHE  = 320;

#if HYDRO_CYD
  TFT_eSPI tft;
  SPIClass touchSpi(VSPI);
  // CYD-Touch: CLK 25, MISO 39, MOSI 32, CS 33, IRQ 36
  XPT2046_Touchscreen touch(33, 36);
  // Rohwerte des resistiven Touch -> Pixel. MUSS am echten Gerät kalibriert
  // werden (Ecken antippen, Rohwerte im Seriellen Monitor ablesen).
  const int TOUCH_X_MIN = 200, TOUCH_X_MAX = 3700;
  const int TOUCH_Y_MIN = 240, TOUCH_Y_MAX = 3800;
#else
  const bool      TOUCH_SPIEGELN = true;
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
  touchBereit = touch.begin(40);     // 40 = Empfindlichkeit
#endif
  tft.fillScreen(0x0000);
  logZeile("SYSTEM", touchBereit ? "Display + Touch bereit" : "Display bereit, Touch NICHT gefunden");
}

// Liefert true bei einer NEUEN Berührung (Finger aufgesetzt) und schreibt die
// Position in Display-Pixeln (0..239, 0..319) nach x/y.
// Gedrückt halten löst nur EINMAL aus.
bool readTouch(int16_t& x, int16_t& y) {
  static bool warGedrueckt = false;
  if (!touchBereit) return false;
#if HYDRO_CYD
  bool gedrueckt = touch.touched();
  if (gedrueckt && !warGedrueckt) {
    TS_Point p = touch.getPoint();
    x = constrain(map(p.x, TOUCH_X_MIN, TOUCH_X_MAX, 0, BREITE - 1), 0, BREITE - 1);
    y = constrain(map(p.y, TOUCH_Y_MIN, TOUCH_Y_MAX, 0, HOEHE - 1), 0, HOEHE - 1);
  }
#else
  bool gedrueckt = touch.touched() > 0;
  if (gedrueckt && !warGedrueckt) {
    TS_Point p = touch.getPoint();
    // Der FT6206 zählt gespiegelt zur Display-Rotation 0 (Ursprung unten rechts).
    // Falls in eurer Wokwi-Version die falsche Taste reagiert: TOUCH_SPIEGELN auf false.
    x = TOUCH_SPIEGELN ? BREITE - 1 - p.x : p.x;
    y = TOUCH_SPIEGELN ? HOEHE - 1 - p.y : p.y;
    x = constrain(x, 0, BREITE - 1);
    y = constrain(y, 0, HOEHE - 1);
  }
#endif
  bool neu = gedrueckt && !warGedrueckt;
  warGedrueckt = gedrueckt;
  if (neu) logZeile("TOUCH", "x=" + String(x) + " y=" + String(y));
  return neu;
}

// ============================================================================
//  ZEICHEN-HILFEN (unabhängig von der Hardware)
// ============================================================================
// Farben im RGB565-Format (funktionieren mit beiden Bibliotheken)
const uint16_t SCHWARZ   = 0x0000;
const uint16_t WEISS     = 0xFFFF;
const uint16_t GRAU      = 0x8410;
const uint16_t DUNKELGRAU= 0x2945;
const uint16_t ROT       = 0xF800;
const uint16_t GRUEN     = 0x07E0;
const uint16_t DUNKELGRUEN = 0x03E0;
const uint16_t BLAU      = 0x041F;
const uint16_t DUNKELBLAU= 0x0010;
const uint16_t CYAN      = 0x07FF;
const uint16_t GELB      = 0xFFE0;
const uint16_t ORANGE    = 0xFD20;

// Wandelt deutsche Umlaute (UTF-8 im Quelltext) in die Zeichentabelle des
// Display-Fonts (CP437) um, damit "ä", "ö", "ü" richtig erscheinen.
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

// Text an Position (x,y). Größe 1 = 6x8 Pixel pro Zeichen.
void text(int16_t x, int16_t y, const String& s, uint8_t groesse, uint16_t farbe, uint16_t hinter) {
  tft.setTextSize(groesse);
  tft.setTextColor(farbe, hinter);
  tft.setCursor(x, y);
  tft.print(fuerDisplay(s));
}

// Text waagerecht zentriert zwischen x0 und x0+breite
void textMitte(int16_t x0, int16_t breite, int16_t y, const String& s, uint8_t groesse,
               uint16_t farbe, uint16_t hinter) {
  int16_t w = fuerDisplay(s).length() * 6 * groesse;
  text(x0 + (breite - w) / 2, y, s, groesse, farbe, hinter);
}

// ----------------------------------------------------------------------------
//  Tasten (Buttons) auf dem Touch-Display
// ----------------------------------------------------------------------------
// (Typ "Taste" steht oben bei den Datentypen)

enum TastenId : uint8_t {
  T_LEER, T_300, T_500, T_750, T_1000, T_1500, T_VOLL, T_KAL,
  T_ZIEL_MINUS, T_ZIEL_PLUS,
  T_ANZAHL_HAUPT
};

const Taste HAUPT_TASTEN[T_ANZAHL_HAUPT] = {
  {  4, 230, 56, 42, "Leer" }, { 63, 230, 56, 42, "300" }, { 122, 230, 56, 42, "500" }, { 181, 230, 56, 42, "750" },
  {  4, 276, 56, 42, "1000" }, { 63, 276, 56, 42, "1500"}, { 122, 276, 56, 42, "Voll"}, { 181, 276, 56, 42, "Kal." },
  {  6, 186, 54, 36, "-" },    {180, 186, 54, 36, "+" }
};
const int PRESET_ML[T_ANZAHL_HAUPT] = { 0, 300, 500, 750, 1000, 1500, 0, 0, 0, 0 };

const Taste TASTE_QUITTIEREN = { 30, 246, 180, 56, "Quittieren" };
const Taste TASTE_KAL_TARA   = { 10, 196, 220, 36, "1. Pad leer: Tara" };
const Taste TASTE_KAL_GEWICHT= { 10, 238, 220, 36, "2. 500 g liegt: OK" };
const Taste TASTE_KAL_FERTIG = { 10, 280, 220, 36, "Fertig" };

bool getroffen(const Taste& t, int16_t x, int16_t y) {
  return x >= t.x && x < t.x + t.w && y >= t.y && y < t.y + t.h;
}

void tasteZeichnen(const Taste& t, uint16_t fuellung, uint16_t schrift, uint8_t groesse = 2) {
  tft.fillRoundRect(t.x, t.y, t.w, t.h, 6, fuellung);
  tft.drawRoundRect(t.x, t.y, t.w, t.h, 6, WEISS);
  textMitte(t.x, t.w, t.y + (t.h - 8 * groesse) / 2, t.beschriftung, groesse, schrift, fuellung);
}

// ============================================================================
//  WAAGE
// ============================================================================
void waageInit() {
  waage.begin(PIN_HX711_DT, PIN_HX711_SCK);
  // Erste Werte abwarten (max. 1 s), damit die Tara stimmt
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

// Tara = aktueller Rohwert bei LEEREM Pad
void taraSetzen() {
  tara = rohMittel;
  referenzGueltig = false;
  speicher.putFloat("tara", tara);
  logZeile("WAAGE", "Tara gesetzt (Rohwert " + String(tara, 1) + ")");
}

// Liest den HX711 (nicht blockierend), filtert und berechnet Gewicht + Ruhe.
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
  if (jetzt - letzteMessung < 100) return;   // 10 Messungen pro Sekunde reichen
  letzteMessung = jetzt;

  long roh = (long)waage.read();
  if (!waageOk) logZeile("WAAGE", "HX711 liefert wieder Daten");
  waageOk = true;
  letzteWaageMs = jetzt;

  // Gleitender Mittelwert über ca. 4 Messungen (glättet Rauschen)
  rohMittel = rohMittel * 0.75f + roh * 0.25f;
  // Bei großen Sprüngen (Flasche abgehoben / abgestellt) sofort übernehmen
  if (fabsf(roh - rohMittel) > 100.0f * faktor) rohMittel = roh;

  gewicht = (rohMittel - tara) / faktor;

  // Ruhig = Gewicht bleibt STABIL_MS lang innerhalb der Toleranz
  if (fabsf(gewicht - ruheStartGewicht) > STABIL_TOLERANZ_G) {
    ruheStartGewicht = gewicht;
    ruheSeit = jetzt;
    gewichtRuhig = false;
  } else if (jetzt - ruheSeit >= STABIL_MS) {
    gewichtRuhig = true;
  }
}

// Wertet das Gewicht aus: Abheben, Abstellen, Trinken, Nachfüllen.
// Wird nur in IDLE / MESSEN / ERINNERUNG / ZIEL_ERREICHT aufgerufen.
void trinkenAuswerten() {
  // Flasche abgehoben? (Hysterese, damit es nicht flackert)
  if (flascheSteht && gewicht < FLASCHE_WEG_G) {
    flascheSteht = false;
    logZeile("WAAGE", "Flasche abgehoben – Änderungen werden ignoriert");
    return;
  }
  // Nur auswerten, wenn das Gewicht ruhig ist
  if (!gewichtRuhig) return;

  if (!flascheSteht && gewicht >= FLASCHE_DA_G) {
    flascheSteht = true;
    logZeile("WAAGE", "Flasche steht (" + String(gewicht, 0) + " g)");
  }
  if (!flascheSteht) return;

  if (!referenzGueltig) {
    referenzGewicht = gewicht;
    referenzGueltig = true;
    logZeile("WAAGE", "Referenz gesetzt: " + String(referenzGewicht, 0) + " g");
    return;
  }

  float differenz = referenzGewicht - gewicht;  // positiv = leichter = getrunken
  if (differenz >= MIN_SCHLUCK_G) {
    int ml = (int)lroundf(differenz);
    getrunkenHeute += ml;
    letzterSchluckMl = ml;
    letzterSchluckMs = millis();
    logZeile("TRINKEN", "+" + String(ml) + " ml getrunken (" + String(referenzGewicht, 0) + " g -> " +
                        String(gewicht, 0) + " g), heute " + String(getrunkenHeute) + " ml");
    referenzGewicht = gewicht;
    hinweisZeigen("+" + String(ml) + " ml, super!");
  } else if (-differenz >= MIN_NACHFUELL_G) {
    logZeile("TRINKEN", "Nachgefüllt (+" + String(-differenz, 0) + " g) – zählt nicht als Trinken");
    referenzGewicht = gewicht;
    hinweisZeigen("Nachgefüllt");
  }
  // kleine Schwankungen: Referenz bleibt, damit kleine Schlucke sich summieren
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
  // Entprellen: 100 ms stabil
  if (roh != nass && millis() - wechselSeit >= 100) {
    nass = roh;
    logZeile("NAESSE", nass ? "Sensor meldet WASSER" : "Sensor wieder trocken");
  }
}

void akkuLesen() {
  static uint32_t letzte = 0;
  if (millis() - letzte < 500) return;
  letzte = millis();
  int adc = analogRead(PIN_AKKU_ADC);   // 0..4095
  // SIMULATION: Poti 0..4095 direkt als 3,0..4,2 V.
  // ECHT: Akku über Spannungsteiler 100k/100k an GPIO35, dann
  //       akkuVolt = analogReadMilliVolts(PIN_AKKU_ADC) * 2 / 1000.0;
  akkuVolt = AKKU_LEER_V + (AKKU_VOLL_V - AKKU_LEER_V) * adc / 4095.0f;
  akkuProzent = constrain((int)lroundf((akkuVolt - AKKU_LEER_V) * 100.0f / (AKKU_VOLL_V - AKKU_LEER_V)), 0, 100);

  if (!akkuNiedrig && akkuVolt < AKKU_NIEDRIG_V) {
    akkuNiedrig = true;
    logZeile("AKKU", "NIEDRIG: " + String(akkuVolt, 2) + " V (" + String(akkuProzent) + " %)");
    telegramSenden("HydroDesk: Akku niedrig (" + String(akkuProzent) + " %)");
  } else if (akkuNiedrig && akkuVolt > AKKU_OK_V) {
    akkuNiedrig = false;
    logZeile("AKKU", "wieder ok: " + String(akkuVolt, 2) + " V (" + String(akkuProzent) + " %)");
  }
}

// Fehleranzeige (rot): Akku niedrig, Waage ohne Daten oder Tara falsch
bool fehlerAktiv() {
  return akkuNiedrig || !waageOk || gewicht < NEGATIV_FEHLER_G;
}

// ============================================================================
//  ZUSTANDSWECHSEL
// ============================================================================
void zustandWechseln(Zustand neu, const String& grund) {
  if (neu == zustand) return;
  logZeile("ZUSTAND", String(zustandName(zustand)) + " -> " + zustandName(neu) + "  (" + grund + ")");
  Zustand alt = zustand;
  zustand = neu;
  zustandSeit = millis();
  bildschirmNeu = true;

  // Aktionen beim BETRETEN eines Zustands
  switch (neu) {
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
      telegramSenden("HydroDesk: Tagesziel erreicht (" + String(getrunkenHeute) + " ml)");
      break;
    case KALIBRIERUNG:
      kalSchritt = 0;
      break;
    default:
      break;
  }
  // Aktionen beim VERLASSEN eines Zustands
  if (alt == NAESSE_SPERRE) {
    digitalWrite(PIN_LAST, HIGH);
    logZeile("LAST", "wieder AN (quittiert)");
  }
  if (alt == NAESSE_SPERRE || alt == KALIBRIERUNG) {
    // Gewicht kann sich verändert haben (Wasser, Kalibriergewicht):
    // neu referenzieren, damit nichts falsch gezählt wird.
    referenzGueltig = false;
    flascheSteht = false;
  }
}

// Bestimmt den "normalen" Zustand neu (siehe Kommentar beim enum)
void zustandAktualisieren() {
  // 1. Höchste Priorität: Wasser
  if (nass && zustand != NAESSE_SPERRE) {
    zustandWechseln(NAESSE_SPERRE, "Nässe-Sensor LOW");
    return;
  }
  // 2. Diese Zustände verlässt man nur per Touch
  if (zustand == NAESSE_SPERRE || zustand == KALIBRIERUNG) return;

  // 3. Messen + Auswerten
  trinkenAuswerten();

  if (getrunkenHeute >= tagesziel) {
    zustandWechseln(ZIEL_ERREICHT, String(getrunkenHeute) + " >= " + String(tagesziel) + " ml");
  } else if (millis() - letzterSchluckMs >= ERINNERUNG_MS) {
    zustandWechseln(ERINNERUNG, String(ERINNERUNG_MS / 1000) + " s nichts getrunken");
  } else if (flascheSteht) {
    zustandWechseln(MESSEN, zustand == ERINNERUNG ? "getrunken"
                          : (zustand == ZIEL_ERREICHT ? "Ziel erhöht" : "Flasche steht"));
  } else {
    zustandWechseln(IDLE, "keine Flasche auf dem Pad");
  }
}

// ============================================================================
//  TOUCH-AKTIONEN
// ============================================================================
void hinweisZeigen(const String& s) {
  hinweisText = s;
  hinweisBisMs = millis() + 3000;
}

void einstellungenSpeichern() {
  speicher.putInt("ziel", tagesziel);
  speicher.putInt("flasche", flascheMl);
  speicher.putFloat("voll", vollGewicht);
}

void touchAuswerten() {
  int16_t x, y;
  if (!readTouch(x, y)) return;

  if (zustand == NAESSE_SPERRE) {
    if (getroffen(TASTE_QUITTIEREN, x, y)) {
      if (nass) {
        logZeile("TOUCH", "Quittieren abgelehnt – Sensor noch nass");
      } else {
        logZeile("TOUCH", "Quittieren");
        zustandWechseln(IDLE, "trocken + quittiert");
      }
    }
    return;   // Bedienung sonst gesperrt
  }

  if (zustand == KALIBRIERUNG) {
    if (getroffen(TASTE_KAL_TARA, x, y)) {
      taraSetzen();
      kalSchritt = 1;
      bildschirmNeu = true;
    } else if (getroffen(TASTE_KAL_GEWICHT, x, y) && kalSchritt >= 1) {
      float neu = (rohMittel - tara) / KALIBRIER_GEWICHT_G;
      if (fabsf(neu) > 0.01f) {
        faktor = neu;
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

  // Hauptbildschirm
  for (uint8_t i = 0; i < T_ANZAHL_HAUPT; i++) {
    if (!getroffen(HAUPT_TASTEN[i], x, y)) continue;
    logZeile("TOUCH", String("Taste \"") + HAUPT_TASTEN[i].beschriftung + "\"");
    switch (i) {
      case T_LEER:
        if (gewicht > 200) {
          hinweisZeigen("Erst Flasche abnehmen!");
        } else {
          taraSetzen();
          flascheSteht = false;
          hinweisZeigen("Tara gesetzt (0 g)");
        }
        break;
      case T_300: case T_500: case T_750: case T_1000: case T_1500:
        flascheMl = PRESET_ML[i];
        vollGewicht = 0;   // neue Flasche -> "Voll" neu speichern
        einstellungenSpeichern();
        logZeile("EINST", "Flaschengröße " + String(flascheMl) + " ml");
        hinweisZeigen("Flasche " + String(flascheMl) + " ml - jetzt Voll");
        break;
      case T_VOLL:
        if (gewicht < FLASCHE_DA_G || !gewichtRuhig) {
          hinweisZeigen("Volle Flasche ruhig abstellen");
        } else {
          vollGewicht = gewicht;
          referenzGewicht = gewicht;
          referenzGueltig = true;
          einstellungenSpeichern();
          logZeile("EINST", "Vollgewicht " + String(vollGewicht, 0) + " g gespeichert");
          hinweisZeigen("Voll: " + String(vollGewicht, 0) + " g");
        }
        break;
      case T_KAL:
        zustandWechseln(KALIBRIERUNG, "Taste Kal.");
        break;
      case T_ZIEL_MINUS:
      case T_ZIEL_PLUS:
        tagesziel += (i == T_ZIEL_PLUS) ? ZIEL_SCHRITT_ML : -ZIEL_SCHRITT_ML;
        tagesziel = constrain(tagesziel, ZIEL_MIN_ML, ZIEL_MAX_ML);
        einstellungenSpeichern();
        logZeile("EINST", "Tagesziel " + String(tagesziel) + " ml");
        break;
    }
    return;
  }
}

// ============================================================================
//  LED-STREIFEN
// ============================================================================
void ledsAktualisieren() {
  static uint32_t letzterRahmen = 0xFFFFFFFF;
  bool blinkAn = (millis() / 500) % 2 == 0;
  uint32_t farbe = 0;
  uint8_t  anzahl = LED_ANZAHL;

  if (zustand == NAESSE_SPERRE) {
    farbe = blinkAn ? leds.Color(255, 110, 0) : leds.Color(80, 35, 0);   // bernstein
  } else if (fehlerAktiv()) {
    farbe = blinkAn ? leds.Color(255, 0, 0) : 0;                         // rot
  } else if (zustand == ERINNERUNG) {
    farbe = blinkAn ? leds.Color(0, 0, 255) : leds.Color(0, 0, 60);      // blau
  } else if (zustand == ZIEL_ERREICHT) {
    farbe = leds.Color(0, 255, 0);                                       // grün
  } else if (zustand == KALIBRIERUNG) {
    farbe = leds.Color(40, 40, 40);
  } else {
    // IDLE / MESSEN: Fortschritt als schwach weiße Balkenanzeige
    farbe = leds.Color(30, 30, 30);
    anzahl = (uint8_t)constrain((long)getrunkenHeute * LED_ANZAHL / max(tagesziel, 1), 0L, (long)LED_ANZAHL);
  }

  uint32_t rahmen = farbe ^ ((uint32_t)anzahl << 24);
  if (rahmen == letzterRahmen) return;   // nur senden, wenn sich etwas ändert
  letzterRahmen = rahmen;
  for (uint8_t i = 0; i < LED_ANZAHL; i++) leds.setPixelColor(i, i < anzahl ? farbe : 0);
  leds.show();
}

// ============================================================================
//  BILDSCHIRME (drawUI)
// ============================================================================
// Jeder Bereich wird nur neu gezeichnet, wenn sich sein Inhalt ändert
// (sonst flackert es). Dafür merken wir uns den zuletzt gezeichneten Text.
// (Typ "Bereich" steht oben bei den Datentypen)
String zuletzt[B_ANZAHL];

bool geaendert(Bereich b, const String& inhalt) {
  if (!bildschirmNeu && zuletzt[b] == inhalt) return false;
  zuletzt[b] = inhalt;
  return true;
}

void hauptbildschirmZeichnen() {
  // Kopfzeile: Name + Akku
  String kopf = String(akkuProzent) + (fehlerAktiv() ? "F" : "");
  if (geaendert(B_KOPF, kopf)) {
    tft.fillRect(0, 0, BREITE, 28, DUNKELBLAU);
    text(6, 7, "HydroDesk", 2, WEISS, DUNKELBLAU);
    uint16_t f = akkuNiedrig ? ROT : (akkuProzent < 50 ? GELB : GRUEN);
    tft.drawRect(172, 7, 34, 14, WEISS);
    tft.fillRect(206, 11, 3, 6, WEISS);
    tft.fillRect(174, 9, 30 * akkuProzent / 100, 10, f);
    text(212, 10, String(akkuProzent), 1, WEISS, DUNKELBLAU);
  }

  // Statuszeile
  String status = String(zustandName(zustand)) + "|" + (flascheSteht ? "1" : "0");
  if (geaendert(B_STATUS, status)) {
    tft.fillRect(0, 30, BREITE, 12, SCHWARZ);
    text(6, 32, String("Status: ") + zustandName(zustand), 1, CYAN, SCHWARZ);
    text(150, 32, flascheSteht ? "Flasche steht" : "keine Flasche", 1, flascheSteht ? GRUEN : GRAU, SCHWARZ);
  }

  // Große Zahl: heute getrunken
  String menge = String(getrunkenHeute) + "|" + String(tagesziel);
  if (geaendert(B_MENGE, menge)) {
    tft.fillRect(0, 44, BREITE, 52, SCHWARZ);
    textMitte(0, BREITE, 50, String(getrunkenHeute) + " ml", 4, WEISS, SCHWARZ);
    textMitte(0, BREITE, 86, "heute getrunken", 1, GRAU, SCHWARZ);
  }

  // Fortschrittsbalken
  int prozent = constrain((long)getrunkenHeute * 100L / max(tagesziel, 1), 0L, 100L);
  String balken = String(prozent);
  if (geaendert(B_BALKEN, balken)) {
    const int16_t bx = 10, by = 100, bw = 220, bh = 22;
    uint16_t f = prozent >= 100 ? GRUEN : BLAU;
    tft.fillRect(bx, by, bw, bh, DUNKELGRAU);
    tft.fillRect(bx, by, bw * prozent / 100, bh, f);
    tft.drawRect(bx, by, bw, bh, WEISS);
    // Text "durchsichtig" (ohne Hintergrund), weil der Balken zweifarbig ist
    tft.setTextSize(2);
    tft.setTextColor(WEISS);          // nur eine Farbe = Hintergrund bleibt sichtbar
    String pt = String(prozent) + " %";
    tft.setCursor(bx + (bw - (int16_t)pt.length() * 12) / 2, by + 4);
    tft.print(pt);
  }

  // Info: Flasche, Gewicht, Füllstand
  String fuell;
  if (vollGewicht > 0 && flascheSteht) {
    float leer = vollGewicht - flascheMl;
    int rest = constrain((int)lroundf(gewicht - leer), 0, flascheMl);
    fuell = "Rest " + String(rest) + " ml (" + String(rest * 100 / flascheMl) + " %)";
  } else if (vollGewicht > 0) {
    fuell = "Flasche abgehoben";
  } else {
    fuell = "Volle Flasche: Taste Voll";
  }
  String info = String(flascheMl) + "|" + String((int)lroundf(gewicht)) + "|" + fuell;
  if (geaendert(B_INFO, info)) {
    tft.fillRect(0, 128, BREITE, 24, SCHWARZ);
    text(10, 130, "Flasche " + String(flascheMl) + " ml  Gewicht " + String((int)lroundf(gewicht)) + " g", 1, WEISS, SCHWARZ);
    text(10, 142, fuell, 1, GRAU, SCHWARZ);
  }

  // Hinweisfeld
  String hinweis;
  uint16_t hf = DUNKELGRAU;
  if (millis() < hinweisBisMs) {
    hinweis = hinweisText;             hf = DUNKELGRAU;
  } else if (!waageOk) {
    hinweis = "Fehler: Waage!";        hf = ROT;
  } else if (gewicht < NEGATIV_FEHLER_G) {
    hinweis = "Pad leeren + Leer";     hf = ROT;
  } else if (akkuNiedrig) {
    hinweis = "Akku niedrig!";         hf = ROT;
  } else if (zustand == ERINNERUNG) {
    hinweis = "Zeit zu trinken!";      hf = BLAU;
  } else if (zustand == ZIEL_ERREICHT) {
    hinweis = "Ziel erreicht!";        hf = DUNKELGRUEN;
  } else {
    uint32_t s = (millis() - letzterSchluckMs) / 1000;
    hinweis = (letzterSchluckMl > 0 ? "Letzter Schluck vor " : "Erinnerung in ") +
              String(letzterSchluckMl > 0 ? s : (ERINNERUNG_MS / 1000 > s ? ERINNERUNG_MS / 1000 - s : 0)) + " s";
  }
  if (geaendert(B_HINWEIS, hinweis + String(hf))) {
    bool lang = fuerDisplay(hinweis).length() > 18;   // lange Texte kleiner schreiben
    tft.fillRoundRect(6, 156, 228, 26, 5, hf);
    textMitte(6, 228, 156 + (lang ? 9 : 5), hinweis, lang ? 1 : 2, WEISS, hf);
  }

  // Zielzeile mit +/- Tasten
  if (geaendert(B_ZIEL, String(tagesziel))) {
    tft.fillRect(0, 184, BREITE, 40, SCHWARZ);
    tasteZeichnen(HAUPT_TASTEN[T_ZIEL_MINUS], DUNKELGRAU, WEISS, 3);
    tasteZeichnen(HAUPT_TASTEN[T_ZIEL_PLUS], DUNKELGRAU, WEISS, 3);
    textMitte(60, 120, 190, "Ziel", 1, GRAU, SCHWARZ);
    textMitte(60, 120, 202, String(tagesziel) + " ml", 2, WEISS, SCHWARZ);
  }

  // Preset-Tasten (gewählte Flaschengröße hervorgehoben)
  if (geaendert(B_TASTEN, String(flascheMl))) {
    tft.fillRect(0, 226, BREITE, HOEHE - 226, SCHWARZ);
    for (uint8_t i = T_LEER; i <= T_KAL; i++) {
      bool gewaehlt = PRESET_ML[i] == flascheMl && PRESET_ML[i] > 0;
      uint16_t f = gewaehlt ? CYAN : (i == T_LEER || i == T_VOLL || i == T_KAL ? DUNKELBLAU : DUNKELGRAU);
      tasteZeichnen(HAUPT_TASTEN[i], f, gewaehlt ? SCHWARZ : WEISS);
    }
  }
}

void naessebildschirmZeichnen() {
  String inhalt = nass ? "nass" : "trocken";
  if (!geaendert(B_HINWEIS, inhalt)) return;
  if (bildschirmNeu) {
    tft.fillScreen(ROT);
    textMitte(0, BREITE, 30, "WASSER", 4, WEISS, ROT);
    textMitte(0, BREITE, 70, "ERKANNT", 4, WEISS, ROT);
    tft.fillRect(20, 112, 200, 3, WEISS);
    textMitte(0, BREITE, 126, "STROM AUS", 3, GELB, ROT);
  }
  tft.fillRect(0, 165, BREITE, 70, ROT);
  textMitte(0, BREITE, 170, nass ? "Sensor: NASS" : "Sensor: trocken", 2, WEISS, ROT);
  textMitte(0, BREITE, 196, nass ? "Gerät abtrocknen," : "Jetzt quittieren,", 1, WEISS, ROT);
  textMitte(0, BREITE, 208, nass ? "Bedienung gesperrt" : "dann Strom wieder an", 1, WEISS, ROT);
  tasteZeichnen(TASTE_QUITTIEREN, nass ? GRAU : DUNKELGRUEN, nass ? DUNKELGRAU : WEISS);
}

void kalibrierbildschirmZeichnen() {
  if (bildschirmNeu) {
    tft.fillScreen(SCHWARZ);
    tft.fillRect(0, 0, BREITE, 28, DUNKELBLAU);
    text(6, 7, "Kalibrierung", 2, WEISS, DUNKELBLAU);
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
  if (geaendert(B_INFO, werte)) {
    tft.fillRect(0, 122, BREITE, 64, SCHWARZ);
    text(8, 126, "Rohwert: " + String((long)rohMittel), 2, CYAN, SCHWARZ);
    text(8, 148, "Gewicht: " + String((int)lroundf(gewicht)) + " g", 2, WEISS, SCHWARZ);
    text(8, 170, "Faktor:  " + String(faktor, 4) + " /g", 1, GRAU, SCHWARZ);
  }
}

// Zeichnet den passenden Bildschirm für den aktuellen Zustand
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
//  SERIELLE BEFEHLE (für Tests und Dokumentation)
// ============================================================================
void statusAusgeben() {
  logZeile("STATUS", String("Zustand=") + zustandName(zustand) +
           " | heute=" + String(getrunkenHeute) + "/" + String(tagesziel) + " ml" +
           " | Gewicht=" + String((int)lroundf(gewicht)) + " g" + (gewichtRuhig ? " (ruhig)" : " (unruhig)") +
           " | Flasche=" + String(flascheMl) + " ml, voll=" + String(vollGewicht, 0) + " g" +
           " | Akku=" + String(akkuVolt, 2) + " V" +
           " | nass=" + String(nass ? "ja" : "nein") +
           " | Last=" + String(digitalRead(PIN_LAST) ? "AN" : "AUS"));
}

void serielleBefehle() {
  static String zeile;
  while (Serial.available()) {
    char c = (char)Serial.read();
    if (c == '\r') continue;
    if (c != '\n') { if (zeile.length() < 32) zeile += c; continue; }
    zeile.trim();
    zeile.toLowerCase();
    if (zeile == "status") {
      statusAusgeben();
    } else if (zeile == "reset") {
      // ECHT: automatisch um Mitternacht (Uhrzeit per NTP über WLAN)
      getrunkenHeute = 0;
      letzterSchluckMs = millis();
      letzterSchluckMl = 0;
      logZeile("TRINKEN", "Tageszähler zurückgesetzt");
    } else if (zeile.length() > 0) {
      Serial.println(F("Befehle: status | reset (Tageszähler auf 0) | hilfe"));
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
  Serial.println(F("=== HydroDesk Base – Wokwi-Simulation ==="));

  pinMode(PIN_NAESSE, INPUT_PULLUP);
  pinMode(PIN_LAST, OUTPUT);
  digitalWrite(PIN_LAST, HIGH);          // Last an
  pinMode(PIN_AKKU_ADC, INPUT);

  leds.begin();
  leds.setBrightness(LED_HELLIGKEIT);
  leds.clear();
  leds.show();

  // Gespeicherte Einstellungen laden (in Wokwi beim Start leer)
  speicher.begin("hydrodesk", false);
  tagesziel   = speicher.getInt("ziel", ZIEL_START_ML);
  flascheMl   = speicher.getInt("flasche", 500);
  vollGewicht = speicher.getFloat("voll", 0);
  faktor      = speicher.getFloat("faktor", WOKWI_FAKTOR);

  anzeigeInit();
  waageInit();
  if (speicher.isKey("tara")) {
    tara = speicher.getFloat("tara", 0);
    logZeile("WAAGE", "Tara aus Speicher: " + String(tara, 1));
  } else {
    taraSetzen();                        // erster Start: Pad muss leer sein
  }

  letzterSchluckMs = millis();
  naesseLesen();
  logZeile("SYSTEM", "Erinnerung nach " + String(ERINNERUNG_MS / 1000) + " s ohne Trinken");
  logZeile("ZUSTAND", "Start in IDLE");
  Serial.println(F("Befehle: status | reset | hilfe"));
}

void loop() {
  naesseLesen();          // 1. Sicherheit zuerst
  akkuLesen();
  waageLesen();
  touchAuswerten();       // 2. Bedienung
  zustandAktualisieren(); // 3. Zustandsautomat
  ledsAktualisieren();    // 4. Ausgaben
  drawUI();
  serielleBefehle();
  delay(5);
}
