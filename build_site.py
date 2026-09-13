"""Render catalog.json into the static file tree the Stremio protocol expects."""

import html
import json
import os
import shutil
import sys
from pathlib import Path

CATALOG_FILE = Path("catalog.json")
OUTPUT_DIR = Path("dist")
BASE_URL = os.environ.get(
    "ADDON_BASE_URL", "https://tanjiakai.github.io/netflix-top-lists"
)

MANIFEST = {
    # Stremio keys installs off this id, so it stays put through renames -
    # changing it would read as a different add-on and force a reinstall.
    "id": "org.stremio.netflix_top_lists",
    "version": "2.1.0",
    "name": "Top Lists",
    "description": (
        "Netflix's official Top 10 in Malaysia, plus horror picks from Shudder."
    ),
    "types": ["movie", "series"],
    "catalogs": [
        {
            "type": "movie",
            "id": "malaysia_movies",
            "name": "Netflix: Top 10 Movies in Malaysia",
        },
        {
            "type": "series",
            "id": "malaysia_tv",
            "name": "Netflix: Top 10 TV in Malaysia",
        },
        {
            "type": "movie",
            "id": "shudder_horror_popular_movies",
            "name": "Shudder: Popular Horror Movies",
        },
        {
            "type": "series",
            "id": "shudder_horror_popular_series",
            "name": "Shudder: Popular Horror Series",
        },
        {
            "type": "movie",
            "id": "shudder_horror_new_movies",
            "name": "Shudder: New Horror Movies",
        },
        {
            "type": "series",
            "id": "shudder_horror_new_series",
            "name": "Shudder: New Horror Series",
        },
    ],
    "resources": ["catalog", "meta"],
    # JustWatch supplies an IMDb ID for most but not every title; the tm/ts prefixes
    # are JustWatch's own ids, used as a fallback so those entries still resolve.
    "idPrefixes": ["tt", "tm", "ts"],
}

CATALOG_TYPES = {catalog["id"]: catalog["type"] for catalog in MANIFEST["catalogs"]}
CATALOG_NAMES = {catalog["id"]: catalog["name"] for catalog in MANIFEST["catalogs"]}


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def wrap(title: str, width: int = 14) -> list[str]:
    lines, current = [], ""
    for word in title.split():
        candidate = f"{current} {word}".strip()
        if len(candidate) > width and current:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines[:5]


def placeholder_svg(title: str) -> str:
    """A 2:3 poster for titles no source has artwork for.

    Netflix's own chart art is landscape only, so it cannot fill a poster slot;
    a generated tile keeps the row visually consistent instead of leaving a gap.
    """
    lines = wrap(title)
    start = 225 - (len(lines) - 1) * 16
    spans = "".join(
        f'<tspan x="150" y="{start + i * 32}">{html.escape(line)}</tspan>'
        for i, line in enumerate(lines)
    )
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="300" height="450" '
        'viewBox="0 0 300 450">'
        '<rect width="300" height="450" fill="#1b1b24"/>'
        '<rect x="0" y="0" width="300" height="6" fill="#e50914"/>'
        '<text x="150" y="70" fill="#8a8a99" font-family="system-ui, sans-serif" '
        'font-size="15" letter-spacing="2" text-anchor="middle">NETFLIX TOP 10</text>'
        f'<text fill="#ececf1" font-family="system-ui, sans-serif" font-size="26" '
        f'font-weight="600" text-anchor="middle">{spans}</text>'
        "</svg>"
    )


def to_preview(item: dict) -> dict:
    meta = {
        "id": item.get("imdb_id") or item["id"],
        "type": item["type"],
        "name": item["title"],
    }
    if item.get("poster"):
        meta["poster"] = item["poster"]
    return meta


def to_meta(item: dict) -> dict:
    meta = to_preview(item)
    if item.get("description"):
        meta["description"] = item["description"]
    if item.get("poster"):
        meta["background"] = item["poster"]
    return meta


def render_index(updated_at: str, week: str, catalogs: dict) -> str:
    manifest_url = f"{BASE_URL}/manifest.json"
    install_url = manifest_url.replace("https://", "stremio://")
    sections = []
    for catalog_id, items in sorted(catalogs.items()):
        rows = "\n".join(
            f"<li><span>{item['rank']}</span>{item['title']}</li>" for item in items
        )
        sections.append(
            f"<section><h2>{CATALOG_NAMES.get(catalog_id, catalog_id)}</h2><ol>{rows}</ol></section>"
        )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Top Lists</title>
<style>
  body {{ font-family: system-ui, sans-serif; max-width: 46rem; margin: 3rem auto;
         padding: 0 1.25rem; line-height: 1.55; background: #14141a; color: #ececf1; }}
  a.install {{ display: inline-block; background: #e50914; color: #fff; padding: .7rem 1.3rem;
               border-radius: 6px; text-decoration: none; font-weight: 600; }}
  code {{ background: #24242e; padding: .15rem .4rem; border-radius: 4px; font-size: .9em; }}
  ol {{ padding-left: 0; list-style: none; }}
  li span {{ display: inline-block; width: 1.9rem; color: #8a8a99; }}
  section {{ margin-top: 2rem; }}
  p.meta {{ color: #8a8a99; font-size: .9rem; }}
</style>
</head>
<body>
<h1>Top Lists</h1>
<p>A Stremio add-on serving curated top lists from streaming services.</p>
<p><a class="install" href="{install_url}">Install in Stremio</a></p>
<p class="meta">Or paste this into Stremio's add-on search: <code>{manifest_url}</code></p>
<p class="meta">Netflix chart for the week ending <strong>{week}</strong>. Netflix publishes
this weekly, on Tuesdays, for the week ending the previous Sunday.</p>
<p class="meta">Last checked: {updated_at}</p>
{"".join(sections)}
</body>
</html>
"""


def main() -> int:
    if not CATALOG_FILE.exists():
        print(f"error: {CATALOG_FILE} not found; run the scraper first", file=sys.stderr)
        return 1

    data = json.loads(CATALOG_FILE.read_text(encoding="utf-8"))
    catalogs = data["catalogs"]
    updated_at = data["updated_at"]
    week = data["week"]

    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)

    manifest = dict(MANIFEST)
    manifest["description"] = (
        f"{MANIFEST['description']} Netflix chart for the week ending {week}."
    )
    write_json(OUTPUT_DIR / "manifest.json", manifest)

    placeholders = 0
    for items in catalogs.values():
        for item in items:
            if not item.get("poster"):
                name = f"{item['id']}.svg"
                path = OUTPUT_DIR / "poster" / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(placeholder_svg(item["title"]), encoding="utf-8")
                item["poster"] = f"{BASE_URL}/poster/{name}"
                placeholders += 1

    meta_count = 0
    for catalog_id, items in catalogs.items():
        catalog_type = CATALOG_TYPES[catalog_id]
        write_json(
            OUTPUT_DIR / "catalog" / catalog_type / f"{catalog_id}.json",
            {"metas": [to_preview(item) for item in items]},
        )
        for item in items:
            meta = to_meta(item)
            write_json(
                OUTPUT_DIR / "meta" / catalog_type / f"{meta['id']}.json",
                {"meta": meta},
            )
            meta_count += 1

    (OUTPUT_DIR / "index.html").write_text(
        render_index(updated_at, week, catalogs), encoding="utf-8"
    )

    print(
        f"built {OUTPUT_DIR}/: {len(catalogs)} catalogs, {meta_count} meta files, "
        f"{placeholders} generated posters"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
