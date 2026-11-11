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
