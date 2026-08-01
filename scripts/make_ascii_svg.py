#!/usr/bin/env python3
"""Turn source-prepped.png into a self-typing, monochrome ASCII SVG.

The image is downsampled to a ~100x53 character grid; each cell's brightness
picks a glyph from a density ramp. Every row is wrapped in a clip that wipes
left-to-right (a block cursor rides the wipe edge), staggered top to bottom.
SMIL animation, plays once, freezes. GitHub renders it.

Usage:
    python scripts/make_ascii_svg.py                # uses source-prepped.png
    python scripts/make_ascii_svg.py --demo         # placeholder silhouette
    STATIC=1 python scripts/make_ascii_svg.py       # frozen frame, no animation

Output: tushar-ascii.svg
"""
import os
import sys
import pathlib

from PIL import Image, ImageDraw, ImageFilter

SRC = "source-prepped.png"
OUT = "tushar-ascii.svg"

COLS, ROWS = 100, 53
RAMP = " .`:-=+*cs#%@"      # bright (sparse) -> dark (dense)
#       ^ leading space clears the background to nothing

CHAR_W, LINE_H = 6.0, 10.0  # monospace advance at font-size 10
FONT_SIZE = 10
INK = "#c9d1d9"             # one light-gray fill - never per-char rainbow
CURSOR = "#39d353"
ROW_DUR = 0.42              # seconds for one row to wipe in
ROW_STAGGER = 0.055         # delay between consecutive rows
STATIC = os.environ.get("STATIC") == "1"
# --light-on-dark: bright pixels become dense glyphs (for lit-subject-on-black
# photos rendered straight onto the terminal canvas, no background removal)
LIGHT_ON_DARK = "--light-on-dark" in sys.argv
# in light-on-dark mode anything below FLOOR is treated as empty background
FLOOR = float(sys.argv[sys.argv.index("--floor") + 1]) if "--floor" in sys.argv else 0.30
GAMMA = float(sys.argv[sys.argv.index("--gamma") + 1]) if "--gamma" in sys.argv else 0.85


def demo_image() -> Image.Image:
    """A soft placeholder bust so the layout can be previewed without a photo."""
    w, h = 600, 700
    img = Image.new("L", (w, h), 255)
    d = ImageDraw.Draw(img)
    d.ellipse((190, 90, 410, 360), fill=105)          # head
    d.ellipse((205, 110, 395, 340), fill=150)         # face light
    d.ellipse((150, 380, 450, 700), fill=80)          # shoulders
    d.ellipse((235, 195, 275, 225), fill=35)          # eyes
    d.ellipse((325, 195, 365, 225), fill=35)
    d.arc((255, 240, 345, 300), 20, 160, fill=45, width=8)  # mouth
    return img.filter(ImageFilter.GaussianBlur(6))


def load_source() -> Image.Image:
    if "--demo" in sys.argv or not pathlib.Path(SRC).exists():
        if "--demo" not in sys.argv:
            print(f"! {SRC} not found - rendering the demo silhouette instead")
        return demo_image()
    return Image.open(SRC).convert("L")


def autocrop(img: Image.Image) -> Image.Image:
    """Trim the white margin so the subject fills the character grid."""
    import numpy as np

    a = np.array(img)
    mask = a < 245
    if not mask.any():
        return img
    ys, xs = np.where(mask)
    pad = 12
    x0, x1 = max(int(xs.min()) - pad, 0), min(int(xs.max()) + pad, a.shape[1])
    y0, y1 = max(int(ys.min()) - pad, 0), min(int(ys.max()) + pad, a.shape[0])
    return img.crop((x0, y0, x1, y1))


def normalize(img: Image.Image) -> Image.Image:
    """Percentile stretch so the subject uses the whole density ramp."""
    import numpy as np

    a = np.array(img).astype(np.float32)
    ink = a.ravel() if LIGHT_ON_DARK else a[a < 245]
    if ink.size == 0:
        return img
    lo, hi = np.percentile(ink, 2), np.percentile(ink, 98)
    if hi - lo < 8:
        return img
    a = (a - lo) / (hi - lo) * 235.0 + 10.0
    return Image.fromarray(np.clip(a, 0, 255).astype("uint8"))


def to_grid(img: Image.Image) -> list[str]:
    img = normalize(img) if LIGHT_ON_DARK else normalize(autocrop(img))
    # soften film grain so the grid reads as shading, not speckle
    img = img.filter(ImageFilter.GaussianBlur(max(1.0, img.size[0] / COLS / 2.2)))
    # characters are ~2x taller than wide, so squash vertically while sampling
    small = img.resize((COLS, ROWS), Image.LANCZOS)
    px = small.load()
    ramp = RAMP
    last = len(ramp) - 1
    rows = []
    for y in range(ROWS):
        line = []
        for x in range(COLS):
            v = px[x, y] / 255.0            # 1.0 = white/background
            if LIGHT_ON_DARK:
                t = max(0.0, (v - FLOOR) / (1.0 - FLOOR)) ** GAMMA
            else:
                t = 1.0 - v
            idx = int(round(min(t, 1.0) * last))
            line.append(ramp[idx])
        rows.append("".join(line).rstrip())
    return rows


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_svg(rows: list[str]) -> str:
    w = COLS * CHAR_W
    h = ROWS * LINE_H + 12
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.0f}" height="{h:.0f}" '
        f'viewBox="0 0 {w:.0f} {h:.0f}" font-family="SFMono-Regular,Menlo,Consolas,'
        f'\'DejaVu Sans Mono\',monospace" font-size="{FONT_SIZE}">',
        '  <rect width="100%" height="100%" fill="#0d1117" rx="10"/>',
    ]

    if not STATIC:
        out.append("  <defs>")
        for i, line in enumerate(rows):
            if not line:
                continue
            rw = len(line) * CHAR_W
            begin = i * ROW_STAGGER
            out.append(
                f'    <clipPath id="w{i}"><rect x="0" y="{i * LINE_H:.1f}" '
                f'height="{LINE_H:.1f}" width="0">'
                f'<animate attributeName="width" from="0" to="{rw:.1f}" '
                f'begin="{begin:.2f}s" dur="{ROW_DUR}s" fill="freeze"/>'
                f"</rect></clipPath>"
            )
        out.append("  </defs>")

    out.append(f'  <g fill="{INK}" xml:space="preserve">')
    for i, line in enumerate(rows):
        if not line:
            continue
        y = (i + 1) * LINE_H
        tl = len(line) * CHAR_W
        clip = "" if STATIC else f' clip-path="url(#w{i})"'
        out.append(
            f'    <text x="0" y="{y:.1f}"{clip} textLength="{tl:.1f}" '
            f'lengthAdjust="spacing">{esc(line)}</text>'
        )
    out.append("  </g>")

    if not STATIC:
        # block cursor riding each wipe edge
        for i, line in enumerate(rows):
            if not line:
                continue
            rw = len(line) * CHAR_W
            begin = i * ROW_STAGGER
            out.append(
                f'  <rect y="{i * LINE_H + 1.5:.1f}" width="{CHAR_W:.1f}" '
                f'height="{LINE_H - 2:.1f}" fill="{CURSOR}" opacity="0" x="0">'
                f'<animate attributeName="x" from="0" to="{rw:.1f}" '
                f'begin="{begin:.2f}s" dur="{ROW_DUR}s" fill="freeze"/>'
                f'<set attributeName="opacity" to="0.9" begin="{begin:.2f}s"/>'
                f'<set attributeName="opacity" to="0" '
                f'begin="{begin + ROW_DUR:.2f}s"/></rect>'
            )

    out.append("</svg>")
    return "\n".join(out)


def main() -> None:
    rows = to_grid(load_source())
    pathlib.Path(OUT).write_text(build_svg(rows))
    print(f"wrote {OUT}  ({COLS}x{ROWS} grid, static={STATIC})")


if __name__ == "__main__":
    main()
