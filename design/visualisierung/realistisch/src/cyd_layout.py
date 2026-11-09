# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 bekuz007 (https://github.com/bekuz007/hydrodesk-base) - siehe LICENSE
# Lage der Bauteile auf der RUECKSEITE des CYD (ESP32-2432S028R, USB-C-Version, Fastsaw).
# Koordinaten in mm, Blick auf die Rueckseite: u nach rechts (0..50), v nach unten (0..86),
# USB-Buchsen bei v = 86. Im Gehaeuse gilt: X = cyd_x + u, Y = cyd_y + v (siehe README).
# Werte aus dem Produktfoto (Amazon B0G1N16Q16, Bild "Unterstuetzt UART-/SPI-...", ca. 10 px/mm)
# abgelesen = geschaetzt (+-0,5 mm), Bauteilgroessen aus Datenblaettern der Gehaeuseformen.
PCB_W, PCB_L, PCB_R = 50.0, 86.0, 3.0
# (name, typ, u0, v0, du, dv, hoehe)
PARTS = [
    ('ESP32-WROOM-32', 'esp', 15.5, -0.6, 18.0, 25.5, 3.1),
    ('RST', 'tact', 1.2, 7.0, 6.2, 3.5, 3.6),
    ('BOOT', 'tact', 1.2, 11.1, 6.2, 3.5, 3.6),
    ('XPT2046', 'tssop16', 2.7, 17.5, 4.4, 5.0, 1.1),
    ('SC8002B', 'sop8', 2.6, 34.3, 3.9, 4.9, 1.5),
    ('P4 SPEAK', 'jst2', 0.3, 56.0, 3.4, 4.4, 4.6),
    ('AMS1117 a', 'sot223', 12.3, 64.2, 6.5, 3.5, 1.6),
    ('AMS1117 b', 'sot223', 21.1, 64.2, 6.5, 3.5, 1.6),
    ('CH340C', 'soic16', 37.2, 65.3, 9.9, 3.9, 1.5),
    ('Q T1', 'sot23', 37.6, 59.0, 1.4, 2.9, 1.0),
    ('Q T2', 'sot23', 42.6, 59.0, 1.4, 2.9, 1.0),
    ('Q AUDIO', 'sot23', 2.2, 68.0, 2.9, 1.4, 1.0),
    ('Q BL', 'sot23', 10.0, 74.6, 2.9, 1.4, 1.0),
    ('RGB-LED', 'led5050', 35.7, 27.0, 5.0, 5.0, 1.6),
    ('microSD', 'sd', 35.5, 40.0, 14.5, 14.0, 1.9),
    ('USB-C', 'usbc', 22.9, 79.4, 8.94, 7.35, 3.26),
    ('Micro-USB', 'microusb', 33.5, 80.8, 7.5, 5.2, 2.9),
    ('P1 VIN-TX-RX-GND', 'jst4h', 12.1, 81.75, 7.0, 4.25, 3.6),
    ('P3 GND-IO35-IO22-IO21', 'jst4v', 45.75, 11.1, 4.25, 7.0, 3.6),
    ('CN1 GND-IO22-IO27-3V3', 'jst4v', 45.75, 27.2, 4.25, 7.0, 3.6),
]
# Steckerpins (Rastermass 1,25 mm), Reihenfolge laut Aufdruck auf der Platine
P3_PINS = ['GND', 'IO35', 'IO22', 'IO21']
CN1_PINS = ['GND', 'IO22', 'IO27', '3V3']
# microSD-Loetfahnen (8 Stueck, 1,1 mm Raster) an der Innenseite des Slots (u ~ 35)
SD_TAIL_U = 34.9
SD_PIN1_V = 41.9          # Annahme: Pin 1 (DAT2) liegt auf der ESP32-Seite
SD_PITCH = 1.1
# Testpunkte laut CYD-Doku (S3 = 5 V, S1 = GND, S5 = 3,3 V)
TESTPADS = {'S3': (30.8, 63.6), 'S1': (30.8, 65.9), 'S5': (30.8, 68.2)}
# kleine SMD-Teile (0603/0805), aus dem Foto grob abgelesen: (u, v, quer?)
PASSIVES = [
    (10.2, 3.2, 0), (12.3, 3.2, 0), (10.2, 5.6, 0), (12.3, 5.6, 0),
    (9.6, 9.0, 1), (9.6, 12.0, 1),
    (39.0, 11.5, 0), (39.0, 13.6, 0), (39.0, 15.7, 0), (39.0, 17.8, 0), (41.3, 12.5, 1), (41.3, 16.5, 1),
    (2.4, 29.2, 0), (5.0, 29.2, 0), (2.4, 41.2, 0), (5.0, 41.2, 0), (2.4, 43.6, 0), (5.0, 43.6, 0),
    (2.4, 46.0, 0), (5.0, 46.0, 0), (2.4, 48.4, 0),
    (13.0, 61.4, 0), (16.8, 61.4, 0), (21.8, 61.4, 0), (25.6, 61.4, 0),
    (13.0, 69.9, 0), (16.8, 69.9, 0), (21.8, 69.9, 0), (25.6, 69.9, 0),
    (18.0, 74.6, 0), (14.2, 76.8, 1), (21.5, 76.8, 1), (24.3, 74.3, 0),
    (30.3, 44.2, 1), (32.5, 44.2, 1), (30.3, 47.6, 1),
    (37.0, 56.3, 0), (40.2, 56.3, 0), (43.6, 56.3, 0), (46.4, 56.3, 0),
    (35.5, 71.8, 0), (38.6, 71.8, 0), (44.4, 72.2, 0), (46.8, 74.8, 1),
    (37.8, 33.5, 0), (40.2, 33.5, 0), (28.6, 57.0, 1), (31.0, 57.0, 1),
]
# leerer Flash-Platz U4 (SOIC-8-Pads), nur Aufdruck/Pads
U4 = (21.5, 30.0, 6.0, 9.5)
