# How the art is generated

The README shows two assets: `info-card.svg` and `contrib-heatmap.svg`.

Info card — the source of truth is the script, not the SVG:

```bash
python scripts/make_info_card.py     # edit ROWS at the top of the file
```

Never hand-edit `info-card.svg`; the next run of the generator silently reverts it.
Each `Focus` line is meant to map to a repo that actually exists, and each project
line describes it at its real maturity — the `[early]` tag on `admet-gnn` is there
on purpose.

Heatmap (the GitHub Action does this daily; run it locally to preview):

```bash
python scripts/fetch_contributions.py     # scrapes your real contributions
python scripts/render_heatmap_svg.py
```

Set `STATIC=1` on either of these to emit a frozen, non-animated frame.

## Retired: the ASCII portrait

`tushar-ascii.svg` was removed from the README, so nothing generates or uses it now.
`scripts/prep_photo.py` and `scripts/make_ascii_svg.py` are kept because they still
work if you ever want it back:

```bash
python scripts/prep_photo.py source-photo.jpg --plain --cutout \
  --crop 0.22,0.16,0.68,0.78 --gain 0.6 \
  --cut 0.42 --ellipse 0.44,0.52,0.42,0.47

python scripts/make_ascii_svg.py --light-on-dark --floor 0.46 --gamma 1.7
```

- `--crop x0,y0,x1,y1` fractions of the frame to keep
- `--cutout` drops the background: threshold brightness, keep the blob at the
  centre of the frame, fill it, feather the edge
- `--cut` brightness that counts as subject (raise it to cut more away)
- `--ellipse cx,cy,rx,ry` hard boundary that trims anything leaking in from the
  sides (other lit people, scenery)
- `--floor` blanks glyphs below this brightness, `--gamma` sets the falloff
