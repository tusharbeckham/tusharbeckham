#!/usr/bin/env python3
"""Render data/contributions.json as an animated 53x7 contribution heatmap.

Rounded boxes reveal once on a diagonal slide-down (CSS keyframes inside the
SVG, then freeze - no looping glow), plus month labels, a Less->More legend
and a stats footer.

Usage:  python scripts/render_heatmap_svg.py
Output: contrib-heatmap.svg
"""
import json
import os
import pathlib
from datetime import date

DATA = pathlib.Path("data/contributions.json")
OUT = "contrib-heatmap.svg"
STATIC = os.environ.get("STATIC") == "1"

PALETTE = ["#161b22", "#0e4429", "#006d32",
           "#26a641", "#39d353", "#69f0a0"]
#          none -> brightest (level 5 is a neon top end)

CELL = 12
GAP = 3
STEP = CELL + GAP
LEFT = 34
TOP = 46
BG = "#0d1117"
BORDER = "#21262d"
DIM = "#7d8590"
TEXT = "#c9d1d9"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
DAY_LABELS = {1: "Mon", 3: "Wed", 5: "Fri"}


def weeks_from(days: list[dict]) -> list[list[dict | None]]:
    """Bucket days into columns of 7 (Sunday first)."""
    cols: list[list[dict | None]] = []
    col: list[dict | None] = []
    first_dow = (date.fromisoformat(days[0]["date"]).weekday() + 1) % 7
    col.extend([None] * first_dow)
    for d in days:
        col.append(d)
        if len(col) == 7:
            cols.append(col)
            col = []
    if col:
        col.extend([None] * (7 - len(col)))
        cols.append(col)
    return cols[-53:]


def main() -> None:
    payload = json.loads(DATA.read_text())
    cols = weeks_from(payload["days"])
    n = len(cols)

    width = LEFT + n * STEP + 18
    height = TOP + 7 * STEP + 74

    style = "" if STATIC else (
        "  <style>\n"
        "    .d { opacity: 0; animation: drop .34s ease-out forwards; }\n"
        "    @keyframes drop { from { opacity: 0; transform: translateY(-7px) scale(.72); }\n"
        "                       to   { opacity: 1; transform: translateY(0) scale(1); } }\n"
        "    .f { opacity: 0; animation: fade .5s ease-out forwards; }\n"
        "    @keyframes fade { to { opacity: 1; } }\n"
        "  </style>"
    )
    cls = "" if STATIC else ' class="d"'
    fcls = "" if STATIC else ' class="f"'
    total_delay = (n + 7) * 0.028

    def fdelay(extra: float = 0.0) -> str:
        return "" if STATIC else (
            f' style="animation-delay:{total_delay + extra:.2f}s"'
        )

    o = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="SFMono-Regular,Menlo,Consolas,'
        f"'DejaVu Sans Mono',monospace\" font-size=\"10\">",
        f'  <rect width="100%" height="100%" rx="10" fill="{BG}" stroke="{BORDER}"/>',
        style,
        f'  <text x="{LEFT}" y="24" fill="{TEXT}" font-size="12">'
        f'<tspan fill="#39d353">{payload["user"]}</tspan>'
        f'<tspan fill="{DIM}"> ~ $ ./contributions.sh</tspan></text>',
    ]

    # month labels
    seen = set()
    for x, col in enumerate(cols):
        first = next((d for d in col if d), None)
        if not first:
            continue
        m = date.fromisoformat(first["date"])
        if m.day <= 7 and m.month not in seen:
            seen.add(m.month)
            o.append(
                f'  <text x="{LEFT + x * STEP}" y="{TOP - 8}" fill="{DIM}"'
                f'{fcls}{fdelay()}>{MONTHS[m.month - 1]}</text>'
            )

    for row, label in DAY_LABELS.items():
        o.append(
            f'  <text x="2" y="{TOP + row * STEP + CELL - 2}" fill="{DIM}"'
            f'{fcls}{fdelay()}>{label}</text>'
        )

    # cells
    for x, col in enumerate(cols):
        for y, day in enumerate(col):
            if not day:
                continue
            lvl = min(int(day["level"]), len(PALETTE) - 1)
            delay = (x + y) * 0.028
            style_attr = "" if STATIC else (
                f' style="animation-delay:{delay:.2f}s;'
                f'transform-origin:{LEFT + x * STEP + CELL / 2:.1f}px '
                f'{TOP + y * STEP + CELL / 2:.1f}px"'
            )
            o.append(
                f'  <rect x="{LEFT + x * STEP}" y="{TOP + y * STEP}" '
                f'width="{CELL}" height="{CELL}" rx="3" fill="{PALETTE[lvl]}"'
                f'{cls}{style_attr}><title>{day["count"]} on {day["date"]}</title>'
                f"</rect>"
            )

    # legend
    ly = TOP + 7 * STEP + 22
    lx = width - 18 - (len(PALETTE) * STEP) - 62
    o.append(f'  <text x="{lx}" y="{ly + 10}" fill="{DIM}"{fcls}{fdelay(0.1)}>Less</text>')
    for k, c in enumerate(PALETTE):
        o.append(
            f'  <rect x="{lx + 30 + k * STEP}" y="{ly}" width="{CELL}" '
            f'height="{CELL}" rx="3" fill="{c}"{fcls}{fdelay(0.1)}/>'
        )
    o.append(
        f'  <text x="{lx + 36 + len(PALETTE) * STEP}" y="{ly + 10}" fill="{DIM}"'
        f'{fcls}{fdelay(0.1)}>More</text>'
    )

    # stats footer
    fy = ly + 36
    stats = (
        f'{payload["total"]:,} contributions in the last year',
        f'current streak {payload["currentStreak"]}d',
        f'longest {payload["longestStreak"]}d',
        f'best day {payload["bestDay"]["count"]}',
    )
    o.append(
        f'  <text x="{LEFT}" y="{fy}" fill="{TEXT}" font-size="11"{fcls}{fdelay(0.16)}>'
        + f'<tspan fill="#39d353">{stats[0]}</tspan>'
        + "".join(f'<tspan fill="{DIM}">  -  {s}</tspan>' for s in stats[1:])
        + "</text>"
    )
    o.append("</svg>")

    pathlib.Path(OUT).write_text("\n".join(o))
    print(f"wrote {OUT}  ({width}x{height}, {n} weeks, static={STATIC})")


if __name__ == "__main__":
    main()
