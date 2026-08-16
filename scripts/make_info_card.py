#!/usr/bin/env python3
"""Hand-author a neofetch-style info card SVG that prints line by line.

Keep story content here - the heatmap already covers the numbers.

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
KEY = "#39d353"          # identity keys
VAL = "#c9d1d9"          # the claim itself
DIM = "#7d8590"          # qualifier / supporting detail
ACCENT = "#58a6ff"       # project names
WARN = "#d29922"         # honest status tags, e.g. [early]

# A row is (key, segments, key_colour).
#   key ""    -> continuation line, no key printed
#   key "--"  -> vertical spacer
#   key "=="  -> horizontal rule
# Each segment is (text, colour), so a line can carry a claim in VAL and its
# qualifier in DIM. Every Focus item below maps to a repo that exists; every
# project line describes it at its real maturity rather than its ambition.
ROWS = [
    ("Role", [("Full-Stack Developer", VAL), (" - ", DIM),
              ("aspiring AI-for-Science engineer", VAL)], KEY),
    ("Bridge", [("Shipped mobile engineering", VAL), (" <-> ", DIM),
                ("scientific machine learning", VAL)], KEY),
    ("--", [], KEY),
    ("Focus", [("Physics-informed forecasting", VAL),
               (" - renewable energy, climate tech", DIM)], KEY),
    ("", [("Molecular property prediction", VAL),
          (" - ADMET, cheminformatics, graph nets", DIM)], KEY),
    ("", [("Anomaly detection", VAL),
          (" - security telemetry, calibrated alerting", DIM)], KEY),
    ("--", [], KEY),
    ("Stack", [("Python", VAL), (" · ", DIM), ("PyTorch", VAL), (" · ", DIM),
               ("NumPy", VAL), (" · ", DIM), ("RDKit", VAL), (" · ", DIM),
               ("React", VAL), (" · ", DIM), ("Capacitor", VAL), (" · ", DIM),
               ("Cloudflare Workers", VAL)], KEY),
    ("==", [], KEY),
    ("Euexia", [("Android health tracker, built solo", VAL),
                (" - native Java foreground service", DIM)], ACCENT),
    ("Alfred", [("Multi-agent system", VAL),
                (" - DAG workflows, signed policy harness, offline memory", DIM)], ACCENT),
    ("solar-forecast", [("Clear-sky physics baseline, ML on the residual", VAL),
                        (" - 0.85 / 0.69 skill", DIM)], ACCENT),
    ("SentinelAI", [("Hybrid intrusion detection, pure NumPy", VAL),
                    (" - Shapley on every alert", DIM)], ACCENT),
    ("admet-gnn", [("ADMET from SMILES", VAL),
                   (" - RDKit + PyG, scaffold-split eval ", DIM),
                   ("[early]", WARN)], ACCENT),
    ("--", [], KEY),
    ("Next", [("deploying a physics-informed neural network", DIM)], KEY),
]

# neofetch prints its palette at the bottom; keeping it makes the homage honest.
SWATCHES = ["#161b22", "#ff5f57", "#39d353", "#febc2e",
            "#58a6ff", "#bc8cff", "#39c5cf", "#c9d1d9"]

WIDTH = 860
PAD = 22
LINE_H = 19
KEY_W = 108
GAP_H = 8
FONT = "SFMono-Regular,Menlo,Consolas,'DejaVu Sans Mono',monospace"
STAGGER = 0.06
RULE_CHARS = 98


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main() -> None:
    header_h = 60
    # Height is derived, so adding a row never silently clips the card.
    body_h = sum(
        GAP_H if key == "--" else (14 if key == "==" else LINE_H)
        for key, _segments, _colour in ROWS
    )
    height = header_h + 14 + body_h + 34

    anim = "" if STATIC else (
        "\n  <style>\n"
        "    .ln { opacity: 0; animation: in .38s ease-out forwards; }\n"
        "    .sw { opacity: 0; animation: pop .3s ease-out forwards; }\n"
        "    @keyframes in  { from { opacity: 0; transform: translateX(-8px); }\n"
        "                     to   { opacity: 1; transform: translateX(0); } }\n"
        "    @keyframes pop { from { opacity: 0; transform: scale(.6); }\n"
        "                     to   { opacity: 1; transform: scale(1); } }\n"
        "  </style>"
    )
    cls = "" if STATIC else ' class="ln"'
    swcls = "" if STATIC else ' class="sw"'

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
        f'font-size="12">{esc(USER)} — neofetch</text>',
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

    for key, segments, key_colour in ROWS:
        if key == "--":
            y += GAP_H
            continue
        if key == "==":
            y += 14
            o.append(f'  <text x="{PAD}" y="{y}"{cls}{delay(i)} fill="{BORDER}">'
                     f'{"-" * RULE_CHARS}</text>')
            i += 1
            continue

        y += LINE_H
        parts = [f'  <text x="{PAD}" y="{y}"{cls}{delay(i)}>']
        if key:
            parts.append(f'<tspan fill="{key_colour}" font-weight="bold">{esc(key)}</tspan>')
            parts.append(f'<tspan fill="{DIM}">:</tspan>')
        for index, (text, colour) in enumerate(segments):
            # The first segment carries the x offset so continuation lines align.
            offset = f' x="{PAD + KEY_W}"' if index == 0 else ""
            parts.append(f'<tspan{offset} fill="{colour}">{esc(text)}</tspan>')
        parts.append("</text>")
        o.append("".join(parts))
        i += 1

    # Palette row, aligned with the value column.
    y += 16
    o.append("  <g>")
    for index, colour in enumerate(SWATCHES):
        x = PAD + KEY_W + index * 16
        stagger = "" if STATIC else f' style="animation-delay:{(i + index) * 0.02 + i * STAGGER:.2f}s"'
        o.append(f'    <rect{swcls}{stagger} x="{x}" y="{y - 9}" width="13" height="10" '
                 f'fill="{colour}"/>')
    o.append("  </g>")
    o.append("</svg>")

    pathlib.Path(OUT).write_text("\n".join(o) + "\n", encoding="utf-8")
    print(f"wrote {OUT}  ({WIDTH}x{height}, static={STATIC})")


if __name__ == "__main__":
    main()
