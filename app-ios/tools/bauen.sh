#!/bin/bash
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Baut die HydroDesk-App für ein echtes iPhone (ohne die Xcode-Oberfläche zu öffnen).
# Aufruf:  tools/bauen.sh            (vom Ordner app-ios aus, oder per VS-Code-Task)
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -f Config/Secrets.xcconfig ]; then
  echo "FEHLER: Config/Secrets.xcconfig fehlt."
  echo "Bitte erst anlegen:  cp Config/Secrets.xcconfig.example Config/Secrets.xcconfig  und ausfüllen."
  exit 1
fi

xcodebuild \
  -project HydroDesk.xcodeproj \
  -scheme HydroDesk \
  -configuration Debug \
  -destination 'generic/platform=iOS' \
  -derivedDataPath build \
  -allowProvisioningUpdates \
  -skipMacroValidation \
  build
echo
echo "Fertig: build/Build/Products/Debug-iphoneos/HydroDesk.app"
