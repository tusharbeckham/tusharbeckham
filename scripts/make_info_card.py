#!/usr/bin/env python3
"""Hand-author a neofetch-style info card SVG that prints line by line.

Deliberately four fields: Role, Bridge, Focus, Next. The repo list belongs on the
profile grid, not restated here - listing projects in the card read as padding.

This is the SOURCE for info-card.svg. Edit ROWS below and re-run; never hand-edit
the SVG, or the next build silently reverts it.

Usage:
    python scripts/make_info_card.py
    STATIC=1 python scripts/make_info_card.py   # frozen frame for Quick Look

Output: info-card.svg
"""
import os
import pathlib

OUT = "info-card.svg"
STATIC = os.environ.get("STATIC") == "1"

USER = "tushar@github"
HOST = "theoria-lab"

BG = "#0d1117"
BORDER = "#21262d"
KEY = "#39d353"          # field names
VAL = "#c9d1d9"          # the claim itself
DIM = "#7d8590"          # qualifier / supporting detail
ACCENT = "#58a6ff"

# A row is (key, segments).
#   key ""    -> continuation line, no key printed
#   key "--"  -> vertical spacer
# Each segment is (text, colour) so a line can carry the claim in VAL and its
# qualifier in DIM. Every Focus line maps to a repo that actually exists.
ROWS = [
    ("Role", [("Full-Stack Developer", VAL), (" - ", DIM),
              ("aspiring AI-for-Science engineer", VAL)]),
    ("Bridge", [("Mobile engineering", VAL), ("  \u2192  ", DIM),
                ("scientific machine learning", VAL)]),
    ("--", []),
    ("Focus", [("Physics-informed forecasting", VAL),
               (" - renewable energy, climate tech", DIM)]),
    ("", [("Molecular property prediction", VAL),
          (" - ADMET, cheminformatics, graph nets", DIM)]),
    ("", [("Anomaly detection", VAL),
          (" - security telemetry, calibrated alerting", DIM)]),
    ("--", []),
    ("Next", [("deploying a physics-informed neural network", DIM)]),
]

WIDTH = 660
PAD = 22
LINE_H = 19
KEY_W = 72
GAP_H = 8
FONT = "SFMono-Regular,Menlo,Consolas,'DejaVu Sans Mono',monospace"
STAGGER = 0.07
RULE_CHARS = 74


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main() -> None:
    header_h = 58
    # Height is derived, so adding a row never silently clips the card.
    body_h = sum(GAP_H if key == "--" else LINE_H for key, _segments in ROWS)
    height = header_h + 14 + body_h + 16

    anim = "" if STATIC else (
        "\n  <style>\n"
        "    .ln { opacity: 0; animation: in .38s ease-out forwards; }\n"
        "    @keyframes in { from { opacity: 0; transform: translateX(-8px); }\n"
        "                    to   { opacity: 1; transform: translateX(0); } }\n"
        "  </style>"
    )
    cls = "" if STATIC else ' class="ln"'

    def delay(i: int) -> str:
        return "" if STATIC else f' style="animation-delay:{i * STAGGER:.2f}s"'

    o = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" '
        f'viewBox="0 0 {WIDTH} {height}" font-family="{FONT}" font-size="13">',
        f'  <rect width="100%" height="100%" rx="10" fill="{BG}" stroke="{BORDER}"/>',
        f'  <rect x="0.5" y="0.5" width="{WIDTH - 1}" height="32" rx="10" fill="#161b22"/>',
        f'  <rect x="0.5" y="22" width="{WIDTH - 1}" height="11" fill="#161b22"/>',
        f'  <line x1="0" y1="33" x2="{WIDTH}" y2="33" stroke="{BORDER}"/>',
        '  <circle cx="20" cy="16.5" r="5" fill="#ff5f57"/>',
        '  <circle cx="38" cy="16.5" r="5" fill="#febc2e"/>',
        '  <circle cx="56" cy="16.5" r="5" fill="#28c840"/>',
        f'  <text x="{WIDTH / 2:.0f}" y="21" text-anchor="middle" fill="{DIM}" '
        f'font-size="12">neofetch</text>',
        anim,
    ]

    i = 0
    y = header_h
    o.append(
        f'  <text x="{PAD}" y="{y}"{cls}{delay(i)} fill="{KEY}" font-weight="bold">'
        f'{esc(USER)}<tspan fill="{DIM}" font-weight="normal"> @ </tspan>'
        f'<tspan fill="{ACCENT}">{esc(HOST)}</tspan></text>'
    )
    i += 1
    y += 14
    o.append(f'  <text x="{PAD}" y="{y}"{cls}{delay(i)} fill="{BORDER}">'
             f'{"-" * RULE_CHARS}</text>')
    i += 1

    for key, segments in ROWS:
        if key == "--":
            y += GAP_H
            continue
        y += LINE_H
        parts = [f'  <text x="{PAD}" y="{y}"{cls}{delay(i)}>']
        if key:
            parts.append(f'<tspan fill="{KEY}" font-weight="bold">{esc(key)}</tspan>')
            parts.append(f'<tspan fill="{DIM}">:</tspan>')
        for index, (text, colour) in enumerate(segments):
            # The first segment carries the x offset so continuation lines align.
            offset = f' x="{PAD + KEY_W}"' if index == 0 else ""
            parts.append(f'<tspan{offset} fill="{colour}">{esc(text)}</tspan>')
        parts.append("</text>")
        o.append("".join(parts))
        i += 1

    o.append("</svg>")

    pathlib.Path(OUT).write_text("\n".join(o) + "\n", encoding="utf-8")
    print(f"wrote {OUT}  ({WIDTH}x{height}, static={STATIC})")


if __name__ == "__main__":
    main()
