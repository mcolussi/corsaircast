#!/usr/bin/env python3
"""The App Store product page header, from the site's scene: `app-store/header.png` and `app-store/header.mov`.

Run from anywhere: `python3 -I tools/build-header.py` (needs rsvg-convert and the Swift toolchain).

Apple's header is 3840 × 1646 (21:9), and only its centred art safe area — 1646 × 661 at (1097, 493) — is
promised on every device, so the scene is CROPPED rather than scaled: the horizon just below the middle, the ship
moved left into the safe area, and the tentacles lifted into the lower sea (they sit below the safe area, so a
narrow crop loses them and keeps the ship). The castle and moon are scenery for the wider screens.

The video is a 10 s loop at 30 fps. Every motion completes a whole number of cycles in the loop, so the last frame
flows into the first: the ship bobs twice, the glints shimmer four times, the tentacles writhe once. Its first frame
is the still, which is also the video's poster frame.
"""
import importlib.util, math, pathlib, re, subprocess, tempfile

TOOLS = pathlib.Path(__file__).resolve().parent
SITE = TOOLS.parent
OUT = SITE / "app-store"
spec = importlib.util.spec_from_file_location("build_art", TOOLS / "build-art.py")
art = importlib.util.module_from_spec(spec)
spec.loader.exec_module(art)

W, H, FPS, LOOP = 3840, 1646, 30, 10.0
CROP_TOP, SHIP_SHIFT, TENTACLE_LIFT = 43, -260, -150  # viewBox units; the scene is 1600 wide, so 1 unit = 2.4 px
GLINTS = [(432, 90, 0), (446, 64, 14), (462, 110, -10), (480, 46, 6), (500, 80, -4), (524, 36, 12)]


def wave(t, cycles, phase=0.0):
    return math.sin(2 * math.pi * cycles * t / LOOP + phase)


def frame(t):
    s = art.depths()
    s = s.replace('viewBox="0 0 1600 1100" preserveAspectRatio="xMidYMid slice"',
                  f'viewBox="0 {CROP_TOP} 1600 {1600 * H / W:.0f}" width="{W}" height="{H}"')
    s = re.sub(r"<style>.*?</style>", "", s, flags=re.S)  # The site's CSS bob; the frames move the ship instead.
    # The ship: two bobs per loop, a slight roll that leads the heave.
    dy, roll = 3.0 * wave(t, 2), -0.8 * wave(t, 2, 0.7)
    s = s.replace('<g id="vessel">', f'<g transform="translate({SHIP_SHIFT} {dy:.3f}) rotate({roll:.3f} 1080 420)">'
                  '<g id="vessel">', 1)
    s = s.replace("\n  </g>\n  <rect y=", "\n  </g></g>\n  <rect y=", 1)
    # The glints: each fades and drifts on its own phase.
    glints = "\n".join(
        f'    <rect x="{1260 - w / 2 + dx + 5 * wave(t, 2, i * 0.9):.1f}" y="{y}" width="{w}" height="1.6" rx=".8"'
        f' opacity="{0.55 + 0.45 * wave(t, 4, i * 1.3):.3f}"/>' for i, (y, w, dx) in enumerate(GLINTS))
    s, n = re.subn(rf'(<g fill="{art.MOON}" opacity="\.32">\n).*?(\n  </g>)', lambda m: m[1] + glints + m[2], s,
                   count=1, flags=re.S)
    assert n == 1, "the glints' group moved in build-art.py"
    # The tentacles: one slow writhe — the heading sways and the curl tightens and loosens.
    arms = "\n".join(
        f'    <path d="{art.tentacle(x0, y0, h + 3.5 * wave(t, 1, i * 1.1), length, w0, k0, k1 * (1 + 0.12 * wave(t, 1, i * 1.1 + 1.2)))}"/>'
        for i, (x0, y0, h, length, w0, k0, k1) in enumerate(art.TENTACLES))
    s, n = re.subn(rf'<g fill="{art.INK}">\n    <path d="M.*?(\n  </g>)',
                   lambda m: f'<g fill="{art.INK}" transform="translate(0 {TENTACLE_LIFT})">\n' + arms + m[1], s,
                   count=1, flags=re.S)
    assert n == 1, "the tentacles' group moved in build-art.py"
    return s


OUT.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory() as tmp:
    frames = pathlib.Path(tmp)
    count = int(FPS * LOOP)
    for i in range(count):
        (frames / f"f{i:04d}.svg").write_text(frame(i / FPS))
    subprocess.run(f'ls *.svg | xargs -P 8 -I{{}} sh -c \'rsvg-convert -w {W} -h {H} -b "{art.SKY}" "{{}}" '
                   f'-o "$(basename {{}} .svg).png"\'', shell=True, cwd=frames, check=True)
    for svg in frames.glob("*.svg"):
        svg.unlink()
    (frames / "f0000.png").replace(OUT / "header.png")
    subprocess.run(["cp", str(OUT / "header.png"), str(frames / "f0000.png")], check=True)
    subprocess.run(["swift", str(TOOLS / "encode-header.swift"), str(frames), str(OUT / "header.mov")], check=True)
print("wrote app-store/header.png and app-store/header.mov")
