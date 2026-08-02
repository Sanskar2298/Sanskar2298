import json
import sys
from datetime import datetime
from collections import defaultdict

PALETTE = ["#161b22", "#0d4f2b", "#0f8a3d", "#1fc953", "#3ef07a", "#6dffab"]
# none -> brightest, punched up saturation/brightness at every level

BOX_SIZE = 11
BOX_GAP = 3
CELL = BOX_SIZE + BOX_GAP
LEFT_MARGIN = 30
TOP_MARGIN = 20
LEGEND_HEIGHT = 30
FOOTER_HEIGHT = 26
WEEKS = 53
DAYS = 7
DIAGONAL_STAGGER = 0.012
BOX_DURATION = 0.28

MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def clamp_level(level, count):
    if level is not None and 0 <= level <= 5:
        return level
    if count is None:
        return 0
    if count == 0:
        return 0
    if count <= 2:
        return 1
    if count <= 5:
        return 2
    if count <= 9:
        return 3
    if count <= 15:
        return 4
    return 5


def build_grid(days):
    if not days:
        return [], []

    parsed = []
    for d in days:
        try:
            dt = datetime.strptime(d["date"], "%Y-%m-%d")
        except (ValueError, KeyError):
            continue
        parsed.append((dt, d))
    parsed.sort(key=lambda x: x[0])

    if not parsed:
        return [], []

    weekday_of = lambda dt: (dt.weekday() + 1) % 7

    grid = defaultdict(dict)
    day0 = parsed[0][0]
    day0_sunday_delta = weekday_of(day0)
    for dt, d in parsed:
        days_since_start = (dt - day0).days + day0_sunday_delta
        week_idx = days_since_start // 7
        wd = weekday_of(dt)
        grid[week_idx][wd] = d

    max_week = max(grid.keys()) if grid else 0
    grid_list = [grid.get(w, {}) for w in range(max_week + 1)]

    month_marks = []
    seen_months = set()
    for w_idx, week in enumerate(grid_list):
        for wd in range(7):
            d = week.get(wd)
            if not d:
                continue
            dt = datetime.strptime(d["date"], "%Y-%m-%d")
            key = (dt.year, dt.month)
            if key not in seen_months:
                seen_months.add(key)
                month_marks.append((w_idx, MONTH_LABELS[dt.month - 1]))
            break

    return grid_list, month_marks


def build_svg(data):
    days = data.get("days", [])
    stats = data.get("stats", {})
    grid, month_marks = build_grid(days)

    n_weeks = max(len(grid), 1)
    width = LEFT_MARGIN + n_weeks * CELL + 20
    height = TOP_MARGIN + DAYS * CELL + LEGEND_HEIGHT + FOOTER_HEIGHT

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" font-family="monospace">',
        "<style>",
        ".box { }",
        ".label { fill:#8b949e; font-size:11px; }",
        ".footer { fill:#8b949e; font-size:12px; }",
        "@keyframes revealBox { from { opacity:0; transform:translate(-4px,-4px);} "
        "to { opacity:1; transform:translate(0,0);} }",
        "</style>",
        f'<rect width="{width}" height="{height}" fill="transparent"/>',
    ]

    for w_idx, label in month_marks:
        x = LEFT_MARGIN + w_idx * CELL
        parts.append(f'<text x="{x}" y="{TOP_MARGIN - 6}" class="label">{label}</text>')

    for w_idx, week in enumerate(grid):
        for wd in range(DAYS):
            d = week.get(wd)
            level = clamp_level(
                d.get("level") if d else 0,
                d.get("count") if d else 0,
            )
            color = PALETTE[level]
            x = LEFT_MARGIN + w_idx * CELL
            y = TOP_MARGIN + wd * CELL
            delay = (w_idx + wd) * DIAGONAL_STAGGER
            title = f'{d["date"]}: {d.get("count", 0) or 0} contributions' if d else ""

            parts.append(
                f'<rect class="box" x="{x}" y="{y}" width="{BOX_SIZE}" height="{BOX_SIZE}" '
                f'rx="2" fill="{color}" opacity="0" style="animation:revealBox {BOX_DURATION}s '
                f'ease-out {delay:.3f}s forwards">'
                + (f'<title>{title}</title>' if title else "")
                + "</rect>"
            )

    legend_y = TOP_MARGIN + DAYS * CELL + 18
    parts.append(f'<text x="{LEFT_MARGIN}" y="{legend_y}" class="label">Less</text>')
    lx = LEFT_MARGIN + 40
    for i, color in enumerate(PALETTE):
        parts.append(
            f'<rect x="{lx + i * (BOX_SIZE + 3)}" y="{legend_y - 10}" '
            f'width="{BOX_SIZE}" height="{BOX_SIZE}" rx="2" fill="{color}"/>'
        )
    parts.append(
        f'<text x="{lx + len(PALETTE) * (BOX_SIZE + 3) + 6}" y="{legend_y}" class="label">More</text>'
    )

    footer_y = legend_y + 22
    total = stats.get("total_contributions", 0)
    streak = stats.get("current_streak", 0)
    longest = stats.get("longest_streak", 0)
    footer_text = f"{total} contributions in the last year | current streak {streak}d | longest {longest}d"
    parts.append(f'<text x="{LEFT_MARGIN}" y="{footer_y}" class="footer">{footer_text}</text>')

    parts.append("</svg>")
    return "\n".join(parts)


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "data/contributions.json"
    out = sys.argv[2] if len(sys.argv) > 2 else "contrib-heatmap.svg"

    with open(src) as f:
        data = json.load(f)

    svg = build_svg(data)
    with open(out, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Wrote {out}")
