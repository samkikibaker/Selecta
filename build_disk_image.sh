#!/bin/sh

# Create a folder (named dmg) to prepare our DMG in (if it doesn't already exist).
mkdir -p dist/dmg

# Empty the dmg folder.
rm -r dist/dmg/*

# Copy the app bundle to the dmg folder.
cp -r "dist/selecta.app" dist/dmg

# If the DMG already exists, delete it.
test -f "dist/selecta.dmg" && rm "dist/selecta.dmg"
create-dmg \
  --volname "selecta" \
  --window-pos 200 120 \
  --window-size 600 300 \
  --icon-size 100 \
  --icon "selecta.app" 175 120 \
  --hide-extension "selecta.app" \
  --app-drop-link 425 120 \
  "dist/selecta.dmg" \
  "dist/dmg/"