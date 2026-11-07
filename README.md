# Corsair Cast — website

The static site at https://mcolussi.github.io/corsaircast/ (GitHub Pages, `main`, root). The App Store
Support URL. The privacy policy is a separate repo, `corsaircast-privacy`, whose URL ships in the app.

The copy follows the App Store listing (`docs/app-store/listing.md` in the app repo); change both together.

## Regenerating the art

    python3 -I tools/build-art.py   # depths.svg, icon.svg, tools/touch-icon.svg (reads the app repo's icon)
    tools/render-png.sh             # apple-touch-icon.png and og.png, with headless Chrome

Fonts are self-hosted under the SIL Open Font License (`fonts/OFL-*.txt`).
