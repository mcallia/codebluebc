#!/usr/bin/env python3
"""Build the web edition straight from the Word file.

The Word document is the source of truth. Structure is recovered from
paragraph styles and run formatting laid down by the design system, so the
essay can be re-published after any round of edits in Word without hand
-porting changes back into a build script.
"""
import re, json, os, base64, io, zipfile, sys
from xml.etree import ElementTree as ET
from PIL import Image

DOCX = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/v15d.docx"
OUT = "/home/claude/webbuild/content.json"

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS = {"w": W, "r": R}
def q(t): return "{%s}%s" % (W, t)

zf = zipfile.ZipFile(DOCX)
root = ET.fromstring(zf.read("word/document.xml"))
body = root.find("w:body", NS)

rels = {}
for rel in ET.fromstring(zf.read("word/_rels/document.xml.rels")):
    rels[rel.get("Id")] = rel.get("Target")

# ── assets ───────────────────────────────────────────────────────────────
ASSETS, ASSET_IDS = {}, {}
def asset(part, max_w, quality):
    if part in ASSET_IDS:
        return ASSET_IDS[part]
    im = Image.open(io.BytesIO(zf.read(part)))
    if im.mode in ("RGBA", "LA", "P"):
        bg = Image.new("RGB", im.size, "white")
        im = im.convert("RGBA"); bg.paste(im, mask=im.split()[-1]); im = bg
    else:
        im = im.convert("RGB")
    if im.width > max_w:
        im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
    buf = io.BytesIO(); im.save(buf, "WEBP", quality=quality, method=6)
    aid = "a%02d" % len(ASSETS)
    ASSETS[aid] = "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()
    ASSET_IDS[part] = aid
    return aid

def imgpart(p):
    """the media part referenced by the first image in this paragraph"""
    for blip in p.iter("{http://schemas.openxmlformats.org/drawingml/2006/main}blip"):
        rid = blip.get("{%s}embed" % R)
        tgt = rels.get(rid)
        if tgt:
            return "word/" + tgt.lstrip("/")
    return None

# ── paragraph reading ────────────────────────────────────────────────────
def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def runs_html(p):
    """inner html for a paragraph, preserving bold / italic / superscript"""
    out = []
    for r in p.iter(q("r")):
        txt = "".join(t.text or "" for t in r.iter(q("t")))
        if not txt:
            if r.find(".//" + q("br")) is not None: out.append(" ")
            continue
        rPr = r.find("w:rPr", NS)
        b = i = sup = False
        if rPr is not None:
            b = rPr.find("w:b", NS) is not None and \
                rPr.find("w:b", NS).get(q("val")) not in ("false", "0")
            i = rPr.find("w:i", NS) is not None
            va = rPr.find("w:vertAlign", NS)
            sup = va is not None and va.get(q("val")) == "superscript"
        s = esc(txt)
        if sup: s = f"<sup>{s}</sup>"
        if b: s = f"<strong>{s}</strong>"
        if i: s = f"<em>{s}</em>"
        out.append(s)
    s = "".join(out)
    s = re.sub(r"</strong>(\s*)<strong>", r"\1", s)
    s = re.sub(r"</em>(\s*)<em>", r"\1", s)
    return re.sub(r"\s+", " ", s).strip()

def ptext(p):
    return re.sub(r"\s+", " ", "".join(t.text or "" for t in p.iter(q("t")))).strip()

def style(p):
    pPr = p.find("w:pPr", NS)
    if pPr is None: return None
    s = pPr.find("w:pStyle", NS)
    return s.get(q("val")) if s is not None else None

def sig(p):
    """(pStyle, font, halfpoint-size, colour) of the first text-bearing run"""
    st = style(p)
    for r in p.iter(q("r")):
        if not any(t.text for t in r.iter(q("t"))): continue
        rPr = r.find("w:rPr", NS)
        f = sz = col = None
        if rPr is not None:
            rf = rPr.find("w:rFonts", NS); f = rf.get(q("ascii")) if rf is not None else None
            s = rPr.find("w:sz", NS);      sz = s.get(q("val")) if s is not None else None
            c = rPr.find("w:color", NS);   col = c.get(q("val")) if c is not None else None
        return (st, f, sz, col)
    return (st, None, None, None)

def has_left_rule(p):
    """design.js gives notes a left hairline — the one reliable note marker"""
    pPr = p.find("w:pPr", NS)
    if pPr is None: return False
    bdr = pPr.find("w:pBdr", NS)
    return bdr is not None and bdr.find("w:left", NS) is not None

# ── walk ─────────────────────────────────────────────────────────────────
# Empty paragraphs carry the design's hairline rules and vertical air. They
# have no meaning on the web and would break every lookahead, so drop them.
kids = [c for c in body if c.tag == q("tbl")
        or (c.tag == q("p") and (
            "".join(t.text or "" for t in c.iter(q("t"))).strip() or imgpart(c)))]

MONO_SRC   = ("Courier New", "14", "7A8896")   # figure source / plate caption
FIGNO      = ("Courier New", "14", "3AA6DE")   # FIG. NN
FIGTITLE   = ("Arial", "22", None)
NUMERAL    = ("Arial", "200", "3AA6DE")
THESIS     = (None, "26", "7A8896")
KICKER_SZ  = ("Courier New", "20")

out, chapters = [], []
open_section = False
slug_n = [0]
def slug(s):
    slug_n[0] += 1
    base = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:40]
    return f"s{slug_n[0]}-{base}"

def close():
    global open_section
    if open_section:
        out.append("</section>")
        open_section = False

def cell_paras(tc):
    return [runs_html(p) for p in tc.findall("w:p", NS)]

# find the first real section head — everything before it is cover + TOC,
# which the web edition authors fresh
start = 0
for n, k in enumerate(kids):
    if k.tag == q("p") and style(k) in ("Heading1",) and ptext(k) == "About This Report":
        start = n; break

i = start
list_buf = []
def flush_list():
    if list_buf:
        out.append('<ol class="numlist">' + "".join(f"<li>{x}</li>" for x in list_buf) + "</ol>")
        list_buf.clear()

while i < len(kids):
    k = kids[i]

    # ── tables ───────────────────────────────────────────────────────────
    if k.tag == q("tbl"):
        flush_list()
        rows = k.findall("w:tr", NS)
        grid = [[cell_paras(tc) for tc in r.findall("w:tc", NS)] for r in rows]
        # a single row of numeral+label cells is a stat strip
        if len(grid) == 1 and all(len(c) >= 2 for c in grid[0]):
            items = "".join(
                f'<div class="stat"><span class="statnum">{c[0]}</span>'
                f'<span class="statlab">{" ".join(c[1:])}</span></div>' for c in grid[0])
            out.append(f'<div class="statrow">{items}</div>')
        else:
            hdr = [" ".join(c).strip() for c in grid[0]]
            trs = []
            for row in grid[1:]:
                tds = "".join(
                    f'<td data-l="{hdr[j].replace(chr(34), "&quot;") if j < len(hdr) else ""}">'
                    f'{" ".join(x for x in c if x)}</td>' for j, c in enumerate(row))
                trs.append(f"<tr>{tds}</tr>")
            out.append('<div class="tablewrap"><table><thead><tr>'
                       + "".join(f"<th>{h}</th>" for h in hdr)
                       + "</tr></thead><tbody>" + "".join(trs) + "</tbody></table></div>")
        i += 1; continue

    p = k
    st = style(p)
    s = sig(p)
    t = ptext(p)
    ipart = imgpart(p)

    # ── numbered list ────────────────────────────────────────────────────
    if st == "ListParagraph":
        html = runs_html(p)
        if ipart:
            aid = asset(ipart, 1200, 74)
            html += f'<span class="inlineplate"><img loading="lazy" data-a="{aid}" alt=""></span>'
        if html: list_buf.append(html)
        i += 1; continue
    flush_list()

    # ── chapter opener: kicker · numeral · title · thesis [· plate] ──────
    if s[1:] == NUMERAL and i + 2 < len(kids):
        kick = ptext(kids[i - 1]) if i else ""
        title_p = kids[i + 1]
        thesis_p = kids[i + 2] if i + 2 < len(kids) else None
        if style(title_p) == "Heading1":
            close()
            a = slug(ptext(title_p)); chapters.append((a, kick, ptext(title_p)))
            out.append(f'<section class="chapter" id="{a}">')
            open_section = True
            th = runs_html(thesis_p) if thesis_p is not None and sig(thesis_p)[1:] == THESIS else ""
            out.append('<div class="opener">'
                       f'<p class="kicker">{esc(kick)}</p>'
                       f'<p class="numeral" aria-hidden="true">{esc(t)}</p>'
                       f'<h2>{runs_html(title_p)}</h2>'
                       + (f'<p class="thesis">{th}</p>' if th else ""))
            step = 3 if th else 2
            nxt = kids[i + step] if i + step < len(kids) else None
            if nxt is not None and nxt.tag == q("p") and imgpart(nxt) and not ptext(nxt):
                aid = asset(imgpart(nxt), 1080, 70)
                out.append(f'<div class="openerplate"><img loading="lazy" data-a="{aid}" alt=""></div>')
                step += 1
            out.append("</div>")
            i += step; continue

    # ── section head (Heading1 at 40) ────────────────────────────────────
    if st == "Heading1" and s[2] == "40":
        close()
        kick = ptext(kids[i - 1]) if i and sig(kids[i - 1])[1:3] == KICKER_SZ else ""
        a = slug(t); chapters.append((a, kick, t))
        out.append(f'<section class="chapter" id="{a}">')
        open_section = True
        out.append('<div class="sectionhead">'
                   + (f'<p class="kicker">{esc(kick)}</p>' if kick else "")
                   + f"<h2>{runs_html(p)}</h2></div>")
        if ipart:                                  # a head that carries its own plate
            aid = asset(ipart, 1080, 70)
            out.append(f'<div class="openerplate"><img loading="lazy" data-a="{aid}" alt=""></div>')
        i += 1; continue

    if st == "Heading2":
        out.append(f"<h3>{runs_html(p)}</h3>"); i += 1; continue
    if st == "Heading3":
        out.append(f"<h4>{runs_html(p)}</h4>"); i += 1; continue

    # ── figure: FIG. NN · title · image · source ─────────────────────────
    if s[1:] == FIGNO and re.match(r"^FIG\.\s*\d+", t):
        num = re.sub(r"^FIG\.\s*", "", t)
        title = runs_html(kids[i + 1]) if i + 1 < len(kids) else ""
        j = i + 2
        while j < len(kids) and not imgpart(kids[j]) and j < i + 5: j += 1
        aid = asset(imgpart(kids[j]), 1500, 86) if j < len(kids) and imgpart(kids[j]) else None
        src = ""
        if j + 1 < len(kids) and sig(kids[j + 1])[1:] == MONO_SRC:
            src = runs_html(kids[j + 1]); j += 1
        out.append('<figure class="fig">'
                   f'<p class="figno">Fig. {esc(num)}</p>'
                   f'<h5 class="figtitle">{title}</h5>'
                   + (f'<div class="figscroll"><img loading="lazy" data-a="{aid}" '
                      f'alt="{re.sub(chr(60)+"[^"+chr(62)+"]*"+chr(62), "", title)}"></div>' if aid else "")
                   + '<p class="swipe">Swipe the chart to read it &rarr;</p>'
                   + (f"<figcaption>{src}</figcaption>" if src else "")
                   + "</figure>")
        i = j + 1; continue

    # ── plate: image followed by a mono caption ──────────────────────────
    if ipart and not t:
        cap = ""
        if i + 1 < len(kids) and kids[i + 1].tag == q("p") and sig(kids[i + 1])[1:] == MONO_SRC:
            cap = runs_html(kids[i + 1])
        aid = asset(ipart, 1400, 78)
        out.append('<figure class="plate">'
                   f'<img loading="lazy" data-a="{aid}" alt="">'
                   + (f"<figcaption>{cap}</figcaption>" if cap else "")
                   + "</figure>")
        i += 2 if cap else 1; continue

    # ── pull quote (oversized body run) ──────────────────────────────────
    if s[1] is None and s[2] == "27":
        cite = ""
        if i + 1 < len(kids) and sig(kids[i + 1])[1:3] == ("Courier New", "15"):
            cite = f"<cite>{runs_html(kids[i + 1])}</cite>"
        out.append(f'<blockquote class="pull"><p>{runs_html(p)}</p>{cite}</blockquote>')
        i += 2 if cite else 1; continue

    # ── note: a run of left-ruled paragraphs, mono label first ───────────
    if has_left_rule(p):
        j = i
        parts = []
        while j < len(kids) and kids[j].tag == q("p") and has_left_rule(kids[j]):
            parts.append(runs_html(kids[j])); j += 1
        label, rest = parts[0], parts[1:]
        out.append(f'<aside class="note"><p class="notelabel">{label}</p>'
                   + "".join(f"<p>{x}</p>" for x in rest) + "</aside>")
        i = j; continue

    # ── kicker line; skipped when an opener or section head will claim it ─
    if s[1] == "Courier New" and s[2] in ("20", "18"):
        nxt = kids[i + 1] if i + 1 < len(kids) else None
        claimed = nxt is not None and nxt.tag == q("p") and (
            sig(nxt)[1:] == NUMERAL or (style(nxt) == "Heading1" and sig(nxt)[2] == "40"))
        if t and not claimed:
            out.append(f'<p class="kicker">{esc(t)}</p>')
        i += 1; continue

    # ── mono footnote / credit line ──────────────────────────────────────
    if s[1] == "Courier New" and s[2] in ("16", "15", "14", "13"):
        if t: out.append(f'<p class="cred">{runs_html(p)}</p>')
        i += 1; continue

    # ── ordinary prose ───────────────────────────────────────────────────
    html = runs_html(p)
    if html:
        out.append(f"<p>{html}</p>")
    elif ipart:
        aid = asset(ipart, 1400, 78)
        out.append(f'<figure class="plate"><img loading="lazy" data-a="{aid}" alt=""></figure>')
    i += 1

flush_list()
close()

# ── cover + colophon furniture (authored fresh, not from the docx) ──────
def local(path, max_w, quality):
    if path in ASSET_IDS: return ASSET_IDS[path]
    im = Image.open(path)
    if im.mode in ("RGBA", "LA", "P"):
        bg = Image.new("RGB", im.size, "white"); im = im.convert("RGBA")
        bg.paste(im, mask=im.split()[-1]); im = bg
    else: im = im.convert("RGB")
    if im.width > max_w:
        im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
    buf = io.BytesIO(); im.save(buf, "WEBP", quality=quality, method=6)
    aid = "a%02d" % len(ASSETS)
    ASSETS[aid] = "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()
    ASSET_IDS[path] = aid
    return aid

P = "/home/claude/photos/"
json.dump({"body": "\n".join(out), "chapters": chapters, "assets": ASSETS,
           "cover":  local(P + "hero_wide.jpg", 1600, 80),
           "logo":   local(P + "logo_mcallister.png", 520, 90),
           "aapor":  local(P + "logo_aapor.png", 420, 90),
           "esomar": local(P + "logo_esomar.png", 420, 90)},
          open(OUT, "w"), ensure_ascii=False)

total = sum(len(v) for v in ASSETS.values())
print(f"{len(out)} blocks · {len(chapters)} chapters · {len(ASSETS)} assets "
      f"· {total/1e6:.2f} MB of data URIs")
