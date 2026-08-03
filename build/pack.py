#!/usr/bin/env python3
"""Assemble the encrypted single-file web edition."""
import json, os, base64, secrets, re
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

PASSWORD = "angus2026dataessay"
ITER = 310_000

C = json.load(open("/home/claude/webbuild/content.json"))

# ── the essay document (this whole string gets encrypted) ────────────────
nav = "".join(
    f'<a href="#{a}"><span class="nk">{k}</span><span class="nt">{t}</span></a>'
    for a, k, t in C["chapters"])

cover = f"""
<header class="cover" id="top">
  <p class="kicker cover-kicker">A McAllister Data Essay</p>
  <h1><span>Moving Forward</span><span class="w">on Fresh Water</span></h1>
  <p class="deck">What sixteen years of public-opinion research tells the BC watershed
  security campaign about how British Columbians think about their fresh water — and how
  to turn this drought summer into watershed security policy before Budget 2027.</p>
  <img class="hero" data-a="{C['cover']}" alt="">
  <div class="statrow cover-stats">
    <div class="stat"><span class="statnum">10</span><span class="statlab">studies</span></div>
    <div class="stat"><span class="statnum">16</span><span class="statlab">years of tracking</span></div>
    <div class="stat"><span class="statnum">2010–2026</span><span class="statlab">field period</span></div>
  </div>
  <p class="coverdeck">Public values around fresh water have been rock-steady for over a
  decade. What moved — fast, and only recently — is the ground underneath them. Here is
  what that buys us, where we are still weak, and what must be done to move forward.</p>
  <p class="logoline"><img class="logo" data-a="{C['logo']}" alt="McAllister Opinion Research"></p>
  <p class="coverdate">August 1, 2026</p>
</header>
<nav class="toc" aria-label="Contents">
  <p class="kicker">Contents</p>
  <div class="tocgrid">{nav}</div>
</nav>
"""

colophon = f"""
<footer class="colophon">
  <p class="logoline"><img class="logo" data-a="{C['logo']}" alt=""></p>
  <p class="mono">Prepared under the direction of Angus McAllister · McAllister Opinion
  Research · August 1, 2026</p>
  <p class="mono dim">Moving Forward on Fresh Water · A McAllister Data Essay · Sixteen
  years of tracking British Columbian public opinion, 2010–2026</p>
  <p class="mono dim">Confidential — for the campaign team and its advisers.</p>
</footer>
"""

DOC = cover + '<main class="essay">' + C["body"] + "</main>" + colophon

# AAPOR / ESOMAR marks sit in About This Report
DOC = DOC.replace(
    "<p>Who. ",
    f'<p class="creds"><img class="cred" data-a="{C["aapor"]}" alt="AAPOR">'
    f'<img class="cred" data-a="{C["esomar"]}" alt="ESOMAR"></p><p>Who. ', 1)

PAYLOAD = json.dumps({"doc": DOC, "assets": C["assets"]}, ensure_ascii=False)

# ── encrypt ──────────────────────────────────────────────────────────────
salt, iv = secrets.token_bytes(16), secrets.token_bytes(12)
key = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt,
                 iterations=ITER).derive(PASSWORD.encode())
ct = AESGCM(key).encrypt(iv, PAYLOAD.encode("utf-8"), None)
b64 = lambda x: base64.b64encode(x).decode()
print(f"payload {len(PAYLOAD)/1e6:.2f} MB → ciphertext {len(ct)/1e6:.2f} MB")

CSS = r"""
:root{
  --ink:#12233F; --water:#3AA6DE; --clay:#C4643C; --graphite:#7A8896;
  --hair:#D8DFE5; --mist:#F4F7F9; --paper:#FFFFFF;
  --display:"Helvetica Neue",Helvetica,Arial,sans-serif;
  --body:Charter,Cambria,Georgia,"Times New Roman",serif;
  --mono:ui-monospace,"SF Mono",Menlo,Consolas,"Courier New",monospace;
  --measure:34rem;
  --wide:min(72rem,100% - 3rem);
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%;scroll-behavior:smooth}
@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}
  *{animation:none!important;transition:none!important}}
body{margin:0;background:var(--paper);color:var(--ink);
  font-family:var(--body);font-size:clamp(1rem,.96rem + .25vw,1.11rem);
  line-height:1.72;-webkit-font-smoothing:antialiased}
img{max-width:100%;height:auto;display:block}

/* ── gate ─────────────────────────────────────────────── */
#gate{min-height:100svh;display:grid;place-items:center;padding:2rem}
.gatecard{width:min(30rem,100%)}
.gatecard .rule{border-top:2px solid var(--ink);margin:0 0 .9rem}
.gatecard h1{font-family:var(--display);font-weight:700;letter-spacing:-.03em;
  font-size:clamp(2rem,1.4rem + 2.6vw,3rem);line-height:1.04;margin:.2rem 0 1rem}
.gatecard h1 .w{color:var(--water);display:block}
.gatecard p{color:var(--graphite);font-size:.95rem;margin:0 0 1.5rem}
.field{display:flex;gap:.5rem;flex-wrap:wrap}
input[type=password]{flex:1 1 12rem;min-width:0;font-family:var(--mono);font-size:1rem;
  padding:.8rem .9rem;border:1px solid var(--hair);border-radius:2px;color:var(--ink);
  background:var(--mist)}
input[type=password]:focus{outline:2px solid var(--water);outline-offset:1px}
button{font-family:var(--mono);font-size:.78rem;letter-spacing:.14em;text-transform:uppercase;
  padding:.85rem 1.4rem;border:0;border-radius:2px;background:var(--ink);color:#fff;cursor:pointer}
button:hover{background:var(--water)}
button[disabled]{opacity:.55;cursor:progress}
#msg{margin:.9rem 0 0;font-family:var(--mono);font-size:.78rem;letter-spacing:.06em;
  min-height:1.2em;color:var(--clay)}
.gatefoot{margin-top:2.4rem;border-top:1px solid var(--hair);padding-top:.9rem}
.gatefoot img{width:150px;opacity:.9}

/* ── chrome ───────────────────────────────────────────── */
#doc{display:none}
#bar{position:fixed;inset:0 0 auto;z-index:40;background:rgba(255,255,255,.93);
  backdrop-filter:blur(8px);border-bottom:1px solid var(--hair)}
#bar .inner{width:var(--wide);margin:0 auto;display:flex;align-items:center;gap:1rem;
  height:44px;font-family:var(--mono);font-size:.66rem;letter-spacing:.12em;
  text-transform:uppercase;color:var(--graphite)}
#bar .t{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
#bar .spacer{flex:1}
#bar button{background:none;color:var(--ink);border:1px solid var(--hair);padding:.3rem .6rem;
  font-size:.66rem}
#prog{position:absolute;left:0;bottom:-1px;height:2px;background:var(--water);width:0}
#drawer{position:fixed;inset:44px 0 auto;z-index:39;background:#fff;
  border-bottom:1px solid var(--hair);display:none;max-height:70svh;overflow:auto}
#drawer.open{display:block}
#drawer .tocgrid{width:var(--wide);margin:0 auto;padding:1.4rem 0 1.8rem}

/* ── layout ───────────────────────────────────────────── */
.essay,.cover,.toc,.colophon{width:var(--wide);margin-inline:auto}
.essay>section>p,.essay>section>ol,.essay>section>ul,
.essay h3,.essay h4,.cover .deck,.cover .coverdeck,.colophon p{max-width:var(--measure)}
.essay>section>p{margin:0 0 1.15em}

/* ── cover ────────────────────────────────────────────── */
.cover{padding:5.5rem 0 3rem}
.kicker{font-family:var(--mono);font-size:.68rem;letter-spacing:.24em;text-transform:uppercase;
  color:var(--water);margin:0 0 1.1rem}
.cover-kicker{border-top:3px solid var(--ink);padding-top:.85rem}
.cover h1{font-family:var(--display);font-weight:700;letter-spacing:-.035em;line-height:.98;
  font-size:clamp(2.6rem,1.3rem + 6vw,6rem);margin:0 0 1.4rem}
.cover h1 span{display:block}
.cover h1 .w{color:var(--water)}
.deck{font-size:clamp(1.05rem,1rem + .4vw,1.3rem);line-height:1.55;margin:0 0 2rem;
  padding-top:1.4rem;border-top:1px solid var(--hair)}
.hero{width:100%;margin:0 0 1.8rem}
.coverdeck{color:var(--graphite);margin:1.6rem 0 2.4rem}
.logoline{margin:0 0 .5rem}
.logo{width:190px}
.coverdate{font-family:var(--mono);font-size:.74rem;letter-spacing:.14em;color:var(--graphite);
  margin:0;padding-top:.8rem;border-top:1px solid var(--hair)}
.creds{display:flex;gap:1.4rem;align-items:center;margin:1.2rem 0 1.4rem}
.cred{height:34px;width:auto}

/* ── contents ─────────────────────────────────────────── */
.toc{padding:2.5rem 0 1rem;border-top:3px solid var(--ink)}
.tocgrid{display:grid;gap:.15rem;grid-template-columns:repeat(auto-fill,minmax(15rem,1fr))}
.tocgrid a{display:block;padding:.55rem 0;border-bottom:1px solid var(--hair);
  text-decoration:none;color:var(--ink)}
.tocgrid a:hover{background:var(--mist)}
.nk{display:block;font-family:var(--mono);font-size:.6rem;letter-spacing:.18em;
  text-transform:uppercase;color:var(--graphite)}
.nt{display:block;font-family:var(--display);font-weight:600;font-size:.94rem;
  letter-spacing:-.01em;line-height:1.3;margin-top:.15rem}

/* ── chapters ─────────────────────────────────────────── */
.chapter{padding:3.2rem 0 1rem;scroll-margin-top:60px}
.opener{padding:2rem 0 2.6rem;border-top:3px solid var(--ink);margin-bottom:2rem}
.opener .numeral{font-family:var(--display);font-weight:700;color:var(--water);
  font-size:clamp(5rem,3rem + 12vw,11rem);line-height:.82;letter-spacing:-.06em;
  margin:.6rem 0 1.2rem;border-bottom:1px solid var(--hair);padding-bottom:1.2rem}
.opener h2{font-family:var(--display);font-weight:700;letter-spacing:-.03em;line-height:1.06;
  font-size:clamp(1.7rem,1.2rem + 2.2vw,2.9rem);margin:0 0 1rem;max-width:22ch}
.opener .thesis{color:var(--graphite);font-size:clamp(1.02rem,.98rem + .4vw,1.25rem);
  line-height:1.55;margin:0;max-width:44ch}
.sectionhead{padding:1.4rem 0 1.6rem;border-top:3px solid var(--ink);margin-bottom:1.6rem}
.sectionhead h2{font-family:var(--display);font-weight:700;letter-spacing:-.03em;
  font-size:clamp(1.55rem,1.2rem + 1.6vw,2.4rem);line-height:1.1;margin:0}
h3{font-family:var(--display);font-weight:700;letter-spacing:-.02em;
  font-size:clamp(1.15rem,1.05rem + .55vw,1.45rem);line-height:1.25;
  margin:2.6rem 0 .9rem;padding-top:1rem;border-top:1px solid var(--hair)}
h4{font-family:var(--display);font-weight:700;color:var(--water);letter-spacing:-.01em;
  font-size:1.02rem;margin:2rem 0 .7rem}
strong{font-weight:700}
em{font-style:italic}

/* ── figures ──────────────────────────────────────────── */
.fig{margin:2.4rem 0 2.6rem;padding-top:.7rem;border-top:2px solid var(--ink)}
.figno{font-family:var(--mono);font-size:.64rem;letter-spacing:.22em;text-transform:uppercase;
  color:var(--water);margin:0 0 .3rem}
.figtitle{font-family:var(--display);font-weight:700;letter-spacing:-.02em;
  font-size:clamp(1.02rem,.98rem + .35vw,1.22rem);line-height:1.3;margin:0 0 .9rem;
  max-width:44ch}
.figscroll{overflow-x:auto;-webkit-overflow-scrolling:touch}
.fig img{width:100%}
.swipe{display:none;font-family:var(--mono);font-size:.6rem;letter-spacing:.16em;text-transform:uppercase;color:var(--graphite);margin:.45rem 0 0}
.fig figcaption,.plate figcaption{font-family:var(--mono);font-size:.68rem;line-height:1.65;
  color:var(--graphite);margin-top:.6rem;max-width:60ch}
.fig figcaption{padding-bottom:.8rem;border-bottom:1px solid var(--hair)}
.openerplate{margin:2.2rem 0 0}
.openerplate img{width:100%;display:block;border-radius:2px}
.plate{margin:2.4rem 0 2.6rem}
.plate img{width:100%}

/* ── quotes, notes, stats ─────────────────────────────── */
.pull{margin:2.6rem 0;padding:1.3rem 0;border-top:2px solid var(--ink);
  border-bottom:2px solid var(--ink)}
.pull p{font-family:var(--body);font-size:clamp(1.2rem,1.05rem + .8vw,1.65rem);
  line-height:1.42;margin:0;max-width:34ch}
.pull cite{display:block;font-family:var(--mono);font-style:normal;font-size:.7rem;
  color:var(--graphite);margin-top:.8rem;letter-spacing:.04em}
.note{margin:1.8rem 0;padding:.2rem 0 .2rem 1.1rem;border-left:3px solid var(--water);
  max-width:calc(var(--measure) + 1.1rem)}
.notelabel{font-family:var(--mono);font-size:.66rem;letter-spacing:.2em;text-transform:uppercase;
  color:var(--water);margin:0 0 .35rem}
.note p{margin:0}
.statrow{display:grid;gap:1.2rem;grid-template-columns:repeat(auto-fit,minmax(11rem,1fr));
  margin:2rem 0;padding:1.3rem 0;border-top:2px solid var(--ink);border-bottom:2px solid var(--ink)}
.statnum{display:block;font-family:var(--display);font-weight:700;letter-spacing:-.045em;
  font-size:clamp(2.1rem,1.5rem + 2.4vw,3.3rem);line-height:1}
.statlab{display:block;font-family:var(--mono);font-size:.66rem;line-height:1.5;
  color:var(--graphite);margin-top:.45rem}
.cover-stats{margin:0 0 .4rem}

/* ── lists ────────────────────────────────────────────── */
.numlist{counter-reset:n;list-style:none;padding:0;margin:1.4rem 0 1.8rem}
.numlist li{counter-increment:n;position:relative;padding-left:2.6rem;margin-bottom:1.1rem}
.numlist li::before{content:counter(n);position:absolute;left:0;top:.12em;
  font-family:var(--mono);font-weight:700;font-size:.86rem;color:var(--water)}
ul.numlist li::before{content:"—"}

/* ── tables ───────────────────────────────────────────── */
.tablewrap{margin:1.8rem 0 2.2rem;overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:.86rem;line-height:1.5}
thead th{font-family:var(--mono);font-size:.6rem;letter-spacing:.14em;text-transform:uppercase;
  color:var(--graphite);text-align:left;font-weight:400;padding:.6rem .9rem .6rem 0;
  border-top:2px solid var(--ink);border-bottom:1px solid var(--hair);vertical-align:bottom}
tbody td{padding:.75rem .9rem .75rem 0;border-bottom:1px solid var(--hair);vertical-align:top}
tbody tr:last-child td{border-bottom:2px solid var(--ink)}
tbody td:first-child{font-weight:700}

/* ── colophon ─────────────────────────────────────────── */
.colophon{padding:3rem 0 5rem;margin-top:2.5rem;border-top:3px solid var(--ink)}
.mono{font-family:var(--mono);font-size:.72rem;line-height:1.7;color:var(--graphite);margin:.4rem 0}
.dim{color:#9AA7B4}

@media (max-width:760px){
  :root{--wide:calc(100% - 2.2rem)}
  .cover{padding:4.5rem 0 2rem}
  .tablewrap table{min-width:34rem}
  .fig,.plate,.openerplate{margin-left:-1.1rem;margin-right:-1.1rem}
  .fig>*:not(.figscroll),.plate>figcaption{padding-left:1.1rem;padding-right:1.1rem}
  .figscroll{padding:0 1.1rem}
  .figscroll img{min-width:40rem;width:40rem;max-width:none}
  .swipe{display:block;padding-left:1.1rem}
}
@media print{
  #bar,#drawer,#gate{display:none!important}
  #doc{display:block!important}
  .chapter{break-inside:auto}
  .opener,.fig,.plate,.pull,.statrow{break-inside:avoid}
}
"""

JS = r"""
const $=s=>document.querySelector(s);
const b64d=s=>Uint8Array.from(atob(s),c=>c.charCodeAt(0));
const D={s:"__SALT__",i:"__IV__",c:"__CT__",n:__ITER__};

async function unlock(pw){
  const enc=new TextEncoder();
  const base=await crypto.subtle.importKey("raw",enc.encode(pw),"PBKDF2",false,["deriveKey"]);
  const key=await crypto.subtle.deriveKey(
    {name:"PBKDF2",salt:b64d(D.s),iterations:D.n,hash:"SHA-256"},
    base,{name:"AES-GCM",length:256},false,["decrypt"]);
  const plain=await crypto.subtle.decrypt({name:"AES-GCM",iv:b64d(D.i)},key,b64d(D.c));
  return JSON.parse(new TextDecoder().decode(plain));
}

function render(payload){
  const doc=$("#doc");
  doc.innerHTML=payload.doc;
  doc.querySelectorAll("img[data-a]").forEach(im=>{
    const u=payload.assets[im.dataset.a]; if(u) im.src=u;
  });
  $("#gate").remove();
  doc.style.display="block";
  document.title="Moving Forward on Fresh Water — A McAllister Data Essay";
  $("#bar").style.display="block";
  wireChrome();
  try{sessionStorage.setItem("mf-ok","1")}catch(e){}
}

function wireChrome(){
  const bar=$("#bar"), prog=$("#prog"), label=$("#bar .t"), drawer=$("#drawer");
  const secs=[...document.querySelectorAll(".chapter")];
  const nav=document.querySelector(".toc .tocgrid");
  if(nav) drawer.innerHTML='<div class="tocgrid">'+nav.innerHTML+'</div>';
  drawer.querySelectorAll("a").forEach(a=>a.addEventListener("click",()=>drawer.classList.remove("open")));
  $("#menu").addEventListener("click",()=>drawer.classList.toggle("open"));
  const onScroll=()=>{
    const h=document.documentElement;
    const p=h.scrollTop/Math.max(1,h.scrollHeight-h.clientHeight);
    prog.style.width=(p*100).toFixed(2)+"%";
    let cur=null;
    for(const s of secs){ if(s.getBoundingClientRect().top<=90) cur=s; }
    if(cur){
      const k=cur.querySelector(".kicker"), t=cur.querySelector("h2");
      label.textContent=k?k.textContent:(t?t.textContent:"");
    } else label.textContent="Moving Forward on Fresh Water";
  };
  addEventListener("scroll",onScroll,{passive:true}); onScroll();
}

addEventListener("DOMContentLoaded",()=>{
  const form=$("#gateform"), pw=$("#pw"), msg=$("#msg"), btn=$("#go");
  form.addEventListener("submit",async e=>{
    e.preventDefault();
    btn.disabled=true; msg.style.color="var(--graphite)"; msg.textContent="Decrypting…";
    try{
      const payload=await unlock(pw.value.trim());
      msg.textContent="";
      render(payload);
    }catch(err){
      msg.style.color="var(--clay)";
      msg.textContent="That password doesn't open this document.";
      btn.disabled=false; pw.select();
    }
  });
  pw.focus();
});
"""

JS = (JS.replace("__SALT__", b64(salt)).replace("__IV__", b64(iv))
        .replace("__CT__", b64(ct)).replace("__ITER__", str(ITER)))

HTML = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Protected document — McAllister Opinion Research</title>
<meta name="robots" content="noindex,nofollow,noarchive">
<meta name="referrer" content="no-referrer">
<meta name="description" content="Password-protected research document.">
<meta name="theme-color" content="#12233F">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' fill='%2312233F'/%3E%3Cpath d='M16 6c4 6 7 9.5 7 13a7 7 0 0 1-14 0c0-3.5 3-7 7-13z' fill='%233AA6DE'/%3E%3C/svg%3E">
<style>{CSS}</style>
</head>
<body>

<div id="bar" style="display:none">
  <div class="inner">
    <span class="t">Moving Forward on Fresh Water</span>
    <span class="spacer"></span>
    <button id="menu" type="button" aria-label="Contents">Contents</button>
  </div>
  <div id="prog"></div>
</div>
<div id="drawer" aria-label="Contents"></div>

<div id="gate">
  <div class="gatecard">
    <p class="rule"></p>
    <p class="kicker">A McAllister Data Essay · Confidential</p>
    <h1><span>Moving Forward</span><span class="w">on Fresh Water</span></h1>
    <p>Sixteen years of public-opinion research on fresh water in British Columbia.
       This document is encrypted. Enter the password you were given to read it.</p>
    <form id="gateform" autocomplete="off">
      <div class="field">
        <input id="pw" type="password" placeholder="Password" aria-label="Password"
               autocomplete="current-password" spellcheck="false">
        <button id="go" type="submit">Unlock</button>
      </div>
      <p id="msg" role="status" aria-live="polite"></p>
    </form>
    <div class="gatefoot">
      <img data-logo alt="McAllister Opinion Research">
      <p class="mono dim">Prepared under the direction of Angus McAllister ·
      McAllister Opinion Research · August 1, 2026</p>
    </div>
  </div>
</div>

<div id="doc"></div>

<script>
document.querySelector("[data-logo]").src="{C['assets'][C['logo']]}";
{JS}
</script>
</body>
</html>
"""

out = "/home/claude/webbuild/essay.html"
open(out, "w", encoding="utf-8").write(HTML)
print(f"wrote {out} · {os.path.getsize(out)/1e6:.2f} MB")
