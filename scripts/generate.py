"""Genera los SVG del perfil de GitHub (paleta azul marino + negro).

Uso:
    GITHUB_TOKEN=... python scripts/generate.py            # datos reales vía GraphQL
    python scripts/generate.py --demo                      # datos de ejemplo, sin red

Salida: assets/*.svg
"""
from __future__ import annotations

import datetime as dt
import json
import os
import sys
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

USER = os.environ.get("PROFILE_USER", "GonzalezLazaro")
OUT = Path(__file__).resolve().parent.parent / "assets"

# ---------- Paleta ----------
BG = "#05070d"          # negro
PANEL = "#0a1224"       # negro azulado
NAVY = "#0b1f44"        # azul marino
NAVY_2 = "#12306b"
BORDER = "#1a2f5a"
ACCENT = "#3b82f6"
ACCENT_2 = "#60a5fa"
SOFT = "#93c5fd"
TEXT = "#e6edf7"
MUTED = "#8ba3c7"
DIM = "#4b6a9b"
BLUES = ["#60a5fa", "#3b82f6", "#2563eb", "#1d4ed8", "#1e3a8a", "#93c5fd"]

SANS = "'Segoe UI', Ubuntu, 'Helvetica Neue', Arial, sans-serif"
MONO = "'JetBrains Mono', 'Cascadia Code', Consolas, 'SFMono-Regular', Menlo, monospace"

# Descripciones propias para las tarjetas (se usan si el repo no tiene descripción)
DESCRIPTIONS = {
    "Encuestas-Sistemas": "Sistema de encuestas para equipos internos.",
    "api-enlaces": "API de gestión de enlaces con interfaz web.",
    "api": "API REST en Python.",
    "Widget": "Widget web embebible.",
}

# Repos destacados (el README enlaza assets/project-<nombre>.svg)
FEATURED = ["Encuestas-Sistemas", "api-enlaces", "api", "Widget"]

MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


def e(s: str) -> str:
    return escape(str(s), {'"': "&quot;"})


def write(name: str, svg: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(svg.strip() + "\n", encoding="utf-8")


def grid_defs(pid: str, size: int = 32) -> str:
    return (
        f'<pattern id="{pid}" width="{size}" height="{size}" patternUnits="userSpaceOnUse">'
        f'<path d="M {size} 0 L 0 0 0 {size}" fill="none" stroke="{NAVY}" stroke-width="1" opacity="0.55"/>'
        "</pattern>"
    )


# ---------- Datos ----------
QUERY = """
query($login: String!) {
  user(login: $login) {
    followers { totalCount }
    repositories(ownerAffiliations: OWNER, privacy: PUBLIC, first: 100, orderBy: {field: PUSHED_AT, direction: DESC}) {
      totalCount
      nodes {
        name description url isFork pushedAt stargazerCount
        primaryLanguage { name }
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name } } }
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


def fetch() -> dict:
    token = os.environ["GITHUB_TOKEN"]
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        payload = json.load(r)
    if "errors" in payload:
        raise RuntimeError(f"GraphQL error: {payload['errors']}")
    return payload["data"]["user"]


def _get(url: str):
    headers = {"Accept": "application/vnd.github+json"}
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"bearer {os.environ['GITHUB_TOKEN']}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as r:
        return json.load(r)


def fetch_rest() -> dict:
    """Respaldo sin GraphQL: repos y lenguajes vía REST, sin calendario de contribuciones."""
    api = "https://api.github.com"
    user = _get(f"{api}/users/{USER}")
    repos = _get(f"{api}/users/{USER}/repos?per_page=100&sort=pushed")
    nodes = []
    for r in repos:
        langs = _get(r["languages_url"])
        nodes.append({
            "name": r["name"], "description": r["description"], "url": r["html_url"], "isFork": r["fork"],
            "pushedAt": r["pushed_at"], "stargazerCount": r["stargazers_count"],
            "primaryLanguage": {"name": r["language"]} if r["language"] else None,
            "languages": {"edges": [{"size": v, "node": {"name": k}} for k, v in langs.items()]},
        })
    return {"followers": {"totalCount": user["followers"]},
            "repositories": {"totalCount": user["public_repos"], "nodes": nodes},
            "contributionsCollection": None}


def demo() -> dict:
    today = dt.date.today()
    days = []
    for i in range(364, -1, -1):
        d = today - dt.timedelta(days=i)
        days.append({"date": d.isoformat(), "contributionCount": (3 if i % 5 == 0 else 0) if i < 120 else 0})
    weeks = [{"contributionDays": days[i:i + 7]} for i in range(0, len(days), 7)]
    repos = [
        ("Widget", "HTML", "2026-10-13T18:26:28Z", [("HTML", 9000), ("JavaScript", 3000)]),
        ("Encuestas-Sistemas", "Python", "2026-02-04T19:04:29Z", [("Python", 20000), ("HTML", 4000)]),
        ("api", "Python", "2025-06-26T19:31:01Z", [("Python", 8000)]),
        ("api-enlaces", "HTML", "2025-06-25T18:39:07Z", [("HTML", 6000), ("Mako", 500)]),
    ]
    return {
        "followers": {"totalCount": 1},
        "repositories": {
            "totalCount": 5,
            "nodes": [
                {
                    "name": n, "description": None, "url": f"https://github.com/{USER}/{n}", "isFork": False,
                    "pushedAt": p, "stargazerCount": 0, "primaryLanguage": {"name": l},
                    "languages": {"edges": [{"size": s, "node": {"name": ln}} for ln, s in langs]},
                }
                for n, l, p, langs in repos
            ],
        },
        "contributionsCollection": {"contributionCalendar": {"totalContributions": 82, "weeks": weeks}},
    }


def streaks(weeks: list) -> tuple[int, int]:
    days = [d for w in weeks for d in w["contributionDays"]]
    days.sort(key=lambda d: d["date"])
    longest = run = 0
    for d in days:
        run = run + 1 if d["contributionCount"] > 0 else 0
        longest = max(longest, run)
    current = 0
    for i, d in enumerate(reversed(days)):
        if d["contributionCount"] > 0:
            current += 1
        elif i == 0:
            continue  # hoy todavía sin contribuciones no corta la racha
        else:
            break
    return current, longest


# ---------- SVGs estáticos ----------
def header() -> str:
    roles = ["Senior Systems Analyst", "Backend &amp; Data Engineer", "Tech Lead · Python · SQL Server · Azure"]
    role_nodes = "".join(
        f'<text class="role r{i}" x="72" y="268" font-family="{MONO}" font-size="22" fill="{ACCENT_2}">'
        f'<tspan fill="{DIM}">$ </tspan>{r}</text>'
        for i, r in enumerate(roles)
    )
    nodes = [(900, 120), (1010, 90), (1090, 170), (985, 230), (880, 280), (1060, 300), (950, 165)]
    links = [(0, 1), (1, 2), (2, 3), (3, 4), (3, 5), (0, 6), (6, 3), (6, 2), (4, 6)]
    link_svg = "".join(
        f'<line x1="{nodes[a][0]}" y1="{nodes[a][1]}" x2="{nodes[b][0]}" y2="{nodes[b][1]}" class="link" style="animation-delay:{i * 0.35:.2f}s"/>'
        for i, (a, b) in enumerate(links)
    )
    node_svg = "".join(
        f'<circle cx="{x}" cy="{y}" r="5" class="node" style="animation-delay:{i * 0.4:.1f}s"/>'
        f'<circle cx="{x}" cy="{y}" r="2" fill="{TEXT}"/>'
        for i, (x, y) in enumerate(nodes)
    )
    return f"""
<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="380" viewBox="0 0 1200 380" role="img" aria-label="Lazaro Gonzalez — Senior Systems Analyst">
  <defs>
    {grid_defs("g")}
    <radialGradient id="glow" cx="0.78" cy="0.45" r="0.55">
      <stop offset="0" stop-color="{NAVY_2}" stop-opacity="0.85"/>
      <stop offset="0.55" stop-color="{NAVY}" stop-opacity="0.35"/>
      <stop offset="1" stop-color="{BG}" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="fade" x1="0" x2="1">
      <stop offset="0" stop-color="{BG}" stop-opacity="1"/>
      <stop offset="0.45" stop-color="{BG}" stop-opacity="0.6"/>
      <stop offset="1" stop-color="{BG}" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="scan" x1="0" x2="1">
      <stop offset="0" stop-color="{ACCENT}" stop-opacity="0"/>
      <stop offset="0.5" stop-color="{ACCENT}" stop-opacity="0.35"/>
      <stop offset="1" stop-color="{ACCENT}" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="name" x1="0" x2="1">
      <stop offset="0" stop-color="{TEXT}"/>
      <stop offset="1" stop-color="{SOFT}"/>
    </linearGradient>
    <clipPath id="clip"><rect width="1200" height="380" rx="18"/></clipPath>
  </defs>
  <style>
    .link {{ stroke: {ACCENT}; stroke-width: 1.4; stroke-dasharray: 6 8; opacity: .55; animation: dash 6s linear infinite; }}
    .node {{ fill: {ACCENT}; opacity: .25; animation: pulse 3s ease-in-out infinite; transform-box: fill-box; transform-origin: center; }}
    .ring {{ fill: none; stroke: {NAVY_2}; stroke-width: 1.2; transform-origin: 985px 190px; }}
    .ring.a {{ stroke-dasharray: 4 10; animation: spin 40s linear infinite; }}
    .ring.b {{ stroke-dasharray: 60 30; stroke: {ACCENT}; opacity: .35; animation: spin 25s linear infinite reverse; }}
    .scan {{ animation: scan 7s ease-in-out infinite; }}
    .role {{ opacity: 0; animation: roles 12s infinite; }}
    .r1 {{ animation-delay: 4s; }} .r2 {{ animation-delay: 8s; }}
    .cursor {{ animation: blink 1s steps(1) infinite; }}
    .dot {{ animation: blink 2s ease-in-out infinite; }}
    @keyframes dash {{ to {{ stroke-dashoffset: -140; }} }}
    @keyframes pulse {{ 0%,100% {{ opacity: .15; transform: scale(1); }} 50% {{ opacity: .6; transform: scale(2.2); }} }}
    @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
    @keyframes scan {{ 0% {{ transform: translateX(-400px); }} 100% {{ transform: translateX(1300px); }} }}
    @keyframes roles {{ 0% {{ opacity: 0; }} 4%,30% {{ opacity: 1; }} 34%,100% {{ opacity: 0; }} }}
    @keyframes blink {{ 50% {{ opacity: 0; }} }}
  </style>
  <g clip-path="url(#clip)">
    <rect width="1200" height="380" fill="{BG}"/>
    <rect width="1200" height="380" fill="url(#g)"/>
    <rect width="1200" height="380" fill="url(#glow)"/>
    <rect width="1200" height="380" fill="url(#fade)"/>
    <circle class="ring a" cx="985" cy="190" r="150"/>
    <circle class="ring b" cx="985" cy="190" r="118"/>
    <circle class="ring a" cx="985" cy="190" r="84"/>
    {link_svg}
    {node_svg}
    <rect class="scan" x="0" y="0" width="260" height="380" fill="url(#scan)" opacity=".35"/>

    <text x="72" y="98" font-family="{MONO}" font-size="16" letter-spacing="4" fill="{ACCENT_2}">HOLA, MUNDO. SOY</text>
    <text x="68" y="182" font-family="{SANS}" font-size="76" font-weight="700" fill="url(#name)" letter-spacing="-1">Lazaro Gonzalez</text>
    <rect x="72" y="208" width="120" height="3" rx="1.5" fill="{ACCENT}"/>
    {role_nodes}
    <rect class="cursor" x="72" y="286" width="12" height="3" fill="{ACCENT_2}"/>

    <circle class="dot" cx="80" cy="330" r="5" fill="#22c55e"/>
    <text x="94" y="335" font-family="{MONO}" font-size="14" fill="{MUTED}">Córdoba, Argentina  ·  abierto a colaborar</text>
    <rect x="0.5" y="0.5" width="1199" height="379" rx="18" fill="none" stroke="{BORDER}"/>
  </g>
</svg>"""


def terminal() -> str:
    K, S, N, C, P = ACCENT_2, SOFT, TEXT, DIM, MUTED  # keyword, string, name, comment, punct
    lines = [
        [(C, "# lazaro.py")],
        [(K, "class "), (N, "Lazaro"), (P, ":")],
        [(N, "    role     "), (P, "= "), (S, '"Senior Systems Analyst"')],
        [(N, "    team     "), (P, "= "), (S, '"Tech lead · 6 devs · Scrum"')],
        [(N, "    industry "), (P, "= "), (S, '"Medicina prepaga"')],
        [(N, "    stack    "), (P, "= {")],
        [(S, '        "backend"'), (P, ": ["), (S, '"Python"'), (P, ", "), (S, '"Django"'), (P, ", "), (S, '"FastAPI"'), (P, ", "), (S, '"Flask"'), (P, "],")],
        [(S, '        "data"   '), (P, ": ["), (S, '"SQL Server"'), (P, ", "), (S, '"PostgreSQL"'), (P, ", "), (S, '"MySQL"'), (P, ", "), (S, '"Airflow"'), (P, "],")],
        [(S, '        "cloud"  '), (P, ": ["), (S, '"Azure"'), (P, ", "), (S, '"Docker"'), (P, ", "), (S, '"Azure DevOps"'), (P, "],")],
        [(P, "    }")],
        [(N, "    focus    "), (P, "= ["), (S, '"APIs"'), (P, ", "), (S, '"ETL"'), (P, ", "), (S, '"calidad de datos"'), (P, ", "), (S, '"integraciones"'), (P, "]")],
        [],
        [(K, "    def "), (N, "motto"), (P, "(self) -> "), (K, "str"), (P, ":")],
        [(K, "        return "), (S, '"Automatizar lo repetitivo, cuidar los datos."')],
    ]
    y0, lh = 92, 27
    out = []
    for i, segs in enumerate(lines):
        y = y0 + i * lh
        out.append(f'<text x="40" y="{y}" font-family="{MONO}" font-size="15" fill="{DIM}" text-anchor="end" opacity=".6">{i + 1}</text>')
        if segs:
            spans = "".join(f'<tspan fill="{c}">{e(t)}</tspan>' for c, t in segs)
            out.append(
                f'<text class="ln" style="animation-delay:{0.12 * i:.2f}s" x="62" y="{y}" font-family="{MONO}" font-size="15" xml:space="preserve">{spans}</text>'
            )
    h = y0 + len(lines) * lh + 18
    cy = y0 + (len(lines) - 1) * lh - 13
    return f"""
<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="{h}" viewBox="0 0 1200 {h}" role="img" aria-label="Sobre mí en código Python">
  <defs>{grid_defs("tg", 24)}
    <linearGradient id="bar" x1="0" x2="1"><stop offset="0" stop-color="{NAVY}"/><stop offset="1" stop-color="{PANEL}"/></linearGradient>
  </defs>
  <style>
    .ln {{ opacity: 0; animation: in .5s ease-out forwards; }}
    .cur {{ animation: blink 1s steps(1) infinite; }}
    @keyframes in {{ from {{ opacity: 0; transform: translateX(-6px); }} to {{ opacity: 1; transform: none; }} }}
    @keyframes blink {{ 50% {{ opacity: 0; }} }}
  </style>
  <rect width="1200" height="{h}" rx="16" fill="{BG}"/>
  <rect width="1200" height="{h}" rx="16" fill="url(#tg)" opacity=".35"/>
  <path d="M16 0 H1184 A16 16 0 0 1 1200 16 V48 H0 V16 A16 16 0 0 1 16 0 Z" fill="url(#bar)"/>
  <circle cx="30" cy="24" r="6" fill="#1e3a8a"/><circle cx="52" cy="24" r="6" fill="#2563eb"/><circle cx="74" cy="24" r="6" fill="#60a5fa"/>
  <text x="600" y="29" text-anchor="middle" font-family="{MONO}" font-size="13" fill="{MUTED}">~/perfil/lazaro.py — python</text>
  <line x1="0" y1="48" x2="1200" y2="48" stroke="{BORDER}"/>
  {''.join(out)}
  <rect class="cur" x="728" y="{cy}" width="9" height="17" fill="{ACCENT_2}"/>
  <rect x="0.5" y="0.5" width="1199" height="{h - 1}" rx="16" fill="none" stroke="{BORDER}"/>
</svg>"""


def section(slug: str, num: str, title: str) -> None:
    write(f"title-{slug}.svg", f"""
<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="70" viewBox="0 0 1200 70" role="img" aria-label="{e(title)}">
  <defs>
    <linearGradient id="l" x1="0" x2="1"><stop offset="0" stop-color="{ACCENT}"/><stop offset="1" stop-color="{ACCENT}" stop-opacity="0"/></linearGradient>
  </defs>
  <style>
    .sweep {{ animation: sweep 4s ease-in-out infinite; }}
    @keyframes sweep {{ 0% {{ transform: translateX(-200px); opacity: 0; }} 30% {{ opacity: 1; }} 100% {{ transform: translateX(1000px); opacity: 0; }} }}
  </style>
  <text x="4" y="40" font-family="{MONO}" font-size="15" fill="{ACCENT_2}" letter-spacing="2">{num} /</text>
  <text x="64" y="42" font-family="{SANS}" font-size="28" font-weight="700" fill="{TEXT}">{e(title)}</text>
  <line x1="4" y1="60" x2="1196" y2="60" stroke="{BORDER}"/>
  <line x1="4" y1="60" x2="420" y2="60" stroke="url(#l)" stroke-width="2"/>
  <rect class="sweep" x="0" y="59" width="160" height="2" fill="{SOFT}" opacity=".8"/>
</svg>""")


# ---------- SVGs con datos ----------
def stats_card(u: dict) -> str:
    cc = u.get("contributionsCollection")
    if cc:
        cal = cc["contributionCalendar"]
        cur, longest = streaks(cal["weeks"])
        total = str(cal["totalContributions"])
    else:
        cur = longest = total = "—"
    repos = [r for r in u["repositories"]["nodes"] if not r["isFork"]]
    stars = sum(r["stargazerCount"] for r in repos)
    items = [
        (total, "contribuciones", "último año"),
        (str(cur), "racha actual", "días"),
        (str(longest), "racha máxima", "días"),
        (str(u["repositories"]["totalCount"]), "repos públicos", f"{stars} ★"),
    ]
    w, h = 1200, 190
    col = (w - 48) / 4
    cells = []
    for i, (val, label, sub) in enumerate(items):
        x = 24 + i * col
        cells.append(f"""
    <g class="cell" style="animation-delay:{i * 0.15:.2f}s">
      <rect x="{x + 8}" y="24" width="{col - 16}" height="{h - 48}" rx="12" fill="{PANEL}" stroke="{BORDER}"/>
      <rect x="{x + 8}" y="24" width="4" height="{h - 48}" rx="2" fill="{BLUES[i]}"/>
      <text x="{x + 34}" y="64" font-family="{MONO}" font-size="13" fill="{MUTED}" letter-spacing="1.5">{e(label.upper())}</text>
      <text x="{x + 32}" y="122" font-family="{SANS}" font-size="46" font-weight="700" fill="{TEXT}">{e(val)}</text>
      <text x="{x + 34}" y="148" font-family="{MONO}" font-size="13" fill="{DIM}">{e(sub)}</text>
    </g>""")
    return f"""
<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Estadísticas de GitHub">
  <style>
    .cell {{ opacity: 0; animation: up .6s ease-out forwards; }}
    @keyframes up {{ from {{ opacity: 0; transform: translateY(8px); }} to {{ opacity: 1; transform: none; }} }}
  </style>
  <rect width="{w}" height="{h}" rx="16" fill="{BG}" stroke="{BORDER}"/>
  {''.join(cells)}
</svg>"""


def languages_card(u: dict) -> str:
    totals: dict[str, int] = {}
    for r in u["repositories"]["nodes"]:
        if r["isFork"] or r["name"] == USER:
            continue
        for edge in r["languages"]["edges"]:
            totals[edge["node"]["name"]] = totals.get(edge["node"]["name"], 0) + edge["size"]
    top = sorted(totals.items(), key=lambda kv: -kv[1])[:5]
    total = sum(v for _, v in top) or 1
    w, h = 1200, 150
    bar_x, bar_w = 32, w - 64
    segs, legend, x = [], [], bar_x
    for i, (name, size) in enumerate(top):
        sw = bar_w * size / total
        segs.append(f'<rect x="{x:.1f}" y="58" width="{max(sw - 3, 2):.1f}" height="14" fill="{BLUES[i]}"/>')
        x += sw
        lx = 32 + i * 230
        legend.append(
            f'<circle cx="{lx + 6}" cy="108" r="6" fill="{BLUES[i]}"/>'
            f'<text x="{lx + 20}" y="113" font-family="{SANS}" font-size="15" fill="{TEXT}">{e(name)}</text>'
            f'<text x="{lx + 20 + 9 * len(name) + 10}" y="113" font-family="{MONO}" font-size="13" fill="{MUTED}">{100 * size / total:.1f}%</text>'
        )
    return f"""
<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Lenguajes más usados">
  <defs><clipPath id="b"><rect x="{bar_x}" y="58" width="{bar_w}" height="14" rx="7"/></clipPath></defs>
  <style>
    .grow {{ transform-origin: {bar_x}px 0; animation: grow 1.2s cubic-bezier(.2,.8,.2,1) forwards; transform: scaleX(0); }}
    @keyframes grow {{ to {{ transform: scaleX(1); }} }}
  </style>
  <rect width="{w}" height="{h}" rx="16" fill="{BG}" stroke="{BORDER}"/>
  <text x="32" y="38" font-family="{MONO}" font-size="13" fill="{MUTED}" letter-spacing="1.5">LENGUAJES EN REPOS PÚBLICOS</text>
  <rect x="{bar_x}" y="58" width="{bar_w}" height="14" rx="7" fill="{PANEL}"/>
  <g clip-path="url(#b)"><g class="grow">{''.join(segs)}</g></g>
  {''.join(legend)}
</svg>"""


def project_cards(u: dict) -> list[str]:
    names = []
    by_name = {r["name"]: r for r in u["repositories"]["nodes"]}
    repos = [by_name[n] for n in FEATURED if n in by_name]
    for i, r in enumerate(repos):
        desc = r["description"] or DESCRIPTIONS.get(r["name"], "Proyecto en desarrollo.")
        if len(desc) > 58:
            desc = desc[:55].rstrip() + "…"
        lang = (r["primaryLanguage"] or {}).get("name", "—")
        d = dt.datetime.fromisoformat(r["pushedAt"].replace("Z", "+00:00"))
        upd = f"actualizado {MESES[d.month - 1]} {d.year}"
        svg = f"""
<svg xmlns="http://www.w3.org/2000/svg" width="590" height="170" viewBox="0 0 590 170" role="img" aria-label="{e(r['name'])}">
  <defs>
    <linearGradient id="h" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{NAVY}"/><stop offset="1" stop-color="{BG}"/></linearGradient>
  </defs>
  <style>
    .edge {{ stroke-dasharray: 120 1400; animation: run 6s linear infinite; animation-delay: {i * 1.2:.1f}s; }}
    @keyframes run {{ to {{ stroke-dashoffset: -1520; }} }}
  </style>
  <rect width="590" height="170" rx="14" fill="url(#h)"/>
  <rect x="0.5" y="0.5" width="589" height="169" rx="14" fill="none" stroke="{BORDER}"/>
  <rect class="edge" x="0.5" y="0.5" width="589" height="169" rx="14" fill="none" stroke="{ACCENT_2}" stroke-width="1.5"/>
  <g transform="translate(28 34)" fill="none" stroke="{ACCENT_2}" stroke-width="1.6">
    <path d="M2 2h12l4 4v14H2z"/><path d="M6 10h8M6 14h6"/>
  </g>
  <text x="60" y="52" font-family="{SANS}" font-size="22" font-weight="700" fill="{TEXT}">{e(r['name'])}</text>
  <text x="28" y="94" font-family="{SANS}" font-size="15" fill="{MUTED}">{e(desc)}</text>
  <circle cx="34" cy="136" r="6" fill="{ACCENT}"/>
  <text x="48" y="141" font-family="{MONO}" font-size="13" fill="{TEXT}">{e(lang)}</text>
  <text x="140" y="141" font-family="{MONO}" font-size="13" fill="{DIM}">★ {r['stargazerCount']}</text>
  <text x="562" y="141" text-anchor="end" font-family="{MONO}" font-size="13" fill="{DIM}">{upd}</text>
</svg>"""
        write(f"project-{r['name']}.svg", svg)
        names.append(r["name"])
    return names


def main() -> None:
    if "--demo" in sys.argv:
        u = demo()
    else:
        try:
            u = fetch()
        except Exception as exc:  # noqa: BLE001
            print(f"GraphQL no disponible ({exc}); uso REST", file=sys.stderr)
            u = fetch_rest()
    write("header.svg", header())
    write("about.svg", terminal())
    for slug, num, title in [("sobre-mi", "01", "Sobre mí"), ("stack", "02", "Stack"),
                             ("proyectos", "03", "Proyectos"), ("actividad", "04", "Actividad")]:
        section(slug, num, title)
    write("stats.svg", stats_card(u))
    write("languages.svg", languages_card(u))
    names = project_cards(u)
    print("ok:", ", ".join(names))


if __name__ == "__main__":
    main()
