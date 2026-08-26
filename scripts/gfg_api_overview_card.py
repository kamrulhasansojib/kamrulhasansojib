import os
from datetime import datetime, timezone
import requests

API_URL = os.environ.get("GFG_API_URL", "").strip()
COOKIE_HEADER = (os.environ.get("GFG_COOKIE_HEADER") or "").strip()
USERNAME = os.environ.get("GFG_USERNAME", "kamrulhasansojib19").strip()

# IMPORTANT: output name (match your README path)
OUT_FILE = "assets/gfg-problems-overview.svg"

ORDER = ["School", "Basic", "Easy", "Medium", "Hard"]
COLORS = {
    "School": "#7EE7F9",
    "Basic": "#CDEB8B",
    "Easy": "#8BC34A",
    "Medium": "#FFA726",
    "Hard": "#FF7043",
}

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

    # এই endpoint "School" দেয় না
    totals["School"] = 0

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

    # Match LeetCode SVG size exactly
    W, H = 500, 400

    # Donut geometry (left side)
    cx, cy, r, sw = 135, 210, 86, 20
    segs, total = donut_segments(counts, cx, cy, r, sw)

    updated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Legend (right side)
    legend_x = 300
    y0, dy = 155, 34
    legend = []
    for i, name in enumerate(ORDER):
        y = y0 + i * dy
        legend.append(
            f'''
    <rect x="{legend_x}" y="{y-12}" width="14" height="14" rx="3" fill="{COLORS[name]}"/>
    <text x="{legend_x+22}" y="{y}" fill="#C9D1D9" font-size="14"
          font-family="ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Ubuntu">
      {esc(name)} ({counts.get(name, 0)})
    </text>'''
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="GFG Problems Overview">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0D1117"/>
      <stop offset="100%" stop-color="#0B1220"/>
    </linearGradient>
  </defs>

  <rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="18" fill="url(#bg)" stroke="#30363D"/>

  <text x="28" y="58" fill="#FFFFFF" font-size="20" font-weight="700"
        font-family="ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Ubuntu">
    Problems Overview
  </text>

  <!-- donut background -->
  <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#21262D" stroke-width="{sw}"/>

  <!-- donut segments (start from top) -->
  <g transform="rotate(-90 {cx} {cy})">
{segs}
  </g>

  <!-- center numbers -->
  <text x="{cx}" y="{cy-2}" text-anchor="middle" fill="#FFFFFF" font-size="38" font-weight="800"
        font-family="ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Ubuntu">
    {total}
  </text>
  <text x="{cx}" y="{cy+26}" text-anchor="middle" fill="#8B949E" font-size="14"
        font-family="ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Ubuntu">
    Problems Solved
  </text>

  <!-- legend -->
  {''.join(legend)}

  <text x="28" y="{H-22}" fill="#8B949E" font-size="11"
        font-family="ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Ubuntu">
    Source: practiceapi.geeksforgeeks.org • Updated: {esc(updated)} • User: {esc(USERNAME)}
  </text>
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
