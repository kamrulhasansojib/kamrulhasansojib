import os
import re
from datetime import datetime, timezone

from playwright.sync_api import sync_playwright

USERNAME = os.environ.get("GFG_USERNAME", "kamrulhasansojib19").strip()

# GFG বিভিন্ন URL এ widget দেখায়—তাই multiple try
URLS = [
    f"https://www.geeksforgeeks.org/user/{USERNAME}/practice/",
    f"https://www.geeksforgeeks.org/user/{USERNAME}/",
    f"https://www.geeksforgeeks.org/profile/{USERNAME}/",
    f"https://www.geeksforgeeks.org/profile/{USERNAME}/?ref=profile",
]

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


def parse_counts_anywhere(text_or_html: str):
    """
    Works if the page contains:
      School (0) Basic (1) Easy (0) Medium (0) Hard (0)
    Either in text or inside svg/html.
    """
    counts = {}
    for name in ORDER:
        m = re.search(rf"{name}\s*\(\s*(\d+)\s*\)", text_or_html, flags=re.IGNORECASE)
        if m:
            counts[name] = int(m.group(1))
    if len(counts) == 5:
        return {k: counts[k] for k in ORDER}
    return None


def parse_counts_json_like(html: str):
    """
    Fallback: sometimes counts exist as JSON in HTML like:
      "school":0,"basic":1,"easy":0,"medium":0,"hard":0
    """
    found = {}
    key_map = {"School": "school", "Basic": "basic", "Easy": "easy", "Medium": "medium", "Hard": "hard"}
    for label, key in key_map.items():
        m = re.search(rf'"{key}"\s*:\s*(\d+)', html, flags=re.IGNORECASE)
        if m:
            found[label] = int(m.group(1))
    if len(found) == 5:
        return {k: found[k] for k in ORDER}
    return None


def auto_scroll(page, steps=14):
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(800)
    for _ in range(steps):
        page.mouse.wheel(0, 900)
        page.wait_for_timeout(650)
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(1500)


def donut_segments(counts):
    total = sum(counts.values())
    if total <= 0:
        return "", total

    segs, offset = [], 0.0
    for name in ORDER:
        val = counts.get(name, 0)
        if val <= 0:
            continue
        pct = (val / total) * 100.0
        segs.append(
            f'''
      <circle cx="140" cy="120" r="72" pathLength="100"
              fill="none" stroke="{COLORS[name]}" stroke-width="18"
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

  <circle cx="140" cy="120" r="72" fill="none" stroke="#21262D" stroke-width="18"/>

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
    counts = None

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            viewport={"width": 1400, "height": 900},
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
            ),
        )
        page = ctx.new_page()

        for url in URLS:
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(2500)
                auto_scroll(page)
                # wait a bit more for lazy widgets
                page.wait_for_timeout(3500)
            except Exception:
                continue

            # Try from rendered text
            try:
                text = page.locator("body").inner_text(timeout=10000)
            except Exception:
                text = ""
            counts = parse_counts_anywhere(text)
            if counts:
                break

            # Try from rendered HTML
            html = page.content()
            counts = parse_counts_anywhere(html)
            if counts:
                break

            counts = parse_counts_json_like(html)
            if counts:
                break

        browser.close()

    if not counts:
        counts = {k: 0 for k in ORDER}

    svg = build_svg(counts)
    os.makedirs("assets", exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(svg)

    print("Counts:", counts, "Total:", sum(counts.values()))
    print("Generated:", OUT_FILE)


if __name__ == "__main__":
    main()
