#!/usr/bin/env python3
"""Build the project pages for projects.eviethegremlinn.com.

Source of truth: projects.json (content) + style.css (design tokens).
Output: index.html plus <slug>/index.html, all with relative links, so the folder
works whether it is served at /projects/ or as a subdomain root.

Stdlib only. Run: python3 _build.py
"""

from __future__ import annotations

import html
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
SITE = "https://eviethegremlinn.com"
REPO = "https://github.com/ZaviiNet/evie-site"
BUILT = "2026-09-25"

LABEL = {"shipped": "Shipped", "wip": "In progress"}


def esc(text) -> str:
    return html.escape(str(text), quote=True)


def head(title: str, description: str, depth: int, canonical: str) -> str:
    up = "../" * depth
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<meta name="color-scheme" content="dark">
<link rel="canonical" href="{esc(canonical)}">
<meta name="robots" content="index, follow, noai, noimageai">
<meta name="tdm-reservation" content="1">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{esc(canonical)}">
<meta property="og:type" content="website">
<link rel="icon" type="image/svg+xml" href="{up}favicon.svg">
<link rel="alternate icon" href="{up}favicon.ico">
<link rel="stylesheet" href="{up}style.css">
</head>
<body>
"""


def footer() -> str:
    return f"""<footer>
<p>Built and maintained by <a href="{SITE}">Evie</a> &middot; <a href="{SITE}/ai-policy/">no ai training</a> &middot; <a href="{REPO}">source</a></p>
</footer>
</body>
</html>
"""


def evidence_item(item: str) -> str:
    if " — " in item:
        path, note = item.split(" — ", 1)
        return f"<li><code>{esc(path)}</code><br>{esc(note)}</li>"
    return f"<li>{esc(item)}</li>"


def card(p: dict) -> str:
    tags = "".join(f'<span class="tag">{esc(t)}</span>' for t in p.get("tags", []))
    return f"""<a class="card" href="./{esc(p['slug'])}/">
<div class="card-top"><h3>{esc(p['name'])}</h3><span class="pill {esc(p['status'])}">{LABEL[p['status']]}</span></div>
<p>{esc(p['summary'])}</p>
<div class="tags"><span class="tag when">{esc(p['period'])}</span>{tags}</div>
<span class="go">read the writeup &rarr;</span>
</a>"""


def build_index(data: dict) -> str:
    shipped = [p for p in data["projects"] if p["status"] == "shipped"]
    wip = [p for p in data["projects"] if p["status"] != "shipped"]

    out = [head(f"{data['title']} — Evie", data["lede"], 0, SITE + "/projects/")]
    out.append('<main>\n')
    out.append(
        f"""<header class="page-head">
<a class="back" href="{SITE}">&larr; eviethegremlinn.com</a>
<h1>{esc(data['title'])}</h1>
<p class="lede">{esc(data['lede'])}</p>
</header>
"""
    )
    for key, items in (("shipped", shipped), ("wip", wip)):
        if not items:
            continue
        out.append(f'<section id="{key}">\n<h2>{esc(data["sections"][key])} &mdash; {len(items)}</h2>\n<div class="grid">\n')
        out.append("\n".join(card(p) for p in items))
        out.append("\n</div>\n</section>\n")
    out.append("</main>\n")
    out.append(footer())
    return "".join(out)


def build_project(p: dict, prev_p, next_p) -> str:
    head_tags = "".join(f'<span class="tag">{esc(t)}</span>' for t in p.get("tags", []))
    out = [head(f"{p['name']} — Evie", p["summary"], 1, f"{SITE}/projects/{p['slug']}/")]
    out.append('<main>\n<article class="article">\n')
    out.append(
        f"""<header class="page-head">
<a class="back" href="../">&larr; all projects</a>
<h1>{esc(p['name'])}</h1>
<div class="meta">
<span class="pill {esc(p['status'])}">{LABEL[p['status']]}</span>
<span class="dot">&middot;</span><span>{esc(p['period'])}</span>
<span class="dot">&middot;</span><span>writeup {BUILT}</span>
</div>
<p class="lede">{esc(p['summary'])}</p>
<div class="tags head-tags">{head_tags}</div>
</header>

<div class="prose">
"""
    )

    stats = p.get("stats") or []
    if stats:
        cells = "".join(
            f'<div class="stat"><span class="k">{esc(k)}</span><span class="v">{esc(v)}</span></div>'
            for k, v in stats
        )
        out.append(f'<div class="stats">{cells}</div>\n')

    out.append('<h2><span class="num">01</span>The problem</h2>\n')
    out.extend(f"<p>{esc(par)}</p>\n" for par in p["problem"])

    out.append('<h2><span class="num">02</span>What I built</h2>\n')
    out.extend(f"<p>{esc(par)}</p>\n" for par in p["solution"])

    out.append('<div class="panel"><h3>Evidence</h3><ul>\n')
    out.extend(evidence_item(e) + "\n" for e in p.get("evidence", []))
    out.append("</ul></div>\n")

    if p.get("honest"):
        out.append(f'<div class="panel"><h3>Honest note</h3><p>{esc(p["honest"])}</p></div>\n')

    out.append("</div>\n")

    left = (
        f'<a href="../{esc(prev_p["slug"])}/"><span class="label">Previous</span>&larr; {esc(prev_p["name"])}</a>'
        if prev_p
        else '<a href="../"><span class="label">Index</span>&larr; all projects</a>'
    )
    right = (
        f'<a href="../{esc(next_p["slug"])}/"><span class="label">Next</span>{esc(next_p["name"])} &rarr;</a>'
        if next_p
        else '<span class="spacer"></span>'
    )
    out.append(f'<nav class="next-prev">{left}<span class="spacer"></span>{right}</nav>\n')

    out.append("</article>\n</main>\n")
    out.append(footer())
    return "".join(out)


def verify(root: pathlib.Path) -> list[str]:
    """Every relative href/src in the generated tree must resolve to a real file."""
    problems = []
    attr = re.compile(r'(?:href|src)="([^"]+)"')
    for page in sorted(root.rglob("*.html")):
        text = page.read_text(encoding="utf-8")
        for target in attr.findall(text):
            if target.startswith(("http://", "https://", "mailto:", "#", "data:")):
                continue
            resolved = (page.parent / target).resolve()
            if target.endswith("/"):
                resolved = resolved / "index.html"
            if not resolved.exists():
                problems.append(f"{page.relative_to(root)} -> {target}")
    return problems


def main() -> int:
    data = json.loads((HERE / "projects.json").read_text(encoding="utf-8"))
    projects = data["projects"]

    slugs = [p["slug"] for p in projects]
    if len(slugs) != len(set(slugs)):
        print("FATAL: duplicate slug in projects.json", file=sys.stderr)
        return 1

    (HERE / "index.html").write_text(build_index(data), encoding="utf-8")

    for i, p in enumerate(projects):
        prev_p = projects[i - 1] if i > 0 else None
        next_p = projects[i + 1] if i < len(projects) - 1 else None
        page = HERE / p["slug"] / "index.html"
        page.parent.mkdir(parents=True, exist_ok=True)
        page.write_text(build_project(p, prev_p, next_p), encoding="utf-8")

    problems = verify(HERE)
    shipped = sum(1 for p in projects if p["status"] == "shipped")
    print(f"built {len(projects)} projects ({shipped} shipped / {len(projects) - shipped} in progress) + index")
    if problems:
        print("BROKEN LINKS:")
        for line in problems:
            print("  " + line)
        return 1
    print("all relative links resolve")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
