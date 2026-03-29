#!/usr/bin/env python3
"""Build static HTML under ../www/ from data/manifest.json and templates/."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "manifest.json"
TEMPLATES = ROOT / "templates"
OUT = ROOT / "www"


def esc(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def merge_defaults(defaults: dict, project: dict) -> dict:
    out = {**defaults, **project}
    return out


def status_label(status: str) -> str:
    s = (status or "placeholder").lower()
    if s == "live":
        return "● Live"
    if s in ("dev", "development"):
        return "● In development"
    if s in ("soon", "coming-soon", "coming_soon"):
        return "● Soon"
    return "● TBD"


def card_muted_classes(status: str) -> str:
    s = (status or "placeholder").lower()
    if s == "live":
        return ""
    if s in ("dev", "development"):
        return ""
    return "dim-status coming-soon"


def card_html(p: dict, base: str) -> str:
    accent = p.get("accent") or "teal"
    accent_cls = "amber-accent" if accent == "amber" else "teal-accent"
    stat_txt = status_label(p.get("status", ""))
    extra = card_muted_classes(p.get("status", ""))
    href = p.get("listing_href") or f"{base}/{p['id']}/"
    inner = f"""
      <div class="card-accent"></div>
      <div class="card-status">{stat_txt}</div>
      <div class="card-title">{p['short_title_html']}</div>
      <div class="card-genre">{esc(p.get('genre', ''))}</div>
      <div class="card-desc">{p['description_html']}</div>
      <div class="card-arrow">↗</div>
    """
    classes = f"game-card {accent_cls} {extra}".strip()
    return f'<a href="{esc(href)}" class="{classes}">{inner}</a>'


def btn_accent(p: dict) -> str:
    accent = p.get("accent") or "teal"
    return "btn-primary amber" if accent == "amber" else "btn-primary teal"


def play_parts(p: dict) -> tuple[str, str]:
    url = (p.get("play_url") or "").strip()
    primary = btn_accent(p)
    if url:
        return f'<a class="btn {primary}" href="{esc(url)}">Play in browser</a>', ""
    msg = esc(p.get("play_unavailable_message") or "")
    return (
        f'<span class="btn {primary}" aria-disabled="true">Play in browser</span>',
        f'<p class="desc">{msg}</p>' if msg else "",
    )


def dynamicgo_downloads_index_html(site: dict) -> str:
    """Static download picker for Raylib zips deployed under /downloads/dynamicgo/."""
    title = f"Dynamic GO — desktop — {site['title']}"
    rows = [
        ("DynamicGO-darwin-arm64.zip", "macOS · Apple Silicon"),
        ("DynamicGO-darwin-x86_64.zip", "macOS · Intel"),
        ("DynamicGO-linux-aarch64.zip", "Linux · arm64 / aarch64"),
        ("DynamicGO-linux-arm64.zip", "Linux · arm64"),
        ("DynamicGO-linux-x86_64.zip", "Linux · x86_64"),
    ]
    base = "/downloads/dynamicgo/"
    links = "\n      ".join(
        f'<li><a href="{esc(base + name)}" download>{esc(label)}</a> — <code>{esc(name)}</code></li>'
        for name, label in rows
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{esc(title)}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Syne+Mono&family=Bebas+Neue&family=DM+Mono:ital,wght@0,300;0,400;1,300&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/assets/portal.css">
</head>
<body>
  <div class="glow-amber"></div>
  <div class="glow-teal"></div>
  <div class="wrap project-page">
    <div class="back-row"><a href="/games/dynamicgo/">← Dynamic GO</a></div>
    <header class="project-hero">
      <div class="header-label">Desktop</div>
      <div class="card-title">Dynamic<br>GO</div>
      <div class="card-genre">Raylib · macOS &amp; Linux</div>
    </header>
    <section class="project-body">
      <div class="desc">
        Unzip the archive for your platform, open a terminal in that folder, run
        <code>./DynamicGO</code>. On macOS you may need to allow the binary under
        System Settings → Privacy &amp; Security. CI may only publish some of the
        files below — 404 means that build was not uploaded for this release.
      </div>
      <ul class="download-list" style="margin-top:24px;padding-left:1.25rem;line-height:2;">
        {links}
      </ul>
    </section>
    <footer>
      <div>{esc(site["footer_left"])}</div>
      <div>{esc(site["footer_right"])}</div>
    </footer>
  </div>
</body>
</html>
"""


def desktop_parts(p: dict) -> tuple[str, str]:
    url = (p.get("desktop_download_url") or "").strip()
    label = esc(p.get("desktop_download_label") or "Download desktop app")
    primary = btn_accent(p)
    if url:
        return f'<a class="btn {primary}" href="{esc(url)}" rel="noopener">{label}</a>', ""
    msg = esc(
        p.get("desktop_unavailable_message")
        or "Desktop build not published yet."
    )
    return (
        f'<span class="btn {primary}" aria-disabled="true">{label}</span>',
        f'<p class="desc">{msg}</p>' if msg else "",
    )


def project_page_html(site: dict, p: dict) -> str:
    stat_txt = status_label(p.get("status", ""))
    play_a, play_n = play_parts(p)
    desk_a, desk_n = desktop_parts(p)
    repo = (p.get("repo_url") or "").strip()
    repo_line = (
        f'<div class="meta-grid"><dt>Source</dt><dd><a href="{esc(repo)}">{esc(repo)}</a></dd></div>'
        if repo
        else ""
    )
    ws = esc(p.get("workspace_path", ""))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{esc(p["title"])} — {esc(site["title"])}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Syne+Mono&family=Bebas+Neue&family=DM+Mono:ital,wght@0,300;0,400;1,300&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/assets/portal.css">
</head>
<body>
  <div class="glow-amber"></div>
  <div class="glow-teal"></div>
  <div class="wrap project-page">
    <div class="back-row"><a href="/">← {esc(site["title"])}</a></div>
    <header class="project-hero">
      <div class="header-label">{esc(stat_txt)}</div>
      <div class="card-title">{p["short_title_html"]}</div>
      <div class="card-genre">{esc(p.get("genre", ""))}</div>
    </header>
    <section class="project-body">
      <div class="desc">{p["description_html"]}</div>
      <div class="actions">
        {play_a}
        {desk_a}
      </div>
      {play_n}
      {desk_n}
      <div class="note-box">
        <strong>Workspace path</strong><br>
        {ws}
      </div>
      {repo_line}
    </section>
    <footer>
      <div>{esc(site["footer_left"])}</div>
      <div>{esc(site["footer_right"])}</div>
    </footer>
  </div>
</body>
</html>
"""


def index_html(site: dict, games_cards: str, apps_cards: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{esc(site["title"])}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Syne+Mono&family=Bebas+Neue&family=DM+Mono:ital,wght@0,300;0,400;1,300&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/assets/portal.css">
</head>
<body>
  <div class="glow-amber"></div>
  <div class="glow-teal"></div>
  <div class="wrap">
    <header>
      <div class="header-label">{esc(site["header_label"])}</div>
      <div class="wordmark">Game<span class="seed">Seeds</span></div>
      <div class="tagline">{esc(site["tagline"])}</div>
    </header>
    <div class="section-label">Games</div>
    <div class="games-grid">
      {games_cards}
    </div>
    <div class="section-label">Apps</div>
    <div class="games-grid">
      {apps_cards}
    </div>
    <footer>
      <div>{esc(site["footer_left"])}</div>
      <div>{esc(site["footer_right"])}</div>
    </footer>
  </div>
</body>
</html>
"""


def main() -> int:
    if not DATA.is_file():
        print(f"generate_site: missing {DATA}", file=sys.stderr)
        return 1
    raw = json.loads(DATA.read_text(encoding="utf-8"))
    site = raw["site"]
    defaults = raw.get("defaults", {})
    projects = [merge_defaults(defaults, p) for p in raw["projects"]]

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "assets").mkdir(parents=True, exist_ok=True)
    css_src = TEMPLATES / "assets" / "portal.css"
    if css_src.is_file():
        shutil.copy2(css_src, OUT / "assets" / "portal.css")

    games = [p for p in projects if p.get("type") == "game"]
    apps = [p for p in projects if p.get("type") == "app"]

    games_cards = "\n      ".join(card_html(p, "/games") for p in games)
    apps_cards = "\n      ".join(card_html(p, "/apps") for p in apps)
    (OUT / "index.html").write_text(
        index_html(site, games_cards, apps_cards), encoding="utf-8"
    )

    for p in games:
        d = OUT / "games" / p["id"]
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(
            project_page_html(site, p), encoding="utf-8"
        )
    for p in apps:
        d = OUT / "apps" / p["id"]
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(
            project_page_html(site, p), encoding="utf-8"
        )

    dl = OUT / "downloads" / "dynamicgo"
    dl.mkdir(parents=True, exist_ok=True)
    (dl / "index.html").write_text(
        dynamicgo_downloads_index_html(site), encoding="utf-8"
    )

    print(f"Wrote {OUT} ({len(games)} games, {len(apps)} apps).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
