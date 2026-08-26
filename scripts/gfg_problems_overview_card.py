import os
import json
from datetime import datetime, timezone

from playwright.sync_api import sync_playwright

USERNAME = os.environ.get("GFG_USERNAME", "kamrulhasansojib19").strip()
PROFILE_URL = f"https://www.geeksforgeeks.org/profile/{USERNAME}/"
OUT_FILE = "assets/gfg-problems-overview.svg"

COLORS = {
    "School": "#7EE7F9",
    "Basic": "#CDEB8B",
    "Easy": "#8BC34A",
    "Medium": "#FFA726",
    "Hard": "#FF7043",
}
ORDER = ["School", "Basic", "Easy", "Medium", "Hard"]


def deep_find_counts(obj):
    if isinstance(obj, dict):
        lower_keys = {str(k).lower(): k for k in obj.keys()}
        need = ["school", "basic", "easy", "medium", "hard"]
        if all(k in lower_keys for k in need):
            try:
                counts = {
                    "School": int(obj[lower_keys["school"]]),
                    "Basic": int(obj[lower_keys["basic"]]),
                    "Easy": int(obj[lower_keys["easy"]]),
                    "Medium": int(obj[lower_keys["medium"]]),
                    "Hard": int(obj[lower_keys["hard"]]),
                }
                if all(v >= 0 for v in counts.values()):
                    return counts
            except Exception:
                pass

        for v in obj.values():
            found = deep_find_counts(v)
            if found:
                return found

    if isinstance(obj, list):
        for it in obj:
            found = deep_find_counts(it)
            if found:
                return found

    return None


def esc(s: str) -> str:
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def donut_segments(counts):
    total = sum(counts.values())
    if total <= 0:
        return "", total

    segs = []
    offset = 0.0
    for name in ORDER:
        val = counts.get(name, 0)
        if val <= 0:
            continue
        pct = (val / total) * 100.0
        segs.append(
            f'''
      <circle cx="140" cy="120" r="72" pathLength="100"
              fill="none" stroke="{COLORS[name]}" stroke-width="18"
              stroke-linecap="butt"
              stroke-dasharray="{pct:.6f} {100.0 - pct:.6f}"
              stroke-dashoffset="{-offset:.6f}" />'''
        )
        offset += pct
    return "\n".join(segs), total


def build_svg(counts):
    os.makedirs("assets", exist_ok=True)
    segments, total = donut_segments(counts)
    updated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    legend = []
    y0, dy = 86, 28
    for i, name in enumerate(ORDER):
        y = y0 + i * dy
        legend.append(
            f'''
    <rect x="440" y="{y-12}" width="14" height="14" rx="3" fill="{COLORS[name]}"/>
    <text x="462" y="{y}" fill="#C9D1D9" font-size="14"
          font-family="ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Ubuntu">
      {esc(name)} ({counts.get(name, 0)})
    </text>'''
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="720" height="260" viewBox="0 0 720 260" role="img" aria-label="GFG Problems Overview">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0D1117"/>
      <stop offset="100%" stop-color="#0B1220"/>
    </linearGradient>
  </defs>

  <rect x="0.5" y="0.5" width="719" height="259" rx="16" fill="url(#bg)" stroke="#30363D"/>

  <text x="32" y="46" fill="#FFFFFF" font-size="20" font-weight="700"
        font-family="ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Ubuntu">
    Problems Overview
  </text>

  <circle cx="140" cy="120" r="72" fill="none" stroke="#21262D" stroke-width="18" />

  <g transform="rotate(-90 140 120)">
{segments if segments else ""}
  </g>

  <text x="140" y="118" text-anchor="middle" fill="#FFFFFF" font-size="34" font-weight="800"
        font-family="ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Ubuntu">
    {total}
  </text>
  <text x="140" y="142" text-anchor="middle" fill="#8B949E" font-size="14"
        font-family="ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Ubuntu">
    Problems Solved
  </text>

  {''.join(legend)}

  <text x="32" y="236" fill="#8B949E" font-size="11"
        font-family="ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Ubuntu">
    Source: geeksforgeeks.org • Updated: {esc(updated)} • User: {esc(USERNAME)}
  </text>
</svg>
"""


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(PROFILE_URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(5000)

        # Read Next.js data
        next_data = page.eval_on_selector("script#__NEXT_DATA__", "el => el.textContent")
        browser.close()

    data = json.loads(next_data) if next_data else {}
    counts = deep_find_counts(data) or {k: 0 for k in ORDER}

    print("Counts:", counts, "Total:", sum(counts.values()))

    svg = build_svg(counts)
    os.makedirs("assets", exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(svg)

    print("Generated:", OUT_FILE)


if __name__ == "__main__":
    main()
