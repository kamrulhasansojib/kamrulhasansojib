import os
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
    totals["School"] = 0  # এই endpoint School দেয় না

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

    # Match LeetCode aspect ratio exactly
    W, H = 500, 400

    # Donut (left)
    cx, cy, r, sw = 145, 230, 92, 22
    segs, total = donut_segments(counts, cx, cy, r, sw)

    # Header (top-left)
    logo_cx, logo_cy, logo_r = 40, 52, 16
    header_x = 66

    # Legend (right)
    legend_x = 320
    y0, dy = 165, 34  # bigger font spacing
    legend = []
    for i, name in enumerate(ORDER):
        y = y0 + i * dy
        legend.append(
            f'''
    <rect x="{legend_x}" y="{y-13}" width="16" height="16" rx="2" fill="{COLORS[name]}"/>
    <text x="{legend_x+24}" y="{y}" fill="#E6EDF3" font-size="16" font-weight="600"
          font-family="ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Ubuntu">
      {esc(name)} ({counts.get(name, 0)})
    </text>'''
        )

    # NOTE: No border radius for the card (sharp corners)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="GeeksforGeeks Overview">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0D1117"/>
      <stop offset="100%" stop-color="#0B1220"/>
    </linearGradient>
  </defs>

  <rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" fill="url(#bg)" stroke="#30363D"/>

  <!-- GFG Logo (simple) -->
  <circle cx="{logo_cx}" cy="{logo_cy}" r="{logo_r}" fill="{GFG_GREEN}" />
  <text x="{logo_cx}" y="{logo_cy+6}" text-anchor="middle" fill="#FFFFFF"
        font-size="14" font-weight="800"
        font-family="ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Ubuntu">
    GFG
  </text>

  <!-- Username + Brand -->
  <text x="{header_x}" y="56" fill="#FFFFFF" font-size="18" font-weight="800"
        font-family="ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Ubuntu">
    {esc(USERNAME)}
  </text>
  <text x="{header_x}" y="80" fill="{GFG_GREEN}" font-size="16" font-weight="800"
        font-family="ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Ubuntu">
    GeeksforGeeks
  </text>

  <!-- donut background -->
  <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#21262D" stroke-width="{sw}"/>

  <!-- donut segments (start from top) -->
  <g transform="rotate(-90 {cx} {cy})">
{segs}
  </g>

  <!-- center numbers -->
  <text x="{cx}" y="{cy-4}" text-anchor="middle" fill="#FFFFFF" font-size="44" font-weight="900"
        font-family="ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Ubuntu">
    {total}
  </text>
  <text x="{cx}" y="{cy+30}" text-anchor="middle" fill="#9AA4B2" font-size="16" font-weight="600"
        font-family="ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Ubuntu">
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
