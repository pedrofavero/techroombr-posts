#!/usr/bin/env python3
"""
Renderizador NatGeo — The Tech Room
Uso: python3 engine/render_natgeo.py posts/xx.json
Foto é a página. Texto mínimo. Sem artifício.
"""
import base64, json, mimetypes, sys
from html import escape
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
TPL = (ROOT / "engine" / "natgeo.html").read_text(encoding="utf-8")

def uri(p):
    p = Path(p); p = p if p.is_absolute() else ROOT / p
    mime = mimetypes.guess_type(p.name)[0] or "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(p.read_bytes()).decode()}"

def cover(s, post):
    return f'''
<div class="page cover">
  <div class="photo" style="background-image:url('{uri(s["photo"])}')"></div>
  <div class="masthead">{escape(post["masthead"])}</div>
  <div class="text">
    <h1>{escape(s["title"])}</h1>
    <div class="dek">{escape(s.get("dek",""))}</div>
  </div>
  <div class="handle">{escape(post["handle"])}</div>
</div>'''

def inner(s, post):
    fig = f'<div class="fig" style="background-image:url(\'{uri(s["photo"])}\')"></div>' if s.get("photo") else ""
    cap = f'<div class="cap">{escape(s["caption"])}</div>' if s.get("caption") else ""
    body = "".join(f"<p>{escape(t)}</p>" for t in s.get("body", []))
    kicker = f'<div class="kicker">{escape(s["kicker"])}</div>' if s.get("kicker") else ""
    return f'''
<div class="page inner">
  <div class="masthead">{escape(post["masthead"])}</div>
  {kicker}
  <h2>{escape(s["heading"])}</h2>
  {fig}{cap}
  {body}
  <div class="handle">{escape(post["handle"])}</div>
</div>'''

def sources(s, post):
    items = "".join(f'<li>{escape(i["who"])}<span>{escape(i.get("what",""))}</span></li>' for i in s["items"])
    return f'''
<div class="page sources">
  <div class="masthead">{escape(post["masthead"])}</div>
  <div class="kicker">Fontes</div>
  <ul>{items}</ul>
  <div class="handle">{escape(post["handle"])}</div>
</div>'''

B = {"cover": cover, "inner": inner, "sources": sources}

def main(paths):
    with sync_playwright() as p:
        br = p.chromium.launch()
        for path in paths:
            post = json.loads(Path(path).read_text(encoding="utf-8"))
            post.setdefault("masthead", "The Tech Room"); post.setdefault("handle", "@techroombr")
            out = ROOT / "posts" / post["slug"]; out.mkdir(parents=True, exist_ok=True)
            pg = br.new_page(viewport={"width": 1080, "height": 1350})
            pngs = []
            for n, s in enumerate(post["slides"], 1):
                pg.set_content(TPL.replace("<!-- CONTENT -->", B[s["type"]](s, post)), wait_until="load")
                pg.wait_for_timeout(150)
                f = out / f"{n:02d}.png"; pg.screenshot(path=str(f)); pngs.append(f)
                print(f"  {f.relative_to(ROOT)}")
            pg.close()
            if post.get("legenda"):
                (out / "legenda.txt").write_text(post["legenda"], encoding="utf-8")
            prancha(pngs, out / "_prancha.jpg")
        br.close()

def prancha(pngs, dest):
    """Prancha de conferência: todas as páginas lado a lado, reduzidas."""
    from PIL import Image
    th = [Image.open(p).convert("RGB").resize((360, 450)) for p in pngs]
    cols = min(3, len(th)); rows = -(-len(th) // cols)
    sheet = Image.new("RGB", (cols * 360 + (cols + 1) * 12, rows * 450 + (rows + 1) * 12), "#E5E5E5")
    for i, im in enumerate(th):
        sheet.paste(im, (12 + (i % cols) * 372, 12 + (i // cols) * 462))
    sheet.save(dest, quality=88)

if __name__ == "__main__":
    main(sys.argv[1:])
