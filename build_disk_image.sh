#!/bin/sh

# Create a folder (named dmg) to prepare our DMG in (if it doesn't already exist).
mkdir -p dist/dmg

# Empty the dmg folder.
rm -r dist/dmg/*

# Copy the app bundle to the dmg folder.
cp -r "dist/Selecta.app" dist/dmg

# If the DMG already exists, delete it.
test -f "dist/Selecta.dmg" && rm "dist/Selecta.dmg"
create-dmg \
  --volname "Selecta" \
  --window-pos 200 120 \
  --window-size 600 300 \
  --icon-size 100 \
  --icon "Selecta.app" 175 120 \
  --hide-extension "Selecta.app" \
  --app-drop-link 425 120 \
  "dist/Selecta.dmg" \
  "dist/dmg/"
