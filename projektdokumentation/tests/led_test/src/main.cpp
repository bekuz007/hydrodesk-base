#include <Arduino.h>
#include <FastLED.h>

#define DATA_PIN 27   // gelbes Kabel am CN1
#define NUM_LEDS 160  // ganzer Streifen (1 m)
CRGB leds[NUM_LEDS];

void setup() {
  FastLED.addLeds<WS2812B, DATA_PIN, GRB>(leds, NUM_LEDS);
  FastLED.setBrightness(10);  // niedrig: nur 3,3 V vom CYD
}

void loop() {
  fill_solid(leds, NUM_LEDS, CRGB::Red);   FastLED.show(); delay(500);
  fill_solid(leds, NUM_LEDS, CRGB::Green); FastLED.show(); delay(500);
  fill_solid(leds, NUM_LEDS, CRGB::Blue);  FastLED.show(); delay(500);
}
