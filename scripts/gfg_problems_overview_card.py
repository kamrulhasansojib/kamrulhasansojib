import os
import re
import json
import math
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

USERNAME = os.environ.get("GFG_USERNAME", "kamrulhasansojib19").strip()

URLS = [
    f"https://www.geeksforgeeks.org/profile/{USERNAME}/",
    f"https://www.geeksforgeeks.org/user/{USERNAME}/",
    f"https://www.geeksforgeeks.org/user/{USERNAME}/practice/",
]

OUT_FILE = "assets/gfg-problems-overview.svg"

COLORS = {
    "School": "#7EE7F9",
    "Basic": "#CDEB8B",
    "Easy": "#8BC34A",
    "Medium": "#FFA726",
    "Hard": "#FF7043",
}

ORDER = ["School", "Basic", "Easy", "Medium", "Hard"]


def fetch_html() -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    last_err = None
    for url in URLS:
        try:
            r = requests.get(url, headers=headers, timeout=35)
            if r.status_code == 200 and len(r.text) > 2000:
                return r.text
            last_err = f"{url} -> {r.status_code}"
        except Exception as e:
            last_err = f"{url} -> {e}"
    raise RuntimeError(f"Failed to fetch GFG HTML. Last error: {last_err}")


def deep_find_counts(obj):
    """
    Try to find a dict that contains difficulty counts.
    We look for keys like school/basic/easy/medium/hard.
    """
    if isinstance(obj, dict):
        lower_map = {str(k).lower(): k for k in obj.keys()}
        need = ["school", "basic", "easy", "medium", "hard"]
        if all(k in lower_map for k in need):
            try:
                counts = {
                    "School": int(obj[lower_map["school"]]),
                    "Basic": int(obj[lower_map["basic"]]),
                    "Easy": int(obj[lower_map["easy"]]),
                    "Medium": int(obj[lower_map["medium"]]),
                    "Hard": int(obj[lower_map["hard"]]),
                }
                # sanity check: non-negative
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


def parse_counts_from_next_data(html: str):
    soup = BeautifulSoup(html, "html.parser")
    s = soup.find("script", id="__NEXT_DATA__")
    if not s or not s.string:
        return None
    try:
        data = json.loads(s.string)
    except Exception:
        return None
    return deep_find_counts(data)


def parse_counts_by_regex(html: str):
    # fallback: find `"school":number` etc in the HTML
    pattern = re.compile(
        r'"school"\s*:\s*(\d+).*?"basic"\s*:\s*(\d+).*?"easy"\s*:\s*(\d+).*?"medium"\s*:\s*(\d+).*?"hard"\s*:\s*(\d+)',
        re.IGNORECASE | re.DOTALL,
    )
    m = pattern.search(html)
    if not m:
        return None
    return {
        "School": int(m.group(1)),
        "Basic": int(m.group(2)),
        "Easy": int(m.group(3)),
        "Medium": int(m.group(4)),
        "Hard": int(m.group(5)),
    }


def get_counts(html: str):
    counts = parse_counts_from_next_data(html)
    if counts:
        return counts
    counts = parse_counts_by_regex(html)
    if counts:
        return counts

    # last fallback: show zeros (card will still render)
    return {k: 0 for k in ORDER}


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
        # no solved -> no segments
        return "", total

    # Use circle pathLength=100 so dash units are percentages
    segs = []
    offset = 0.0

    for name in ORDER:
        val = counts.get(name, 0)
        if val <= 0:
            continue
        pct = (val / total) * 100.0

        # stroke-dasharray: {pct} {100-pct}
        # dashoffset to stack segments
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

    # Layout
    # Card: 720x260, donut left, legend right
    legend_items = []
    y0 = 86
    dy = 28
    for i, name in enumerate(ORDER):
        y = y0 + i * dy
        legend_items.append(
            f'''
    <rect x="440" y="{y-12}" width="14" height="14" rx="3" fill="{COLORS[name]}"/>
    <text x="462" y="{y}" fill="#C9D1D9" font-size="14" font-family="ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Ubuntu">
      {esc(name)} ({counts.get(name, 0)})
    </text>'''
        )

    # Donut background + segments rotated -90 so start at top
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="720" height="260" viewBox="0 0 720 260" role="img" aria-label="GFG Problems Overview">
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

  <!-- Donut -->
  <circle cx="140" cy="120" r="72" fill="none" stroke="#21262D" stroke-width="18" />

  <g transform="rotate(-90 140 120)">
{segments if segments else ""}
  </g>

  <!-- Center text -->
  <text x="140" y="118" text-anchor="middle" fill="#FFFFFF" font-size="34" font-weight="800"
        font-family="ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Ubuntu">
    {total}
  </text>
  <text x="140" y="142" text-anchor="middle" fill="#8B949E" font-size="14"
        font-family="ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Ubuntu">
    Problems Solved
  </text>

  <!-- Legend -->
  {''.join(legend_items)}

  <text x="32" y="236" fill="#8B949E" font-size="11"
        font-family="ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Ubuntu">
    Source: geeksforgeeks.org • Updated: {esc(updated)} • User: {esc(USERNAME)}
  </text>
</svg>
"""
    return svg


def main():
    html = fetch_html()
    counts = get_counts(html)
    svg = build_svg(counts)

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(svg)

    print("Generated:", OUT_FILE)
    print("Counts:", counts, "Total:", sum(counts.values()))


if __name__ == "__main__":
    main()
