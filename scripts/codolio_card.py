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
ORANGE = "#FFB86C"

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


def parse_from_rendered_text(text: str):
    # questions solved
    qs = None
    m = re.search(r"Questions\s*Solved\s*[:\-]?\s*(\d+)", text, flags=re.IGNORECASE)
    if m:
        qs = int(m.group(1))

    # active days
    ad = None
    m = re.search(r"Active\s*Days\s*[:\-]?\s*(\d+)", text, flags=re.IGNORECASE)
    if m:
        ad = int(m.group(1))

    # try name from first big line (fallback)
    display_name = "Codolio"
    # often profile has "Kamrul Hasan Sojib" visible
    # keep it simple: if handle is there, keep name as handle owner unknown -> use handle as fallback
    display_name = HANDLE

    # username shown as @handle
    username = HANDLE

    return display_name, username, qs, ad


def build_svg(display_name: str, username: str, qs, ad, logo_uri: str | None):
    W, H = 500, 400  # same ratio as your GFG/LeetCode
    rx = 0  # sharp corners

    qs_text = qs if qs is not None else "N/A"
    ad_text = ad if ad is not None else "N/A"

    if logo_uri:
        logo = f'<image href="{logo_uri}" x="24" y="26" width="30" height="30" />'
    else:
        logo = (
            f'<rect x="24" y="26" width="30" height="30" fill="{ACCENT}"/>'
            f'<text x="39" y="47" text-anchor="middle" fill="#0D1117" '
            f'font-size="14" font-weight="900" font-family="{FONT}">C</text>'
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Codolio Card">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{BG1}"/>
      <stop offset="100%" stop-color="{BG2}"/>
    </linearGradient>
  </defs>

  <rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="{rx}" fill="url(#bg)" stroke="{BORDER}"/>

  {logo}

  <text x="64" y="50" fill="{TEXT}" font-size="22" font-weight="900" font-family="{FONT}">
    {esc(display_name)}
  </text>
  <text x="64" y="78" fill="{ACCENT}" font-size="17" font-weight="900" font-family="{FONT}">
    Codolio
  </text>
  <text x="64" y="104" fill="{MUTED}" font-size="14" font-weight="700" font-family="{FONT}">
    @{esc(username)}
  </text>

  <!-- Stat boxes -->
  <rect x="24" y="140" width="216" height="98" rx="12" fill="#0B1220" stroke="{BORDER}"/>
  <rect x="260" y="140" width="216" height="98" rx="12" fill="#0B1220" stroke="{BORDER}"/>

  <text x="132" y="170" text-anchor="middle" fill="{ORANGE}" font-size="14" font-weight="900" font-family="{FONT}">
    Questions Solved
  </text>
  <text x="132" y="214" text-anchor="middle" fill="{TEXT}" font-size="38" font-weight="900" font-family="{FONT}">
    {esc(qs_text)}
  </text>

  <text x="368" y="170" text-anchor="middle" fill="{ACCENT}" font-size="14" font-weight="900" font-family="{FONT}">
    Active Days
  </text>
  <text x="368" y="214" text-anchor="middle" fill="{TEXT}" font-size="38" font-weight="900" font-family="{FONT}">
    {esc(ad_text)}
  </text>
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

    display_name, username, qs, ad = parse_from_rendered_text(text)
    print("Parsed:", {"display_name": display_name, "username": username, "questions_solved": qs, "active_days": ad})

    logo_uri = fetch_logo_data_uri(CODOLIO_LOGO_URL)
    svg = build_svg(display_name, username, qs, ad, logo_uri)

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(svg)

    print("Generated:", OUT_FILE)


if __name__ == "__main__":
    main()
