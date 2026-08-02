#!/usr/bin/env python3
"""Hand-author a neofetch-style info card SVG that prints line by line.

Keep story content here - the heatmap already covers the numbers.

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
KEY = "#39d353"
VAL = "#c9d1d9"
DIM = "#7d8590"
ACCENT = "#58a6ff"

# (key, value) - key "" continues the previous block, "--" is a spacer
ROWS = [
    ("Role", "Full-Stack Developer - Aspiring AI-for-Science Engineer"),
    ("Bridge", "Mobile development and Scientific Machine Learning"),
    ("Focus", "Renewable energy - climate tech"),
    ("--", ""),
    ("Euexia", "Android health tracker, built solo"),
    ("", "React + Capacitor, native Java foreground service"),
    ("--", ""),
    ("Alfred", "Multi-agent AI assistant on the edge"),
    ("", "streaming RAG chat, persistent memory"),
    ("--", ""),
    ("Next", "Deploy a Physics-Informed Neural Network"),
]

PAD = 22
LINE_H = 19
KEY_W = 88
FONT = ("SFMono-Regular,Menlo,Consolas,'DejaVu Sans Mono',monospace")
STAGGER = 0.07


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main() -> None:
    width = 620
    header_h = 58
    body_rows = len(ROWS)
    height = header_h + body_rows * LINE_H + 22

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
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="{FONT}" font-size="13">',
        f'  <rect width="100%" height="100%" rx="10" fill="{BG}" stroke="{BORDER}"/>',
        f'  <rect x="0.5" y="0.5" width="{width - 1}" height="32" rx="10" fill="#161b22"/>',
        f'  <rect x="0.5" y="22" width="{width - 1}" height="11" fill="#161b22"/>',
        f'  <line x1="0" y1="33" x2="{width}" y2="33" stroke="{BORDER}"/>',
        '  <circle cx="20" cy="16.5" r="5" fill="#ff5f57"/>',
        '  <circle cx="38" cy="16.5" r="5" fill="#febc2e"/>',
        '  <circle cx="56" cy="16.5" r="5" fill="#28c840"/>',
        f'  <text x="{width / 2:.0f}" y="21" text-anchor="middle" fill="{DIM}" '
        f'font-size="12">neofetch</text>',
    ]
    o.append(anim)

    i = 0
    y = header_h
    o.append(
        f'  <text x="{PAD}" y="{y}"{cls}{delay(i)} fill="{KEY}" font-weight="bold">'
        f'{esc(USER)}<tspan fill="{DIM}" font-weight="normal"> @ </tspan>'
        f'<tspan fill="{ACCENT}">{esc(HOST)}</tspan></text>'
    )
    i += 1
    y += 14
    o.append(
        f'  <text x="{PAD}" y="{y}"{cls}{delay(i)} fill="{BORDER}">'
        f'{"-" * 58}</text>'
    )
    i += 1

    for key, val in ROWS:
        if key == "--":
            y += 8
            continue
        y += LINE_H
        parts = [f'  <text x="{PAD}" y="{y}"{cls}{delay(i)}>']
        if key:
            parts.append(f'<tspan fill="{KEY}" font-weight="bold">{esc(key)}</tspan>')
            parts.append(f'<tspan fill="{DIM}">:</tspan>')
        parts.append(
            f'<tspan x="{PAD + KEY_W}" fill="{VAL if key else DIM}">{esc(val)}</tspan>'
        )
        parts.append("</text>")
        o.append("".join(parts))
        i += 1

    o.append("</svg>")

    pathlib.Path(OUT).write_text("\n".join(o))
    print(f"wrote {OUT}  ({width}x{height}, static={STATIC})")


if __name__ == "__main__":
    main()
