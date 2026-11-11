#!/bin/bash
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Baut die App, installiert sie auf dem iPhone (Kabel) und startet sie.
# Aufruf:  tools/run-device.sh "Name-oder-ID-deines-iPhones"
# Die Namen/IDs zeigt:  xcrun devicectl list devices
set -euo pipefail
cd "$(dirname "$0")/.."

GERAET="${1:-}"
if [ -z "$GERAET" ]; then
  echo "Bitte den Namen oder die ID deines iPhones angeben. Diese Geräte sind bekannt:"
  echo
  xcrun devicectl list devices
  echo
  echo "Dann:  tools/run-device.sh \"Name oder ID\""
  exit 1
fi

./tools/bauen.sh

# Bundle-ID aus Secrets.xcconfig lesen (Zeile APP_BUNDLE_ID = ...)
BUNDLE_ID="$(grep -E '^[[:space:]]*APP_BUNDLE_ID[[:space:]]*=' Config/Secrets.xcconfig | tail -1 | sed -E 's/^[^=]*=[[:space:]]*//; s/[[:space:]]*(\/\/.*)?$//' | tr -d '\r')"
if [ -z "$BUNDLE_ID" ]; then
  echo "FEHLER: APP_BUNDLE_ID in Config/Secrets.xcconfig ist leer."
  exit 1
fi

APP="build/Build/Products/Debug-iphoneos/HydroDesk.app"
echo "Installiere $APP auf \"$GERAET\" …"
xcrun devicectl device install app --device "$GERAET" "$APP"
echo "Starte $BUNDLE_ID …"
xcrun devicectl device process launch --device "$GERAET" --terminate-existing "$BUNDLE_ID"
echo
echo "Läuft. Falls iOS meldet \"Nicht vertrauenswürdiger Entwickler\": Einstellungen > Allgemein > VPN & Geräteverwaltung."
