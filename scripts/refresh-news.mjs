#!/usr/bin/env node
/**
 * CodeBlue BC — news feed refresher.
 * Merges: BC Watershed Security Coalition RSS + Google News (B.C. water search)
 * into data/news.json, preserving hand-curated CodeBlue entries.
 * No dependencies; runs on Node 18+.
 */
import { readFileSync, writeFileSync } from "node:fs";

const NEWS_PATH = new URL("../data/news.json", import.meta.url);
const UA = { headers: { "User-Agent": "CodeBlueBC-site/1.0 (+https://github.com)" } };

function decode(s = "") {
  return s
    .replace(/<!\[CDATA\[(.*?)\]\]>/gs, "$1")
    .replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"').replace(/&#0?39;/g, "'").replace(/&apos;/g, "'")
    .replace(/&nbsp;/g, " ").trim();
}

function parseRss(xml) {
  const items = [];
  const blocks = xml.match(/<item[\s\S]*?<\/item>/g) || [];
  for (const b of blocks) {
    const pick = (tag) => {
      const m = b.match(new RegExp(`<${tag}[^>]*>([\\s\\S]*?)</${tag}>`, "i"));
      return m ? decode(m[1]) : "";
    };
    const title = pick("title");
    const link = pick("link");
    const pub = pick("pubDate");
    if (!title || !link) continue;
    let date = "";
    const d = new Date(pub);
    if (!isNaN(d)) date = d.toISOString().slice(0, 10);
    items.push({ title, url: link, date });
  }
  return items;
}

async function fetchText(url) {
  const res = await fetch(url, UA);
  if (!res.ok) throw new Error(`${res.status} ${url}`);
  return res.text();
}

async function main() {
  const current = JSON.parse(readFileSync(NEWS_PATH, "utf8"));
  const keep = (current.items || []).filter((i) => i.cat === "codeblue"); // hand-curated
  const merged = [...keep];
  const seen = new Set(keep.map((i) => i.url));

  // 1. Coalition RSS
  try {
    const xml = await fetchText("https://watershedsecurity.ca/feed/");
    for (const it of parseRss(xml).slice(0, 8)) {
      if (seen.has(it.url)) continue;
      seen.add(it.url);
      merged.push({ cat: "coalition", source: "BC Watershed Security Coalition", ...it });
    }
    console.log("coalition feed OK");
  } catch (e) {
    console.warn("coalition feed failed:", e.message);
    for (const i of (current.items || []).filter((x) => x.cat === "coalition")) {
      if (!seen.has(i.url)) { seen.add(i.url); merged.push(i); }
    }
  }

  // 2. Google News — B.C. water stories
  try {
    const q = encodeURIComponent('"British Columbia" (watershed OR drought OR "water restrictions" OR "fresh water" OR snowpack)');
    const xml = await fetchText(`https://news.google.com/rss/search?q=${q}&hl=en-CA&gl=CA&ceid=CA:en`);
    for (const it of parseRss(xml).slice(0, 12)) {
      if (seen.has(it.url)) continue;
      seen.add(it.url);
      const srcMatch = it.title.match(/ - ([^-]+)$/);
      merged.push({
        cat: "media",
        source: srcMatch ? srcMatch[1].trim() : "News",
        ...it,
        title: srcMatch ? it.title.slice(0, it.title.lastIndexOf(" - ")) : it.title
      });
    }
    console.log("google news OK");
  } catch (e) {
    console.warn("google news failed:", e.message);
    for (const i of (current.items || []).filter((x) => x.cat === "media")) {
      if (!seen.has(i.url)) { seen.add(i.url); merged.push(i); }
    }
  }

  merged.sort((a, b) => (b.date || "").localeCompare(a.date || ""));
  const out = {
    updated: new Date().toISOString(),
    note: current.note,
    items: merged.slice(0, 40)
  };
  writeFileSync(NEWS_PATH, JSON.stringify(out, null, 1) + "\n");
  console.log(`wrote ${out.items.length} items`);
}

main().catch((e) => { console.error(e); process.exit(1); });
