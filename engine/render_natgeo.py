#!/usr/bin/env python3
"""
Renderizador NatGeo — The Tech Room
Uso: python3 engine/render_natgeo.py posts/<slug>/post.json [...]
Saída: posts/<slug>/01.png … NN.png, legenda.txt, _prancha.jpg

Tipos de página (campo "type"):
  cover     photo, title, dek
  inner     kicker, heading, [photo, caption], body[], [bullets[]], [example{tag,text[]}]
  stat      kicker, heading?, big, unit?, label, body[]
  chart     kicker, heading, bars[{name,value,label?,other?}], note?, body[]
  timeline  kicker, heading, items[{when,what}], body[]
  steps     kicker, heading, steps[{title,text}], body[]
  compare   kicker, heading, a{title,lines[]}, b{title,lines[]}, body[]
  sources   items[{who,what}]
A cor de destaque (--accent) é extraída da foto da capa; pode ser fixada em post["accent"].
"""
import base64, colorsys, json, mimetypes, sys
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

def accent_from(photo):
    """Cor dominante saturada da foto, clareada para destacar sobre fundo escuro."""
    im = Image.open(path(photo)).convert("RGB").resize((80, 80))
    best, score = (31, 78, 121), -1
    for cnt, (r, g, b) in im.getcolors(80 * 80):
        h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
        sc = cnt * (s ** 1.5) * (1 - abs(l - .45))
        if s > .25 and .15 < l < .75 and sc > score:
            best, score = (r, g, b), sc
    h, l, s = colorsys.rgb_to_hls(*[c / 255 for c in best])
    l = max(min(l, .78), .68); s = min(max(s, .45), .7)
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return "#%02x%02x%02x" % (int(r * 255), int(g * 255), int(b * 255))

# ---------- blocos ----------
def P(lines): return "".join(f"<p>{escape(t)}</p>" for t in lines or [])
def K(s): return f'<div class="kicker">{escape(s["kicker"])}</div>' if s.get("kicker") else ""
def H(s): return f'<h2>{escape(s["heading"])}</h2>' if s.get("heading") else ""
def frame(post, s, body, mode="soft", cls=""):
    """mode: 'sharp' (foto nítida, texto embaixo) ou 'soft' (foto desfocada, texto na área toda)."""
    bg = s.get("bg") or s.get("photo") or post["_cover_photo"]
    cap = f'<div class="cap">{escape(s["caption"])}</div>' if mode == "sharp" and s.get("caption") else ""
    return (f'<div class="page {mode} {cls}"><div class="bg" style="background-image:url(\'{uri(bg)}\')"></div><div class="scrim"></div>'
            f'<div class="masthead">{escape(post["masthead"])}</div>{cap}<div class="content">{body}</div>'
            f'<div class="handle">{escape(post["handle"])}</div></div>')

def cover(s, post):
    return f'''<div class="page sharp cover"><div class="bg" style="background-image:url('{uri(s["photo"])}')"></div><div class="scrim"></div>
  <div class="masthead">{escape(post["masthead"])}</div>
  <div class="text"><h1>{escape(s["title"])}</h1><div class="dek">{escape(s.get("dek",""))}</div></div>
  <div class="handle">{escape(post["handle"])}</div></div>'''

def inner(s, post):
    ul = ("<ul class='list'>" + "".join(f"<li>{escape(t)}</li>" for t in s["bullets"]) + "</ul>") if s.get("bullets") else ""
    ex = ""
    if s.get("example"):
        e = s["example"]
        ex = f'<div class="example"><div class="tag">{escape(e.get("tag","Exemplo"))}</div>{P(e.get("text"))}</div>'
    mode = "sharp" if s.get("photo") and not s.get("bullets") and not s.get("example") else "soft"
    return frame(post, s, K(s) + H(s) + P(s.get("body")) + ul + ex + P(s.get("after")), mode)

def stat(s, post):
    unit = f'<small>{escape(s["unit"])}</small>' if s.get("unit") else ""
    return frame(post, s, K(s) + H(s) + f'<div class="big">{escape(s["big"])}{unit}</div><div class="label">{escape(s.get("label",""))}</div>' + P(s.get("body")), "soft", "stat")

def chart(s, post):
    bars = s["bars"]; mx = max(b["value"] for b in bars) or 1
    rows = "".join(
        f'<div class="row{" other" if b.get("other") else ""}"><div class="name">{escape(b["name"])}</div>'
        f'<div><div class="bar" style="width:{max(2, b["value"] / mx * 100):.1f}%"></div></div>'
        f'<div class="val">{escape(b.get("label", str(b["value"])))}</div></div>' for b in bars)
    note = f'<div class="note">{escape(s["note"])}</div>' if s.get("note") else ""
    return frame(post, s, K(s) + H(s) + f'<div class="chart">{rows}{note}</div>' + P(s.get("body")))

def timeline(s, post):
    items = "".join(f'<div class="item"><div class="when">{escape(i["when"])}</div><div class="what">{escape(i["what"])}</div></div>' for i in s["items"])
    return frame(post, s, K(s) + H(s) + f'<div class="timeline">{items}</div>' + P(s.get("body")))

def steps(s, post):
    st = "".join(f'<div class="step"><div class="n">{n}</div><div><div class="t">{escape(i["title"])}</div><div class="d">{escape(i["text"])}</div></div></div>' for n, i in enumerate(s["steps"], 1))
    return frame(post, s, K(s) + H(s) + f'<div class="steps">{st}</div>' + P(s.get("body")))

def compare(s, post):
    def col(c, cls): return f'<div class="col {cls}"><h3>{escape(c["title"])}</h3>{P(c.get("lines"))}</div>'
    return frame(post, s, K(s) + H(s) + f'<div class="compare">{col(s["a"], "a")}{col(s["b"], "b")}</div>' + P(s.get("body")))

def sources(s, post):
    items = "".join(f'<li>{escape(i["who"])}<span>{escape(i.get("what",""))}</span></li>' for i in s["items"])
    return frame(post, s, '<div class="kicker">Fontes</div><ul>' + items + '</ul>', "soft", "sources")

B = {"cover": cover, "inner": inner, "stat": stat, "chart": chart, "timeline": timeline, "steps": steps, "compare": compare, "sources": sources}

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
            accent = post.get("accent") or (accent_from(cov["photo"]) if cov else "#1F4E79")
            tpl = TPL.replace("--accent: #9CC8E8", f"--accent: {accent}")
            out = ROOT / "posts" / post["slug"]; out.mkdir(parents=True, exist_ok=True)
            pg = br.new_page(viewport={"width": 1080, "height": 1350})
            pngs = []
            for n, s in enumerate(post["slides"], 1):
                pg.set_content(tpl.replace("<!-- CONTENT -->", B[s["type"]](s, post)), wait_until="load")
                pg.wait_for_timeout(150)
                f = out / f"{n:02d}.png"; pg.screenshot(path=str(f)); pngs.append(f)
                # alerta de estouro: conteúdo maior que a página
                box = pg.evaluate("(()=>{const c=document.querySelector('.content');if(!c)return null;const r=c.getBoundingClientRect();const k=c.lastElementChild?c.lastElementChild.getBoundingClientRect().bottom:r.bottom;return [r.top,k]})()")
                if box and (box[0] < 130 or box[1] > 1235): print(f"  AVISO: página {n} estourou (topo {int(box[0])}px / base {int(box[1])}px) — reduzir texto")
                print(f"  {f.relative_to(ROOT)}")
            pg.close()
            if post.get("legenda"):
                (out / "legenda.txt").write_text(post["legenda"], encoding="utf-8")
            prancha(pngs, out / "_prancha.jpg")
            print(f"  accent {accent}")
        br.close()

if __name__ == "__main__":
    main(sys.argv[1:])
