#!/usr/bin/env python3
"""
make_ascii_svg.py — convert a prepped grayscale photo into a self-typing,
monochrome ASCII-art SVG.
"""
import sys
from PIL import Image

RAMP = " .`:-=+*cs#%@"
GRID_COLS = 160
GRID_ROWS = 90
CHAR_W = 4.5
CHAR_H = 8.5
FONT_SIZE = 8
FILL_COLOR = "#8b949e"
CURSOR_COLOR = "#39d353"
ROW_STAGGER = 0.045
ROW_DURATION = 0.35


def image_to_ascii_grid(path, cols, rows):
    img = Image.open(path).convert("L")
    img = img.resize((cols, rows))
    pixels = list(img.getdata())

    ramp_len = len(RAMP)
    lines = []
    for r in range(rows):
        row_chars = []
        for c in range(cols):
            brightness = pixels[r * cols + c]
            idx = int((255 - brightness) / 255 * (ramp_len - 1))
            row_chars.append(RAMP[idx])
        lines.append("".join(row_chars))
    return lines


def escape_xml(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_svg(lines):
    width = GRID_COLS * CHAR_W
    height = GRID_ROWS * CHAR_H

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.0f} {height:.0f}" '
        f'width="{width:.0f}" height="{height:.0f}" font-family="monospace">',
        "<style>",
        f".ascii-row {{ font-size:{FONT_SIZE}px; fill:{FILL_COLOR}; white-space:pre; }}",
        f".cursor {{ fill:{CURSOR_COLOR}; }}",
        "</style>",
        f'<rect width="{width:.0f}" height="{height:.0f}" fill="transparent"/>',
    ]

    for i, line in enumerate(lines):
        y = (i + 1) * CHAR_H
        start = i * ROW_STAGGER
        row_width = len(line) * CHAR_W
        clip_id = f"clip{i}"
        text_escaped = escape_xml(line)

        svg_parts.append(f'<clipPath id="{clip_id}">')
        svg_parts.append(f'  <rect x="0" y="{y - CHAR_H:.1f}" width="0" height="{CHAR_H:.1f}">')
        svg_parts.append(
            f'    <animate attributeName="width" from="0" to="{row_width:.1f}" '
            f'begin="{start:.3f}s" dur="{ROW_DURATION}s" fill="freeze" calcMode="spline" '
            f'keySplines="0.25 0.1 0.25 1"/>'
        )
        svg_parts.append("  </rect>")
        svg_parts.append("</clipPath>")

        svg_parts.append(f'<g clip-path="url(#{clip_id})">')
        svg_parts.append(f'  <text x="0" y="{y:.1f}" class="ascii-row">{text_escaped}</text>')
        svg_parts.append("</g>")

        svg_parts.append(
            f'<rect class="cursor" x="0" y="{y - CHAR_H:.1f}" width="{CHAR_W:.1f}" height="{CHAR_H:.1f}" opacity="0">'
            f'<animate attributeName="x" from="0" to="{row_width:.1f}" '
            f'begin="{start:.3f}s" dur="{ROW_DURATION}s" fill="freeze" calcMode="spline" '
            f'keySplines="0.25 0.1 0.25 1"/>'
            f'<animate attributeName="opacity" values="1;1;0" keyTimes="0;0.9;1" '
            f'begin="{start:.3f}s" dur="{ROW_DURATION}s" fill="freeze"/>'
            f'</rect>'
        )

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "source-prepped.png"
    out = sys.argv[2] if len(sys.argv) > 2 else "avi-ascii.svg"

    grid = image_to_ascii_grid(src, GRID_COLS, GRID_ROWS)
    svg = build_svg(grid)
    with open(out, "w") as f:
        f.write(svg)
    print(f"Wrote {out}")
