#include <Arduino.h>
// Regensensor-Test: LM393 DO an IO27 (LOW = nass)
const int PIN = 27;
void setup(){ Serial.begin(115200); pinMode(PIN, INPUT_PULLUP); Serial.println("Regensensor-Test gestartet"); }
void loop(){ Serial.println(digitalRead(PIN)==LOW ? "NASS" : "trocken"); delay(500); }
