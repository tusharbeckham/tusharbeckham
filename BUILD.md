# Regenerating the profile art

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r scripts/requirements.txt
```

## Portrait (only when the photo changes)

The committed portrait was built from `source-photo.jpg` (lit subject on a dark
field), so it uses the light-on-dark path: bright pixels become dense glyphs,
the dark surroundings fall away to spaces.

```bash
python scripts/prep_photo.py source-photo.jpg --plain --crop 0.22,0.16,0.68,0.78 --gain 0.6
python scripts/make_ascii_svg.py --light-on-dark --floor 0.46 --gamma 1.7
```

Tuning knobs:

| Flag | What it does |
| --- | --- |
| `--crop x0,y0,x1,y1` | fractions of the frame; crop tight to the head, the grid is only 100x53 |
| `--gain` | CLAHE strength in `prep_photo.py` (lower = less grain) |
| `--floor` | anything darker than this is background, rendered as spaces |
| `--gamma` | >1 thins the shading, <1 fattens it |
| `STATIC=1` | emit a frozen frame instead of the typing animation |

For a normal, brightly-lit photo on a plain background use the original path
instead (rembg cutout, CLAHE, composite onto white, dark pixels = dense glyphs):

```bash
python scripts/prep_photo.py source-photo.jpg
python scripts/make_ascii_svg.py
```

## Info card (only when your details change)

```bash
python scripts/make_info_card.py
```

## Heatmap (automatic, daily)

```bash
python scripts/fetch_contributions.py    # add --demo to work offline
python scripts/render_heatmap_svg.py
```

GitHub Actions runs those two on a cron and commits the result.
