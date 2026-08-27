import os, re, json, base64
from typing import Any
import requests

HANDLE = (os.environ.get("CODOLIO_HANDLE") or "sojib19").strip()
PROFILE_URL = f"https://codolio.com/profile/{HANDLE}"
OUT_FILE = "assets/codolio-card.svg"

FONT = "ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,Arial"
BG1, BG2 = "#0D1117", "#0B1220"
BORDER = "#30363D"
TEXT = "#E6EDF3"
MUTED = "#9AA4B2"
ACCENT = "#22C55E"

# Favicon as logo (stable). You can change to another codolio logo URL later.
CODOLIO_LOGO_URL = "https://codolio.com/favicon.ico"


def esc(s: str) -> str:
    return (
        str(s)
        .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        .replace('"', "&quot;").replace("'", "&apos;")
    )


def fetch_html(url: str) -> str:
    r = requests.get(url, headers={"user-agent": "Mozilla/5.0"}, timeout=30)
    r.raise_for_status()
    return r.text


def extract_next_data(html: str):
    m = re.search(
        r'<script[^>]+id="__NEXT_DATA__"[^>]*>\s*(\{.*?\})\s*</script>',
        html, flags=re.DOTALL
    )
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except Exception:
        return None


def deep_find(obj: Any, keys: list[str]):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if str(k).lower() in [x.lower() for x in keys]:
                return v
        for v in obj.values():
            got = deep_find(v, keys)
            if got is not None:
                return got
    elif isinstance(obj, list):
        for it in obj:
            got = deep_find(it, keys)
            if got is not None:
                return got
    return None


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


def parse_profile(html: str):
    data = extract_next_data(html)

    display_name = "Codolio"
    username = HANDLE
    questions_solved = None
    active_days = None

    if data:
        display_name = deep_find(data, ["name", "fullName", "displayName"]) or display_name
        username = deep_find(data, ["username", "handle", "userName"]) or username
        questions_solved = deep_find(data, ["questionsSolved", "totalSolved", "problemsSolved", "solved"])
        active_days = deep_find(data, ["activeDays", "daysActive", "streakDays"])

    # regex fallback
    if questions_solved is None:
        m = re.search(r"Questions\s*Solved\D+(\d+)", html, flags=re.IGNORECASE)
        if m:
            questions_solved = int(m.group(1))

    if active_days is None:
        m = re.search(r"Active\s*Days\D+(\d+)", html, flags=re.IGNORECASE)
        if m:
            active_days = int(m.group(1))

    try:
        questions_solved = int(questions_solved) if questions_solved is not None else None
    except Exception:
        questions_solved = None

    try:
        active_days = int(active_days) if active_days is not None else None
    except Exception:
        active_days = None

    return {
        "display_name": str(display_name),
        "username": str(username),
        "questions_solved": questions_solved,
        "active_days": active_days,
    }


def build_svg(info: dict, logo_uri: str | None):
    W, H = 500, 400

    name = esc(info["display_name"])
    user = esc(info["username"])
    qs = info["questions_solved"]
    ad = info["active_days"]

    qs_text = esc(qs if qs is not None else "N/A")
    ad_text = esc(ad if ad is not None else "N/A")

    if logo_uri:
        logo = f'<image href="{logo_uri}" x="24" y="26" width="30" height="30" />'
    else:
        logo = (
            f'<rect x="24" y="26" width="30" height="30" fill="{ACCENT}"/>'
            f'<text x="39" y="47" text-anchor="middle" fill="#0D1117" '
            f'font-size="14" font-weight="900" font-family="{FONT}">C</text>'
        )

    # sharp corners => rx = 0
    rx = 0

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
    {name}
  </text>
  <text x="64" y="78" fill="{ACCENT}" font-size="17" font-weight="900" font-family="{FONT}">
    Codolio
  </text>
  <text x="64" y="104" fill="{MUTED}" font-size="14" font-weight="700" font-family="{FONT}">
    @{user}
  </text>

  <!-- Stat boxes -->
  <rect x="24" y="140" width="216" height="98" rx="12" fill="#0B1220" stroke="{BORDER}"/>
  <rect x="260" y="140" width="216" height="98" rx="12" fill="#0B1220" stroke="{BORDER}"/>

  <text x="132" y="170" text-anchor="middle" fill="#FFB86C" font-size="14" font-weight="900" font-family="{FONT}">
    Questions Solved
  </text>
  <text x="132" y="214" text-anchor="middle" fill="{TEXT}" font-size="38" font-weight="900" font-family="{FONT}">
    {qs_text}
  </text>

  <text x="368" y="170" text-anchor="middle" fill="{ACCENT}" font-size="14" font-weight="900" font-family="{FONT}">
    Active Days
  </text>
  <text x="368" y="214" text-anchor="middle" fill="{TEXT}" font-size="38" font-weight="900" font-family="{FONT}">
    {ad_text}
  </text>
</svg>
"""


def main():
    os.makedirs("assets", exist_ok=True)
    html = fetch_html(PROFILE_URL)
    info = parse_profile(html)
    logo_uri = fetch_logo_data_uri(CODOLIO_LOGO_URL)
    svg = build_svg(info, logo_uri)

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(svg)

    print("Parsed:", info)
    print("Generated:", OUT_FILE)


if __name__ == "__main__":
    main()
