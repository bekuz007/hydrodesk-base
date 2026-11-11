# HydroDesk iPhone-App – Design- und Build-Spezifikation (vollständig)

Stand: 11.11.2026 · Grundlage: `HydroDesk_Build_Spezifikation.pdf` (11 Seiten) und `HydroDesk_App_UI_Design.pdf` (49 Seiten, alle Screens in Light und Dark).

Die Spezifikation brach am Ende ab (Claude hatte beim Schreiben sein Nutzungslimit erreicht). Dieses Dokument ist die **vervollständigte Fassung**.
Was **nicht** in der Original-Spezifikation stand und aus dem Design-PDF abgeleitet oder festgelegt wurde, ist mit **[ergänzt]** markiert und steht gesammelt im Abschnitt „Ergänzungen“ ganz unten.

**Verbindlich:** Farben, Schriftgrößen, Abstände, Texte und Zahlenformate. Nichts hinzuerfinden.
**Backend:** bleibt das echte Supabase (Login, Profil, Schlucke, Admin), dazu echtes Bluetooth (CoreBluetooth), Demo-Modus und Offline-Modus. Das in der Spezifikation vorgeschlagene `DataStore`-Protokoll wurde **bewusst nicht** eingeführt: Die vorhandenen Dienste (`AuthService`, `ProfileService`, `DrinkService`, `GeraeteManager`) leisten schon dasselbe und laufen mit der echten Datenbank. [ergänzt]

## 1. Rahmenbedingungen

| Punkt | Vorgabe |
|---|---|
| Plattform | iPhone ab iOS 17, Hochformat |
| Framework | SwiftUI mit Systemkomponenten: `TabView`, `NavigationStack` mit großen Titeln, Swift Charts, `Toggle`, segmentierter `Picker`, `.alert` |
| Schrift | SF Pro; große Zahlen in SF Pro Rounded (`.system(size:weight:design:.rounded)`). Keine eigenen Fonts |
| Icons | nur SF Symbols (z. B. `drop.fill`, `checkmark.circle.fill`, `arrow.triangle.2.circlepath`). Keine Emojis |
| Liquid Glass | ab iOS 26 bekommen Tab- und Navigationsleiste den Glas-Stil automatisch vom System. Karten bleiben klar, kein eigenes Glas/Blur |
| Barrierefreiheit | Dynamic Type bis AX3, sinnvolle VoiceOver-Reihenfolge, Tippflächen mind. 44 × 44 pt, Textkontrast mind. 4,5 : 1, Farbe nie das einzige Signal |
| Referenzrahmen | 393 × 852 pt (iPhone 6,1"), zusätzlich iPhone SE (375 × 667 pt) |
| Sprache | alle sichtbaren Texte Deutsch (echte Umlaute), Code-Bezeichner dürfen englisch sein |

## 2. Navigation

Auth-Gate beim Start:

1. Kurze Ladeanzeige mit App-Marke, während die Sitzung geprüft wird (`StartView`).
2. Keine Sitzung → Anmelden/Registrieren (`LoginView`).
3. Sitzung vorhanden oder „Ohne Konto testen“ → Haupt-App.

Haupt-App: `TabView` mit drei Tabs, jeder ein eigener `NavigationStack` mit großem Titel:

| Tab | Titel | SF Symbol |
|---|---|---|
| 1 | Heute | `drop.fill` |
| 2 | Verlauf | `chart.bar.fill` |
| 3 | Profil | `person.fill` |

Admin ist **kein** Tab. Der Admin-Screen wird per `NavigationLink` aus dem Profil geöffnet und nur bei Rolle `admin` angezeigt.

## 3. Datenmodell (Richtwerte)

Mengen immer in Millilitern als `Int`.

- **Benutzer:in:** id, name, email, gewicht (kg, Dezimaltastatur), größe (cm), tagesziel (berechnet oder vom Gerät gemeldet), rolle (`user`/`admin`). → Supabase-Tabelle `profiles`.
- **Schluck:** id, zeit (Anzeige `HH:mm Uhr`), menge (z. B. 200), quelle („HydroDesk“/„Demo“), hochgeladen (`false` → Sync-Symbol an der Zeile). → SwiftData `DrinkEntry` und Supabase `drink_entries`.
- **Tag (Verlauf):** datum, schluckeCount, mengeMl, zielErreicht (wahr, wenn Menge ≥ Tagesziel). Wird aus den Schlucken berechnet.
- **Gerätestatus:** sieben Fälle: suchen, verbinden, verbunden, getrennt, bluetoothAus, keineBerechtigung, demo (`VerbindungsStatus`).

## 4. Farb-Tokens (Light / Dark)

Markenfarben als Color-Assets im Asset-Katalog (`Assets.xcassets/*.colorset`, je „Any“ und „Dark“). Systemfarben direkt aus SwiftUI (Hex nur zur Kontrolle).

| Token (Asset) | Verwendung | Light | Dark |
|---|---|---|---|
| Wasserblau Fläche (`WasserblauFlaeche`) | Hauptbuttons, App-Icon (weißer Text darauf) | #0277BD | #0277BD |
| Wasserblau Text/Akzent (`WasserblauText`, auch `AccentColor`) | Ring, Prozent, Mengen, aktiver Tab, Links (nur auf Karten) | #0277BD | #4FC3F7 |
| Wasserhell / Lichtlinie (`Wasserhell`) | Lichtlinie, Akzent im Dark Mode | #4FC3F7 | #4FC3F7 |
| Zielgrün (`Zielgruen`) | Ziel erreicht, Verbunden, Häkchen, Ring/Linie bei Ziel | #2E7D32 | #66BB6A |
| Warnorange Punkt (`WarnorangePunkt`) | Statuspunkt Bluetooth aus / keine Berechtigung | #EF6C00 | #FFA040 |
| Warnorange Text (`WarnorangeText`) | Statustext der orangen Zustände | #B55400 | #FFA040 |
| Systemrot Text (`SystemrotText`) | Fehler, destruktiv, Fehlerrand | #D70015 | #FF453A |
| Systemrot Lichtlinie (`SystemrotLichtlinie`) | Akku niedrig / Fehler | #FF3B30 | #FF453A |
| Destruktiv Fläche (`DestruktivFlaeche`) | Hintergrund Abmelden-Button | #FDECEC | #3A1A18 |
| Systemgrau Punkt (`SystemgrauPunkt`) | Statuspunkt Getrennt | #8E8E93 | #8E8E93 |
| label | Haupttext, Zahlen | #000000 | #FFFFFF |
| secondaryLabel | Nebeninfos, inaktive Tabs, Quelle | #68686E | #A1A1A6 |
| systemGroupedBackground | Screen-Hintergrund | #F2F2F7 | #000000 |
| secondarySystemGroupedBackground | Karten | #FFFFFF | #1C1C1E |
| tertiarySystemGroupedBackground | Eingabefelder, Vorschau-Box | #F2F2F7 | #2C2C2E |
| Sekundärbutton Fläche (`Sekundaerbutton`) | Trennen, Jetzt synchronisieren | #E5E5EA | #3A3A3C |
| separator | Trennlinien in Listen | #D8D8DC | #38383A |
| Spur (`Spur`) | leerer Teil von Ring und Balken | #E5E5EA | #2C2C2E |
| Lichtlinie aus (`LichtlinieAus`) | getrennt / Bluetooth aus / keine Berechtigung | #D1D1D6 | #3A3A3C |

## 5. Typografie, Abstände, Radien, Linienstärken

Schrift mit SwiftUI-Textstilen (Dynamic Type greift automatisch), Zahlen mit `.monospacedDigit()`.

| Textstil | Größe | Gewicht | Verwendung |
|---|---|---|---|
| `.largeTitle` | 34 pt | bold | Screen-Titel Heute, Verlauf, Profil, Admin |
| `.title` | 28 pt | bold | App-Name auf Start und Anmelden |
| `.headline` | 17 pt | semibold | Kartentitel, Buttons, „noch 1.500 ml“ |
| `.body` | 17 pt | regular | Eingabefelder, Listen-Labels, Uhrzeit/Menge |
| `.subheadline` | 15 pt | regular/semibold | Untertitel, „/ 2.750 ml“, Statustext (semibold) |
| `.footnote` | 13 pt | regular | Hinweise, Tipps, Fehler-/Infotexte, E-Mail |
| `.caption` | 12 pt | regular | Sync-Zeile, Legende, Fußzeile |
| `.caption2` | 11 pt | semibold | Werte über den Balken im Diagramm |
| `.system(size: 60, weight: .bold, design: .rounded)` | 60 pt | bold, rounded | Tagesmenge im Ring, `.monospacedDigit()` (skaliert mit Dynamic Type) |

| Abstand | Wert |
|---|---|
| Screen-Rand | 16 pt |
| Abstand zwischen Karten | 16 pt |
| Innenabstand Karte | 16 pt |
| Abstand innerhalb Karte | 8–12 pt |
| Tippfläche / Button-Höhe | 44 pt (Anmelden 50 pt) |
| Fortschrittsring | 220 pt |
| Lichtlinie Breite | 160 pt |

| Radius | Wert |
|---|---|
| Karte | 16 pt |
| Alert | 14 pt (System) |
| Button | 12 pt |
| Eingabefeld, Vorschau-Box | 10 pt |
| Segmented Control außen/innen | 9 / 7 pt (System) |
| Lichtlinie, Balken | 2 pt |
| App-Icon (96 pt) | 22 pt |

| Linienstärke | Wert |
|---|---|
| Fortschrittsring | 18 pt |
| Fortschrittsbalken | 4 pt |
| Lichtlinie | 3 pt |
| Ziellinie (gestrichelt) | 1,5 pt |
| Fehlerrand am Feld | 1,5 pt |
| Trennlinie Liste | 1 pt |
| SF-Symbol-Strich | 2 pt |

## 6. Komponenten (`UI/Theme.swift`, `UI/Komponenten.swift`, `UI/GeraeteKarte.swift`)

| Komponente | Beschreibung |
|---|---|
| `Karte` | Container auf `secondarySystemGroupedBackground`, Radius 16, Innenabstand 16, Abstand 16 zwischen Karten |
| `FortschrittsRing` | 220 pt, Strich 18, runde Enden. Spur in Spur-Farbe, Fortschritt Wasserblau, bei Ziel Zielgrün. Mitte: große Zahl (60 pt Rounded), darunter „/ 2.750 ml“ und Prozent (Prozent in Ring-Farbe) |
| `Lichtlinie` | waagerecht 3 pt, Radius 2, weicher Glow. blau = trinken/verbunden, grün = Ziel erreicht, rot = Akku niedrig/Fehler, grau ohne Glow = aus. Unter dem Ring und als Statusleiste (volle Breite) oben in der Gerätekarte |
| `StatusChip` | Punkt 10 pt in Statusfarbe oder kleiner Spinner (Suchen/Verbinden) + Statustext (`.subheadline`, semibold). Nie nur Farbe |
| Schluck-Zeile | Uhrzeit (`HH:mm Uhr`), Quelle („HydroDesk“/„Demo“), Menge (`+200 ml`, Wasserblau, semibold), plus `arrow.triangle.2.circlepath`, wenn noch nicht hochgeladen. Höhe mind. 40 pt |
| Tages-Zeile | Karte je Tag: Titel („Montag, 9. November“), darunter „11 Schlucke · 2.800 ml“, `checkmark.circle.fill` bei Ziel, schmaler Balken (4 pt) |
| Buttons (`.hydro(...)`) | Höhe 44 pt (Anmelden 50), Radius 12, `.headline`. Haupt = Wasserblau Fläche + weißer Text; Ladezustand mit Spinner und geändertem Text („Speichert …“); deaktiviert = reduzierte Deckkraft; sekundär = Sekundärbutton-Fläche; destruktiv = rote Schrift auf „Destruktiv Fläche“ |
| Eingabefeld | Zeile 50 pt. Fehler: roter Rand 1,5 pt + roter Fehlertext (`.footnote`) darunter |
| Toggle-Zeile | System-`Toggle` rechts, Titel und Erklärung (`.footnote`) links |
| `LeerZustand` | SF Symbol in secondaryLabel, darunter Text (`.subheadline`), zentriert |
| `Rueckmeldung` | Symbol + Text: Erfolg grün (`checkmark.circle.fill`), Fehler rot (`exclamationmark.circle.fill`), Info blau (`info.circle`) [ergänzt: Symbole aus dem Design] |
| `AppMarke` | App-Icon-Optik: blaue Fläche, weißer Tropfen, Lichtlinie darunter, Glow (96 pt, Radius 22) |

## 7. Screens und Zustände

Beispieldaten durchgängig: Lena, 70 kg, 175 cm, Tagesziel 2.750 ml, heute 1.250 ml (45 %). Jeder Screen in Light und Dark.

### 7.1 Start
Zentriert: App-Icon mit Lichtlinie, „HydroDesk“ (`.title` bold), kleiner Spinner, „Sitzung wird geprüft …“.

### 7.2 Anmelden / Registrieren
- Oben die Marke: Icon, „HydroDesk“, Untertitel „Dein Trink-Tracker für den Schreibtisch“.
- Segmented Control „Anmelden | Registrieren“.
- Felder als Zeilen in einer Karte (je 50 pt, Trennlinie dazwischen): Name (nur bei Registrieren), E-Mail, Passwort (Platzhalter „Passwort (mind. 6 Zeichen)“).
- Hauptbutton (50 pt) „Anmelden“ bzw. „Konto erstellen“; darunter Zweitbutton „Ohne Konto testen“ mit Hinweis „Daten bleiben nur auf dem iPhone“ (`.caption`).
- Zustände:
  - **Standard** – Anmelden und Registrieren.
  - **Ladezustand** – Hauptbutton mit Spinner, „Anmelden …“ (beim Registrieren „Konto erstellen …“ [ergänzt]).
  - **Fehler** – roter Text mit Symbol unter den Feldern („Bitte eine gültige E-Mail-Adresse eingeben.“), betroffenes Feld mit rotem Rand (1,5 pt). Weitere Prüftexte: „Bitte einen Namen eingeben.“, „Das Passwort braucht mindestens 6 Zeichen.“ (je mit rotem Rand am Feld). Serverfehler (z. B. „E-Mail oder Passwort ist falsch.“) ohne Feldrand.
  - **Info** – blauer Text mit Symbol: „Konto angelegt. Bitte den Bestätigungslink in der E-Mail öffnen und dann anmelden.“ (danach wechselt die Ansicht auf „Anmelden“).
  - **Cloud nicht eingerichtet** – unauffällige Box mit orangem Warnsymbol: „Cloud noch nicht eingerichtet – nur ‚Ohne Konto testen‘ möglich“; Hauptbutton deaktiviert.

### 7.3 Heute (Hauptscreen)
1. **Fortschritt:** großer Ring, Mitte „1.250“, darunter „/ 2.750 ml“ und „45 %“. Darunter die Lichtlinie (blau, bei Ziel grün). Darunter „noch 1.500 ml“ oder – bei erreichtem Ziel – `checkmark.circle.fill` + „Ziel erreicht“ (grün, Ring grün). Darunter die Zielherkunft (`.footnote`):
   „Tagesziel aus deinem Profil“ · „Tagesziel vom HydroDesk“ · „Standardwert – bitte Profil ausfüllen“ (Letzteres als Link in Wasserblau mit `chevron.right`, **wechselt zum Tab Profil** [ergänzt]).
2. **Gerätekarte** (sieben Zustände, Abschnitt 8).
3. **Heutige Schlucke:** oben „Zuletzt: +200 ml um 14:32 Uhr“, darunter die Liste (Uhrzeit, Quelle, Menge, Sync-Symbol), **höchstens acht Zeilen**, dann „… und 3 weitere“. Leerzustand: Symbol `drop` + „Heute noch nichts getrunken.“
4. **Sync-Zeile** unten, klein und grau (`.caption`):
   - „Alle Einträge sind gespeichert.“
   - „3 Einträge werden hochgeladen, sobald Internet da ist.“ (mit Symbol `arrow.triangle.2.circlepath`)
   - „Offline-Modus: Einträge werden nur auf diesem iPhone gespeichert.“
   - Schlägt der Abgleich fehl, steht hier „Synchronisierung fehlgeschlagen: …“ (Verhalten der App, bleibt).

Varianten mindestens: normal (45 %), Ziel erreicht (2.900 / 2.750 ml, 105 %), leer (0 ml, „Suchen …“), Bluetooth aus, Demo-Modus.

### 7.4 Verlauf
- **Letzte 7 Tage:** Balkendiagramm (Swift Charts), Werte über den Balken in Litern („2,1 l“, `.caption2` semibold), gestrichelte Ziellinie (1,5 pt). Balken blau, bei erreichtem Ziel grün. Keine Y-Achse. Legende (`.caption`): „Gestrichelte Linie = Tagesziel (2.750 ml), grün = Ziel erreicht“.
  Die x-Achse zeigt die **letzten sieben Tage bis heute** (im Design „Do Fr Sa So Mo Di Mi“), nicht fest Mo–So [ergänzt].
- Überschrift „LETZTE 30 TAGE“ (`.footnote`, Großbuchstaben), darunter je Tag eine Karte: „Montag, 9. November“, „11 Schlucke · 2.800 ml“ (Menge in Wasserblau, bei Ziel grün), Häkchen bei Ziel, schmaler Balken [Anordnung aus dem Design].
- **Leerzustand** (keine Einträge): nur eine Karte mit Symbol `chart.bar` und „Noch keine Einträge. Verbinde den HydroDesk oder schalte den Demo-Modus ein.“ (ohne Diagramm, wie im Design).

### 7.4a Tagesseite (aus Verlauf und Heute) **[ergänzt – Wunsch des Nutzers, nicht im Design-PDF]**
Zeigt **alle** Einträge eines Tages (auf „Heute“ sind es höchstens acht).
- **Öffnen:** Tipp auf eine Tageskarte unter „LETZTE 30 TAGE“ (rechts mit `chevron.right`), Tipp auf einen Tag im 7-Tage-Diagramm (Spalte des Balkens, auch bei 0 ml) oder Tipp auf „… und N weitere“ auf „Heute“ (öffnet den heutigen Tag).
- **Titel** (klein, `.inline`): Wochentag + Datum, z. B. „Mittwoch, 11. Nov.“
- **Zusammenfassung** (Karte): Menge groß (SF Pro Rounded, `.title`) mit „/ 2.750 ml“ und Prozent, schmaler Balken, „6 Schlucke“, bei erreichtem Ziel `checkmark.circle.fill` + „Ziel erreicht“ (grün).
- **Karte „Alle Einträge“:** Liste, neuester zuerst, dieselbe Zeile wie auf „Heute“ (Uhrzeit `HH:mm Uhr`, Quelle, `+200 ml`, Sync-Symbol, solange nicht hochgeladen). Leerzustand: Symbol `drop` + „An diesem Tag gibt es keine Einträge.“
- **Daten:** lokale Datenbank (SwiftData; enthält die per Sync geholten letzten 30 Tage), gefiltert nach Nutzer:in und den Tagesgrenzen in der Ortszeit des Handys (00:00 Uhr inklusive bis 00:00 Uhr des Folgetags exklusive). Als Tagesziel gilt das aktuelle Tagesziel.
- Logik und Tests: `Core/TagDetail.swift`, `HydroDeskTests/TagDetailTests.swift`.

### 7.5 Profil
Drei Karten und eine Fußzeile:
- **Körperdaten:** Zeilen „Name“, „Gewicht“ (kg, Dezimaltastatur), „Größe“ (cm); Beschriftung links, Eingabefeld rechts (Tertiär-Hintergrund, Radius 10, Einheit dahinter). Live-Vorschau in einer Box: „Tagesziel: 2.750 ml (Körperoberfläche 1,85 m² × 1.500 ml)“; ohne Eingabe: „Gewicht und Größe eingeben, dann wird das Tagesziel berechnet.“ Hinweis (`.footnote`): „Formel nach Mosteller, gerundet auf 50 ml, 1.500–3.500 ml. Richtwert, keine medizinische Empfehlung.“ Button „Speichern“ (Zustand „Speichert …“), Rückmeldung mit Häkchen „Gespeichert. Neues Tagesziel: 2.750 ml“.
  **Tastatur:** Über der Tastatur steht der Knopf „Fertig“; die Tastatur geht auch beim Speichern und beim Wischen nach unten weg (Fehlerbehebung aus Commit 88f4f7e, bleibt unverändert).
- **Einstellungen:** Schalter „Demo-Modus“ mit Erklärung „Simuliert den HydroDesk – zum Vorführen ohne Hardware.“; Zeile „Synchronisierung“ mit Wert („alles hochgeladen“ / „3 Einträge warten“ / „Offline-Modus“); Button „Jetzt synchronisieren“ (im Offline-Modus sichtbar, aber deaktiviert [ergänzt: Design zeigt den Button auch dort]).
- **Konto:** Zeile „E-Mail“ (lena@beispiel.de; im Offline-Modus „Ohne Konto – nur dieses iPhone“), Zeile „Rolle“ („user“/„admin“), nur für Admins der Button „Admin: alle Nutzer anzeigen“ (sekundär, mit `chevron.right`), Button „Abmelden“ (destruktiv; im Offline-Modus „Offline-Modus beenden“).
- **Abmelden-Dialog** (`.alert` „Abmelden?“, Buttons „Abbrechen“ / „Abmelden“) in zwei Varianten:
  - mit offenen Einträgen: „3 Einträge sind noch nicht hochgeladen. Sie bleiben auf dem iPhone und werden nach der nächsten Anmeldung hochgeladen.“
  - ohne: „Deine Daten bleiben gespeichert.“
- **Fußzeile** (`.caption`): „HydroDesk App 1.0 · Schulprojekt FI-AE“.

### 7.6 Admin: Heute (nur Rolle admin)
- Großer Titel „Admin: Heute“, Hinweis oben: „Alle Nutzer mit der heutigen Trinkmenge. Bearbeiten geht im Supabase-Dashboard.“
- Toolbar rechts: Neu laden (`arrow.clockwise`).
- Liste in **einer** Karte mit Trennlinien: Name (Admins mit „· Admin“), E-Mail klein darunter, rechts „1.250 / 2.750 ml“ (grün mit Häkchen bei erreichtem Ziel), darunter Fortschrittsbalken.
- Zustände: **Laden** (Spinner, „Nutzer werden geladen …“), **Fehler** (Symbol `exclamationmark.triangle`, roter Text „Laden fehlgeschlagen: …“, Button „Erneut laden“), **Liste** (im Design fünf Beispielnutzer:innen).

## 8. Gerät, BLE und die sieben Zustände

Echtes Bluetooth läuft über CoreBluetooth (`HydroBleManager`), der Demo-Modus erzeugt Schlucke lokal („Schluck simulieren (+200 ml)“) und braucht keine Hardware. Die Gerätekarte zeigt: Lichtlinie oben, Titel, Statuspunkt/Spinner + Statustext, optional Akku, Aktionsbutton(s). Logik: `Core/Anzeige.swift` (`GeraeteKarteModell`, getestet).

| # | Titel | Status (Farbe) | Lichtlinie | Button(s) | Zusatz |
|---|---|---|---|---|---|
| 1 | HydroDesk | Suchen … (blau, Spinner) | blau | Trennen | Tipp: „Der HydroDesk ist nur kurz nach dem Trinken bzw. Einschalten sichtbar. Notfalls das Gerät kurz aus- und einschalten.“ |
| 2 | HydroDesk | Verbinden … (blau, Spinner) | blau | Trennen | – |
| 3 | HydroDesk | Verbunden (grün) | blau, bei Ziel grün | Trennen | Zeile „Gerät meldet: 1.250 / 2.750 ml · Akku 88 %“ |
| 4 | HydroDesk | Getrennt (grau) | aus | Verbinden | – |
| 5 | HydroDesk | Bluetooth ist aus (orange) | aus | Erneut versuchen | „Bitte Bluetooth in den Einstellungen oder im Kontrollzentrum einschalten.“ |
| 6 | HydroDesk | Keine Berechtigung (orange) | aus | iPhone-Einstellungen öffnen | „Ohne Bluetooth-Berechtigung kann die App das Gerät nicht finden.“ |
| 7 | HydroDesk (Demo-Modus) | Verbunden (Demo) (grün) | blau, bei Ziel grün | Trennen · Schluck simulieren (+200 ml) | – (Statuszeile steht unter dem Titel) |

Akku-Symbol: Batterie-Symbol (Rahmen mit Füllung, `battery.0percent` … `battery.100percent`), Prozent als Text daneben („Akku 88 %“). Bei **Akku niedrig**: Lichtlinie rot **und** Hinweistext – nie Farbe allein. [Schwelle und Text ergänzt, siehe unten]

## 9. Sync und Offline

Schlucke werden immer **zuerst lokal** gespeichert (SwiftData) und bei Verbindung hochgeladen. Pro Eintrag ein Sync-Symbol (`arrow.triangle.2.circlepath`), solange `hochgeladen == false`. Backend ist das echte Supabase; keine Zugangsdaten in der App oder auf GitHub (`Config/Secrets.xcconfig` ist gitignored), nie der `service_role`-Schlüssel.

Drei Sync-Zustände für die Zeile unten auf „Heute“ und im Profil:

| Zustand | Heute (unten) | Profil (Zeile „Synchronisierung“) |
|---|---|---|
| Alles gespeichert | „Alle Einträge sind gespeichert.“ | „alles hochgeladen“ |
| Ausstehend | „3 Einträge werden hochgeladen, sobald Internet da ist.“ | „3 Einträge warten“ |
| Offline (nach „Ohne Konto testen“) | „Offline-Modus: Einträge werden nur auf diesem iPhone gespeichert.“ | „Offline-Modus“ |

Der Button „Jetzt synchronisieren“ im Profil stößt den Upload an.

## 10. Tagesziel-Berechnung nach Mosteller

Körperoberfläche (BSA) = √(Größe[cm] × Gewicht[kg] / 3600); Tagesziel[ml] = min(3500, max(1500, auf 50 ml gerundet(BSA × 1500))).
Beispiel: 175 cm, 70 kg → BSA ≈ 1,85 m² → 2.775 → gerundet 2.750 ml.

- Ohne Gewicht oder Größe: kein berechnetes Ziel, Hinweistext anzeigen, Standardwert (2.000 ml) nutzen. Das Ziel „aus deinem Profil“ gilt nur, wenn **Gewicht und Größe** eingetragen sind [ergänzt – sonst würde der in der Datenbank vorbelegte Standardwert fälschlich als „aus deinem Profil“ erscheinen].
- Zielherkunft steuert die Zeile unter dem Ring (Abschnitt 7.3). Reihenfolge: Profil → Gerät → Standardwert.
- Immer als Richtwert kennzeichnen, keine medizinische Empfehlung.

## 11. Zahlen- und Textformate (de-DE)

Alles im deutschen Format (`Format.swift`, `Locale(identifier: "de_DE")`), Zahlen mit `.monospacedDigit()`.

| Fall | Format | Beispiel |
|---|---|---|
| Menge ml | Tausenderpunkt, Leerzeichen vor Einheit | 1.250 ml |
| Menge Liter | eine Nachkommastelle, Komma | 2,1 l |
| Prozent | Leerzeichen vor % (auf ganze Zahl gerundet: 600 von 2.750 → 22 %) | 45 % |
| Uhrzeit | 24-Stunden, mit „Uhr“ | 14:32 Uhr |
| Datum lang | Wochentag, Tag. Monat | Montag, 9. November |
| Datum kurz | abgekürzt | Mo, 9. Nov. |

Datum/Uhrzeit immer über `DateFormatter` mit `de_DE`, nie feste Strings zusammenbauen.

## 12. Was die KI vermeiden soll  *(im Original fehlend, aus den Vorgaben der Spezifikation abgeleitet [ergänzt])*

- Keine Funktionen, Screens, Tabs, Texte oder Farben, die weder im Design noch hier stehen.
- Keine Emojis, keine eigenen Fonts, keine selbstgebauten Tab-/Navigationsleisten, kein eigenes Glas/Blur auf Karten.
- Keine festen Schriftgrößen außer der großen Ringzahl (60 pt, skaliert mit Dynamic Type).
- Keine englischen Zahlen-/Datumsformate, keine festen Datums-Strings.
- Farbe nie als einziges Signal (immer Symbol oder Text dazu).
- Keine Zugangsdaten oder Schlüssel im Code oder auf GitHub; nie den `service_role`-Schlüssel verwenden.
- Keine medizinischen Aussagen: das Tagesziel ist ein Richtwert.
- Bestehende Funktionen nicht kaputtmachen: Supabase-Login/Profil/Sync, BLE, Offline-first (SwiftData), Demo-Modus, Admin-Ansicht, „Fertig“-Knopf im Profil.

## Ergänzungen und Festlegungen (nicht in der Original-Spezifikation)

1. **Fehlender Abschnitt „Was die KI vermeiden soll“** (Seite 1 verweist darauf, im PDF nicht vorhanden) → Abschnitt 12.
2. **Akku niedrig:** die Spezifikation nennt keine Schwelle und keinen Text → Schwelle **≤ 15 %**, Hinweis „Akku niedrig – bitte bald laden.“ (nur wenn das Gerät den Akkustand mitschickt).
3. **Verlauf, 7 Tage:** Design zeigt die letzten sieben Tage bis heute statt fest Mo–So.
4. **Verlauf, Tageskarte:** Anordnung „6 Schlucke · 1.250 ml“ und Überschrift „LETZTE 30 TAGE“ aus dem Design; Einzahl „1 Schluck“.
5. **Verlauf leer:** nur die Leerzustands-Karte (ohne Diagramm), wie im Design.
6. **Zielherkunft Profil** nur mit Gewicht und Größe (Abschnitt 10); Link „Standardwert …“ wechselt zum Profil.
7. **Symbole der Rückmeldungen** (Fehler `exclamationmark.circle.fill`, Info `info.circle`, Cloud-Warnung `exclamationmark.triangle.fill`) aus dem Design.
8. **Konto im Offline-Modus:** E-Mail-Zeile „Ohne Konto – nur dieses iPhone“, Rolle „user“; „Jetzt synchronisieren“ sichtbar, aber deaktiviert.
9. **Admin-Button** im Profil: sekundärer Stil mit Pfeil (aus dem Design); Fehlerzustand mit Symbol und „Erneut laden“.
10. **Einzahl-Texte** („1 Eintrag wird hochgeladen …“, „1 Eintrag wartet“, Abmelden-Dialog) – die Spezifikation kennt nur die Mehrzahl.
11. **Prozent** wird gerundet (Design: 600 von 2.750 ml = 22 %); Ring und Balken zeigen höchstens 100 %.
12. **Gerätekarte:** „Gerät meldet …“ nur im Zustand „Verbunden“ (nicht im Demo-Modus); im Design-PDF ist die Übersichtsseite „alle sieben Zustände“ nur teilweise exportiert (1, 3, 5, 7) – die Zustände 2, 4 und 6 stammen aus der Tabelle der Spezifikation.
13. **Beibehalten, weil weder Design noch Spezifikation etwas anderes sagen:** Texte bei Fehlern des Abgleichs („Synchronisierung läuft …/abgeschlossen/fehlgeschlagen“), Profil-Fehlermeldung „Lokal gespeichert, aber nicht in Supabase: …“, Serverfehler-Übersetzungen beim Login, automatischer Neustart der Gerätesuche, stündlicher Abgleich.
14. **`DataStore`-Protokoll** nicht eingeführt (siehe oben).
15. **Tagesseite** (Abschnitt 7.4a) auf Wunsch des Nutzers hinzugefügt.

### Noch nicht geprüft
- Dynamic Type AX3 und iPhone SE (375 × 667 pt) wurden im Code berücksichtigt (Textstile, `ScaledMetric`, `ViewThatFits`), aber nicht auf einem echten SE bzw. mit AX3 ausprobiert.
- Das Aussehen auf dem iPhone muss der Nutzer gegen das Design-PDF prüfen.
