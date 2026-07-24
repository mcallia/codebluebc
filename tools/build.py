#!/usr/bin/env python3
"""CodeBlue BC site builder.
Stitches tools/pages/*.html bodies into the shared shell (head, header, footer).
Usage:  python3 tools/build.py          # builds all pages into repo root
Each body file starts with:  <!--META {json} -->
META keys: title, desc, nav, js (list), css (list), bodyclass, og (image path)
"""
import json, re, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGES = ROOT / "tools" / "pages"

NAV = [
    ("home", "index.html", "Home"),
    ("emergency", "emergency.html", "The Emergency"),
    ("plan", "plan.html", "The Plan"),
    ("watch", "watch.html", "Water Watch"),
    ("news", "news.html", "News"),
    ("stories", "stories.html", "Stories"),
    ("movement", "movement.html", "The Movement"),
]

SITE_NAME = "CodeBlue BC"
TAGLINE = "Because water is life."
BASE = "https://mcallia.github.io/codebluebc/"  # deployed base URL (og tags, canonical)

def nav_html(current):
    links = []
    for key, href, label in NAV:
        cur = ' aria-current="page"' if key == current else ""
        links.append(f'<a href="{href}"{cur}>{label}</a>')
    links.append('<a class="nav-cta" href="action.html">Take Action</a>')
    return "\n      ".join(links)

def nav_mobile_html(current):
    links = []
    for key, href, label in NAV:
        cur = ' aria-current="page"' if key == current else ""
        links.append(f'<a href="{href}"{cur}>{label}</a>')
    links.append('<a class="nav-cta" href="action.html">Take Action</a>')
    return "\n    ".join(links)

HEAD = """<!DOCTYPE html>
<html lang="en-CA">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta property="og:site_name" content="CodeBlue BC">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="website">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{base}assets/img/{og}">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="{canonical}">
<meta name="theme-color" content="#081058">
<link rel="icon" type="image/png" sizes="32x32" href="assets/img/favicon-32.png">
<link rel="apple-touch-icon" href="assets/img/apple-touch-icon.png">
<link rel="preload" href="assets/fonts/archivo-1.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="assets/fonts/inter-1.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="css/fonts.css">
<link rel="stylesheet" href="css/site.css">
{extra_css}
</head>
<body class="{bodyclass}">
<a class="skip-link" href="#main">Skip to content</a>
<header class="site-header">
  <div class="header-bar">
    <a class="brand" href="index.html" aria-label="CodeBlue BC home">
      <img src="assets/img/mark.png" alt="" width="49" height="44">
      <span class="brand-word">CODE<span class="b">BLUE</span><span class="bc">BC</span></span>
    </a>
    <nav class="nav-desktop" aria-label="Primary">
      {nav}
    </nav>
    <button class="nav-toggle" aria-expanded="false" aria-label="Menu">
      <svg class="ic-burger" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.4" stroke-linecap="round"><path d="M3 6h18M3 12h18M3 18h18"/></svg>
      <svg class="ic-close" style="display:none" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.4" stroke-linecap="round"><path d="M5 5l14 14M19 5L5 19"/></svg>
    </button>
  </div>
</header>
<nav class="nav-mobile" aria-label="Mobile">
    {nav_mobile}
</nav>
<main id="main">
"""

FOOTER = """</main>
<footer class="site-footer">
  <div class="container">
    <div class="footer-grid">
      <div>
        <img class="footer-logo" src="assets/img/logo-light.png" alt="CodeBlue BC — Because water is life.">
        <p class="small" style="color:#9fc0d8">A citizens&rsquo; campaign to secure and sustain British Columbia&rsquo;s fresh water sources. Forever.</p>
        <div class="social">
          <a href="https://www.facebook.com/codebluebc" aria-label="CodeBlue BC on Facebook"><svg viewBox="0 0 24 24"><path d="M13.5 21v-8h2.7l.4-3.1h-3.1V7.9c0-.9.3-1.5 1.6-1.5h1.7V3.6c-.3 0-1.3-.1-2.5-.1-2.5 0-4.2 1.5-4.2 4.3v2.1H7.4V13h2.7v8h3.4z"/></svg></a>
          <a href="https://www.instagram.com/codebluebc/" aria-label="CodeBlue BC on Instagram"><svg viewBox="0 0 24 24"><path d="M12 2.2c3.2 0 3.6 0 4.9.1 1.2.1 1.8.2 2.2.4.6.2 1 .5 1.4.9.4.4.7.8.9 1.4.2.4.4 1 .4 2.2.1 1.3.1 1.7.1 4.9s0 3.6-.1 4.9c-.1 1.2-.2 1.8-.4 2.2-.2.6-.5 1-.9 1.4-.4.4-.8.7-1.4.9-.4.2-1 .4-2.2.4-1.3.1-1.7.1-4.9.1s-3.6 0-4.9-.1c-1.2-.1-1.8-.2-2.2-.4-.6-.2-1-.5-1.4-.9-.4-.4-.7-.8-.9-1.4-.2-.4-.4-1-.4-2.2-.1-1.3-.1-1.7-.1-4.9s0-3.6.1-4.9c.1-1.2.2-1.8.4-2.2.2-.6.5-1 .9-1.4.4-.4.8-.7 1.4-.9.4-.2 1-.4 2.2-.4 1.3-.1 1.7-.1 4.9-.1zm0 1.8c-3.1 0-3.5 0-4.8.1-1.1.1-1.5.2-1.9.3-.5.2-.8.4-1.1.7-.3.3-.5.6-.7 1.1-.1.4-.3.8-.3 1.9-.1 1.2-.1 1.6-.1 4.8s0 3.5.1 4.8c.1 1.1.2 1.5.3 1.9.2.5.4.8.7 1.1.3.3.6.5 1.1.7.4.1.8.3 1.9.3 1.2.1 1.6.1 4.8.1s3.5 0 4.8-.1c1.1-.1 1.5-.2 1.9-.3.5-.2.8-.4 1.1-.7.3-.3.5-.6.7-1.1.1-.4.3-.8.3-1.9.1-1.2.1-1.6.1-4.8s0-3.5-.1-4.8c-.1-1.1-.2-1.5-.3-1.9-.2-.5-.4-.8-.7-1.1-.3-.3-.6-.5-1.1-.7-.4-.1-.8-.3-1.9-.3-1.2-.1-1.6-.1-4.8-.1zm0 3.1a5 5 0 1 1 0 10 5 5 0 0 1 0-10zm0 8.2a3.2 3.2 0 1 0 0-6.4 3.2 3.2 0 0 0 0 6.4zm6.4-8.4a1.2 1.2 0 1 1-2.4 0 1.2 1.2 0 0 1 2.4 0z"/></svg></a>
        </div>
      </div>
      <div>
        <h4>Explore</h4>
        <a href="emergency.html">The Emergency</a><br>
        <a href="plan.html">The CodeBlue Plan</a><br>
        <a href="watch.html">Water Watch <span style="font-size:.7em; color:#ff5964">●</span> Live</a><br>
        <a href="news.html">News</a><br>
        <a href="stories.html">Stories</a><br>
        <a href="heroes.html">Watershed Heroes</a><br>
        <a href="podcast.html">The Freshwater Stream</a>
      </div>
      <div>
        <h4>Get Involved</h4>
        <a href="action.html">Take Action</a><br>
        <a href="https://www.codebluebc.ca/letterwriter">Send Your Message</a><br>
        <a href="https://www.codebluebc.ca/add-your-voice">Add Your Voice</a><br>
        <a href="https://www.codebluebc.ca/donate">Donate</a><br>
        <a href="movement.html">The Movement</a><br>
        <a href="about.html">About &amp; Contact</a>
      </div>
      <div>
        <h4>Powered By</h4>
        <div class="ww-credit">
          <img src="assets/img/ww-logo.png" alt="Watershed Watch Salmon Society">
          <span>CodeBlue BC is supported by <a href="https://watershedwatch.ca/">Watershed Watch Salmon Society</a> and allies across British Columbia.</span>
        </div>
        <p class="small" style="color:#7f9ab0; margin-top:1rem">Aligned with the <a href="https://watershedsecurity.ca/">BC Watershed Security Coalition</a> — 57+ organizations representing 285,000 British Columbians.</p>
      </div>
    </div>
    <div class="footer-fine">
      <span>© <span data-year>2026</span> CodeBlue BC · Because water is life.</span>
      <span>We acknowledge that this work takes place on the unceded territories of Indigenous nations throughout the lands and waters now called British Columbia.</span>
      <span><a href="about.html#credits">Photo credits</a></span>
    </div>
  </div>
</footer>
<script src="js/site.js"></script>
{extra_js}
</body>
</html>
"""

def build():
    built = []
    for body_file in sorted(PAGES.glob("*.html")):
        raw = body_file.read_text()
        m = re.match(r"\s*<!--META\s*(\{.*?\})\s*-->", raw, re.S)
        meta = json.loads(m.group(1)) if m else {}
        body = raw[m.end():] if m else raw
        title = meta.get("title", SITE_NAME)
        head = HEAD.format(
            title=title,
            desc=meta.get("desc", TAGLINE).replace('"', "&quot;"),
            og=meta.get("og", "hero-river.jpg"),
            base=BASE,
            canonical=BASE + ("" if body_file.name == "index.html" else body_file.name),
            bodyclass=meta.get("bodyclass", ""),
            nav=nav_html(meta.get("nav", "")),
            nav_mobile=nav_mobile_html(meta.get("nav", "")),
            extra_css="\n".join(f'<link rel="stylesheet" href="{c}">' for c in meta.get("css", [])),
        )
        footer = FOOTER.format(
            extra_js="\n".join(f'<script src="{j}"></script>' for j in meta.get("js", [])),
        )
        out = ROOT / body_file.name
        out.write_text(head + body.strip() + "\n" + footer)
        built.append(body_file.name)
    print(f"built {len(built)} pages: {', '.join(built)}")

if __name__ == "__main__":
    build()
