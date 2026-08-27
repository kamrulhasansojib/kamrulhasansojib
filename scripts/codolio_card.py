import os
import re
import base64
import requests
from playwright.sync_api import sync_playwright

HANDLE = (os.environ.get("CODOLIO_HANDLE") or "sojib19").strip()
PROFILE_URL = f"https://codolio.com/profile/{HANDLE}"
OUT_FILE = "assets/codolio-card.svg"

FONT = "ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,Arial"
BG1, BG2 = "#0D1117", "#0B1220"
BORDER = "#30363D"
TEXT = "#E6EDF3"
MUTED = "#9AA4B2"
ACCENT = "#22C55E"

GREEN = "#22C55E"   # Easy
ORANGE = "#F59E0B"  # Medium
RED = "#EF4444"     # Hard
BOX_BG = "#0B1220"

CODOLIO_LOGO_URL = "https://codolio.com/favicon.ico"


def esc(s: str) -> str:
    return (
        str(s)
        .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        .replace('"', "&quot;").replace("'", "&apos;")
    )


def fetch_logo_data_uri(url: str) -> str | None:
    try:
        r = requests.get(url, headers={"user-agent": "Mozilla/5.0"}, timeout=20)
        if r.status_code != 200 or not r.content:
            return None
        b64 = base64.b64encode(r.content).decode("ascii")
        ctype = (r.headers.get("content-type") or "").lower()
        if "png" in ctype:
            mime = "image/png"
        elif "svg" in ctype:
            mime = "image/svg+xml"
        else:
            mime = "image/x-icon"
        return f"data:{mime};base64,{b64}"
    except Exception:
        return None


def find_stat_int(text: str, label: str) -> int | None:
    m = re.search(rf"{re.escape(label)}\s*[:\-]?\s*(\d+)", text, flags=re.IGNORECASE)
    return int(m.group(1)) if m else None


def parse_name_handle(text: str):
    display_name = HANDLE
    username = HANDLE

    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for i, ln in enumerate(lines):
        if re.fullmatch(rf"@{re.escape(HANDLE)}", ln):
            username = HANDLE
            if i > 0:
                display_name = lines[i - 1]
            break

    return display_name, username


def parse_dsa_block(text: str):
    # Prefer: "DSA ... Easy 5 ... Medium 1 ... Hard 0"
    m = re.search(
        r"DSA.*?Easy\D{0,20}(\d+).*?Medium\D{0,20}(\d+).*?Hard\D{0,20}(\d+)",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if m:
        return int(m.group(1)), int(m.group(2)), int(m.group(3))

    def any_diff(name: str):
        mm = re.search(rf"\b{name}\b\D{{0,15}}(\d+)", text, flags=re.IGNORECASE)
        return int(mm.group(1)) if mm else None

    return any_diff("Easy"), any_diff("Medium"), any_diff("Hard")


def donut_segments(values: dict, order: list[str], colors: dict, cx: int, cy: int, r: int, sw: int):
    total = sum(int(values.get(k, 0) or 0) for k in order)
    if total <= 0:
        return "", 0

    segs = []
    offset = 0.0
    for k in order:
        v = int(values.get(k, 0) or 0)
        if v <= 0:
            continue
        pct = (v / total) * 100.0
        segs.append(
            f'''
      <circle cx="{cx}" cy="{cy}" r="{r}" pathLength="100"
              fill="none" stroke="{colors[k]}" stroke-width="{sw}"
              stroke-dasharray="{pct:.6f} {100.0 - pct:.6f}"
              stroke-dashoffset="{-offset:.6f}" />'''
        )
        offset += pct

    return "\n".join(segs), total


def build_svg(display_name, username, qs, ad, easy, medium, hard, logo_uri: str | None):
    W, H = 500, 400

    # Outer card rounded like your screenshot
    outer_rx = 18

    qs_text = qs if qs is not None else "N/A"
    ad_text = ad if ad is not None else "N/A"

    easy_text = easy if easy is not None else "N/A"
    medium_text = medium if medium is not None else "N/A"
    hard_text = hard if hard is not None else "N/A"

    easy_v = 0 if easy is None else int(easy)
    med_v = 0 if medium is None else int(medium)
    hard_v = 0 if hard is None else int(hard)

    # Logo
    if logo_uri:
        logo = f'<image href="{logo_uri}" x="24" y="22" width="30" height="30" />'
    else:
        logo = (
            f'<rect x="24" y="22" width="30" height="30" fill="{ACCENT}"/>'
            f'<text x="39" y="44" text-anchor="middle" fill="#0D1117" font-size="14" font-weight="900" font-family="{FONT}">C</text>'
        )

    # Header positions
    hx = 64

    # Top stat boxes
    box_y = 92
    box_w = 216
    box_h = 92
    gap = 20

    # ---- DSA layout (NO container background/border) ----
    # Moved UP + more bottom gap
    dsa_title_x = 40
    dsa_title_y = 226  # was 242

    # Donut (left) moved UP
    donut_cx = 120
    donut_cy = 302      # was 320
    donut_r = 56
    donut_sw = 14

    dsa_vals = {"Easy": easy_v, "Medium": med_v, "Hard": hard_v}
    segs, total = donut_segments(
        dsa_vals,
        order=["Easy", "Medium", "Hard"],
        colors={"Easy": GREEN, "Medium": ORANGE, "Hard": RED},
        cx=donut_cx, cy=donut_cy, r=donut_r, sw=donut_sw
    )

    # Rows (right) moved UP, bottom gap increased
    row_x = 260
    row_w = 216
    row_h = 34
    row_gap = 10
    row_y0 = 242  # was 258

    def row(y, label, color, value):
        return f"""
  <rect x="{row_x}" y="{y}" width="{row_w}" height="{row_h}" rx="10" fill="{BOX_BG}" stroke="{BORDER}"/>
  <text x="{row_x + 14}" y="{y + 23}" fill="{color}" font-size="18" font-weight="900" font-family="{FONT}">{label}</text>
  <text x="{row_x + row_w - 14}" y="{y + 23}" text-anchor="end" fill="{TEXT}" font-size="18" font-weight="900" font-family="{FONT}">{esc(value)}</text>
"""

    # One-line: Codolio @handle
    brand_line = f"""<text x="{hx}" y="74" font-size="16" font-weight="900" font-family="{FONT}">
      <tspan fill="{ACCENT}">Codolio</tspan>
      <tspan fill="{MUTED}"> @{esc(username)}</tspan>
    </text>"""

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Codolio Card">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{BG1}"/>
      <stop offset="100%" stop-color="{BG2}"/>
    </linearGradient>
  </defs>

  <rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="{outer_rx}" fill="url(#bg)" stroke="{BORDER}"/>

  {logo}

  <text x="{hx}" y="48" fill="{TEXT}" font-size="22" font-weight="900" font-family="{FONT}">
    {esc(display_name)}
  </text>
  {brand_line}

  <!-- Stat boxes -->
  <rect x="24" y="{box_y}" width="{box_w}" height="{box_h}" rx="16" fill="{BOX_BG}" stroke="{BORDER}"/>
  <rect x="{24 + box_w + gap}" y="{box_y}" width="{box_w}" height="{box_h}" rx="16" fill="{BOX_BG}" stroke="{BORDER}"/>

  <text x="{24 + box_w/2}" y="{box_y + 28}" text-anchor="middle" fill="#FFB86C" font-size="14" font-weight="900" font-family="{FONT}">
    Questions Solved
  </text>
  <text x="{24 + box_w/2}" y="{box_y + 70}" text-anchor="middle" fill="{TEXT}" font-size="42" font-weight="900" font-family="{FONT}">
    {esc(qs_text)}
  </text>

  <text x="{24 + box_w + gap + box_w/2}" y="{box_y + 28}" text-anchor="middle" fill="{ACCENT}" font-size="14" font-weight="900" font-family="{FONT}">
    Active Days
  </text>
  <text x="{24 + box_w + gap + box_w/2}" y="{box_y + 70}" text-anchor="middle" fill="{TEXT}" font-size="42" font-weight="900" font-family="{FONT}">
    {esc(ad_text)}
  </text>

  <!-- DSA Title (no container box) -->
  <text x="{dsa_title_x}" y="{dsa_title_y}" fill="{TEXT}" font-size="22" font-weight="900" font-family="{FONT}">
    DSA Distribution
  </text>

  <!-- Donut -->
  <circle cx="{donut_cx}" cy="{donut_cy}" r="{donut_r}" fill="none" stroke="#21262D" stroke-width="{donut_sw}"/>
  <g transform="rotate(-90 {donut_cx} {donut_cy})">
{segs}
  </g>

  <text x="{donut_cx}" y="{donut_cy + 6}" text-anchor="middle" fill="{TEXT}" font-size="34" font-weight="900" font-family="{FONT}">
    {total}
  </text>
  <text x="{donut_cx}" y="{donut_cy + 32}" text-anchor="middle" fill="{MUTED}" font-size="14" font-weight="800" font-family="{FONT}">
    Solved
  </text>

  <!-- Right rows -->
  {row(row_y0 + 0*(row_h+row_gap), "Easy", GREEN, easy_text)}
  {row(row_y0 + 1*(row_h+row_gap), "Medium", ORANGE, medium_text)}
  {row(row_y0 + 2*(row_h+row_gap), "Hard", RED, hard_text)}
</svg>
"""


def main():
    os.makedirs("assets", exist_ok=True)

    # Codolio stats are JS-loaded -> render with Playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.goto(PROFILE_URL, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(3000)
        text = page.inner_text("body")
        browser.close()

    display_name, username = parse_name_handle(text)
    qs = find_stat_int(text, "Questions Solved")
    ad = find_stat_int(text, "Active Days")
    easy, medium, hard = parse_dsa_block(text)

    print("Parsed:", {
        "display_name": display_name,
        "username": username,
        "questions_solved": qs,
        "active_days": ad,
        "easy": easy,
        "medium": medium,
        "hard": hard,
    })

    logo_uri = fetch_logo_data_uri(CODOLIO_LOGO_URL)
    svg = build_svg(display_name, username, qs, ad, easy, medium, hard, logo_uri)

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(svg)

    print("Generated:", OUT_FILE)


if __name__ == "__main__":
    main()
