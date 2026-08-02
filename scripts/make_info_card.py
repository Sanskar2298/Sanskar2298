#!/usr/bin/env python3
import os

INFO = {
    "title": "sanskar@github",
    "rows": [
        ("Now", "B.Tech ECE @ NIT Hamirpur | CGPA 8.46 | ISTE Web Dev Coordinator"),
        ("Building", "Atlas - AI workspace SaaS | Lexora - RAG doc intelligence"),
        ("Stack", "Python | TypeScript | Next.js | FastAPI | LangChain | Docker"),
        ("Highlights", "1st/100+ CV robotics @ NIT Hamirpur | 3rd AlgoWars GDG"),
        ("More", "300+ DSA solved | Organizer: Hult Prize, PRODYOGIKI (800+ users)"),
    ],
}

WIDTH = 640
ROW_HEIGHT = 36
TITLE_BAR_HEIGHT = 40
PADDING = 20
LABEL_COLOR = "#39d353"
VALUE_COLOR = "#c9d1d9"
BG_COLOR = "#0d1117"
BORDER_COLOR = "#30363d"
TITLE_COLOR = "#8b949e"
FONT = "monospace"
STAGGER = 0.18
FADE_DUR = 0.5


def build_svg(info, static):
    rows = info["rows"]
    height = TITLE_BAR_HEIGHT + len(rows) * ROW_HEIGHT + PADDING

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {height}" '
        f'width="{WIDTH}" height="{height}" font-family="{FONT}">',
        "<style>",
        f'.title {{ fill:{TITLE_COLOR}; font-size:13px; }}',
        f'.label {{ fill:{LABEL_COLOR}; font-size:13px; font-weight:bold; }}',
        f'.value {{ fill:{VALUE_COLOR}; font-size:12px; }}',
        "</style>",
        f'<rect x="0" y="0" width="{WIDTH}" height="{height}" rx="8" fill="{BG_COLOR}" '
        f'stroke="{BORDER_COLOR}" stroke-width="1"/>',
        f'<circle cx="20" cy="20" r="6" fill="#ff5f56"/>',
        f'<circle cx="40" cy="20" r="6" fill="#ffbd2e"/>',
        f'<circle cx="60" cy="20" r="6" fill="#27c93f"/>',
        f'<text x="{WIDTH/2}" y="25" text-anchor="middle" class="title">{info["title"]}</text>',
        f'<line x1="0" y1="{TITLE_BAR_HEIGHT}" x2="{WIDTH}" y2="{TITLE_BAR_HEIGHT}" stroke="{BORDER_COLOR}"/>',
    ]

    for i, (label, value) in enumerate(rows):
        y = TITLE_BAR_HEIGHT + (i + 1) * ROW_HEIGHT - 10
        start = i * STAGGER
        opacity_style = 'opacity="1"' if static else 'opacity="0"'

        parts.append(f'<g {opacity_style}>')
        if not static:
            parts.append(
                f'  <animate attributeName="opacity" from="0" to="1" '
                f'begin="{start:.2f}s" dur="{FADE_DUR}s" fill="freeze"/>'
            )
            parts.append(
                f'  <animateTransform attributeName="transform" type="translate" '
                f'from="-12,0" to="0,0" begin="{start:.2f}s" dur="{FADE_DUR}s" '
                f'fill="freeze" calcMode="spline" keySplines="0.25 0.1 0.25 1"/>'
            )
        parts.append(f'  <text x="{PADDING}" y="{y}" class="label">{label}:</text>')
        parts.append(f'  <text x="{PADDING + 115}" y="{y}" class="value">{value}</text>')
        parts.append("</g>")

    parts.append("</svg>")
    return "\n".join(parts)


if __name__ == "__main__":
    static = os.environ.get("STATIC") == "1"
    svg = build_svg(INFO, static)
    out = "info-card.svg"
    with open(out, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Wrote {out}{' (static)' if static else ''}")
