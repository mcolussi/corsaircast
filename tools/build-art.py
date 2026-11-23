#!/usr/bin/env python3
"""Generates the site's art: `depths.svg` (the hero scene) and `icon.svg` (the app icon, flat).

Run from anywhere: `python3 -I tools/build-art.py`. The SVGs are committed; this is their source.
The colours here are the page's tokens in index.html — change both together.
"""
import math, os, pathlib, re

SITE = pathlib.Path(__file__).resolve().parent.parent
# The app's icon lives in the app repo, checked out next to this one; ICON_ASSETS overrides.
ICON_ASSETS = pathlib.Path(os.environ.get("ICON_ASSETS", SITE.parent / "blue_harvest/App/CorsairCast.icon/Assets"))

SKY, SEA_TOP, ABYSS = "#0d1524", "#16263d", "#05080e"
INK, CASTLE, MOON, RED = "#03060b", "#0a1120", "#e8e2d2", "#ee3934"


def tentacle(x0, y0, heading_deg, length, w0, k0, k1, p=2.2, n=150, tip=1.2):
    """A tapering silhouette whose curvature ramps from k0 to k1 toward the tip, so it ends in a curl."""
    th, x, y, ds, pts = math.radians(heading_deg), x0, y0, length / n, []
    for i in range(n + 1):
        s = i / n
        k = k0 + (k1 - k0) * s ** p
        # Never wider than the curl's radius, or the inner edge folds back on itself in a sliver.
        w = min(w0 * (1 - s) ** 1.05, 0.7 / max(abs(k), 1e-6))
        pts.append((x, y, th, max(tip, w)))
        th += k * ds
        x, y = x + math.cos(th) * ds, y + math.sin(th) * ds
    side = lambda sign: [(x + math.cos(t + sign * math.pi / 2) * w, y + math.sin(t + sign * math.pi / 2) * w)
                         for x, y, t, w in pts]
    ring = side(-1) + side(1)[::-1]
    return "M" + " L".join(f"{a:.1f} {b:.1f}" for a, b in ring) + "Z"


# (base x, base y — below the canvas so no cut end shows, heading — -90 is straight up, length, base half-width, curvature start, curvature at tip)
# Negative curvature curls counter-clockwise. They rise under the castle and stop well short of the ship.
TENTACLES = [
    (150, 1180, -80, 700, 48, 0.0006, 0.022),
    (330, 1200, -95, 820, 56, -0.0008, -0.020),
    (560, 1210, -66, 860, 50, -0.0012, 0.026),
    (40, 1160, -60, 560, 38, -0.0004, 0.030),
    (760, 1220, -58, 600, 40, 0.0010, -0.028),
    (440, 1220, -100, 500, 30, 0.0006, 0.034),
]

HORIZON = 420

SHIP = f"""
  <g id="ship" fill="{INK}">
    <!-- hull: raised stern at left, the bow and bowsprit pointing right, away from the castle -->
    <path d="M962 384 L996 384 L1000 398 L1150 398 L1176 392 L1212 386 L1214 389 L1172 404 L1150 432 Q1070 440 992 432 L966 404Z"/>
    <rect x="1029" y="262" width="4" height="138"/>
    <rect x="1104" y="286" width="4" height="114"/>
    <path d="M1031 276 Q1066 300 1068 336 Q1068 362 1060 382 L1031 382Z"/>
    <path d="M1031 276 Q1002 300 1000 336 Q1000 362 1008 382 L1031 382Z" opacity=".9"/>
    <path d="M1106 302 Q1134 322 1136 350 Q1136 370 1130 386 L1106 386Z"/>
    <path d="M1106 302 Q1082 322 1080 350 Q1080 370 1086 386 L1106 386Z" opacity=".9"/>
    <path d="M1108 290 L1210 386 L1112 386Z" opacity=".85"/>
  </g>
  <path id="flag" fill="{RED}" d="M1033 262 L1062 266 L1054 271 L1062 276 L1033 276Z"/>
  <circle cx="968" cy="378" r="9" fill="{RED}" opacity=".18"/>
  <circle cx="968" cy="378" r="3.2" fill="{RED}"/>"""

# Kafka's castle on the far horizon: towers, one lit window, the office no one has seen.
CASTLE_SVG = f"""
  <g fill="{CASTLE}">
    <path d="M60 {HORIZON} Q150 360 250 352 Q360 346 470 372 Q520 392 560 {HORIZON}Z"/>
    <rect x="170" y="296" width="44" height="80"/><path d="M166 296 L192 258 L218 296Z"/>
    <rect x="236" y="250" width="58" height="122"/><path d="M232 250 L265 196 L298 250Z"/>
    <rect x="312" y="300" width="40" height="70"/><path d="M308 300 L332 268 L356 300Z"/>
    <rect x="370" y="322" width="64" height="52"/>
    <rect x="376" y="312" width="8" height="12"/><rect x="392" y="312" width="8" height="12"/>
    <rect x="408" y="312" width="8" height="12"/><rect x="424" y="312" width="8" height="12"/>
  </g>
  <rect x="261" y="286" width="5" height="9" fill="#c9b37a" opacity=".55"/>"""


# The scene moves like the App Store header (tools/build-header.py): a 10 s loop where the ship bobs twice, the
# glints shimmer and the tentacles writhe once. The glints run slower than the header's 2.5 s shimmer and 5 s drift
# (user, 2026-11-23: a little slower on the page), so they're off the loop, which a CSS animation doesn't need.
# The writhe is SMIL, since CSS can't morph a path in every browser; SMIL ignores prefers-reduced-motion, so
# index.html swaps in depths-still.svg for that.
LOOP, WRITHE_KEYS = 10.0, 16
SHIMMER, DRIFT = 6.0, 12.0  # seconds per cycle


def writhe(i, x0, y0, h, length, w0, k0, k1):
    """One tentacle's writhe, keyed like the header's frames: the heading sways, the curl tightens and loosens."""
    wave = lambda t, phase: math.sin(2 * math.pi * t / LOOP + phase)
    keys = [LOOP * j / WRITHE_KEYS for j in range(WRITHE_KEYS)] + [0.0]
    values = ";".join(tentacle(x0, y0, h + 3.5 * wave(t, i * 1.1), length, w0, k0,
                               k1 * (1 + 0.12 * wave(t, i * 1.1 + 1.2))) for t in keys)
    return f'<animate attributeName="d" dur="{LOOP:g}s" repeatCount="indefinite" values="{values}"/>'


def depths(animated=True):
    tentacles = "\n".join(
        f'    <path d="{tentacle(*t)}">\n      {writhe(i, *t)}\n    </path>' if animated else f'    <path d="{tentacle(*t)}"/>'
        for i, t in enumerate(TENTACLES))
    # Each glint fades and drifts on its own phase, as in the header (negative delays start them mid-cycle).
    glints = "\n".join(
        f'    <rect x="{1260 - w / 2 + dx:.0f}" y="{y}" width="{w}" height="1.6" rx=".8"'
        + (f' style="animation-delay: {-SHIMMER * ((i * 1.3) % (2 * math.pi)) / (2 * math.pi):.2f}s,'
           f' {-DRIFT * ((i * 0.9) % (2 * math.pi)) / (2 * math.pi):.2f}s"' if animated else "") + "/>"
        for i, (y, w, dx) in enumerate(
            [(432, 90, 0), (446, 64, 14), (462, 110, -10), (480, 46, 6), (500, 80, -4), (524, 36, 12)]))
    motion = """
    #vessel { animation: bob 5s ease-in-out infinite; transform-origin: 1080px 420px; }
    @keyframes bob { 0%, 100% { transform: translateY(-3px) rotate(.8deg); } 50% { transform: translateY(3px) rotate(-.8deg); } }
    #glints rect { animation: shimmer SHIMMERs ease-in-out infinite, drift DRIFTs ease-in-out infinite; }
    @keyframes shimmer { 0%, 100% { opacity: .55; } 25% { opacity: 1; } 75% { opacity: .1; } }
    @keyframes drift { 0%, 100% { transform: none; } 25% { transform: translateX(5px); } 75% { transform: translateX(-5px); } }
    @media (prefers-reduced-motion: reduce) { #vessel, #glints rect { animation: none; } }""".replace(
        "SHIMMERs", f"{SHIMMER:g}s").replace("DRIFTs", f"{DRIFT:g}s") if animated else ""
    glint_id = ' id="glints"' if animated else ""  # build-header.py matches the still group's exact text.
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1100" preserveAspectRatio="xMidYMid slice">
  <!-- Generated by tools/build-art.py — edit that, not this. -->
  <defs>
    <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{SKY}"/><stop offset="1" stop-color="#16223a"/>
    </linearGradient>
    <linearGradient id="sea" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{SEA_TOP}"/><stop offset=".45" stop-color="#0b1424"/>
      <stop offset="1" stop-color="{ABYSS}"/>
    </linearGradient>
    <radialGradient id="halo"><stop offset="0" stop-color="{MOON}" stop-opacity=".16"/>
      <stop offset="1" stop-color="{MOON}" stop-opacity="0"/></radialGradient>
  </defs>
  <style>{motion}
  </style>
  <rect width="1600" height="{HORIZON + 1}" fill="url(#sky)"/>
  <!-- The halo stays inside the canvas: clipped at the top edge it reads as a hard-edged box. -->
  <circle cx="1260" cy="200" r="190" fill="url(#halo)"/>
  <circle cx="1260" cy="200" r="62" fill="{MOON}"/>
  {CASTLE_SVG}
  <g id="vessel">{SHIP}
  </g>
  <rect y="{HORIZON}" width="1600" height="{1100 - HORIZON}" fill="url(#sea)"/>
  <rect y="{HORIZON}" width="1600" height="1.2" fill="{MOON}" opacity=".18"/>
  <g{glint_id} fill="{MOON}" opacity=".32">
{glints}
  </g>
  <g fill="{INK}">
{tentacles}
  </g>
</svg>
"""


def icon(radius=228):
    """The App Store icon's Default appearance, flattened: red tile, white head, pink headphones.
    radius=0 is the home-screen variant: iOS masks apple-touch-icon itself, so rounded corners would show black."""
    def body(name):
        s = (ICON_ASSETS / name).read_text()
        s = re.sub(r"<!--.*?-->", "", s, flags=re.S)
        return s[s.index("<defs>") if "<defs>" in s else s.index("<g"):s.rindex("</svg>")].strip()
    head = body("02-cat-head.svg").replace('id="artwork"', 'fill="#fffbfb"')
    phones = body("01-headphones.svg").replace('id="artwork"', 'fill="#ffbab8"')
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024">
  <!-- Generated by tools/build-art.py from the app repo's App/CorsairCast.icon — edit that, not this. -->
  <rect width="1024" height="1024" rx="{radius}" fill="{RED}"/>
  {head}
  {phones}
</svg>
"""


if __name__ == "__main__":  # tools/build-header.py imports the scene without writing it.
    (SITE / "depths.svg").write_text(depths())
    (SITE / "depths-still.svg").write_text(depths(animated=False))
    (SITE / "icon.svg").write_text(icon())
    (SITE / "tools/touch-icon.svg").write_text(icon(radius=0))
    print("wrote depths.svg, depths-still.svg, icon.svg, tools/touch-icon.svg — now run tools/render-png.sh")
