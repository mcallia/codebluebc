# CodeBlue BC — Website Redesign Prototype

A ground-up redesign of [codebluebc.ca](https://www.codebluebc.ca/) — same logo, same brand
colours, same campaign content, completely new experience. Built as a static site: no CMS, no
build step required to host it, works on GitHub Pages or any web host.

**Because water is life.**

## What's new vs. the current site

- **A visual narrative.** The site is built on the campaign's own metaphor — a hospital *code
  blue* — with the logo's EKG heartbeat line as the recurring visual spine.
- **A scrollytelling explainer** (`emergency.html`): the state of B.C.'s waters told as a
  patient chart, with a sticky pulse monitor that degrades and recovers as you scroll.
- **Live data** (`watch.html` + homepage tiles): current drought levels by basin (interactive
  map), real-time river flows with sparklines, Indigenous-led water scarcity assessments and
  snow basin indices — all read client-side from public government feeds. No API keys.
- **An auto-refreshing newsroom** (`news.html`): a GitHub Action refreshes `data/news.json`
  every 6 hours from the Coalition's RSS feed and Google News.
- **Coalition content woven in** (`movement.html` and throughout): the BC Watershed Security
  Coalition's 2026 asks, stats and latest releases.
- **Sourced numbers.** Every statistic links to a public source (2024 Freshwater Insights
  poll, Coalition reports, news coverage). See the Sources accordion on the Emergency page.
- Mobile-first, self-hosted fonts, no trackers, accessible (reduced-motion support, alt text,
  keyboard nav, colour palettes validated for colour-blind separation).

## Structure

```
index.html            Home
emergency.html        The Emergency — scrollytelling explainer
plan.html             The CodeBlue Plan
watch.html            Water Watch — live dashboard
news.html             Newsroom (auto-refreshing) + curated clipping file
stories.html          Stories index (links to originals)
heroes.html           Watershed Heroes
podcast.html          The Freshwater Stream
movement.html         The Movement (Coalition)
action.html           Take Action
about.html            About + photo credits
404.html              Not found
css/site.css          Design system (all styling)
css/fonts.css         Self-hosted font faces
js/site.js            Shared behaviour (nav, reveals, pulse bar, home live tiles)
js/watch.js           Dashboard feeds (drought map, gauges, scarcity, snow)
js/news.js            Newsroom rendering + filters
data/news.json        News feed (auto-refreshed by GitHub Action)
scripts/refresh-news.mjs      Feed refresher (no dependencies, Node 18+)
.github/workflows/refresh-news.yml   Scheduled refresh (every 6h)
tools/build.py        Page builder (stitches tools/pages/* into the shared shell)
tools/pages/*.html    Page bodies (edit these, then run the builder)
assets/img            Logo, favicons, photography (credits in about.html)
```

## Editing

Quick fix: edit the built `*.html` files directly — they're plain HTML.

Proper edit: change the page body in `tools/pages/<page>.html` (or the shared header/footer in
`tools/build.py`), then:

```bash
python3 tools/build.py
```

Local preview:

```bash
python3 -m http.server 8000
# open http://localhost:8000
```

## Live data feeds (all public, CORS-enabled, keyless)

| Panel | Source |
|---|---|
| Drought levels map | B.C. Drought Information Portal ArcGIS layer (`BC_Current_Drought_Levels`) |
| Water scarcity assessments | B.C. Water Scarcity ArcGIS layer (incl. Indigenous-led assessments) |
| River flows | ECCC `api.weather.gc.ca` hydrometric-realtime (stations listed in `js/watch.js`) |
| Snow basin index | B.C. River Forecast Centre ArcGIS layer (seasonal) |
| News | Coalition RSS + Google News via scheduled GitHub Action |

Each panel fails soft: if a feed is down, the site says so instead of showing stale numbers.

## Licensing notes

- CodeBlue BC logo and campaign photography © CodeBlue BC / Watershed Watch Salmon Society.
- Additional photography: Wikimedia Commons under CC licences — full attribution in
  `about.html#credits` (required if imagery is reused elsewhere).
- Fonts: Archivo, Inter, IBM Plex Mono (SIL Open Font License, self-hosted).
- Map tiles: © OpenStreetMap contributors & CARTO.

## Status

This is a **redesign prototype for partner review** — not yet the production site. The letter
tool, signup form and donation links point to the existing NationBuilder tools, so every
call-to-action works today. Cutover would mean pointing the codebluebc.ca domain here (or
porting the design into NationBuilder) and wiring the forms natively.

## Protected research documents

Two encrypted, unlisted pages live in the repo root. They are **not** linked from the site,
not in `sitemap.xml`, and carry `noindex` — but they *are* deliberately left crawlable so the
`noindex` can actually be read (a `robots.txt` Disallow would hide the tag and can leave a
bare URL indexed).

| File | Document | Unlock |
|---|---|---|
| `2026-codeblue-16-year-insights.html` | 2026 CodeBlue 16 Year Insights (StaticCrypt) | shared password |
| `moving-forward-on-fresh-water.html` | Moving Forward on Fresh Water — A McAllister Data Essay | shared password |

Each is a single self-contained file. The document body, all charts and all photography are
AES-256-GCM ciphertext; the key is derived in the browser with PBKDF2-SHA256 (310,000
iterations) from the password. Nothing readable ships in the page source, so a wrong password
returns nothing rather than hiding something. Rebuild pipeline for the data essay lives outside
this repo (`webbuild/convert.py` + `webbuild/pack.py` in the authoring session).

**These are share-with-a-link documents, not secrets.** Anyone holding the link and the
password can read and forward the file. Rotate the password by regenerating the page.
