import os
import base64
from datetime import datetime, timezone
import requests

API_URL = os.environ.get("GFG_API_URL", "").strip()
COOKIE_HEADER = (os.environ.get("GFG_COOKIE_HEADER") or "").strip()
USERNAME = os.environ.get("GFG_USERNAME", "kamrulhasansojib19").strip()

OUT_FILE = "assets/gfg-problems-overview.svg"

ORDER = ["School", "Basic", "Easy", "Medium", "Hard"]
COLORS = {
    "School": "#7EE7F9",
    "Basic": "#CDEB8B",
    "Easy": "#8BC34A",
    "Medium": "#FFA726",
    "Hard": "#FF7043",
}

GFG_GREEN = "#2F8D46"

# A stable GFG logo URL (PNG). If this ever changes, replace URL only.
GFG_LOGO_URL = "https://media.geeksforgeeks.org/wp-content/cdn-uploads/gfg_200x200-min.png"

FONT = "ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Ubuntu"

def esc(s: str) -> str:
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )

def fetch_json() -> dict:
    if not API_URL:
        raise RuntimeError("GFG_API_URL missing")

    headers = {
        "accept": "application/json, text/plain, */*",
        "user-agent": "Mozilla/5.0",
        "origin": "https://www.geeksforgeeks.org",
        "referer": "https://www.geeksforgeeks.org/",
    }
    if COOKIE_HEADER:
        headers["cookie"] = COOKIE_HEADER

    r = requests.get(API_URL, headers=headers, timeout=40)
    print("API status:", r.status_code)
    if r.status_code != 200:
        raise RuntimeError(r.text[:500])
    return r.json()

def compute_counts(data: dict) -> dict:
    totals = {k: 0 for k in ORDER}
    totals["School"] = 0  # this endpoint doesn't provide School

    for topic in data.get("counts", []):
        for d in topic.get("difficulties", []):
            name = (d.get("name") or "").strip().lower()
            solved = int(d.get("solved") or 0)
            if name == "basic":
                totals["Basic"] += solved
            elif name == "easy":
                totals["Easy"] += solved
            elif name == "medium":
                totals["Medium"] += solved
            elif name == "hard":
                totals["Hard"] += solved

    return totals

def fetch_logo_data_uri() -> str | None:
    """
    Downloads GFG logo and returns data URI for embedding inside SVG.
    Returns None if download fails.
    """
    try:
        r = requests.get(
            GFG_LOGO_URL,
            headers={"user-agent": "Mozilla/5.0", "accept": "image/*,*/*"},
            timeout=25,
        )
        if r.status_code != 200 or not r.content:
            return None
        b64 = base64.b64encode(r.content).decode("ascii")
        return f"data:image/png;base64,{b64}"
    except Exception:
        return None

def donut_segments(counts: dict, cx: int, cy: int, r: int, sw: int):
    total = sum(counts.values())
    if total <= 0:
        return "", total

    segs, offset = [], 0.0
    for name in ORDER:
        v = counts.get(name, 0)
        if v <= 0:
            continue
        pct = (v / total) * 100.0
        segs.append(
            f'''
      <circle cx="{cx}" cy="{cy}" r="{r}" pathLength="100"
              fill="none" stroke="{COLORS[name]}" stroke-width="{sw}"
              stroke-dasharray="{pct:.6f} {100.0 - pct:.6f}"
              stroke-dashoffset="{-offset:.6f}" />'''
        )
        offset += pct

    return "\n".join(segs), total

def build_svg(counts: dict) -> str:
    os.makedirs("assets", exist_ok=True)

    # Match LeetCode card ratio
    W, H = 500, 400

    # Donut placement (left)
    cx, cy, r, sw = 155, 245, 94, 22
    segs, total = donut_segments(counts, cx, cy, r, sw)

    # Header placement
    logo_x, logo_y, logo_size = 24, 28, 30
    header_x = 64

    # Legend placement (right)
    legend_x = 320
    y0, dy = 165, 34
    legend = []
    for i, name in enumerate(ORDER):
        y = y0 + i * dy
        legend.append(
            f'''
    <rect x="{legend_x}" y="{y-13}" width="16" height="16" fill="{COLORS[name]}"/>
    <text x="{legend_x+24}" y="{y}" fill="#E6EDF3" font-size="17" font-weight="700" font-family="{FONT}">
      {esc(name)} ({counts.get(name, 0)})
    </text>'''
        )

    # Try embed official logo
    logo_data_uri = fetch_logo_data_uri()
    if logo_data_uri:
        logo_svg = f'''
  <image href="{logo_data_uri}" x="{logo_x}" y="{logo_y}" width="{logo_size}" height="{logo_size}" />'''
    else:
        # fallback if logo download fails
        logo_svg = f'''
  <rect x="{logo_x}" y="{logo_y}" width="{logo_size}" height="{logo_size}" fill="{GFG_GREEN}" />
  <text x="{logo_x + logo_size/2}" y="{logo_y + logo_size/2 + 6}" text-anchor="middle"
        fill="#FFFFFF" font-size="14" font-weight="900" font-family="{FONT}">GFG</text>'''

    # No border-radius (sharp corners) => no rx
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="GeeksforGeeks Overview">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0D1117"/>
      <stop offset="100%" stop-color="#0B1220"/>
    </linearGradient>
  </defs>

  <rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" fill="url(#bg)" stroke="#30363D"/>

  <!-- Logo -->
  {logo_svg}

  <!-- Username -->
  <text x="{header_x}" y="52" fill="#FFFFFF" font-size="20" font-weight="900" font-family="{FONT}">
    {esc(USERNAME)}
  </text>

  <!-- Brand -->
  <text x="{header_x}" y="78" fill="{GFG_GREEN}" font-size="18" font-weight="900" font-family="{FONT}">
    GeeksforGeeks
  </text>

  <!-- donut background -->
  <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#21262D" stroke-width="{sw}"/>

  <!-- donut segments -->
  <g transform="rotate(-90 {cx} {cy})">
{segs}
  </g>

  <!-- center numbers -->
  <text x="{cx}" y="{cy-6}" text-anchor="middle" fill="#FFFFFF" font-size="50" font-weight="900" font-family="{FONT}">
    {total}
  </text>
  <text x="{cx}" y="{cy+30}" text-anchor="middle" fill="#9AA4B2" font-size="17" font-weight="700" font-family="{FONT}">
    Problems Solved
  </text>

  <!-- legend -->
  {''.join(legend)}
</svg>
"""

def main():
    data = fetch_json()
    counts = compute_counts(data)
    print("Counts:", counts, "Total:", sum(counts.values()))

    svg = build_svg(counts)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(svg)

    print("Generated:", OUT_FILE)

if __name__ == "__main__":
    main()
