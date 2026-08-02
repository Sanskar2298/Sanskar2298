#!/usr/bin/env python3
"""
prep_photo.py — turn a raw photo into a clean, high-contrast, background-removed
grayscale image ready for ASCII conversion.

Usage:
    python scripts/prep_photo.py source-photo.jpg [output.png]
"""
import sys
import io
from pathlib import Path

import numpy as np
import cv2
from PIL import Image
from rembg import remove


def prep(src_path: str, out_path: str = "source-prepped.png") -> None:
    src_bytes = Path(src_path).read_bytes()

    # 1. Remove background so only the subject remains (transparent elsewhere)
    print("Removing background...")
    fg_bytes = remove(src_bytes)
    fg_img = Image.open(io.BytesIO(fg_bytes)).convert("RGBA")

    # 2. Composite onto pure white so background maps to blank end of ASCII ramp
    white_bg = Image.new("RGBA", fg_img.size, (255, 255, 255, 255))
    composited = Image.alpha_composite(white_bg, fg_img).convert("RGB")

    # 3. Convert to grayscale and boost local contrast with CLAHE
    print("Boosting contrast (CLAHE)...")
    gray = cv2.cvtColor(np.array(composited), cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    contrasted = clahe.apply(gray)

    out_img = Image.fromarray(contrasted)
    out_img.save(out_path)
    print(f"Wrote {out_path} ({out_img.size[0]}x{out_img.size[1]})")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/prep_photo.py <source-photo> [output.png]")
        sys.exit(1)
    out = sys.argv[2] if len(sys.argv) > 2 else "source-prepped.png"
    prep(sys.argv[1], out)
