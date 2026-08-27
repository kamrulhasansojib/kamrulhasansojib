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

ORANGE = "#F59E0B"
RED = "#EF4444"
GREEN = "#22C55E"

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
    """
    Finds: 'Questions Solved 43' or 'Questions Solved: 43'
    """
    m = re.search(rf"{re.escape(label)}\s*[:\-]?\s*(\d+)", text, flags=re.IGNORECASE)
    return int(m.group(1)) if m else None


def find_difficulty(text: str, name: str) -> int | None:
    """
    Prefer line-based exact matches:
      Easy 5
      Medium 1
      Hard 0
    """
    # line based
    for line in text.splitlines():
        line = line.strip()
        m = re.match(rf"^{re.escape(name)}\s*\(?\s*(\d+)\s*\)?$", line, flags=re.IGNORECASE)
        if m:
            return int(m.group(1))

    # fallback any-where match (less strict)
    m = re.search(rf"\b{re.escape(name)}\b\D{{0,10}}(\d+)", text, flags=re.IGNORECASE)
    return int(m.group(1)) if m else None


def parse_from_rendered_text(text: str):
    # Basic profile stats
    qs = find_stat_int(text, "Questions Solved")
    ad = find_stat_int(text, "Active Days")

    easy = find_difficulty(text, "Easy")
    medium = find_difficulty(text, "Medium")
    hard = find_difficulty(text, "Hard")

    # Name + @handle (best-effort)
    display_name = HANDLE
    username = HANDLE

    # if '@sojib19' exists, try use previous non-empty line as name
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for i, ln in enumerate(lines):
        if re.fullmatch(rf"@{re.escape(HANDLE)}", ln):
            username = HANDLE
            if i > 0:
                display_name = lines[i - 1]
            break

    return display_name, username, qs, ad, easy, medium, hard


def build_svg(display_name: str, username: str, qs, ad, easy, medium, hard, logo_uri: str | None):
    W, H = 500, 400
    rx = 0  # sharp corners to match your other cards

    qs_text = qs if qs is not None else "N/A"
    ad_text = ad if ad is not None else "N/A"

    easy_text = easy if easy is not None else "N/A"
    med_text = medium if medium is not None else "N/A"
    hard_text = hard if hard is not None else "N/A"

    if logo_uri:
        logo = f'<image href="{logo_uri}" x="24" y="24" width="30" height="30" />'
    else:
        logo = (
            f'<rect x="24" y="24" width="30" height="30" fill="{ACCENT}"/>'
            f'<text x="39" y="45" text-anchor="middle" fill="#0D1117" '
            f'font-size="14" font-weight="900" font-family="{FONT}">C</text>'
        )

    # Layout positions
    # Header
    hx = 64

    # Stat boxes
    box_y = 96
    box_h = 92
    box_w = 216
    box_gap = 20

    # DSA distribution container
    dsa_x = 24
    dsa_y = 208
    dsa_w = 452
    dsa_h = 168

    # Row style
    row_x = dsa_x + 18
    row_w = dsa_w - 36
    row_h = 34
    row_gap = 12
    row_y0 = dsa_y + 52

    def dsa_row(y, label, color, value):
        return f"""
  <rect x="{row_x}" y="{y}" width="{row_w}" height="{row_h}" rx="10" fill="#0B1220" stroke="{BORDER}"/>
  <text x="{row_x + 16}" y="{y + 23}" fill="{color}" font-size="16" font-weight="900" font-family="{FONT}">{label}</text>
  <text x="{row_x + row_w - 16}" y="{y + 23}" text-anchor="end" fill="{TEXT}" font-size="16" font-weight="900" font-family="{FONT}">{esc(value)}</text>
"""

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Codolio Card">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{BG1}"/>
      <stop offset="100%" stop-color="{BG2}"/>
    </linearGradient>
  </defs>

  <rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="{rx}" fill="url(#bg)" stroke="{BORDER}"/>

  {logo}

  <text x="{hx}" y="46" fill="{TEXT}" font-size="22" font-weight="900" font-family="{FONT}">
    {esc(display_name)}
  </text>
  <text x="{hx}" y="72" fill="{ACCENT}" font-size="17" font-weight="900" font-family="{FONT}">
    Codolio
  </text>
  <text x="{hx}" y="96" fill="{MUTED}" font-size="14" font-weight="700" font-family="{FONT}">
    @{esc(username)}
  </text>

  <!-- Stat boxes -->
  <rect x="24" y="{box_y}" width="{box_w}" height="{box_h}" rx="12" fill="#0B1220" stroke="{BORDER}"/>
  <rect x="{24 + box_w + box_gap}" y="{box_y}" width="{box_w}" height="{box_h}" rx="12" fill="#0B1220" stroke="{BORDER}"/>

  <text x="{24 + box_w/2}" y="{box_y + 28}" text-anchor="middle" fill="#FFB86C" font-size="14" font-weight="900" font-family="{FONT}">
    Questions Solved
  </text>
  <text x="{24 + box_w/2}" y="{box_y + 70}" text-anchor="middle" fill="{TEXT}" font-size="36" font-weight="900" font-family="{FONT}">
    {esc(qs_text)}
  </text>

  <text x="{24 + box_w + box_gap + box_w/2}" y="{box_y + 28}" text-anchor="middle" fill="{ACCENT}" font-size="14" font-weight="900" font-family="{FONT}">
    Active Days
  </text>
  <text x="{24 + box_w + box_gap + box_w/2}" y="{box_y + 70}" text-anchor="middle" fill="{TEXT}" font-size="36" font-weight="900" font-family="{FONT}">
    {esc(ad_text)}
  </text>

  <!-- DSA Distribution -->
  <rect x="{dsa_x}" y="{dsa_y}" width="{dsa_w}" height="{dsa_h}" rx="14" fill="rgba(0,0,0,0)" stroke="{BORDER}"/>
  <text x="{dsa_x + 18}" y="{dsa_y + 32}" fill="{TEXT}" font-size="18" font-weight="900" font-family="{FONT}">
    DSA Distribution
  </text>
  <text x="{dsa_x + 18}" y="{dsa_y + 52}" fill="{MUTED}" font-size="12" font-weight="700" font-family="{FONT}">
    Based on Difficulty
  </text>

  {dsa_row(row_y0 + 0*(row_h+row_gap), "Easy", GREEN, easy_text)}
  {dsa_row(row_y0 + 1*(row_h+row_gap), "Medium", ORANGE, med_text)}
  {dsa_row(row_y0 + 2*(row_h+row_gap), "Hard", RED, hard_text)}
</svg>
"""


def main():
    os.makedirs("assets", exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.goto(PROFILE_URL, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(3000)
        text = page.inner_text("body")
        browser.close()

    display_name, username, qs, ad, easy, medium, hard = parse_from_rendered_text(text)
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
