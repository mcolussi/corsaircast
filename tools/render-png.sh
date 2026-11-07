#!/bin/zsh
# Renders the site's PNGs with headless Chrome: apple-touch-icon.png (180², from tools/touch-icon.svg) and
# og.png (1200×630, from tools/og.html). Run after tools/build-art.py.
set -euo pipefail
cd "$(dirname "$0")/.."
chrome="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
shot() { "$chrome" --headless --disable-gpu --hide-scrollbars --allow-file-access-from-files \
           --virtual-time-budget=3000 --window-size="$2" --screenshot="$PWD/$3" "file://$PWD/$1" 2>/dev/null; }
# Headless Chrome will not lay out a window narrower than ~500px, so render large and scale down.
shot tools/touch-icon.svg 540,540 apple-touch-icon.png
sips -z 180 180 apple-touch-icon.png >/dev/null
shot tools/og.html 1200,630 og.png
file apple-touch-icon.png og.png
