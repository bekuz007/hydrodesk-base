// =====================================================================
//  HydroDesk Base  -  parametrisches 3D-Druck-Gehaeuse (OpenSCAD)
//  Teile:  part = "base" | "cover" | "pad" | "cap" | "assembly" | "exploded"
//                 | "inside" (Boden + Bauteile, ohne Deckel/Pad) | "section"
//                 | "cap_check_cyd" / "cap_check_base" (Kollisionstests der Abdeckkappe)
//  Koordinaten: X = Breite (links->rechts), Y = Tiefe (vorne=0 -> hinten),
//               Z = Hoehe (Tischflaeche = 0).  Alle Masse in mm.
//  Drucker: FDM, PLA, 0,4-mm-Duese.  Alle Teile ohne Stuetzmaterial.
// =====================================================================

part = "assembly";

$fn = 48;
e   = 0.01;          // kleiner Ueberstand fuer saubere Boolean-Schnitte

/* ===================== AUSSENMASSE ===================== */
W        = 180;      // Breite X
D        = 100;      // Tiefe Y  (95 gewuenscht -> 100 noetig, damit 90er Pad + 1 mm Spalt + 4 mm Rahmen passt)
H        = 25;       // Gesamthoehe inkl. Deckel (20 unmoeglich: Waegezelle 12,7 + Boden + Abstandshalter + Pad)
R_corner = 8;        // senkrechter Eckradius
wall     = 2.4;      // Wandstaerke (6 Bahnen a 0,4)
floor_t  = 2.0;      // Bodenstaerke
cover_t  = 2.0;      // Deckelplatte
top_chamfer = 1.2;   // weiche Oberkante (45-Grad-Fase am Deckel)
bot_chamfer = 0.6;   // kleine Fase unten (gegen "Elefantenfuss")
clr      = 0.3;      // allgemeines Spiel
base_h   = H - cover_t;   // Hoehe der Bodenwanne (Oberkante Wand) = 23

/* ===================== CYD  ESP32-2432S028R ===================== */
// Quelle: github.com/witnessmenow/ESP32-Cheap-Yellow-Display
//   OriginalDocumentation/3-Structure_Diagram/Dimensions.png  (50x86, Loecher 42x78, R1.6)
//   3dModels/Havenview_CYD_CAD/*.step (Gesamtdicke 9,8: Bauteile 4,7 | PCB 1,5 | LCD+Touch 3,6)
cyd_w        = 50;     // PCB Breite  (hier in X, Hochformat)
cyd_l        = 86;     // PCB Laenge  (hier in Y)
cyd_pcb_t    = 1.5;
cyd_hole_in  = 4.0;    // Lochmitte vom PCB-Rand (Lochabstand 42 x 78)
cyd_hole_d   = 3.2;    // M3
cyd_front_h  = 3.6;    // LCD + Touch ueber PCB-Oberseite
cyd_back_h   = 4.7;    // hoechste Bauteile auf der PCB-Rueckseite
cyd_tp_w     = 50;     // Touchpanel / LCD-Glas
cyd_tp_l     = 69.2;
cyd_aa_w     = 43.2;   // sichtbare Flaeche (active area)
cyd_aa_l     = 57.6;
cyd_aa_shift = 3.5;    // AA-Mitte liegt ca. 2,9-4,3 mm vom PCB-Zentrum weg vom USB-Ende (aus Zeichnung abgeleitet)
cyd_tp_shift = 0.7;    // LCD-Glas-Mitte ca. 0-1,4 mm weg vom USB-Ende
win_margin   = 1.5;    // Fenster = AA + 1,5 mm je Seite (deckt Toleranz der AA-Lage ab)
cyd_x        = 4.4;    // linke PCB-Kante
cyd_back_gap = 0.8;    // Abstand PCB-Hinterkante (USB-Seite) zur Innenwand
cyd_y        = D - wall - cyd_back_gap - cyd_l;     // vordere PCB-Kante (=10.8)
cyd_cx       = cyd_x + cyd_w/2;
cyd_cy       = cyd_y + cyd_l/2;
lcd_gap      = 0.3;    // Luft LCD-Oberseite <-> Deckel
lcd_recess   = 0.8;    // Tasche in der Deckel-Unterseite ueber dem LCD (Deckel dort nur 1,2 mm)
lcd_top_z    = base_h + lcd_recess - lcd_gap;          // 23.5
cyd_pcb_z    = lcd_top_z - cyd_front_h - cyd_pcb_t;    // PCB-Unterseite = 18.4
cyd_holes    = [ for (ix=[0,1]) for (iy=[0,1])
                 [cyd_x + cyd_hole_in + ix*(cyd_w-2*cyd_hole_in),
                  cyd_y + cyd_hole_in + iy*(cyd_l-2*cyd_hole_in)] ];
// USB-Ausschnitt hinten: breit genug fuer Micro-USB UND USB-C (2-USB-Variante) inkl. Stecker-Tuelle
cyd_usb_w    = 32;
cyd_usb_h    = 7.6;
cyd_usb_zc   = cyd_pcb_z - 1.6;
cyd_usb_r    = 2;      // Eckradius des USB-Ausschnitts

/* ===================== Abdeckkappe fuer den CYD-USB-Ausschnitt ===================== */
// Steckbare Kappe: verschliesst den grossen Programmier-Ausschnitt hinten (Kunde sieht ein
// geschlossenes Geraet). Der USB-C-Ladeanschluss des TC4056 bleibt offen.
cap_clr      = 0.15;   // Spiel Stopfen <-> Ausschnitt je Seite
cap_rand     = 1.5;    // Flansch steht je Seite so weit ueber den Ausschnitt
cap_flange_t = 1.2;    // Flanschdicke (steht aussen 1,2 mm vor)
cap_chamfer  = 0.5;    // Fase an der sichtbaren Flanschkante
cap_gap_in   = 0.2;    // Stopfen endet 0,2 mm VOR der Wand-Innenseite (USB-Buchse sitzt nur 0,8 mm dahinter)
cap_plug_d   = wall - cap_gap_in;   // Stopfentiefe = 2,2 mm
cap_shell    = 1.0;    // Wandstaerke des hohlen Stopfens (federt beim Einstecken etwas)
cap_rib_h    = 0.30;   // Quetschrippen: Hoehe ueber Stopfenflaeche -> 0,15 mm Uebermass je Seite
cap_rib_w    = 0.8;    // Rippenbreite an der Basis (Dreieckprofil)
cap_rib_x    = [-12, -4, 4, 12];    // Rippenlagen oben/unten (vom Ausschnitt-Mittelpunkt)
cap_notch_w  = 8;      // Fingernagel-Kerbe unten mittig im Flansch (Wandseite)
cap_notch_d  = 0.6;    // Kerbentiefe in die Flanschrueckseite
cap_pull     = 0;      // nur Vorschau: Kappe um so viele mm nach hinten herausgezogen
cap_fw = cyd_usb_w + 2*cap_rand;    // Flansch 35 x 10,6 mm
cap_fh = cyd_usb_h + 2*cap_rand;

/* ===================== Akku / Module ===================== */
bat_w = 34.5; bat_l = 56; bat_h = 10.3;     // EEMB LP103454 2000 mAh (34,5 x 55(+1) x 10,3)
bat_x = cyd_cx - bat_w/2;
bat_y = D - wall - 0.6 - bat_l;             // liegt unter dem CYD, hinten
boost_w = 37; boost_l = 17;                 // MT3608-Boost (optional), unter dem CYD vorne
boost_x = cyd_cx - boost_w/2;  boost_y = 19;
strip_x = 56;                               // Modul-Streifen rechts neben dem CYD
tc_w = 17; tc_l = 26;                       // TC4056 USB-C Lademodul
tc_x = strip_x; tc_y = D - wall - tc_l;
tc_pcb_z  = floor_t + 1.5;                  // PCB liegt auf 1,5 mm Leisten
tc_usb_w  = 10;  tc_usb_h = 4.5;            // Buchsenoeffnung
tc_usb_zc = tc_pcb_z + 1.6 + 1.63;
tc_plug_w = 13.5; tc_plug_h = 7.5; tc_plug_d = 1.2;  // Aussenmulde fuer die Stecker-Tuelle
mos_w = 17; mos_l = 30;  mos_x = strip_x; mos_y = 37.5;   // MOSFET-Modul
cmp_w = 16; cmp_l = 30;  cmp_x = strip_x;       cmp_y = 5.3; // LM393-Auswertemodul des Regensensors
hx_w = 34; hx_l = 21;    hx_x = 136; hx_y = 60;          // HX711

/* ===================== Pad / Waegezelle ===================== */
pad_size = 90;   pad_gap = 1.0;   pad_r = 4;
open_size = pad_size + 2*pad_gap;          // 92
pad_cx = 126;    pad_cy = D/2;
pad_x0 = pad_cx - pad_size/2;  pad_y0 = pad_cy - pad_size/2;
open_x0 = pad_cx - open_size/2; open_y0 = pad_cy - open_size/2;
lc_l = 80; lc_w = 12.7; lc_h = 12.7;       // 5-kg-Biegebalken (TAL220-Bauform)
lc_hole_end = 5; lc_hole_pitch = 15;       // Loecher bei 5 und 20 mm von jedem Ende (Datenblatt TAL220)
lc_y0 = pad_cy - lc_l/2;  lc_y1 = lc_y0 + lc_l;   // Balken laeuft in Y, mittig unter dem Pad
lc_boss_h = 3.0;                           // Sockel unter festem Ende (M5, hinten, Kabelseite)
lc_z0 = floor_t + lc_boss_h;               // Unterkante Waegezelle = 5
pad_z0 = lc_z0 + lc_h;                     // Unterkante Pad-Rippen/-Sockel = 17.7
pad_under = 2.2;                           // Rippen + Sockel unter der Platte (=Abstandshalter)
pad_t = 2.4;                               // Plattenstaerke
rim_h = 2.3;  rim_w = 1.6;                 // Tropfrand
notch_w = 8;                               // Ablaufkerbe im Rand (links, Richtung Sensor)
rib_t = 1.6;                               // (nicht mehr benutzt)
chan_w = 15;                               // Breite Freikanal ueber der Zelle (Zelle 12,7)
pad_sock_y1 = lc_y0 + lc_hole_end + lc_hole_pitch + 4.5;  // Ende Auflage-Sockel (34.5)
pad_plate_z = pad_z0 + pad_under;          // 19.9
pad_top_z   = pad_plate_z + pad_t;         // 22.3
pad_rim_top = pad_top_z + rim_h;           // 24.6
mat_t = 1.5;

/* ===================== Regensensor / Ablauf ===================== */
rs_w = 40; rs_l = 54;                       // FC-37 / YL-83 Platine
rs_x = 75.5; rs_y = 20; rs_pocket = 0.8;
slit_w = 3; slit_l = 16;                   // Schlitz im Deckel neben der Pad-Kante

/* ===================== LED-Rille vorne ===================== */
led_x0 = 6.5; led_x1 = 173.5;              // 167 mm = 10 LEDs @ 60 LED/m (16,67 mm Raster)
led_z0 = 3.5; led_hb = 10.5; led_d = 3.5;  // Boden, Hoehe Rueckwand, Tiefe
front_in = led_d + 1.6;                    // Innenseite Frontwand (verdickt bis z=16)
front_thick_top = 16;

/* ===================== Fuesse / Schrauben ===================== */
foot_d = 13; foot_depth = 1.0; foot_in = 11;
screw_pilot = 2.5;                         // M3 selbstschneidend (fuer Gewindeeinsatz: 4.0)
cov_bosses = [[77,7],[77,93],[175.5,20],[175.5,80]];
cov_pad_h  = 2;                            // Verdickung unter dem Deckel an Schraubstellen
assert(pad_rim_top <= H, "Pad ragt ueber das Gehaeuse - H erhoehen");
assert(D - cap_plug_d >= D - wall, "Kappen-Stopfen ragt nach innen ueber die Wand (USB-Buchse!)");
assert(cyd_cx + cap_fw/2 < tc_x + tc_w/2 - tc_plug_w/2 - 1, "Kappen-Flansch ueberdeckt die USB-C-Lademulde");
assert(cyd_usb_zc + cap_fh/2 < base_h, "Kappen-Flansch ragt ueber die Wand");
assert(lcd_top_z - cyd_front_h - cyd_pcb_t - cyd_back_h > floor_t + bat_h, "Akku stoesst an CYD");

/* ===================== Hilfsmodule ===================== */
module rrect(w,d,r){ translate([r,r]) offset(r=r) square([w-2*r,d-2*r]); }
module rbox(p,s,r){ translate(p) linear_extrude(s[2]) rrect(s[0],s[1],r); }
module slot_y(cx,cz,w,h,y0,len,r=1.5){        // abgerundete Oeffnung durch eine Wand in Y
  translate([0,y0,0]) rotate([-90,0,0]) linear_extrude(len)
    translate([cx-w/2,-cz-h/2]) rrect(w,h,min(r,h/2-e));
}
module stops(x,y,w,l,h=3,t=1.2,a=4){          // 4 Eck-Anschlaege fuer ein Modul
  for (ix=[0,1]) for (iy=[0,1]) {
    px = ix ? x+w+clr : x-clr-t;  py = iy ? y+l+clr : y-clr-t;
    translate([px, iy ? y+l+clr-a+t : y-clr-t, floor_t-e]) cube([t,a,h]);
    translate([ix ? x+w+clr-a+t : x-clr-t, py, floor_t-e]) cube([a,t,h]);
  }
}

/* ===================== BODENWANNE ===================== */
module outer_shell(h){
  hull(){
    linear_extrude(e) offset(delta=-bot_chamfer) rrect(W,D,R_corner);
    translate([0,0,bot_chamfer]) linear_extrude(h-bot_chamfer) rrect(W,D,R_corner);
  }
}
module led_groove(){
  translate([led_x0,0,0]) rotate([90,0,90]) linear_extrude(led_x1-led_x0)
    polygon([[-1,led_z0],[led_d,led_z0],[led_d,led_z0+led_hb],[-1,led_z0+led_hb+led_d+1]]);
  // Kabelloch vom linken Rillenende nach innen
  translate([led_x0+4, led_d-e, led_z0+5]) rotate([-90,0,0]) cylinder(d=5, h=front_in-led_d+1);
}
module base(){
  difference(){
    union(){
      difference(){
        outer_shell(base_h);
        translate([0,0,floor_t]) linear_extrude(base_h) offset(delta=-wall) rrect(W,D,R_corner);
      }
      // verdickte Frontwand hinter der LED-Rille
      intersection(){
        translate([wall-e, wall-e, floor_t-e]) cube([W-2*wall+2*e, front_in-wall+e, front_thick_top-floor_t]);
        linear_extrude(base_h) rrect(W,D,R_corner);
      }
      // CYD-Abstandshalter (Schraube kommt von oben durch Deckel + CYD)
      for (p=cyd_holes) translate([p[0],p[1],floor_t-e]) cylinder(d=6.5, h=cyd_pcb_z-floor_t+e);
      // Schraubdome fuer den Deckel
      for (p=cov_bosses) hull(){
        translate([p[0],p[1],floor_t-e]) cylinder(d=6, h=base_h-cov_pad_h-floor_t);
        wy = p[1] < D/2 ? wall-1 : D-wall;          // Steg zur Wand
        if (p[0] < W-10) translate([p[0]-2, wy, floor_t-e]) cube([4,1,base_h-cov_pad_h-floor_t]);
      }
      // Sockel fuer festes Ende der Waegezelle (+ seitliche Fuehrung)
      translate([pad_cx-8, lc_y1-(lc_hole_end+lc_hole_pitch+4.5), floor_t-e])
        cube([16, lc_hole_end+lc_hole_pitch+4.5+2, lc_boss_h+e]);
      for (s=[-1,1]) translate([pad_cx + s*(lc_w/2+clr) + (s<0 ? -1.2 : 0), lc_y1-24.5, floor_t-e])
        cube([1.2, 24.5+2, lc_boss_h+1.5]);
      // TC4056: Auflageleisten + Seitenfuehrungen + vorderer Anschlag
      for (xx=[tc_x, tc_x+tc_w-1.5]) translate([xx, tc_y, floor_t-e]) cube([1.5, tc_l, tc_pcb_z-floor_t+e]);
      for (xx=[tc_x-clr-1.2, tc_x+tc_w+clr]) translate([xx, tc_y, floor_t-e]) cube([1.2, tc_l, tc_pcb_z-floor_t+2.5]);
      translate([tc_x+tc_w/2-3, tc_y-clr-1.2, floor_t-e]) cube([6,1.2,tc_pcb_z-floor_t+2]);
      // Anschlaege fuer Akku, Boost, MOSFET, Komparator, HX711
      stops(bat_x, bat_y, bat_w, bat_l, 3);
      stops(boost_x, boost_y, boost_w, boost_l, 2.5);
      stops(mos_x, mos_y, mos_w, mos_l, 3);
      stops(cmp_x, cmp_y, cmp_w, cmp_l, 3);
      stops(hx_x, hx_y, hx_w, hx_l, 3);
    }
    // ---- Schnitte ----
    led_groove();
    // USB des CYD (hinten) und USB-C des Laders (hinten, linke Haelfte)
    slot_y(cyd_cx, cyd_usb_zc, cyd_usb_w, cyd_usb_h, D-wall-1, wall+2, cyd_usb_r);
    slot_y(tc_x+tc_w/2, tc_usb_zc, tc_usb_w, tc_usb_h, D-wall-1, wall+2, 1.5);
    slot_y(tc_x+tc_w/2, tc_usb_zc, tc_plug_w, tc_plug_h, D-tc_plug_d, 2, 2);
    // Fuss-Mulden unten
    for (fx=[foot_in, W-foot_in]) for (fy=[foot_in, D-foot_in])
      translate([fx,fy,-e]) cylinder(d=foot_d, h=foot_depth+e);
    // M5-Senkschrauben (von unten) fuer das feste Ende der Waegezelle
    for (yy=[lc_y1-lc_hole_end, lc_y1-lc_hole_end-lc_hole_pitch]) {
      translate([pad_cx,yy,-e]) cylinder(d=5.5, h=lc_z0+1);
      translate([pad_cx,yy,-e]) cylinder(r1=5.25, r2=0, h=5.25);
    }
    // Bohrungen in Abstandshaltern und Domen (M3 selbstschneidend)
    for (p=cyd_holes) translate([p[0],p[1],cyd_pcb_z-10]) cylinder(d=screw_pilot, h=10+e);
    for (p=cov_bosses) translate([p[0],p[1],base_h-cov_pad_h-11]) cylinder(d=screw_pilot, h=11+e);
    // Mulde fuer Regensensor (Wasser bleibt auf dem Sensor stehen)
    translate([rs_x-0.5, rs_y-0.5, floor_t-rs_pocket]) cube([rs_w+1, rs_l+1, rs_pocket+e]);
  }
}

/* ===================== DECKEL (in Einbaulage) ===================== */
module cover(){
  difference(){
    union(){
      hull(){
        translate([0,0,base_h]) linear_extrude(cover_t-top_chamfer) rrect(W,D,R_corner);
        translate([0,0,H-e]) linear_extrude(e) offset(delta=-top_chamfer) rrect(W,D,R_corner);
      }
      // Zentrierkragen innen an der Wand
      difference(){
        translate([0,0,base_h-1.5]) linear_extrude(1.5+e) difference(){
          offset(delta=-(wall+clr)) rrect(W,D,R_corner);
          offset(delta=-(wall+clr+1.2)) rrect(W,D,R_corner);
        }
        for (p=cov_bosses) translate([p[0],p[1],base_h-3]) cylinder(d=6+1, h=4);
      }
      // Auflagen auf den Schraubdomen
      for (p=cov_bosses) intersection(){
        translate([p[0],p[1],base_h-cov_pad_h]) cylinder(d=6, h=cov_pad_h+e);
        translate([0,0,base_h-cov_pad_h-1]) linear_extrude(cov_pad_h+2) offset(delta=-(wall+clr)) rrect(W,D,R_corner);
      }
      // Klemmhuelsen auf den CYD-Befestigungsloechern
      for (p=cyd_holes) translate([p[0],p[1],cyd_pcb_z+cyd_pcb_t]) cylinder(d=5.5, h=base_h-cyd_pcb_z-cyd_pcb_t+e);
    }
    // Displayfenster (AA + Rand) mit kleiner Fase oben
    hull(){
      translate([cyd_cx-cyd_aa_w/2-win_margin, cyd_cy-cyd_aa_shift-cyd_aa_l/2-win_margin, base_h-1])
        cube([cyd_aa_w+2*win_margin, cyd_aa_l+2*win_margin, H-base_h+0.2]);
      translate([cyd_cx-cyd_aa_w/2-win_margin-0.8, cyd_cy-cyd_aa_shift-cyd_aa_l/2-win_margin-0.8, H-e])
        cube([cyd_aa_w+2*win_margin+1.6, cyd_aa_l+2*win_margin+1.6, 1]);
    }
    // Tasche fuer das LCD-Glas unter dem Deckel
    translate([cyd_cx-(cyd_tp_w+1)/2, cyd_cy-cyd_tp_shift-(cyd_tp_l+2.8)/2, base_h-1])
      cube([cyd_tp_w+1, cyd_tp_l+2.8, 1+lcd_recess]);
    // Pad-Oeffnung + Ablaufschlitz Richtung Regensensor
    translate([open_x0, open_y0, base_h-3]) linear_extrude(H) rrect(open_size, open_size, pad_r+1);
    translate([open_x0-slit_w, pad_cy-slit_l/2, base_h-3]) cube([slit_w+1, slit_l, H]);
    // Schraubloecher M3 mit Senkung (DIN 965 / ISO 7046)
    for (p=concat(cyd_holes, cov_bosses)) {
      translate([p[0],p[1],base_h-5]) cylinder(d=3.4, h=10);
      translate([p[0],p[1],H-1.7]) cylinder(r1=1.7, r2=3.4, h=1.7+e);
    }
  }
}

/* ===================== PAD (in Einbaulage) ===================== */
module pad(){
  difference(){
    union(){
      rbox([pad_x0,pad_y0,pad_plate_z],[pad_size,pad_size,pad_t],pad_r);
      // Tropfrand mit Ablaufkerbe links
      difference(){
        translate([pad_x0,pad_y0,pad_top_z-e]) linear_extrude(rim_h+e) difference(){
          rrect(pad_size,pad_size,pad_r);
          translate([rim_w,rim_w]) rrect(pad_size-2*rim_w,pad_size-2*rim_w,pad_r-rim_w);
        }
        translate([pad_x0-1, pad_cy-notch_w/2, pad_top_z]) cube([rim_w+2, notch_w, rim_h+1]);
      }
      // Unterseite: massiv (Sandwich-Platte, 20 % Infill) bis auf den Kanal ueber der Waegezelle
      rbox([pad_x0,pad_y0,pad_z0],[pad_size,pad_size,pad_under+e],pad_r);
    }
    // Freikanal ueber dem Biegebalken: Pad beruehrt die Zelle NUR am vorderen Ende (Sockel, Y < pad_sock_y1)
    translate([pad_cx-chan_w/2, pad_sock_y1, pad_z0-1]) cube([chan_w, pad_y0+pad_size-pad_sock_y1+1, pad_under+1]);
    // M4-Senkschrauben von oben in das freie Ende der Waegezelle
    for (yy=[lc_y0+lc_hole_end, lc_y0+lc_hole_end+lc_hole_pitch]) {
      translate([pad_cx,yy,pad_z0-1]) cylinder(d=4.5, h=10);
      translate([pad_cx,yy,pad_top_z-4.3]) cylinder(r1=0, r2=4.3, h=4.3+e);
    }
  }
}


/* ===================== ABDECKKAPPE (USB-Ausschnitt CYD) ===================== */
// Modelliert in Drucklage: Flansch-Aussenseite auf dem Druckbett (z=0), Stopfen zeigt nach oben.
// u = Breite (X), v = Hoehe (Z im Geraet), w = Druckhoehe (zeigt im Geraet nach innen, -Y)
module cap_print(){
  pw = cyd_usb_w - 2*cap_clr;  ph = cyd_usb_h - 2*cap_clr;  pr = cyd_usb_r - cap_clr;
  w1 = cap_flange_t + cap_plug_d;
  difference(){
    union(){
      // Flansch mit 45-Grad-Fase an der sichtbaren Aussenkante (liegt auf dem Bett -> ohne Stuetzen)
      hull(){
        linear_extrude(e) offset(delta=-cap_chamfer) rrect_c(cap_fw, cap_fh, cyd_usb_r+cap_rand);
        translate([0,0,cap_chamfer]) linear_extrude(cap_flange_t-cap_chamfer) rrect_c(cap_fw, cap_fh, cyd_usb_r+cap_rand);
      }
      // hohler Stopfen mit kleiner Einfuehrfase oben
      hull(){
        translate([0,0,cap_flange_t-e]) linear_extrude(cap_plug_d-0.3+e) rrect_c(pw, ph, pr);
        translate([0,0,w1-e]) linear_extrude(e) offset(delta=-0.3) rrect_c(pw, ph, pr);
      }
      // Quetschrippen (oben/unten 4x, links/rechts je 1x), laufen in Steckrichtung, oben angeschraegt
      for (u=cap_rib_x) for (s=[-1,1]) cap_rib([u, s*ph/2], s>0 ? 0 : 180);
      for (s=[-1,1]) cap_rib([s*pw/2, 0], s>0 ? -90 : 90);
    }
    // Hohlraum (offen zur Geraete-Innenseite = oben beim Druck)
    translate([0,0,cap_flange_t]) linear_extrude(cap_plug_d+1)
      rrect_c(pw-2*cap_shell, ph-2*cap_shell, max(0.5, pr-cap_shell));
    // Fingernagel-Kerbe: unten mittig in der Flanschrueckseite -> Spalt zur Wand zum Aushebeln
    translate([-cap_notch_w/2, -cap_fh/2-1, cap_flange_t-cap_notch_d]) cube([cap_notch_w, cap_rand+1+e, cap_notch_d+e]);
  }
}
module rrect_c(w,h,r){ translate([-w/2,-h/2]) rrect(w,h,r); }
module cap_rib(p, ang){            // Dreieckrippe, Spitze cap_rib_h ueber der Flaeche
  L = cap_plug_d - 0.4;
  translate([p[0],p[1],cap_flange_t-e]) rotate([0,0,ang]) hull(){
    linear_extrude(L-0.6) polygon([[-cap_rib_w/2,-0.4],[cap_rib_w/2,-0.4],[0,cap_rib_h]]);
    translate([0,0,L-e]) linear_extrude(e) polygon([[-cap_rib_w/4,-0.4],[cap_rib_w/4,-0.4],[0,0]]);
  }
}
// Einbaulage: Flansch aussen an der Rueckwand (y = D ... D+1,2), Stopfen in der Wand
module cap(){
  translate([cyd_cx, D + cap_flange_t + cap_pull, cyd_usb_zc]) rotate([90,0,0]) cap_print();
}

/* ===================== Dummy-Bauteile fuer Vorschau ===================== */
module loadcell(){
  color("silver") difference(){
    translate([pad_cx-lc_w/2, lc_y0, lc_z0]) cube([lc_w, lc_l, lc_h]);
    translate([pad_cx-lc_w/2-1, pad_cy, lc_z0+lc_h/2]) rotate([0,90,0]) cylinder(d=8, h=lc_w+2);
  }
}
module components(){
  // CYD
  color("goldenrod") translate([cyd_x,cyd_y,cyd_pcb_z]) linear_extrude(cyd_pcb_t) rrect(cyd_w,cyd_l,3);
  color([0.08,0.08,0.1]) translate([cyd_cx-cyd_tp_w/2, cyd_cy-cyd_tp_shift-cyd_tp_l/2, cyd_pcb_z+cyd_pcb_t]) cube([cyd_tp_w,cyd_tp_l,cyd_front_h]);
  color([0.2,0.25,0.35]) translate([cyd_cx-cyd_aa_w/2, cyd_cy-cyd_aa_shift-cyd_aa_l/2, lcd_top_z]) cube([cyd_aa_w,cyd_aa_l,0.05]);
  color("dimgray") translate([cyd_x+8, cyd_y+50, cyd_pcb_z-3.2]) cube([18,25.5,3.2]);   // ESP32-Modul (Lage ca.)
  color("silver") translate([cyd_cx+4.5, D-wall-cyd_back_gap-7, cyd_pcb_z-3.2]) cube([9,7.6,3.2]); // USB
  // Akku, Module
  color("lightsteelblue") translate([bat_x,bat_y,floor_t]) cube([bat_w,bat_l,bat_h]);
  color("darkblue")  translate([tc_x,tc_y,tc_pcb_z]) cube([tc_w,tc_l,1.6]);
  color("silver")    translate([tc_x+tc_w/2-4.5, D-wall-7.3, tc_pcb_z+1.6]) cube([9,7.3,3.2]);
  color("purple")    translate([boost_x,boost_y,floor_t+1]) cube([boost_w,boost_l,6]);
  color("darkred")   translate([mos_x,mos_y,floor_t]) cube([mos_w,mos_l,8]);
  color("darkgreen") translate([cmp_x,cmp_y,floor_t]) cube([cmp_w,cmp_l,6]);
  color("green")     translate([hx_x,hx_y,floor_t]) cube([hx_w,hx_l,5]);
  color("teal")      translate([rs_x,rs_y,floor_t-rs_pocket]) cube([rs_w,rs_l,1.6]);
  // LED-Streifen in der Rille
  color("white") translate([led_x0+2, led_d-0.4, led_z0+0.2]) cube([led_x1-led_x0-4, 0.4, 10]);
  for (i=[0:9]) color("gold") translate([led_x0+5.8+i*16.67, led_d-2, led_z0+3]) cube([5,1.6,5]);
  loadcell();
}
module mat(){ color([0.25,0.25,0.25]) translate([pad_x0+rim_w+0.5, pad_y0+rim_w+0.5, pad_top_z]) cube([pad_size-2*rim_w-1, pad_size-2*rim_w-1, mat_t]); }

housing_col = [0.82,0.82,0.82];
pad_col     = [0.15,0.45,0.85];

/* ===================== Auswahl ===================== */
if (part == "base") base();
else if (part == "cover") rotate([180,0,0]) translate([0,0,-H]) cover();   // Oberseite aufs Druckbett
else if (part == "pad")   translate([0,0,-pad_z0]) pad();                    // Rippen aufs Druckbett
else if (part == "cap")   cap_print();                                       // Flansch-Aussenseite aufs Druckbett
else if (part == "cap_check_cyd")  intersection(){ cap(); components(); }    // muss LEER sein
else if (part == "cap_check_base") intersection(){ cap(); base(); }          // nur Quetschrippen (Uebermass)
else if (part == "assembly") {
  color(housing_col) base(); color(housing_col) cover(); color(housing_col) cap();
  color(pad_col) pad(); mat(); components();
}
else if (part == "inside") {
  color(housing_col) base(); components();
}
else if (part == "exploded") {
  color(housing_col) base(); components();
  translate([0,0,35]) { color(pad_col) pad(); translate([0,0,8]) mat(); }
  translate([0,0,85]) color(housing_col) cover();
  translate([0,30,0]) color(housing_col) cap();       // Kappe nach hinten herausgezogen
}
else if (part == "section") {     // Schnitt bei X = Displaymitte und X = Pad-Mitte (zur Kontrolle)
  for (cx=[cyd_cx, pad_cx]) translate([-cx, 0, cx < 100 ? 0 : 35]) intersection(){
    translate([cx, -1, -1]) cube([W, D+2, H+5]);
    union(){ color(housing_col) base(); color(housing_col) cover(); color(housing_col) cap(); color(pad_col) pad(); mat(); components(); }
  }
}
