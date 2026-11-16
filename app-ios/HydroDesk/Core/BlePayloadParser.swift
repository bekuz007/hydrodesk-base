// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE

import Foundation

/// UUIDs und Name des HydroDesk-Geräts. Müssen mit der Firmware übereinstimmen
/// (`wokwi/sketch.ino`: `BT_NAME`, `BT_SERVICE_UUID`, `BT_WERTE_UUID`).
enum HydroBleKonstanten {
    static let geraetename = "HydroDesk"
    static let serviceUUID = "4f9a0001-6c1e-4b8e-9d6a-2b7c1e0a4d10"
    /// Characteristic: lesen + notify, Text wie "1250/2750 ml"
    static let werteUUID = "4f9a0002-6c1e-4b8e-9d6a-2b7c1e0a4d10"
    /// V5 – Steuerung: schreiben, Text-Befehl wie im Seriellen Monitor (z. B. "profil 75.0 180")
    static let befehlUUID = "4f9a0003-6c1e-4b8e-9d6a-2b7c1e0a4d10"
    /// V5 – lesen + notify, JSON mit Gewicht, Profil, Flasche … (siehe `GeraeteStatus`)
    static let statusUUID = "4f9a0004-6c1e-4b8e-9d6a-2b7c1e0a4d10"
    /// V5 – lesen + notify, "<nr>|<text>": Rückmeldung zum letzten Befehl
    static let antwortUUID = "4f9a0005-6c1e-4b8e-9d6a-2b7c1e0a4d10"
}

/// V5: Befehle, die die App an das Gerät schickt (gleiche Syntax wie im Seriellen Monitor).
enum GeraeteBefehl: Equatable {
    /// Körpergewicht und Größe – das Gerät berechnet daraus sein Tagesziel
    case profil(gewichtKg: Double, groesseCm: Int)
    /// Nullpunkt setzen (Pad muss leer sein)
    case tara
    /// Waage mit einem bekannten Gewicht eichen
    case eichen(gramm: Int)
    /// leere bzw. volle Flasche steht auf dem Pad → Gewicht übernehmen
    case flascheLeer
    case flascheVoll
    /// Tageszähler auf 0
    case tagZuruecksetzen

    var text: String {
        switch self {
        case let .profil(kg, cm):
            // Punkt als Dezimaltrenner (Firmware: toFloat), unabhängig von der Sprache des iPhones
            return "profil " + String(format: "%.1f", locale: Locale(identifier: "en_US_POSIX"), kg) + " \(cm)"
        case .tara: return "tara"
        case let .eichen(gramm): return "eichen \(gramm)"
        case .flascheLeer: return "leer"
        case .flascheVoll: return "voll"
        case .tagZuruecksetzen: return "reset"
        }
    }
}

/// V5: Zustand des Geräts aus der Status-Characteristic (JSON der Firmware, `bleStatusJson()`).
/// Beispiel: {"heute":1250,"ziel":2750,"g":420,"ruhig":1,"kg":75.0,"cm":180,"leer":312,"voll":1012,
///            "kap":700,"fl":108,"kalib":1,"zu":"MESSEN","akku":-1,"nass":0,"waage":1}
struct GeraeteStatus: Equatable, Decodable {
    var heuteMl: Int
    var zielMl: Int
    /// aktuelles Gewicht auf dem Pad (g)
    var gewichtG: Int
    var ruhig: Bool
    var profilKg: Double
    var profilCm: Int
    var leerG: Int
    var vollG: Int
    var kapazitaetMl: Int
    /// geschätzter Inhalt der Flasche (ml)
    var flascheMl: Int
    var flascheKalibriert: Bool
    /// Zustand des Geräts, z. B. "MESSEN", "ERINNERUNG", "KALIBRIERUNG"
    var zustand: String
    /// nil = kein Akku (USB)
    var akkuProzent: Int?
    var nass: Bool
    var waageOk: Bool

    private enum CodingKeys: String, CodingKey {
        case heute, ziel, g, ruhig, kg, cm, leer, voll, kap, fl, kalib, zu, akku, nass, waage
    }

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        heuteMl = try c.decode(Int.self, forKey: .heute)
        zielMl = try c.decode(Int.self, forKey: .ziel)
        gewichtG = try c.decodeIfPresent(Int.self, forKey: .g) ?? 0
        ruhig = (try c.decodeIfPresent(Int.self, forKey: .ruhig) ?? 0) != 0
        profilKg = try c.decodeIfPresent(Double.self, forKey: .kg) ?? 0
        profilCm = try c.decodeIfPresent(Int.self, forKey: .cm) ?? 0
        leerG = try c.decodeIfPresent(Int.self, forKey: .leer) ?? 0
        vollG = try c.decodeIfPresent(Int.self, forKey: .voll) ?? 0
        kapazitaetMl = try c.decodeIfPresent(Int.self, forKey: .kap) ?? 0
        flascheMl = try c.decodeIfPresent(Int.self, forKey: .fl) ?? 0
        flascheKalibriert = (try c.decodeIfPresent(Int.self, forKey: .kalib) ?? 0) != 0
        zustand = try c.decodeIfPresent(String.self, forKey: .zu) ?? ""
        let akku = try c.decodeIfPresent(Int.self, forKey: .akku) ?? -1
        akkuProzent = akku >= 0 ? akku : nil
        nass = (try c.decodeIfPresent(Int.self, forKey: .nass) ?? 0) != 0
        waageOk = (try c.decodeIfPresent(Int.self, forKey: .waage) ?? 1) != 0
    }

    static func parse(_ daten: Data) -> GeraeteStatus? {
        // Firmware hängt evtl. ein NUL-Zeichen an → vorher abschneiden
        let sauber = daten.prefix { $0 != 0 }
        return try? JSONDecoder().decode(GeraeteStatus.self, from: Data(sauber))
    }

    /// Stimmt das Profil auf dem Gerät mit dem in der App überein? (Gewicht auf 0,1 kg genau)
    func profilPasst(gewichtKg: Double, groesseCm: Int) -> Bool {
        abs(profilKg - gewichtKg) < 0.05 && profilCm == groesseCm
    }
}

/// V5: Rückmeldung des Geräts zum letzten Befehl, Format "<nr>|<text>" (nr zählt hoch).
struct GeraeteAntwort: Equatable {
    var nummer: Int
    var text: String

    static func parse(_ daten: Data) -> GeraeteAntwort? {
        let roh = String(decoding: daten.prefix { $0 != 0 }, as: UTF8.self)
        guard let trenner = roh.firstIndex(of: "|"), let nr = Int(roh[..<trenner]) else { return nil }
        return GeraeteAntwort(nummer: nr, text: String(roh[roh.index(after: trenner)...]))
    }
}

/// Verbindungszustand, wie er in der App angezeigt wird.
enum VerbindungsStatus: Equatable {
    case keineBerechtigung
    case bluetoothAus
    case getrennt
    case suchen
    case verbinden
    case verbunden
    case demo

    var text: String {
        switch self {
        case .keineBerechtigung: return "Keine Berechtigung"
        case .bluetoothAus: return "Bluetooth ist aus"
        case .getrennt: return "Getrennt"
        case .suchen: return "Suchen …"
        case .verbinden: return "Verbinden …"
        case .verbunden: return "Verbunden"
        case .demo: return "Verbunden (Demo)"
        }
    }

    /// true, wenn eine Verbindung besteht oder gerade aufgebaut wird (dann zeigt die App „Trennen“).
    var aktiv: Bool {
        switch self {
        case .verbunden, .demo, .suchen, .verbinden: return true
        default: return false
        }
    }
}

/// Ein Messwert vom HydroDesk-Gerät.
struct DeviceReading: Equatable {
    /// heute getrunken (ml), zählt das Gerät selbst
    var heuteMl: Int
    /// Tagesziel, das auf dem Gerät eingestellt ist
    var zielMl: Int?
    /// Akkustand (nur, falls die Firmware ihn mitschickt)
    var akkuProzent: Int?
    var rohtext: String

    init(heuteMl: Int, zielMl: Int? = nil, akkuProzent: Int? = nil, rohtext: String = "") {
        self.heuteMl = heuteMl
        self.zielMl = zielMl
        self.akkuProzent = akkuProzent
        self.rohtext = rohtext
    }
}

/// Übersetzt den Text der BLE-Characteristic in einen `DeviceReading`.
///
/// Unterstützte Formate:
///  - aktuelle Firmware:  `"1250/2750 ml"`
///  - mögliche spätere Firmware (JSON): `{"heute":1250,"ziel":2750,"akku":88}`
enum BlePayloadParser {
    private static let textFormat = try! NSRegularExpression(
        pattern: #"^\s*(\d+)\s*/\s*(\d+)\s*(ml)?\s*$"#,
        options: [.caseInsensitive]
    )

    static func parse(_ daten: Data) -> DeviceReading? {
        guard let text = String(data: daten, encoding: .utf8) else { return nil }
        return parse(text)
    }

    static func parse(_ rohtext: String) -> DeviceReading? {
        let text = bereinigen(rohtext)
        if text.hasPrefix("{") { return parseJson(text) }
        let bereich = NSRange(text.startIndex..., in: text)
        guard let treffer = textFormat.firstMatch(in: text, options: [], range: bereich),
              let r1 = Range(treffer.range(at: 1), in: text),
              let r2 = Range(treffer.range(at: 2), in: text),
              let heute = Int(text[r1])
        else { return nil }
        return DeviceReading(heuteMl: heute, zielMl: Int(text[r2]), rohtext: text)
    }

    /// Leerzeichen und abschließende NUL-Zeichen (`\0`) am Anfang/Ende entfernen.
    private static func bereinigen(_ text: String) -> String {
        var s = Substring(text)
        let weg: (Character) -> Bool = { $0 == "\u{0}" || $0.isWhitespace }
        while let l = s.last, weg(l) { s = s.dropLast() }
        while let f = s.first, weg(f) { s = s.dropFirst() }
        return String(s)
    }

    private static func parseJson(_ text: String) -> DeviceReading? {
        guard let daten = text.data(using: .utf8),
              let objekt = (try? JSONSerialization.jsonObject(with: daten)) as? [String: Any],
              let heute = ganzzahl(objekt["heute"])
        else { return nil }
        return DeviceReading(
            heuteMl: heute,
            zielMl: ganzzahl(objekt["ziel"]),
            akkuProzent: ganzzahl(objekt["akku"]),
            rohtext: text
        )
    }

    private static func ganzzahl(_ wert: Any?) -> Int? {
        if let i = wert as? Int { return i }
        if let d = wert as? Double, d == d.rounded(), abs(d) < 1e9 { return Int(d) }
        return nil
    }
}
