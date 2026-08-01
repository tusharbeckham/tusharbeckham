#!/usr/bin/env python3
"""Prep a photo for ASCII conversion.

1. Isolate the subject:
     - default:    remove the background with rembg
     - --dark-bg:  the shot is already lit subject on a dark field, so the
                   image is inverted instead (dark background -> white -> spaces)
2. Boost local contrast with OpenCV CLAHE (flat faces -> real light and shade).
3. Composite onto pure white so the background maps to the blank end of the
   ASCII ramp (white -> spaces).

Usage:
    python scripts/prep_photo.py source-photo.jpg
    python scripts/prep_photo.py source-photo.jpg --dark-bg
    python scripts/prep_photo.py source-photo.jpg --dark-bg --floor 0.42

Output: source-prepped.png  (grayscale)
"""
import sys
import pathlib

import numpy as np
import cv2
from PIL import Image

OUT = "source-prepped.png"
MAX_SIDE = 1200


def arg(name: str, default: float) -> float:
    if name in sys.argv:
        return float(sys.argv[sys.argv.index(name) + 1])
    return default


def load(path: str) -> Image.Image:
    img = Image.open(path).convert("RGB")
    if "--crop" in sys.argv:
        # fractions of the frame: --crop x0,y0,x1,y1
        x0, y0, x1, y1 = (float(v) for v in sys.argv[sys.argv.index("--crop") + 1].split(","))
        w0, h0 = img.size
        img = img.crop((int(x0 * w0), int(y0 * h0), int(x1 * w0), int(y1 * h0)))
    w, h = img.size
    scale = MAX_SIDE / max(w, h)
    if scale < 1:
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    return img


def grabcut_mask(rgb: np.ndarray) -> np.ndarray:
    """Isolate the subject with GrabCut - no rembg / model download needed.

    The frame border seeds the background, a centre box seeds the foreground,
    and the result is feathered so the ASCII edge does not look cut with
    scissors.  Tune with --inset (border margin) and --core (centre box).
    """
    h, w = rgb.shape[:2]
    inset = arg("--inset", 0.06)
    core = arg("--core", 0.34)

    mask = np.full((h, w), cv2.GC_PR_BGD, np.uint8)
    x0, y0 = int(w * inset), int(h * inset)
    x1, y1 = int(w * (1 - inset)), int(h * (1 - inset))
    mask[y0:y1, x0:x1] = cv2.GC_PR_FGD

    cx0, cy0 = int(w * (0.5 - core / 2)), int(h * (0.5 - core / 2))
    cx1, cy1 = int(w * (0.5 + core / 2)), int(h * (0.5 + core / 2))
    mask[cy0:cy1, cx0:cx1] = cv2.GC_FGD

    bgd, fgd = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    cv2.grabCut(cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR), mask, None,
                bgd, fgd, 6, cv2.GC_INIT_WITH_MASK)

    m = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 1, 0).astype(np.uint8)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (17, 17))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, k)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, k)

    n, labels, stats, _ = cv2.connectedComponentsWithStats(m, 8)
    if n > 1:
        keep = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        m = (labels == keep).astype(np.uint8)

    return cv2.GaussianBlur(m.astype(np.float32), (0, 0), 2.5)


def cutout(img: Image.Image) -> Image.Image:
    """Return RGBA with the background removed (falls back to opaque)."""
    try:
        from rembg import remove
    except ImportError:
        print("! rembg not installed - skipping background removal")
        return img.convert("RGBA")
    return remove(img).convert("RGBA")


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("usage: python scripts/prep_photo.py <photo> [--dark-bg]")
    src = sys.argv[1]
    if not pathlib.Path(src).exists():
        sys.exit(f"no such file: {src}")

    dark_bg = "--dark-bg" in sys.argv
    floor = arg("--floor", 0.38)   # how much of the dark field is cleared away
    gain = arg("--gain", 1.15)     # contrast on what survives

    img = load(src)

    if "--plain" in sys.argv:
        # straight grayscale + local contrast; pair with
        # `make_ascii_svg.py --light-on-dark` for lit-subject-on-black photos
        rgb = np.array(img)
        gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        gray = cv2.createCLAHE(clipLimit=float(gain) * 2.0,
                               tileGridSize=(8, 8)).apply(gray)

        if "--cutout" in sys.argv:
            gray = (gray.astype(np.float32) * grabcut_mask(rgb)).astype(np.uint8)

        Image.fromarray(gray).save(OUT)
        print(f"wrote {OUT}  ({gray.shape[1]}x{gray.shape[0]}, plain, "
              f"cutout={'--cutout' in sys.argv})")
        return

    if dark_bg:
        gray = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.2, tileGridSize=(8, 8))
        eq = clahe.apply(gray)

        # --- subject mask: the lit region on the dark field ------------------
        blur = cv2.GaussianBlur(eq, (0, 0), 9)
        mask = (blur.astype(np.float32) / 255.0 > floor).astype(np.uint8)
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, k)
        n, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
        if n > 1:
            keep = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
            mask = (labels == keep).astype(np.uint8)
        mask = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 3)

        # --- shade the subject, keep real lighting ---------------------------
        v = eq.astype(np.float32) / 255.0
        ink = v[mask > 0.5]
        if ink.size:
            lo, hi = np.percentile(ink, 3), np.percentile(ink, 97)
            v = (v - lo) / max(1e-6, hi - lo)
        v = np.clip(0.5 + (v - 0.5) * gain, 0.0, 1.0)
        v = v ** 1.25                      # darken midtones -> denser glyphs
        v = v * mask + (1.0 - mask)        # everything outside the subject -> white
        gray = np.clip(v * 255, 0, 255).astype(np.uint8)
    else:
        rgba = cutout(img)
        rgb = np.array(rgba.convert("RGB"))
        lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)
        clahe = cv2.createCLAHE(clipLimit=2.6, tileGridSize=(8, 8))
        lab[:, :, 0] = clahe.apply(lab[:, :, 0])
        rgb = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)

        alpha = np.array(rgba)[:, :, 3:4].astype(np.float32) / 255.0
        white = np.full_like(rgb, 255, dtype=np.float32)
        flat = (rgb.astype(np.float32) * alpha + white * (1 - alpha)).astype(np.uint8)
        gray = cv2.cvtColor(flat, cv2.COLOR_RGB2GRAY)

        lut = np.array(
            [np.clip(255 / (1 + np.exp(-(i - 128) / 46.0)), 0, 255) for i in range(256)],
            dtype=np.uint8,
        )
        gray = cv2.LUT(gray, lut)

    Image.fromarray(gray).save(OUT)
    print(f"wrote {OUT}  ({gray.shape[1]}x{gray.shape[0]}, dark_bg={dark_bg})")


if __name__ == "__main__":
    main()
