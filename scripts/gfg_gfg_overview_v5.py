import os
import re
import json
from datetime import datetime, timezone
from typing import Any, Optional, Dict

from playwright.sync_api import sync_playwright

USERNAME = os.environ.get("GFG_USERNAME", "kamrulhasansojib19").strip()
COOKIES_JSON = (os.environ.get("GFG_COOKIES_JSON") or "").strip()

OUT_FILE = "assets/gfg-problems-overview.svg"

ORDER = ["School", "Basic", "Easy", "Medium", "Hard"]
COLORS = {
    "School": "#7EE7F9",
    "Basic": "#CDEB8B",
    "Easy": "#8BC34A",
    "Medium": "#FFA726",
    "Hard": "#FF7043",
}

URLS = [
    f"https://www.geeksforgeeks.org/user/{USERNAME}/practice/",
    f"https://www.geeksforgeeks.org/user/{USERNAME}/",
    f"https://www.geeksforgeeks.org/profile/{USERNAME}/",
]

def esc(s: str) -> str:
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )

def normalize_key(k: str) -> str:
    # keep letters only
    return re.sub(r"[^a-z]", "", k.lower())

def try_extract_counts_from_dict(d: dict) -> Optional[Dict[str, int]]:
    # fuzzy match keys like school, schoolCount, school_count, problemsSchool, etc.
    need = {
        "School": ["school"],
        "Basic": ["basic"],
        "Easy": ["easy"],
        "Medium": ["medium"],
        "Hard": ["hard"],
    }

    found = {}
    for raw_k, v in d.items():
        nk = normalize_key(str(raw_k))
        for label, tokens in need.items():
            if any(t in nk for t in tokens):
                # int-like value
                try:
                    iv = int(v)
                    if iv >= 0:
                        # keep the best match; don't overwrite if already set
                        if label not in found:
                            found[label] = iv
                except Exception:
                    pass

    if len(found) == 5:
        return {k: found[k] for k in ORDER}
    return None

def deep_find_counts(obj: Any) -> Optional[Dict[str, int]]:
    if isinstance(obj, dict):
        direct = try_extract_counts_from_dict(obj)
        if direct:
            return direct
        for v in obj.values():
            res = deep_find_counts(v)
            if res:
                return res
    elif isinstance(obj, list):
        for it in obj:
            res = deep_find_counts(it)
            if res:
                return res
    return None

def parse_counts_from_text(text: str) -> Optional[Dict[str, int]]:
    # matches: Basic (1)
    counts = {}
    for name in ORDER:
        m = re.search(rf"{name}\s*\(\s*(\d+)\s*\)", text, flags=re.IGNORECASE)
        if m:
            counts[name] = int(m.group(1))
    if len(counts) == 5:
        return {k: counts[k] for k in ORDER}
    return None

def parse_counts_from_json_like(html: str) -> Optional[Dict[str, int]]:
    # matches: "basic":1 etc (anywhere in HTML)
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
    page.wait_for_timeout(1200)

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

def build_svg(counts, note: str = ""):
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

    note_line = f'<text x="32" y="214" fill="#FFB86C" font-size="11" font-family="ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Ubuntu">{esc(note)}</text>' if note else ""

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
  {note_line}

  <text x="32" y="236" fill="#8B949E" font-size="11"
        font-family="ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Ubuntu">
    Source: geeksforgeeks.org • Updated: {esc(updated)} • User: {esc(USERNAME)}
  </text>
</svg>
"""

def main():
    counts = None
    sniffed_counts = None
    sniffed_from = None

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
        )
        ctx = browser.new_context(
            viewport={"width": 1400, "height": 900},
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
            ),
            locale="en-US",
            timezone_id="Asia/Dhaka",
        )

        # hide webdriver
        ctx.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")

        # optional cookies
        if COOKIES_JSON:
            try:
                cookies = json.loads(COOKIES_JSON)
                # cookies should be a list of cookie dicts
                if isinstance(cookies, list) and cookies:
                    ctx.add_cookies(cookies)
                    print("Loaded cookies from secret ✅")
            except Exception as e:
                print("Cookie JSON parse failed:", e)

        page = ctx.new_page()

        def on_response(resp):
            nonlocal sniffed_counts, sniffed_from
            if sniffed_counts is not None:
                return
            try:
                ct = (resp.headers.get("content-type") or "").lower()
                url = resp.url.lower()
                if ("application/json" in ct) or ("graphql" in url) or ("/api/" in url):
                    data = resp.json()
                    c = deep_find_counts(data)
                    if c:
                        sniffed_counts = c
                        sniffed_from = resp.url
            except Exception:
                pass

        page.on("response", on_response)

        for url in URLS:
            try:
                print("TRY URL:", url)
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(2500)
                auto_scroll(page)
                page.wait_for_timeout(3500)

                body_text = page.locator("body").inner_text(timeout=15000)
                counts = parse_counts_from_text(body_text)
                if counts:
                    print("PARSED FROM RENDERED TEXT ✅")
                    break

                html = page.content()
                counts = parse_counts_from_json_like(html)
                if counts:
                    print("PARSED FROM HTML JSON-LIKE ✅")
                    break

                # try __NEXT_DATA__
                try:
                    nd = page.eval_on_selector("script#__NEXT_DATA__", "el => el.textContent")
                    if nd:
                        data = json.loads(nd)
                        counts = deep_find_counts(data)
                        if counts:
                            print("PARSED FROM __NEXT_DATA__ ✅")
                            break
                except Exception:
                    pass

                # if network sniff already found
                if sniffed_counts:
                    counts = sniffed_counts
                    print("PARSED FROM NETWORK ✅", sniffed_from)
                    break

            except Exception as e:
                print("URL failed:", url, "error:", e)

        browser.close()

    if not counts and sniffed_counts:
        counts = sniffed_counts

    note = ""
    if not counts:
        counts = {k: 0 for k in ORDER}
        note = "Data not visible in GitHub Actions (likely login/anti-bot). Add cookies secret."

    svg = build_svg(counts, note=note)
    os.makedirs("assets", exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(svg)

    print("Counts:", counts, "Total:", sum(counts.values()))
    if sniffed_from:
        print("Network source:", sniffed_from)
    print("Generated:", OUT_FILE)

if __name__ == "__main__":
    main()
