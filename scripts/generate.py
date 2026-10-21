"""Genera los SVG del perfil de GitHub — estilo "identidad viva" en azul marino y negro.

Uso:
    GITHUB_TOKEN=... python scripts/generate.py     # datos reales (GraphQL, con respaldo REST)
    python scripts/generate.py --demo               # datos de ejemplo, sin red

Salida: assets/*.svg
"""
from __future__ import annotations

import datetime as dt
import io
import json
import os
import random
import sys
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

USER = os.environ.get("PROFILE_USER", "GonzalezLazaro")
HANDLE = USER.lower()
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"

# ---------- Paleta: azul marino + negro ----------
BG = "#04060b"
PANEL = "#0a1224"
NAVY = "#0b1f44"
NAVY_2 = "#13306b"
BORDER = "#1a2f5a"
ACCENT = "#3b82f6"
ACCENT_2 = "#60a5fa"
SOFT = "#93c5fd"
TEXT = "#e6edf7"
MUTED = "#8ba3c7"
DIM = "#4b6a9b"
LEVELS = [PANEL, "#0e2a5c", "#1d4ed8", "#3b82f6", "#93c5fd"]

SANS = "'Segoe UI', Ubuntu, 'Helvetica Neue', Arial, sans-serif"
MONO = "'JetBrains Mono', 'Cascadia Code', Consolas, 'SFMono-Regular', Menlo, monospace"

FOCUS = "Python / SQL Server / Azure"
LOCATION = "Córdoba, Argentina"

HIGHLIGHTS = [
    ("Python", "Foco actual", "APIs, automatización y herramientas internas"),
    ("SQL Server", "Datos y reportes", "Modelado, consultas avanzadas y ETL"),
    ("Azure", "Cloud y DevOps", "Despliegues, Docker y Azure DevOps"),
]
STACK = ["Python", "Django", "FastAPI", "Flask", "SQL Server", "PostgreSQL",
         "MySQL", "Apache Airflow", "Azure", "Docker", "Azure DevOps", "Git"]

FEATURED = ["Encuestas-Sistemas", "api-enlaces", "api", "Widget"]
DESCRIPTIONS = {
    "Encuestas-Sistemas": "Sistema de encuestas para equipos internos",
    "api-enlaces": "API de gestión de enlaces con interfaz web",
    "api": "API REST en Python",
    "Widget": "Widget web embebible",
}
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


def e(s) -> str:
    return escape(str(s), {'"': "&quot;"})


def write(name: str, svg: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(svg.strip() + "\n", encoding="utf-8")


def grid(pid: str, size: int = 32, op: float = 0.5) -> str:
    return (f'<pattern id="{pid}" width="{size}" height="{size}" patternUnits="userSpaceOnUse">'
            f'<path d="M {size} 0 L 0 0 0 {size}" fill="none" stroke="{NAVY}" stroke-width="1" opacity="{op}"/></pattern>')


def card_open(w: int, h: int, label: str) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{e(label)}">')


def fmt_month(iso: str) -> str:
    d = dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return f"{MESES[d.month - 1]} {d.year}"


# ---------- Datos ----------
QUERY = """
query($login: String!) {
  user(login: $login) {
    avatarUrl(size: 96)
    followers { totalCount }
    repositories(ownerAffiliations: OWNER, privacy: PUBLIC, first: 100, orderBy: {field: PUSHED_AT, direction: DESC}) {
      totalCount
      nodes {
        name description isFork createdAt pushedAt stargazerCount
        primaryLanguage { name }
      }
    }
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""


def _req(url: str, data: bytes | None = None, accept: str = "application/vnd.github+json"):
    headers = {"Accept": accept, "User-Agent": "profile-generator"}
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"bearer {os.environ['GITHUB_TOKEN']}"
    if data:
        headers["Content-Type"] = "application/json"
    with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=headers), timeout=30) as r:
        return r.read()


def fetch() -> dict:
    payload = json.loads(_req("https://api.github.com/graphql",
                              json.dumps({"query": QUERY, "variables": {"login": USER}}).encode()))
    if "errors" in payload:
        raise RuntimeError(payload["errors"])
    return payload["data"]["user"]


def fetch_rest() -> dict:
    api = "https://api.github.com"
    user = json.loads(_req(f"{api}/users/{USER}"))
    repos = json.loads(_req(f"{api}/users/{USER}/repos?per_page=100&sort=pushed"))
    return {
        "avatarUrl": user["avatar_url"],
        "followers": {"totalCount": user["followers"]},
        "repositories": {"totalCount": user["public_repos"], "nodes": [
            {"name": r["name"], "description": r["description"], "isFork": r["fork"],
             "createdAt": r["created_at"], "pushedAt": r["pushed_at"], "stargazerCount": r["stargazers_count"],
             "primaryLanguage": {"name": r["language"]} if r["language"] else None} for r in repos]},
        "contributionsCollection": None,
    }


def demo() -> dict:
    rnd = random.Random(7)
    today = dt.date.today()
    start = today - dt.timedelta(days=today.weekday() + 1 + 52 * 7)
    days = [{"date": (start + dt.timedelta(days=i)).isoformat(),
             "contributionCount": rnd.choice([0, 0, 0, 0, 1, 2, 4, 7]) if i > 200 else 0}
            for i in range((today - start).days + 1)]
    weeks = [{"contributionDays": days[i:i + 7]} for i in range(0, len(days), 7)]
    data = [("Widget", "HTML", "2026-09-30T12:00:00Z", "2026-10-13T18:26:28Z"),
            ("Encuestas-Sistemas", "Python", "2025-11-10T12:00:00Z", "2026-02-04T19:04:29Z"),
            ("api", "Python", "2025-06-20T12:00:00Z", "2025-06-26T19:31:01Z"),
            ("api-enlaces", "HTML", "2025-06-18T12:00:00Z", "2025-06-25T18:39:07Z")]
    return {
        "avatarUrl": None,
        "followers": {"totalCount": 1},
        "repositories": {"totalCount": 5, "nodes": [
            {"name": n, "description": None, "isFork": False, "createdAt": c, "pushedAt": p,
             "stargazerCount": 0, "primaryLanguage": {"name": l}} for n, l, c, p in data]},
        "contributionsCollection": {"contributionCalendar": {"totalContributions": 82, "weeks": weeks}},
    }


def streaks(weeks: list) -> tuple[int, int, int]:
    days = sorted((d for w in weeks for d in w["contributionDays"]), key=lambda d: d["date"])
    longest = run = 0
    for d in days:
        run = run + 1 if d["contributionCount"] > 0 else 0
        longest = max(longest, run)
    current = 0
    for i, d in enumerate(reversed(days)):
        if d["contributionCount"] > 0:
            current += 1
        elif i == 0:
            continue
        else:
            break
    active = sum(1 for d in days if d["contributionCount"] > 0)
    return current, longest, active


# ---------- Retrato en matriz de puntos ----------
def avatar_dots(u: dict, cx: float, cy: float, radius: float) -> str:
    try:
        from PIL import Image  # noqa: PLC0415
    except ImportError:
        return ""
    raw = None
    local = os.environ.get("AVATAR_FILE")
    try:
        if local:
            raw = Path(local).read_bytes()
        elif u.get("avatarUrl"):
            raw = _req(u["avatarUrl"], accept="image/*")
    except Exception as exc:  # noqa: BLE001
        print(f"sin avatar: {exc}", file=sys.stderr)
    if not raw:
        return ""
    n = 46
    im = Image.open(io.BytesIO(raw)).convert("RGBA").resize((n, n))
    cell = 2 * radius / n
    rnd = random.Random(3)
    out = []
    for y in range(n):
        for x in range(n):
            dx, dy = x - n / 2 + 0.5, y - n / 2 + 0.5
            if dx * dx + dy * dy > (n / 2) ** 2:
                continue
            r, g, b, a = im.getpixel((x, y))
            if a < 40:
                continue
            lum = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255
            if lum < 0.07:
                continue
            color = NAVY_2 if lum < 0.25 else ACCENT if lum < 0.5 else ACCENT_2 if lum < 0.72 else SOFT if lum < 0.88 else TEXT
            rad = cell * (0.18 + 0.32 * lum)
            px, py = cx - radius + (x + 0.5) * cell, cy - radius + (y + 0.5) * cell
            cls = ' class="tw"' if rnd.random() < 0.08 else ""
            delay = f' style="animation-delay:{rnd.random() * 4:.2f}s"' if cls else ""
            out.append(f'<circle{cls}{delay} cx="{px:.1f}" cy="{py:.1f}" r="{rad:.2f}" fill="{color}"/>')
    return "".join(out)


# ---------- Secciones ----------
def hero(u: dict, stats: dict) -> str:
    w, h = 1200, 640
    cx, cy = 905, 285
    dots = avatar_dots(u, cx, cy, 150)
    if not dots:
        dots = f'<text x="{cx}" y="{cy + 30}" text-anchor="middle" font-family="{MONO}" font-size="96" font-weight="700" fill="url(#px)">LG</text>'
    ticks = "".join(
        f'<line x1="{cx}" y1="{cy - 218}" x2="{cx}" y2="{cy - 208}" stroke="{ACCENT}" stroke-width="2" transform="rotate({a} {cx} {cy})" opacity=".7"/>'
        for a in range(0, 360, 30))
    items = [("REPOSITORIOS", stats["repos"]), ("ESTRELLAS", stats["stars"]),
             ("CONTRIBUCIONES", stats["contrib"]), ("SEGUIDORES", stats["followers"])]
    colw = (w - 112) / 4
    stat_svg = "".join(
        f'<g class="up" style="animation-delay:{0.15 * i + .3:.2f}s">'
        f'<text x="{56 + i * colw}" y="548" font-family="{MONO}" font-size="12" letter-spacing="2.5" fill="{DIM}">{label}</text>'
        f'<circle cx="{56 + (i + 1) * colw - 24}" cy="544" r="3.5" fill="{ACCENT}" class="blink" style="animation-delay:{i * .5}s"/>'
        f'<text x="{56 + i * colw}" y="596" font-family="{MONO}" font-size="40" font-weight="700" fill="{TEXT}">{e(v)}</text></g>'
        for i, (label, v) in enumerate(items))
    return f"""
{card_open(w, h, f"Lazaro — {FOCUS} — {LOCATION}")}
  <defs>
    {grid("g", 30, .45)}
    <pattern id="px" width="6" height="6" patternUnits="userSpaceOnUse"><rect width="4.6" height="4.6" fill="{TEXT}"/></pattern>
    <pattern id="pxb" width="6" height="6" patternUnits="userSpaceOnUse"><rect width="4.6" height="4.6" fill="{ACCENT}"/></pattern>
    <radialGradient id="glow" cx="{cx / w}" cy="{cy / h}" r="0.42">
      <stop offset="0" stop-color="{NAVY_2}" stop-opacity=".9"/>
      <stop offset=".6" stop-color="{NAVY}" stop-opacity=".35"/>
      <stop offset="1" stop-color="{BG}" stop-opacity="0"/>
    </radialGradient>
    <clipPath id="c"><rect width="{w}" height="{h}" rx="22"/></clipPath>
  </defs>
  <style>
    .spin {{ transform-origin: {cx}px {cy}px; animation: spin 50s linear infinite; }}
    .spin2 {{ transform-origin: {cx}px {cy}px; animation: spin 30s linear infinite reverse; }}
    .tw {{ animation: tw 3.2s ease-in-out infinite; }}
    .blink {{ animation: blink 2.4s ease-in-out infinite; }}
    .glitch {{ animation: glitch 6s steps(1) infinite; }}
    .up {{ animation: up .7s ease-out backwards; }}
    .scan {{ animation: scan 8s linear infinite; }}
    @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
    @keyframes tw {{ 0%,100% {{ opacity: 1; }} 50% {{ opacity: .2; }} }}
    @keyframes blink {{ 0%,100% {{ opacity: 1; }} 50% {{ opacity: .25; }} }}
    @keyframes glitch {{ 0%,92%,100% {{ transform: translate(0,0); opacity: .0; }} 93% {{ transform: translate(4px,-2px); opacity: .7; }} 95% {{ transform: translate(-3px,1px); opacity: .5; }} 97% {{ transform: translate(2px,0); opacity: .6; }} }}
    @keyframes up {{ from {{ opacity: 0; transform: translateY(6px); }} to {{ opacity: 1; transform: none; }} }}
    @keyframes scan {{ from {{ transform: translateY(-40px); }} to {{ transform: translateY({h + 40}px); }} }}
  </style>
  <g clip-path="url(#c)">
    <rect width="{w}" height="{h}" fill="{BG}"/>
    <rect width="{w}" height="{h}" fill="url(#g)"/>
    <rect width="{w}" height="{h}" fill="url(#glow)"/>
    <rect class="scan" x="0" y="0" width="{w}" height="2" fill="{ACCENT}" opacity=".12"/>

    <text x="56" y="70" font-family="{MONO}" font-size="12" letter-spacing="3.5" fill="{DIM}">PERFIL / IDENTIDAD VIVA</text>
    <text x="{w - 56}" y="70" text-anchor="end" font-family="{MONO}" font-size="13" fill="{ACCENT_2}">@{HANDLE}</text>

    <text x="56" y="170" font-family="{MONO}" font-size="14" letter-spacing="4" fill="{ACCENT_2}">HOLA, MUNDO. SOY</text>
    <text class="glitch" x="52" y="290" font-family="{MONO}" font-size="132" font-weight="800" fill="url(#pxb)">Lazaro</text>
    <text x="52" y="290" font-family="{MONO}" font-size="132" font-weight="800" fill="url(#px)">Lazaro</text>
    <text x="56" y="384" font-family="{MONO}" font-size="20" font-weight="700" fill="{TEXT}">{e(FOCUS)}</text>
    <text x="56" y="414" font-family="{MONO}" font-size="13" fill="{MUTED}">{e(LOCATION)}</text>

    <circle cx="{cx}" cy="{cy}" r="230" fill="none" stroke="{BORDER}"/>
    <g class="spin"><circle cx="{cx}" cy="{cy}" r="214" fill="none" stroke="{ACCENT}" stroke-width="1.5" stroke-dasharray="160 520" opacity=".8"/>{ticks}</g>
    <g class="spin2"><circle cx="{cx}" cy="{cy}" r="190" fill="none" stroke="{NAVY_2}" stroke-width="1.2" stroke-dasharray="3 9"/></g>
    <circle cx="{cx}" cy="{cy}" r="166" fill="{BG}" opacity=".55"/>
    {dots}

    <line x1="56" y1="490" x2="{w - 56}" y2="490" stroke="{BORDER}"/>
    {stat_svg}
    <text x="{w - 56}" y="624" text-anchor="end" font-family="{MONO}" font-size="11" fill="{DIM}">github.com/{USER}</text>
  </g>
  <rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="22" fill="none" stroke="{BORDER}"/>
</svg>"""


def highlights() -> str:
    w, h = 1200, 230
    cw = (w - 48) / 3
    cards = []
    for i, (tech, tag, desc) in enumerate(HIGHLIGHTS):
        x = 16 + i * (cw + 8)
        cards.append(f"""
  <g class="up" style="animation-delay:{i * .2:.1f}s">
    <rect x="{x}" y="16" width="{cw}" height="{h - 32}" rx="16" fill="url(#cg)" stroke="{BORDER}"/>
    <rect class="edge" style="animation-delay:{i * 1.3:.1f}s" x="{x}" y="16" width="{cw}" height="{h - 32}" rx="16" fill="none" stroke="{ACCENT_2}" stroke-width="1.5"/>
    <text x="{x + 28}" y="58" font-family="{MONO}" font-size="12" letter-spacing="2.5" fill="{ACCENT_2}">0{i + 1} · {e(tag.upper())}</text>
    <text x="{x + 26}" y="118" font-family="{SANS}" font-size="40" font-weight="700" fill="{TEXT}">{e(tech)}</text>
    <text x="{x + 28}" y="152" font-family="{SANS}" font-size="15" fill="{MUTED}">{e(desc)}</text>
    <rect x="{x + 28}" y="178" width="{cw - 56}" height="4" rx="2" fill="{PANEL}"/>
    <rect class="bar" style="animation-delay:{i * .25 + .3:.2f}s; transform-origin:{x + 28}px 0" x="{x + 28}" y="178" width="{(cw - 56) * (0.92 - i * 0.12):.0f}" height="4" rx="2" fill="{ACCENT}"/>
  </g>""")
    return f"""
{card_open(w, h, "Áreas de foco")}
  <defs><linearGradient id="cg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{NAVY}"/><stop offset="1" stop-color="{BG}"/></linearGradient></defs>
  <style>
    .up {{ animation: up .7s ease-out backwards; }}
    .bar {{ animation: grow 1.4s cubic-bezier(.2,.8,.2,1) backwards; }}
    .edge {{ stroke-dasharray: 140 1900; animation: run 7s linear infinite; }}
    @keyframes up {{ from {{ opacity: 0; transform: translateY(8px); }} to {{ opacity: 1; transform: none; }} }}
    @keyframes grow {{ from {{ transform: scaleX(0); }} to {{ transform: scaleX(1); }} }}
    @keyframes run {{ to {{ stroke-dashoffset: -2040; }} }}
  </style>
  {''.join(cards)}
</svg>"""


def stack() -> str:
    w, per = 1200, 6
    rows = (len(STACK) + per - 1) // per
    h = 40 + rows * 74
    cw = (w - 32 - (per - 1) * 12) / per
    chips = []
    for i, name in enumerate(STACK):
        r, c = divmod(i, per)
        x, y = 16 + c * (cw + 12), 20 + r * 74
        chips.append(
            f'<g class="up" style="animation-delay:{i * .06:.2f}s">'
            f'<rect x="{x}" y="{y}" width="{cw}" height="58" rx="12" fill="{PANEL}" stroke="{BORDER}"/>'
            f'<rect class="glint" style="animation-delay:{i * .45:.2f}s" x="{x}" y="{y}" width="{cw}" height="58" rx="12" fill="none" stroke="{ACCENT}" stroke-width="1.5"/>'
            f'<circle cx="{x + 24}" cy="{y + 29}" r="5" fill="{ACCENT_2}"/>'
            f'<text x="{x + 40}" y="{y + 34}" font-family="{MONO}" font-size="15" fill="{TEXT}">{e(name)}</text></g>')
    return f"""
{card_open(w, h, "Stack: " + ", ".join(STACK))}
  <style>
    .up {{ animation: up .5s ease-out backwards; }}
    .glint {{ opacity: 0; animation: glint {len(STACK) * .45:.1f}s ease-in-out infinite; }}
    @keyframes up {{ from {{ opacity: 0; transform: translateY(6px); }} to {{ opacity: 1; transform: none; }} }}
    @keyframes glint {{ 0%,100% {{ opacity: 0; }} 4% {{ opacity: 1; }} 12% {{ opacity: 0; }} }}
  </style>
  {''.join(chips)}
</svg>"""


def featured(u: dict) -> list[dict]:
    by = {r["name"]: r for r in u["repositories"]["nodes"]}
    return [by[n] for n in FEATURED if n in by]


def constellation(repos: list[dict]) -> str:
    w, h = 1200, 400
    cx, cy = 600, 200
    pos = [(250, 110), (950, 110), (250, 300), (950, 300)]
    parts = []
    for i, (r, (x, y)) in enumerate(zip(repos, pos)):
        lang = (r["primaryLanguage"] or {}).get("name", "—")
        anchor = "end" if x < cx else "start"
        tx = x - 26 if x < cx else x + 26
        parts.append(f"""
  <path class="flow" style="animation-delay:{i * .4:.1f}s" d="M{cx} {cy} C {(cx + x) / 2} {cy}, {(cx + x) / 2} {y}, {x} {y}" fill="none" stroke="{ACCENT}" stroke-width="1.6"/>
  <circle cx="{x}" cy="{y}" r="16" fill="{PANEL}" stroke="{ACCENT_2}" stroke-width="1.5"/>
  <circle class="pulse" style="animation-delay:{i * .6:.1f}s" cx="{x}" cy="{y}" r="16" fill="none" stroke="{ACCENT_2}"/>
  <circle cx="{x}" cy="{y}" r="5" fill="{SOFT}"/>
  <text x="{tx}" y="{y - 4}" text-anchor="{anchor}" font-family="{SANS}" font-size="20" font-weight="700" fill="{TEXT}">{e(r['name'])}</text>
  <text x="{tx}" y="{y + 20}" text-anchor="{anchor}" font-family="{MONO}" font-size="12" fill="{MUTED}">{e(lang)} · ★ {r['stargazerCount']}</text>""")
    return f"""
{card_open(w, h, "Constelación de proyectos")}
  <defs>{grid("g2", 30, .4)}
    <radialGradient id="cgl" cx=".5" cy=".5" r=".35"><stop offset="0" stop-color="{NAVY_2}" stop-opacity=".8"/><stop offset="1" stop-color="{BG}" stop-opacity="0"/></radialGradient>
    <clipPath id="c2"><rect width="{w}" height="{h}" rx="20"/></clipPath>
  </defs>
  <style>
    .flow {{ stroke-dasharray: 6 10; opacity: .7; animation: dash 4s linear infinite; }}
    .pulse {{ transform-box: fill-box; transform-origin: center; animation: pulse 3s ease-out infinite; }}
    .core {{ transform-box: fill-box; transform-origin: center; animation: spin 18s linear infinite; }}
    @keyframes dash {{ to {{ stroke-dashoffset: -64; }} }}
    @keyframes pulse {{ from {{ transform: scale(1); opacity: .9; }} to {{ transform: scale(2.6); opacity: 0; }} }}
    @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
  </style>
  <g clip-path="url(#c2)">
    <rect width="{w}" height="{h}" fill="{BG}"/>
    <rect width="{w}" height="{h}" fill="url(#g2)"/>
    <rect width="{w}" height="{h}" fill="url(#cgl)"/>
    {''.join(parts)}
    <circle class="core" cx="{cx}" cy="{cy}" r="58" fill="none" stroke="{ACCENT}" stroke-dasharray="10 8"/>
    <circle cx="{cx}" cy="{cy}" r="44" fill="{PANEL}" stroke="{ACCENT_2}" stroke-width="1.5"/>
    <text x="{cx}" y="{cy + 9}" text-anchor="middle" font-family="{MONO}" font-size="26" font-weight="800" fill="url(#cpx)">LG</text>
    <text x="24" y="{h - 20}" font-family="{MONO}" font-size="11" letter-spacing="2" fill="{DIM}">CONSTELACIÓN DE PROYECTOS</text>
  </g>
  <defs><pattern id="cpx" width="3" height="3" patternUnits="userSpaceOnUse"><rect width="2.3" height="2.3" fill="{TEXT}"/></pattern></defs>
  <rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="20" fill="none" stroke="{BORDER}"/>
</svg>"""


def timeline(repos: list[dict]) -> str:
    w, h = 1200, 210
    items = sorted(repos, key=lambda r: r["createdAt"])
    if not items:
        return ""
    t0 = dt.datetime.fromisoformat(items[0]["createdAt"].replace("Z", "+00:00"))
    t1 = dt.datetime.now(dt.timezone.utc)
    span = max((t1 - t0).total_seconds(), 1)
    x0, x1, ly = 70, w - 70, 104
    marks = []
    last_x = -999
    for i, r in enumerate(items):
        t = dt.datetime.fromisoformat(r["createdAt"].replace("Z", "+00:00"))
        x = x0 + (x1 - x0) * (t - t0).total_seconds() / span
        x = min(max(x, last_x + 170), x1 - 60)  # evita superposición de etiquetas
        last_x = x
        up = i % 2 == 0
        ty = ly - 30 if up else ly + 44
        marks.append(f"""
  <g class="up" style="animation-delay:{.3 + i * .25:.2f}s">
    <line x1="{x:.0f}" y1="{ly}" x2="{x:.0f}" y2="{ly - 18 if up else ly + 18}" stroke="{BORDER}"/>
    <circle cx="{x:.0f}" cy="{ly}" r="7" fill="{BG}" stroke="{ACCENT_2}" stroke-width="2"/>
    <text x="{x:.0f}" y="{ty}" text-anchor="middle" font-family="{SANS}" font-size="15" font-weight="700" fill="{TEXT}">{e(r['name'])}</text>
    <text x="{x:.0f}" y="{ty + 18}" text-anchor="middle" font-family="{MONO}" font-size="11" fill="{MUTED}">{fmt_month(r['createdAt'])}</text>
  </g>""")
    return f"""
{card_open(w, h, "Línea de tiempo de proyectos")}
  <defs><linearGradient id="tl" x1="0" x2="1"><stop offset="0" stop-color="{NAVY_2}"/><stop offset="1" stop-color="{ACCENT_2}"/></linearGradient></defs>
  <style>
    .line {{ stroke-dasharray: {x1 - x0}; animation: draw 1.6s ease-out backwards; }}
    .up {{ animation: up .6s ease-out backwards; }}
    .now {{ animation: blink 1.6s ease-in-out infinite; }}
    @keyframes draw {{ from {{ stroke-dashoffset: {x1 - x0}; }} to {{ stroke-dashoffset: 0; }} }}
    @keyframes up {{ from {{ opacity: 0; transform: translateY(6px); }} to {{ opacity: 1; transform: none; }} }}
    @keyframes blink {{ 50% {{ opacity: .2; }} }}
  </style>
  <rect width="{w}" height="{h}" rx="20" fill="{BG}" stroke="{BORDER}"/>
  <line class="line" x1="{x0}" y1="{ly}" x2="{x1}" y2="{ly}" stroke="url(#tl)" stroke-width="2"/>
  {''.join(marks)}
  <circle class="now" cx="{x1}" cy="{ly}" r="5" fill="{SOFT}"/>
  <text x="{x1}" y="{ly + 26}" text-anchor="end" font-family="{MONO}" font-size="11" fill="{ACCENT_2}">hoy</text>
  <text x="24" y="{h - 18}" font-family="{MONO}" font-size="11" letter-spacing="2" fill="{DIM}">LANZAMIENTOS</text>
</svg>"""


def momentum(stats: dict) -> str:
    w, h = 1200, 190
    items = [(stats["contrib"], "contribuciones", "último año"), (stats["current"], "racha actual", "días"),
             (stats["longest"], "racha máxima", "días"), (stats["active"], "días activos", "último año")]
    col = (w - 48) / 4
    cells = "".join(f"""
  <g class="up" style="animation-delay:{i * .15:.2f}s">
    <rect x="{24 + i * col + 8}" y="24" width="{col - 16}" height="{h - 48}" rx="14" fill="{PANEL}" stroke="{BORDER}"/>
    <text x="{24 + i * col + 34}" y="62" font-family="{MONO}" font-size="12" letter-spacing="2.5" fill="{DIM}">{e(label.upper())}</text>
    <circle cx="{24 + (i + 1) * col - 30}" cy="58" r="3.5" fill="{ACCENT}" class="blink" style="animation-delay:{i * .5}s"/>
    <text x="{24 + i * col + 32}" y="122" font-family="{MONO}" font-size="46" font-weight="700" fill="{TEXT}">{e(v)}</text>
    <text x="{24 + i * col + 34}" y="148" font-family="{MONO}" font-size="12" fill="{MUTED}">{e(sub)}</text>
  </g>""" for i, (v, label, sub) in enumerate(items))
    return f"""
{card_open(w, h, "Estadísticas de GitHub")}
  <style>
    .up {{ animation: up .6s ease-out backwards; }}
    .blink {{ animation: blink 2.4s ease-in-out infinite; }}
    @keyframes up {{ from {{ opacity: 0; transform: translateY(8px); }} to {{ opacity: 1; transform: none; }} }}
    @keyframes blink {{ 50% {{ opacity: .25; }} }}
  </style>
  <rect width="{w}" height="{h}" rx="20" fill="{BG}" stroke="{BORDER}"/>
  {cells}
</svg>"""


def heatmap(u: dict, stats: dict) -> str:
    w, h = 1200, 250
    cc = u.get("contributionsCollection")
    weeks = cc["contributionCalendar"]["weeks"] if cc else []
    cell, gap = 16, 4
    gx = (w - len(weeks) * (cell + gap)) / 2 if weeks else 0
    peak = max([d["contributionCount"] for wk in weeks for d in wk["contributionDays"]] + [1])
    cells, months, last_m = [], [], None
    for i, wk in enumerate(weeks):
        for d in wk["contributionDays"]:
            wd = (dt.date.fromisoformat(d["date"]).weekday() + 1) % 7
            c = d["contributionCount"]
            lvl = 0 if c == 0 else min(4, 1 + int(3 * c / peak))
            cls = "hm hot" if lvl >= 3 else "hm"
            cells.append(f'<rect class="{cls}" style="animation-delay:{i * .025:.3f}s" x="{gx + i * (cell + gap):.1f}" y="{52 + wd * (cell + gap)}" width="{cell}" height="{cell}" rx="3.5" fill="{LEVELS[lvl]}"/>')
        m = dt.date.fromisoformat(wk["contributionDays"][0]["date"]).month
        if m != last_m and i < len(weeks) - 2:
            months.append(f'<text x="{gx + i * (cell + gap):.1f}" y="40" font-family="{MONO}" font-size="11" fill="{DIM}">{MESES[m - 1]}</text>')
            last_m = m
    if not weeks:
        cells.append(f'<text x="{w / 2}" y="130" text-anchor="middle" font-family="{MONO}" font-size="14" fill="{MUTED}">calendario disponible en la próxima actualización</text>')
    legend = "".join(f'<rect x="{w - 150 + i * 20}" y="{h - 30}" width="14" height="14" rx="3" fill="{c}"/>' for i, c in enumerate(LEVELS))
    return f"""
{card_open(w, h, "Mapa de contribuciones")}
  <style>
    .hm {{ animation: in .4s ease-out backwards; }}
    .hot {{ animation: in .4s ease-out backwards, glow 3s ease-in-out 2s infinite; }}
    @keyframes in {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
    @keyframes glow {{ 0%,100% {{ opacity: 1; }} 50% {{ opacity: .55; }} }}
  </style>
  <rect width="{w}" height="{h}" rx="20" fill="{BG}" stroke="{BORDER}"/>
  {''.join(months)}
  {''.join(cells)}
  <text x="{gx or 24:.0f}" y="{h - 18}" font-family="{MONO}" font-size="12" fill="{MUTED}">racha actual: {e(stats['current'])} · días activos: {e(stats['active'])}</text>
  <text x="{w - 160}" y="{h - 19}" text-anchor="end" font-family="{MONO}" font-size="11" fill="{DIM}">menos</text>
  {legend}
  <text x="{w - 46}" y="{h - 19}" font-family="{MONO}" font-size="11" fill="{DIM}">más</text>
</svg>"""


def contact() -> str:
    w, h = 1200, 230
    return f"""
{card_open(w, h, "Sigamos en contacto")}
  <defs>{grid("g3", 30, .4)}
    <radialGradient id="cg3" cx=".5" cy="1" r=".7"><stop offset="0" stop-color="{NAVY_2}" stop-opacity=".9"/><stop offset="1" stop-color="{BG}" stop-opacity="0"/></radialGradient>
    <clipPath id="c3"><rect width="{w}" height="{h}" rx="20"/></clipPath>
  </defs>
  <style>
    .pill {{ animation: pulse 2.6s ease-in-out infinite; }}
    @keyframes pulse {{ 0%,100% {{ stroke-opacity: .4; }} 50% {{ stroke-opacity: 1; }} }}
  </style>
  <g clip-path="url(#c3)">
    <rect width="{w}" height="{h}" fill="{BG}"/><rect width="{w}" height="{h}" fill="url(#g3)"/><rect width="{w}" height="{h}" fill="url(#cg3)"/>
    <text x="{w / 2}" y="58" text-anchor="middle" font-family="{MONO}" font-size="12" letter-spacing="3.5" fill="{ACCENT_2}">SIGAMOS EN CONTACTO</text>
    <text x="{w / 2}" y="106" text-anchor="middle" font-family="{SANS}" font-size="34" font-weight="700" fill="{TEXT}">Construyamos algo útil</text>
    <text x="{w / 2}" y="138" text-anchor="middle" font-family="{SANS}" font-size="15" fill="{MUTED}">Backend, ingeniería de datos y automatización.</text>
    <rect class="pill" x="{w / 2 - 150}" y="160" width="300" height="42" rx="21" fill="{PANEL}" stroke="{ACCENT_2}" stroke-width="1.5"/>
    <text x="{w / 2}" y="186" text-anchor="middle" font-family="{MONO}" font-size="14" fill="{TEXT}">github.com/{USER}</text>
  </g>
  <rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="20" fill="none" stroke="{BORDER}"/>
</svg>"""


def main() -> None:
    if "--demo" in sys.argv:
        u = demo()
    else:
        try:
            u = fetch()
        except Exception as exc:  # noqa: BLE001
            print(f"GraphQL no disponible ({exc}); uso REST", file=sys.stderr)
            u = fetch_rest()
    repos = [r for r in u["repositories"]["nodes"] if not r["isFork"]]
    cc = u.get("contributionsCollection")
    if cc:
        cur, longest, active = streaks(cc["contributionCalendar"]["weeks"])
        contrib = cc["contributionCalendar"]["totalContributions"]
    else:
        cur = longest = active = contrib = "—"
    stats = {"repos": u["repositories"]["totalCount"], "stars": sum(r["stargazerCount"] for r in repos),
             "contrib": contrib, "followers": u["followers"]["totalCount"],
             "current": cur, "longest": longest, "active": active}
    feat = featured(u)
    write("hero.svg", hero(u, stats))
    write("highlights.svg", highlights())
    write("stack.svg", stack())
    write("projects.svg", constellation(feat))
    write("timeline.svg", timeline(feat))
    write("momentum.svg", momentum(stats))
    write("heatmap.svg", heatmap(u, stats))
    write("contact.svg", contact())
    print("ok")


if __name__ == "__main__":
    main()
