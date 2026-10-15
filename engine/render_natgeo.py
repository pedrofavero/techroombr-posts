#!/usr/bin/env python3
"""
Renderizador — The Tech Room (v3)
Uso: python3 engine/render_natgeo.py posts/<slug>/post.json [...]
Saída: posts/<slug>/01.png … NN.png, legenda.txt, _prancha.jpg

POST: slug, categoria, masthead, handle, slides[], legenda,
      theme ("dark" padrão: tom escuro extraído da foto da capa | "paper": papel claro | "night": azul-noite),
      display ("sans" padrão Montserrat | "serif": Playfair Display nos títulos e números),
      accent (opcional, cor fixa; senão extraída da foto da capa).
Cada slide pode sobrescrever: theme, display, bg (foto para páginas nítidas), top (true = conteúdo alinhado ao topo).

TIPOS DE PÁGINA
  cover     photo, title, dek, [swipe]
  inner     kicker, heading, [photo, caption] (foto nítida, texto embaixo), body[], [lead], [bullets[]], [check[]], [nocheck[]], [example{tag,text[]}]
  stat      kicker, big, [unit], label, body[]
  split     kicker, heading, cells[2 de {big, unit?, label, text}], body[]
  chart     kicker, heading, bars[{name,value,label,other?}], note, body[]
  dchart    kicker, heading, rows[{name,value(-100..100),label,lo?,hi?}], scale (ex. 40 = ±40%), note, body[]   (barras divergentes)
  timeline  kicker, heading, items[{when,what}], body[]
  steps     kicker, heading, steps[{title,text}], body[]
  compare   kicker, heading, a{title,lines[]}, b{title,lines[]}, body[]
  quote     kicker, text, who, body[]
  card      kicker, heading, rows[{k,v}], body[]
  meter     kicker, heading, total, filled, on_label, off_label, body[]
  diagram   kicker, heading, svg (string SVG com viewBox; use currentColor e var(--accent)), caption, body[]
  custom    html (HTML cru dentro da área de conteúdo), [mode: soft|sharp]
  sources   items[{who,what}]
Texto nos corpos aceita **negrito** e ==destaque== (cor de destaque).
"""
import base64, colorsys, json, mimetypes, re, sys
from html import escape
from pathlib import Path
from playwright.sync_api import sync_playwright
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
TPL = (ROOT / "engine" / "natgeo.html").read_text(encoding="utf-8")

def path(p):
    p = Path(p); return p if p.is_absolute() else ROOT / p

def uri(p):
    p = path(p); mime = mimetypes.guess_type(p.name)[0] or "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(p.read_bytes()).decode()}"

# ---------- cor ----------
def dominant_hue(photo):
    im = Image.open(path(photo)).convert("RGB").resize((80, 80))
    best, score = (31, 78, 121), -1
    for cnt, (r, g, b) in im.getcolors(80 * 80):
        h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
        sc = cnt * (s ** 1.5) * (1 - abs(l - .45))
        if s > .25 and .15 < l < .75 and sc > score:
            best, score = (r, g, b), sc
    return colorsys.rgb_to_hls(*[c / 255 for c in best])

def hexl(h, l, s):
    r, g, b = colorsys.hls_to_rgb(h, l, s); return "#%02x%02x%02x" % (int(r * 255), int(g * 255), int(b * 255))

def theme_vars(theme, hue, accent=None):
    h, _, s = hue
    if theme == "paper":
        v = dict(bg_top="#F6F3EC", bg_bottom="#EDE8DD", ink="#141414", mute="#6A6660", mute2="#3A3835",
                 rule="rgba(0,0,0,.14)", rule2="rgba(0,0,0,.22)", accent=accent or hexl(h, .36, min(max(s, .5), .8)))
    elif theme == "night":
        v = dict(bg_top="#111A2B", bg_bottom="#070C16", ink="#FFFFFF", mute="rgba(255,255,255,.72)", mute2="rgba(255,255,255,.86)",
                 rule="rgba(255,255,255,.2)", rule2="rgba(255,255,255,.35)", accent=accent or hexl(h, .74, min(max(s, .45), .7)))
    else:  # dark: tom da foto
        v = dict(bg_top=hexl(h, .20, .28), bg_bottom=hexl(h, .13, .30), ink="#FFFFFF", mute="rgba(255,255,255,.72)", mute2="rgba(255,255,255,.86)",
                 rule="rgba(255,255,255,.2)", rule2="rgba(255,255,255,.35)", accent=accent or hexl(h, .74, min(max(s, .45), .7)))
    return "; ".join(f"--{k.replace('_','-')}: {val}" for k, val in v.items())

# ---------- texto ----------
def rich(t):
    t = escape(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"==(.+?)==", r"<mark>\1</mark>", t)
    return t

def P(lines, cls=""):
    c = f' class="{cls}"' if cls else ""
    return "".join(f"<p{c}>{rich(t)}</p>" for t in lines or [])
def K(s): return f'<div class="kicker">{escape(s["kicker"])}</div>' if s.get("kicker") else ""
def H(s): return f'<h2>{rich(s["heading"])}</h2>' if s.get("heading") else ""

def frame(post, s, body, mode="soft", cls=""):
    """mode 'sharp' = foto nítida com texto no terço inferior; 'soft' = página de tema."""
    theme = s.get("theme", post.get("theme", "dark"))
    serif = (s.get("display", post.get("display", "sans")) == "serif")
    style = theme_vars(theme, post["_hue"], post.get("accent"))
    cap = f'<div class="cap">{escape(s["caption"])}</div>' if mode == "sharp" and s.get("caption") else ""
    bg = f'<div class="bg" style="background-image:url(\'{uri(s.get("photo") or s.get("bg") or post["_cover_photo"])}\')"></div><div class="scrim"></div>' if mode == "sharp" else ""
    top = " top" if s.get("top") else ""
    pageno = f'<div class="pageno">{post["_n"]:02d} / {post["_total"]:02d}</div>' if post.get("pageno", True) else ""
    return (f'<div class="page {mode}{top} {cls}{" serif" if serif else ""}" style="{style}">{bg}'
            f'<div class="masthead">{escape(post["masthead"])}</div>{cap}<div class="content">{body}</div>'
            f'{pageno}<div class="handle">{escape(post["handle"])}</div></div>')

# ---------- páginas ----------
def cover(s, post):
    serif = (s.get("display", post.get("display", "sans")) == "serif")
    swipe = f'<div class="swipe">{escape(s["swipe"])}</div>' if s.get("swipe") else ""
    return (f'<div class="page sharp cover{" serif" if serif else ""}" style="{theme_vars("dark", post["_hue"])}">'
            f'<div class="bg" style="background-image:url(\'{uri(s["photo"])}\')"></div><div class="scrim"></div>'
            f'<div class="masthead">{escape(post["masthead"])}</div>'
            f'<div class="text"><h1>{rich(s["title"])}</h1><div class="dek">{rich(s.get("dek",""))}</div></div>{swipe}'
            f'<div class="handle">{escape(post["handle"])}</div></div>')

def inner(s, post):
    parts = [K(s), H(s), P(s.get("lead") and [s["lead"]], "lead"), P(s.get("body"))]
    if s.get("bullets"): parts.append("<ul class='list'>" + "".join(f"<li>{rich(t)}</li>" for t in s["bullets"]) + "</ul>")
    if s.get("check"): parts.append("<ul class='check'>" + "".join(f"<li>{rich(t)}</li>" for t in s["check"]) + "</ul>")
    if s.get("nocheck"): parts.append("<ul class='check no'>" + "".join(f"<li>{rich(t)}</li>" for t in s["nocheck"]) + "</ul>")
    if s.get("example"):
        e = s["example"]; parts.append(f'<div class="example"><div class="tag">{escape(e.get("tag","Exemplo"))}</div>{P(e.get("text"))}</div>')
    parts.append(P(s.get("after")))
    mode = "sharp" if s.get("photo") else "soft"
    return frame(post, s, "".join(parts), mode)

def stat(s, post):
    unit = f'<small>{escape(s["unit"])}</small>' if s.get("unit") else ""
    return frame(post, s, K(s) + H(s) + f'<div class="big">{escape(str(s["big"]))}{unit}</div><div class="label">{rich(s.get("label",""))}</div>' + P(s.get("body")), "soft", "stat")

def split(s, post):
    cells = ""
    for i, c in enumerate(s["cells"][:2]):
        unit = f'<small>{escape(c["unit"])}</small>' if c.get("unit") else ""
        cells += (f'<div class="cell {"a" if i == 0 else "b"}"><div class="big">{escape(str(c["big"]))}{unit}</div>'
                  f'<div class="label">{rich(c.get("label",""))}</div><div class="text">{rich(c.get("text",""))}</div></div>')
    return frame(post, s, K(s) + H(s) + f'<div class="split">{cells}</div>' + P(s.get("body")))

def chart(s, post):
    bars = s["bars"]; mx = max(b["value"] for b in bars) or 1
    rows = "".join(
        f'<div class="row{" other" if b.get("other") else ""}"><div class="name">{rich(b["name"])}</div>'
        f'<div><div class="bar" style="width:{max(2, b["value"] / mx * 100):.1f}%"></div></div>'
        f'<div class="val">{escape(b.get("label", str(b["value"])))}</div></div>' for b in bars)
    note = f'<div class="note">{rich(s["note"])}</div>' if s.get("note") else ""
    return frame(post, s, K(s) + H(s) + f'<div class="chart">{rows}{note}</div>' + P(s.get("body")))

def dchart(s, post):
    sc = float(s.get("scale", 50)); half = 50.0
    rows = ""
    for r in s["rows"]:
        v = float(r["value"]); w = min(abs(v) / sc * half, half)
        cls = "neg" if v < 0 else "pos"
        bar = f'<div class="bar {cls}" style="width:{w:.1f}%"></div>'
        ci = ""
        if r.get("lo") is not None and r.get("hi") is not None:
            l = half + max(-sc, float(r["lo"])) / sc * half; h = half + min(sc, float(r["hi"])) / sc * half
            ci = f'<div class="ci" style="left:{l:.1f}%;width:{max(0.5, h - l):.1f}%"></div>'
        pos = f'left:{half:.1f}%' if v >= 0 else f'right:{half:.1f}%'
        val = f'<div class="val" style="{pos}">{escape(r.get("label", str(r["value"])))}</div>'
        rows += f'<div class="row"><div class="name">{rich(r["name"])}</div><div class="track">{bar}{ci}{val}</div></div>'
    axis = f'<div class="axis"><div></div><div><span>{escape(s.get("left", f"−{int(sc)}%"))}</span><span>0</span><span>{escape(s.get("right", f"+{int(sc)}%"))}</span></div></div>'
    note = f'<div class="note">{rich(s["note"])}</div>' if s.get("note") else ""
    return frame(post, s, K(s) + H(s) + f'<div class="dchart">{rows}{axis}{note}</div>' + P(s.get("body")))

def timeline(s, post):
    items = "".join(f'<div class="item"><div class="when">{escape(i["when"])}</div><div class="what">{rich(i["what"])}</div></div>' for i in s["items"])
    return frame(post, s, K(s) + H(s) + f'<div class="timeline">{items}</div>' + P(s.get("body")))

def steps(s, post):
    st = "".join(f'<div class="step"><div class="n">{n}</div><div><div class="t">{rich(i["title"])}</div><div class="d">{rich(i["text"])}</div></div></div>' for n, i in enumerate(s["steps"], 1))
    return frame(post, s, K(s) + H(s) + f'<div class="steps">{st}</div>' + P(s.get("body")))

def compare(s, post):
    def col(c, cls): return f'<div class="col {cls}"><h3>{rich(c["title"])}</h3>{P(c.get("lines"))}</div>'
    return frame(post, s, K(s) + H(s) + f'<div class="compare">{col(s["a"], "a")}{col(s["b"], "b")}</div>' + P(s.get("body")))

def quote(s, post):
    who = f'<div class="who">{escape(s["who"])}</div>' if s.get("who") else ""
    return frame(post, s, K(s) + f'<div class="q">{rich(s["text"])}</div>{who}' + P(s.get("body")), "soft", "quote")

def card(s, post):
    rows = "".join(f'<div class="row"><div class="k">{escape(r["k"])}</div><div class="v">{rich(r["v"])}</div></div>' for r in s["rows"])
    return frame(post, s, K(s) + H(s) + f'<div class="card">{rows}</div>' + P(s.get("body")))

def meter(s, post):
    total, filled = int(s.get("total", 100)), int(s["filled"])
    dots = "".join(f'<i class="{"on" if i < filled else ""}"></i>' for i in range(total))
    leg = f'<div class="legend"><span><i class="on"></i>{escape(s.get("on_label",""))}</span><span><i></i>{escape(s.get("off_label",""))}</span></div>'
    return frame(post, s, K(s) + H(s) + f'<div class="meter"><div class="dots">{dots}</div>{leg}</div>' + P(s.get("body")))

def diagram(s, post):
    cap = f'<div class="cap">{rich(s["caption"])}</div>' if s.get("caption") else ""
    return frame(post, s, K(s) + H(s) + f'<div class="diagram">{s["svg"]}{cap}</div>' + P(s.get("body")))

def custom(s, post):
    return frame(post, s, s["html"], s.get("mode", "soft"))

def sources(s, post):
    items = "".join(f'<li>{escape(i["who"])}<span>{escape(i.get("what",""))}</span></li>' for i in s["items"])
    return frame(post, s, '<div class="kicker">Fontes</div><ul>' + items + '</ul>', "soft", "sources")

B = dict(cover=cover, inner=inner, stat=stat, split=split, chart=chart, dchart=dchart, timeline=timeline, steps=steps,
         compare=compare, quote=quote, card=card, meter=meter, diagram=diagram, custom=custom, sources=sources)

def prancha(pngs, dest):
    th = [Image.open(p).convert("RGB").resize((360, 450)) for p in pngs]
    cols = min(3, len(th)); rows = -(-len(th) // cols)
    sheet = Image.new("RGB", (cols * 360 + (cols + 1) * 12, rows * 450 + (rows + 1) * 12), "#E5E5E5")
    for i, im in enumerate(th):
        sheet.paste(im, (12 + (i % cols) * 372, 12 + (i // cols) * 462))
    sheet.save(dest, quality=88)

def main(paths):
    with sync_playwright() as p:
        br = p.chromium.launch()
        for pth in paths:
            post = json.loads(Path(pth).read_text(encoding="utf-8"))
            post.setdefault("masthead", "The Tech Room"); post.setdefault("handle", "@techroombr")
            cov = next((s for s in post["slides"] if s["type"] == "cover"), None)
            post["_cover_photo"] = cov["photo"] if cov else None
            post["_hue"] = dominant_hue(cov["photo"]) if cov else (0.58, .45, .5)
            post["_total"] = len(post["slides"])
            out = ROOT / "posts" / post["slug"]; out.mkdir(parents=True, exist_ok=True)
            pg = br.new_page(viewport={"width": 1080, "height": 1350})
            pngs = []
            for n, s in enumerate(post["slides"], 1):
                post["_n"] = n
                pg.set_content(TPL.replace("<!-- CONTENT -->", B[s["type"]](s, post)), wait_until="load")
                pg.wait_for_timeout(150)
                f = out / f"{n:02d}.png"; pg.screenshot(path=str(f)); pngs.append(f)
                box = pg.evaluate("(()=>{const c=document.querySelector('.content');if(!c)return null;const r=c.getBoundingClientRect();const k=c.lastElementChild?c.lastElementChild.getBoundingClientRect().bottom:r.bottom;return [r.top,k]})()")
                if box and (box[0] < 130 or box[1] > 1235): print(f"  AVISO: página {n} estourou (topo {int(box[0])}px / base {int(box[1])}px) — reduzir texto")
                print(f"  {f.relative_to(ROOT)}")
            pg.close()
            if post.get("legenda"):
                (out / "legenda.txt").write_text(post["legenda"], encoding="utf-8")
            prancha(pngs, out / "_prancha.jpg")
            print(f"  tema {post.get('theme','dark')} · hue {post['_hue'][0]:.2f}")
        br.close()

if __name__ == "__main__":
    main(sys.argv[1:])
