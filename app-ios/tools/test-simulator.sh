#!/bin/bash
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Führt die XCTest-Unit-Tests im iPhone-Simulator aus (der erste verfügbare iPhone-Simulator wird genommen).
set -euo pipefail
cd "$(dirname "$0")/.."

NAME="$(xcrun simctl list devices available | grep -E '^[[:space:]]+iPhone' | head -1 | sed -E 's/^[[:space:]]+(.*) \([0-9A-F-]{36}\).*/\1/')"
if [ -z "$NAME" ]; then
  echo "FEHLER: Kein iPhone-Simulator gefunden. In Xcode: Settings > Components eine iOS-Runtime laden."
  exit 1
fi
echo "Teste im Simulator: $NAME"
xcodebuild test \
  -project HydroDesk.xcodeproj \
  -scheme HydroDesk \
  -destination "platform=iOS Simulator,name=$NAME" \
  -derivedDataPath build \
  CODE_SIGNING_ALLOWED=NO
