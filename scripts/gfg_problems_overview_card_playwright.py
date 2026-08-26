import os
import re
from datetime import datetime, timezone

from playwright.sync_api import sync_playwright

USERNAME = os.environ.get("GFG_USERNAME", "kamrulhasansojib19").strip()

URLS = [
    f"https://www.geeksforgeeks.org/user/{USERNAME}/practice/",
    f"https://www.geeksforgeeks.org/user/{USERNAME}/",
    f"https://www.geeksforgeeks.org/profile/{USERNAME}/",
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


def parse_counts_from_text(text: str):
    counts = {}
    for name in ORDER:
        m = re.search(rf"{name}\s*\(\s*(\d+)\s*\)", text, flags=re.IGNORECASE)
        if m:
            counts[name] = int(m.group(1))
    if len(counts) == len(ORDER):
        return {k: counts[k] for k in ORDER}
    return None


def parse_counts_from_html(html: str):
    """
    Fallback: rendered HTML-এ JSON/state থাকতে পারে।
    key: "school": 0, "basic": 1 ... এর মতো থাকলে ধরবে।
    """
    key_map = {
        "School": "school",
        "Basic": "basic",
        "Easy": "easy",
        "Medium": "medium",
        "Hard": "hard",
    }

    found = {}
    for label, key in key_map.items():
        m = re.search(rf'"{key}"\s*:\s*(\d+)', html, flags=re.IGNORECASE)
        if m:
            found[label] = int(m.group(1))

    if len(found) == 5:
        return {k: found.get(k, 0) for k in ORDER}
    return None


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


def auto_scroll(page, steps=10):
    # lazy load trigger করার জন্য scroll
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(800)
    for i in range(steps):
        page.evaluate("window.scrollBy(0, Math.floor(document.body.scrollHeight/10))")
        page.wait_for_timeout(900)
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(1200)


def main():
    counts = None

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
            ),
            viewport={"width": 1400, "height": 900},
        )
        page = ctx.new_page()

        for url in URLS:
            print("TRY URL:", url)
            try:
                page.goto(url, wait_until="networkidle", timeout=60000)
            except Exception:
                page.goto(url, wait_until="domcontentloaded", timeout=60000)

            page.wait_for_timeout(2500)
            auto_scroll(page, steps=12)

            print("PAGE URL:", page.url)

            text = page.inner_text("body")
            snippet = " ".join(text.split())[:350]
            print("PAGE TEXT SNIPPET:", snippet)

            counts = parse_counts_from_text(text)
            if counts:
                print("PARSED FROM TEXT ✅")
                break

            html = page.content()
            counts = parse_counts_from_html(html)
            if counts:
                print("PARSED FROM HTML ✅")
                break

        browser.close()

    if not counts:
        counts = {k: 0 for k in ORDER}
        print("FAILED TO PARSE ❌ using fallback zeros")

    print("Counts:", counts, "Total:", sum(counts.values()))

    os.makedirs("assets", exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(build_svg(counts))
    print("Generated:", OUT_FILE)


if __name__ == "__main__":
    main()
