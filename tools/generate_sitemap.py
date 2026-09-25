#!/usr/bin/env python3
"""Generate sitemap.xml and robots.txt for eviethegremlinn.com from the repo tree.

Every index.html in the repo becomes a URL; lastmod is stamped from the last git
commit that touched the file, so the sitemap reflects real edits rather than the
day it was generated.

    python3 tools/generate_sitemap.py           # write sitemap.xml + robots.txt
    python3 tools/generate_sitemap.py --check    # exit 1 if the files are stale

Stdlib only. Run from anywhere.
"""

from __future__ import annotations

import datetime
import pathlib
import re
import subprocess
import sys
from xml.sax.saxutils import escape

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = "https://eviethegremlinn.com"

# most specific pattern first; first match wins
RULES = [
    (re.compile(r"^index\.html$"), "1.0", "weekly"),
    (re.compile(r"^profile/index\.html$"), "0.7", "monthly"),
    (re.compile(r"^projects/index\.html$"), "0.8", "weekly"),
    (re.compile(r"^projects/[^/]+/index\.html$"), "0.6", "monthly"),
    (re.compile(r"^(dom-inos|gremlin-run)/index\.html$"), "0.6", "yearly"),
]
DEFAULT_RULE = ("0.5", "yearly")

SKIP_DIRS = {".git", ".github", "node_modules", "tools"}


def page_files() -> list[pathlib.Path]:
    found = []
    for path in sorted(ROOT.rglob("*.html")):
        rel = path.relative_to(ROOT)
        if any(part in SKIP_DIRS or part.startswith(".") for part in rel.parts):
            continue
        found.append(path)
    return found


def url_for(path: pathlib.Path) -> str:
    rel = path.relative_to(ROOT).as_posix()
    if rel == "index.html":
        return SITE + "/"
    if rel.endswith("/index.html"):
        return f"{SITE}/{rel[: -len('index.html')]}"
    return f"{SITE}/{rel}"


def rule_for(path: pathlib.Path):
    rel = path.relative_to(ROOT).as_posix()
    for pattern, priority, freq in RULES:
        if pattern.match(rel):
            return priority, freq
    return DEFAULT_RULE


def last_modified(path: pathlib.Path) -> str:
    rel = path.relative_to(ROOT).as_posix()
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%cs", "--", rel],
            cwd=ROOT, capture_output=True, text=True, check=True,
        )
        stamp = out.stdout.strip()
        if stamp:
            return stamp
    except (subprocess.SubprocessError, OSError):
        pass
    return datetime.date.fromtimestamp(path.stat().st_mtime).isoformat()


def build() -> tuple[str, list[tuple[str, str]]]:
    entries = []
    for path in page_files():
        priority, freq = rule_for(path)
        entries.append((url_for(path), last_modified(path), freq, priority))

    # homepage first, then alphabetical — a stable, readable order
    entries.sort(key=lambda e: (e[0] != SITE + "/", e[0]))

    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, lastmod, freq, priority in entries:
        lines.append("  <url>")
        lines.append(f"    <loc>{escape(loc)}</loc>")
        lines.append(f"    <lastmod>{lastmod}</lastmod>")
        lines.append(f"    <changefreq>{freq}</changefreq>")
        lines.append(f"    <priority>{priority}</priority>")
        lines.append("  </url>")
    lines.append("</urlset>")
    sitemap = "\n".join(lines) + "\n"

    robots = (
        "User-agent: *\n"
        "Allow: /\n"
        "\n"
        f"Sitemap: {SITE}/sitemap.xml\n"
    )
    return sitemap, robots  # type: ignore[return-value]


def main(argv: list[str]) -> int:
    sitemap, robots = build()
    sitemap_path = ROOT / "sitemap.xml"
    robots_path = ROOT / "robots.txt"

    if "--check" in argv:
        stale = []
        for path, expected in ((sitemap_path, sitemap), (robots_path, robots)):
            actual = path.read_text(encoding="utf-8") if path.exists() else None
            if actual != expected:
                stale.append(path.name)
        if stale:
            print("STALE: " + ", ".join(stale) + " — run tools/generate_sitemap.py")
            return 1
        print("sitemap.xml and robots.txt are up to date")
        return 0

    sitemap_path.write_text(sitemap, encoding="utf-8")
    robots_path.write_text(robots, encoding="utf-8")

    count = sitemap.count("<url>")
    print(f"wrote sitemap.xml ({count} urls) and robots.txt")
    for line in sitemap.splitlines():
        if "<loc>" in line:
            print("  " + line.strip().removeprefix("<loc>").removesuffix("</loc>"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
